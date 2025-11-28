"""
Kafka Consumer Service for processing document messages
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import threading

from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings

# Import AI service (adjust based on your actual AI service)
from app.services.rag_service import get_rag_service
from app.services.langchain_ingestion_service import LangChainIngestionService

# Configure logging with detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)


class KafkaDocumentConsumer:
    """Kafka consumer for processing document messages"""
    
    def __init__(self):
        """Initialize Kafka consumer"""
        self.consumer = None
        self.running = False
        self.thread = None
        
        # MongoDB connection
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.database_name]
        
        # Initialize services
        self.ingestion_service = LangChainIngestionService()
        
        # Kafka configuration
        self.kafka_config = {
            'bootstrap_servers': getattr(settings, 'kafka_bootstrap_servers', 'localhost:9092'),
            'group_id': getattr(settings, 'kafka_consumer_group', 'doc_processor_group'),
            'auto_offset_reset': 'latest',
            'enable_auto_commit': True,
            'value_deserializer': lambda m: json.loads(m.decode('utf-8')) if m else None,
            'key_deserializer': lambda m: m.decode('utf-8') if m else None,
            'max_poll_records': 10,
            'session_timeout_ms': 30000,
            'heartbeat_interval_ms': 10000,
        }
        
        self.topic = getattr(settings, 'kafka_document_topic', 'doc_document')
        
        logger.info(f"📋 Kafka Consumer initialized with config:")
        logger.info(f"   - Bootstrap servers: {self.kafka_config['bootstrap_servers']}")
        logger.info(f"   - Group ID: {self.kafka_config['group_id']}")
        logger.info(f"   - Topic: {self.topic}")
    
    def start(self):
        """Start the Kafka consumer in a separate thread"""
        if self.running:
            logger.warning("⚠️ Kafka consumer is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_consumer, daemon=True)
        self.thread.start()
        logger.info("✅ Kafka consumer thread started")
    
    def stop(self):
        """Stop the Kafka consumer"""
        logger.info("🛑 Stopping Kafka consumer...")
        self.running = False
        
        if self.consumer:
            self.consumer.close()
            
        if self.thread:
            self.thread.join(timeout=5)
            
        logger.info("✅ Kafka consumer stopped")
    
    def _run_consumer(self):
        """Run the consumer loop in a separate thread"""
        try:
            logger.info(f"🚀 Starting Kafka consumer for topic: {self.topic}")
            
            # Create consumer
            self.consumer = KafkaConsumer(
                self.topic,
                **self.kafka_config
            )
            
            logger.info(f"✅ Successfully subscribed to topic: {self.topic}")
            logger.info("👂 Listening for messages...")
            
            # Message counter for debugging
            message_count = 0
            
            while self.running:
                try:
                    # Poll for messages
                    messages = self.consumer.poll(timeout_ms=1000)
                    
                    if messages:
                        logger.debug(f"📨 Received {sum(len(msgs) for msgs in messages.values())} messages")
                        
                        for topic_partition, msgs in messages.items():
                            for message in msgs:
                                message_count += 1
                                logger.info(f"📩 Message #{message_count} received:")
                                logger.info(f"   - Topic: {message.topic}")
                                logger.info(f"   - Partition: {message.partition}")
                                logger.info(f"   - Offset: {message.offset}")
                                logger.info(f"   - Key: {message.key}")
                                logger.info(f"   - Timestamp: {datetime.fromtimestamp(message.timestamp/1000)}")
                                
                                # Process the message
                                asyncio.run(self._process_message(message))
                    
                except KafkaError as e:
                    logger.error(f"❌ Kafka error: {e}")
                    
                except Exception as e:
                    logger.error(f"❌ Unexpected error in consumer loop: {e}", exc_info=True)
                    
        except Exception as e:
            logger.error(f"❌ Failed to start Kafka consumer: {e}", exc_info=True)
            
        finally:
            if self.consumer:
                self.consumer.close()
                logger.info("✅ Kafka consumer connection closed")
    
    async def _process_message(self, message):
        """Process a single document message"""
        try:
            logger.info("🔄 Processing document message...")
            
            # Extract message value
            if not message.value:
                logger.warning("⚠️ Empty message value, skipping")
                return
            
            doc_data = message.value
            logger.debug(f"📄 Document data: {json.dumps(doc_data, indent=2)}")
            
            # Extract document information
            doc_id = doc_data.get('document_id') or doc_data.get('id')
            doc_type = doc_data.get('type', 'unknown')
            doc_content = doc_data.get('content', '')
            doc_metadata = doc_data.get('metadata', {})
            
            logger.info(f"📝 Processing document:")
            logger.info(f"   - ID: {doc_id}")
            logger.info(f"   - Type: {doc_type}")
            logger.info(f"   - Content length: {len(doc_content)} chars")
            logger.info(f"   - Metadata keys: {list(doc_metadata.keys())}")
            
            # Check if document exists in database
            existing_doc = await self.db.knowledge_base_items.find_one({
                "_id": doc_id
            }) if doc_id else None
            
            if existing_doc:
                logger.info(f"📚 Found existing document in database: {existing_doc.get('title', 'Untitled')}")
                
                # Trigger AI service processing
                await self._trigger_ai_processing(existing_doc)
            else:
                logger.warning(f"⚠️ Document {doc_id} not found in database")
                
                # Optionally create new document
                if doc_content:
                    logger.info("📥 Creating new document in database...")
                    await self._create_document(doc_data)
            
            logger.info("✅ Message processing completed")
            
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}", exc_info=True)
    
    async def _trigger_ai_processing(self, document: Dict[str, Any]):
        """Trigger AI service to process the document"""
        try:
            logger.info("🤖 Triggering AI service processing...")
            logger.info(f"   - Document ID: {document.get('_id')}")
            logger.info(f"   - Title: {document.get('title')}")
            logger.info(f"   - Status: {document.get('indexing_status')}")
            
            # Check if already processed
            if document.get('indexing_status') == 'completed':
                logger.info("✅ Document already indexed, skipping AI processing")
                return
            
            # Update status to processing
            await self.db.knowledge_base_items.update_one(
                {"_id": document["_id"]},
                {"$set": {
                    "indexing_status": "processing",
                    "ai_processing_started_at": datetime.utcnow()
                }}
            )
            logger.info("📊 Updated document status to 'processing'")
            
            # Trigger ingestion service
            logger.info("🔧 Starting document ingestion...")
            result = await self.ingestion_service.ingest_document(
                str(document["_id"])
            )
            
            if result.get("success"):
                logger.info(f"✅ AI processing successful:")
                logger.info(f"   - Chunks created: {result.get('chunks_created', 0)}")
                logger.info(f"   - Embeddings generated: {result.get('embeddings_generated', False)}")
                logger.info(f"   - Processing time: {result.get('processing_time', 0):.2f}s")
                
                # Update status to completed
                await self.db.knowledge_base_items.update_one(
                    {"_id": document["_id"]},
                    {"$set": {
                        "indexing_status": "completed",
                        "ai_processing_completed_at": datetime.utcnow(),
                        "ai_processing_result": result
                    }}
                )
            else:
                logger.error(f"❌ AI processing failed: {result.get('error', 'Unknown error')}")
                
                # Update status to failed
                await self.db.knowledge_base_items.update_one(
                    {"_id": document["_id"]},
                    {"$set": {
                        "indexing_status": "failed",
                        "ai_processing_error": result.get('error', 'Unknown error'),
                        "ai_processing_failed_at": datetime.utcnow()
                    }}
                )
            
        except Exception as e:
            logger.error(f"❌ Error triggering AI service: {e}", exc_info=True)
            
            # Update status to failed
            await self.db.knowledge_base_items.update_one(
                {"_id": document["_id"]},
                {"$set": {
                    "indexing_status": "failed",
                    "ai_processing_error": str(e),
                    "ai_processing_failed_at": datetime.utcnow()
                }}
            )
    
    async def _create_document(self, doc_data: Dict[str, Any]):
        """Create a new document in the database"""
        try:
            from bson import ObjectId
            
            new_doc = {
                "_id": doc_data.get('document_id') or str(ObjectId()),
                "title": doc_data.get('title', 'Untitled Document'),
                "content": doc_data.get('content', ''),
                "content_type": doc_data.get('type', 'document'),
                "metadata": doc_data.get('metadata', {}),
                "indexing_status": "pending",
                "created_from_kafka": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.db.knowledge_base_items.insert_one(new_doc)
            logger.info(f"✅ Created new document with ID: {result.inserted_id}")
            
            # Trigger AI processing for the new document
            await self._trigger_ai_processing(new_doc)
            
        except Exception as e:
            logger.error(f"❌ Error creating document: {e}", exc_info=True)


# Global consumer instance
_kafka_consumer: Optional[KafkaDocumentConsumer] = None


def get_kafka_consumer() -> KafkaDocumentConsumer:
    """Get or create Kafka consumer instance"""
    global _kafka_consumer
    if _kafka_consumer is None:
        _kafka_consumer = KafkaDocumentConsumer()
    return _kafka_consumer


def start_kafka_consumer():
    """Start the Kafka consumer"""
    consumer = get_kafka_consumer()
    consumer.start()
    logger.info("✅ Kafka consumer service started")


def stop_kafka_consumer():
    """Stop the Kafka consumer"""
    global _kafka_consumer
    if _kafka_consumer:
        _kafka_consumer.stop()
        _kafka_consumer = None
    logger.info("✅ Kafka consumer service stopped")