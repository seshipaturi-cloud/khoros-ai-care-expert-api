#!/usr/bin/env python3
"""
Test RAG service directly without API authentication
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service import get_rag_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_direct_rag():
    """Test the RAG service directly"""
    
    # Get the RAG service
    rag = get_rag_service()
    
    # The company_id from the database
    company_id = "68c6a8c80fa016e20482025f"
    
    # Test query
    query = "How many emotions does AI care expert detect?"
    
    logger.info("=" * 80)
    logger.info("Testing RAG Service Directly")
    logger.info("=" * 80)
    logger.info(f"Query: {query}")
    logger.info(f"Company ID: {company_id}")
    logger.info("")
    
    try:
        # Test the chat function directly
        result = await rag.chat(
            query=query,
            company_id=company_id,
            search_type="hybrid",
            limit=5
        )
        
        logger.info("=" * 80)
        logger.info("✅ RESULTS:")
        logger.info("=" * 80)
        
        if result.get("success"):
            answer = result.get("answer", "No answer")
            logger.info(f"\n📝 Answer:\n{answer}\n")
            
            sources = result.get("sources", [])
            logger.info(f"📚 Sources found: {len(sources)}")
            
            if sources:
                logger.info("\n📑 Source documents:")
                for i, source in enumerate(sources[:3], 1):
                    logger.info(f"  {i}. {source.get('title', 'Unknown')}")
                    logger.info(f"     Type: {source.get('type', 'unknown')}")
                    if source.get('url'):
                        logger.info(f"     URL: {source['url']}")
        else:
            logger.error(f"❌ Search failed: {result.get('answer', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close the connection
        if hasattr(rag, 'client'):
            rag.client.close()

if __name__ == "__main__":
    asyncio.run(test_direct_rag())