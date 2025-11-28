"""
Media Ingestion Service for processing images, audio, and video files
"""

import logging
import os
import tempfile
from typing import Dict, Any, Optional
from datetime import datetime
import time
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings

# Image processing
from PIL import Image
import pytesseract
import io

# Audio/Video processing
whisper = None
try:
    # First try to import the OpenAI Whisper package
    import whisper
    # Check if it's the OpenAI Whisper by checking for load_model attribute
    if hasattr(whisper, 'load_model'):
        import logging
        logging.info("OpenAI Whisper successfully imported")
    else:
        # This is the graphite whisper package, not what we need
        import logging
        logging.warning("Wrong 'whisper' package detected (graphite whisper). Need 'openai-whisper' for audio transcription.")
        logging.warning("Please install: pip uninstall whisper && pip install openai-whisper")
        whisper = None
except ImportError:
    whisper = None
    import logging
    logging.warning("OpenAI Whisper not installed. Audio/video transcription will not be available.")
    logging.warning("Please install: pip install openai-whisper")

try:
    import youtube_dl
except ImportError:
    youtube_dl = None
    import logging
    logging.warning("youtube_dl not installed. YouTube support will not be available.")

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

logger = logging.getLogger(__name__)


class MediaIngestionService:
    """Service for processing media files (images, audio, video)"""
    
    def __init__(self):
        # MongoDB connection
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.database_name]
        self.collection = self.db.knowledge_base_items
        
        # Initialize embeddings
        self.embeddings = self._initialize_embeddings()
        self.embedding_provider = settings.embedding_provider
        self.embedding_model_name = self._get_embedding_model_name()
        
        # Text splitter for extracted content
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", " ", ""]
        )
        
        # Initialize Whisper model for audio transcription (lazy loading)
        self.whisper_model = None
    
    def _initialize_embeddings(self):
        """Initialize embeddings based on configured provider"""
        provider = settings.embedding_provider.lower()
        
        if provider == "openai":
            if not settings.openai_api_key:
                logger.warning("OpenAI API key not found, falling back to HuggingFace")
                return self._get_huggingface_embeddings()
            
            logger.info(f"Using OpenAI embeddings with model: {settings.openai_embedding_model}")
            return OpenAIEmbeddings(
                openai_api_key=settings.openai_api_key,
                model=settings.openai_embedding_model
            )
        else:
            return self._get_huggingface_embeddings()
    
    def _get_huggingface_embeddings(self):
        """Get HuggingFace embeddings"""
        logger.info(f"Using HuggingFace embeddings with model: {settings.huggingface_embedding_model}")
        return HuggingFaceEmbeddings(
            model_name=settings.huggingface_embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    
    def _get_embedding_model_name(self) -> str:
        """Get the name of the embedding model being used"""
        provider = settings.embedding_provider.lower()
        
        if provider == "openai":
            return settings.openai_embedding_model
        else:
            return settings.huggingface_embedding_model
    
    def _get_whisper_model(self):
        """Lazy load Whisper model for audio transcription"""
        if whisper is None:
            raise ImportError("Whisper is not installed. Please install with: pip install openai-whisper")
        if self.whisper_model is None:
            logger.info("Loading Whisper model for audio transcription...")
            self.whisper_model = whisper.load_model("base")
        return self.whisper_model
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            # Open image with PIL
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text using pytesseract
            text = pytesseract.image_to_string(image)
            
            # Also get basic image metadata
            metadata_text = f"Image: {os.path.basename(image_path)}\n"
            metadata_text += f"Size: {image.size[0]}x{image.size[1]} pixels\n"
            metadata_text += f"Format: {image.format}\n"
            
            # Combine metadata and extracted text
            full_text = metadata_text
            if text.strip():
                full_text += f"\nExtracted Text:\n{text}"
            else:
                full_text += "\n(No text detected in image)"
            
            return full_text
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            # Return basic info even if OCR fails
            return f"Image file: {os.path.basename(image_path)} (OCR extraction failed: {str(e)})"
    
    def extract_transcript_from_audio(self, audio_path: str) -> str:
        """Extract transcript from audio file using Whisper"""
        try:
            model = self._get_whisper_model()
            
            logger.info(f"🎵 Starting audio transcription for: {audio_path}")
            logger.info(f"🎵 File size: {os.path.getsize(audio_path) / (1024*1024):.2f} MB")
            
            # Transcribe the audio
            result = model.transcribe(audio_path)
            
            transcript = result.get("text", "")
            
            # Log the complete transcription details
            logger.info("=" * 80)
            logger.info("📝 AUDIO TRANSCRIPTION COMPLETE")
            logger.info("=" * 80)
            logger.info(f"📁 Audio File: {os.path.basename(audio_path)}")
            logger.info(f"⏱️  Duration: {result.get('duration', 'Unknown')} seconds")
            logger.info(f"🌍 Language: {result.get('language', 'Unknown')}")
            logger.info(f"📏 Transcript Length: {len(transcript)} characters")
            logger.info("-" * 80)
            logger.info("📜 FULL TRANSCRIPT:")
            logger.info("-" * 80)
            logger.info(transcript if transcript else "(No speech detected in audio)")
            logger.info("=" * 80)
            
            # Also log segments if available for debugging
            if 'segments' in result and result['segments']:
                logger.debug(f"📊 Total segments: {len(result['segments'])}")
                for i, segment in enumerate(result['segments'][:5]):  # Show first 5 segments
                    logger.debug(f"  Segment {i+1}: [{segment.get('start', 0):.2f}s - {segment.get('end', 0):.2f}s] {segment.get('text', '')}")
            
            # Add metadata
            metadata_text = f"Audio File: {os.path.basename(audio_path)}\n"
            metadata_text += f"Duration: {result.get('duration', 'Unknown')} seconds\n"
            metadata_text += f"Language: {result.get('language', 'Unknown')}\n"
            
            full_text = metadata_text
            if transcript:
                full_text += f"\nTranscript:\n{transcript}"
            else:
                full_text += "\n(No speech detected in audio)"
            
            return full_text
            
        except Exception as e:
            logger.error(f"❌ Error transcribing audio: {e}")
            logger.error(f"❌ Audio file path: {audio_path}")
            logger.error(f"❌ File exists: {os.path.exists(audio_path)}")
            return f"Audio file: {os.path.basename(audio_path)} (Transcription failed: {str(e)})"
    
    def extract_transcript_from_video(self, video_path: str) -> str:
        """Extract audio from video and transcribe it"""
        try:
            # First extract audio from video
            import moviepy.editor as mp
            
            # Create temp audio file
            temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_audio_path = temp_audio.name
            temp_audio.close()
            
            try:
                # Extract audio from video
                video = mp.VideoFileClip(video_path)
                audio = video.audio
                
                if audio is not None:
                    audio.write_audiofile(temp_audio_path, logger=None)
                    video.close()
                    
                    # Transcribe the extracted audio
                    transcript = self.extract_transcript_from_audio(temp_audio_path)
                    
                    # Update metadata
                    transcript = transcript.replace("Audio File:", "Video File:")
                    
                    return transcript
                else:
                    video.close()
                    return f"Video file: {os.path.basename(video_path)} (No audio track found)"
                    
            finally:
                # Clean up temp audio file
                if os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
                    
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            return f"Video file: {os.path.basename(video_path)} (Processing failed: {str(e)})"
    
    def extract_youtube_transcript(self, youtube_url: str) -> str:
        """Extract transcript from YouTube video"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'skip_download': True
            }
            
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                
                # Get video metadata
                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                uploader = info.get('uploader', 'Unknown')
                description = info.get('description', '')
                
                metadata_text = f"YouTube Video: {title}\n"
                metadata_text += f"Channel: {uploader}\n"
                metadata_text += f"Duration: {duration} seconds\n"
                metadata_text += f"URL: {youtube_url}\n"
                
                # Try to get automatic captions
                automatic_captions = info.get('automatic_captions', {})
                subtitles = info.get('subtitles', {})
                
                transcript = ""
                
                # Try to get English subtitles first
                if 'en' in subtitles:
                    # Download actual subtitles
                    # This would require additional processing
                    transcript = "(Subtitles available but not extracted)"
                elif 'en' in automatic_captions:
                    transcript = "(Automatic captions available but not extracted)"
                else:
                    transcript = "(No transcript available)"
                
                # Add description as content
                if description:
                    transcript += f"\n\nVideo Description:\n{description[:2000]}"  # Limit description length
                
                return metadata_text + "\n" + transcript
                
        except Exception as e:
            logger.error(f"Error extracting YouTube info: {e}")
            return f"YouTube URL: {youtube_url} (Extraction failed: {str(e)})"
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        return len(text) // 4
    
    async def process_media(
        self,
        item_id: str,
        file_path: str,
        media_type: str,
        mime_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a media file and generate embeddings"""
        
        start_time = time.time()
        
        try:
            logger.info(f"Starting media ingestion for item_id: {item_id}, type: {media_type}")
            
            # Update status to processing
            await self.collection.update_one(
                {"_id": item_id},
                {
                    "$set": {
                        "indexing_status": "processing",
                        "embeddings_processed_at": datetime.utcnow()
                    }
                }
            )
            
            # Extract text based on media type
            extracted_text = ""
            
            logger.info(f"🔍 Processing media file: {os.path.basename(file_path)}")
            logger.info(f"🔍 Media type: {media_type}, MIME type: {mime_type}")
            
            if media_type == "image" or mime_type.startswith("image/"):
                logger.info("🖼️ Processing as IMAGE file")
                extracted_text = self.extract_text_from_image(file_path)
            elif media_type == "audio" or mime_type.startswith("audio/"):
                logger.info("🎵 Processing as AUDIO file")
                extracted_text = self.extract_transcript_from_audio(file_path)
            elif media_type == "video" or mime_type.startswith("video/"):
                logger.info("🎬 Processing as VIDEO file")
                extracted_text = self.extract_transcript_from_video(file_path)
            elif media_type == "youtube" and metadata and metadata.get("youtube_url"):
                logger.info("📺 Processing as YOUTUBE video")
                extracted_text = self.extract_youtube_transcript(metadata["youtube_url"])
            else:
                logger.info(f"📄 Processing as generic media type: {media_type}")
                extracted_text = f"Media file: {os.path.basename(file_path)} (Type: {media_type})"
            
            logger.info(f"📝 Extracted text length: {len(extracted_text)} characters")
            
            if not extracted_text:
                raise ValueError("No content could be extracted from the media file")
            
            # Create document for processing
            doc = Document(
                page_content=extracted_text,
                metadata={
                    "source": file_path,
                    "media_type": media_type,
                    "mime_type": mime_type,
                    **(metadata or {})
                }
            )
            
            # Split text into chunks
            chunks = self.text_splitter.split_documents([doc])
            logger.info(f"Split media content into {len(chunks)} chunks")
            
            # Generate embeddings for each chunk
            chunk_texts = [chunk.page_content for chunk in chunks]
            embeddings = self.embeddings.embed_documents(chunk_texts)
            
            # Prepare chunks with embeddings for storage
            embedded_chunks = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                embedded_chunks.append({
                    "chunk_id": f"{item_id}_chunk_{i}",
                    "content": chunk.page_content,
                    "embedding": embedding,
                    "metadata": {
                        **chunk.metadata,
                        "chunk_index": i,
                        "item_id": item_id
                    }
                })
            
            # Calculate statistics
            processing_time = time.time() - start_time
            total_tokens = self.estimate_tokens(extracted_text)
            
            ingestion_stats = {
                "chunks_created": len(chunks),
                "total_characters": len(extracted_text),
                "estimated_tokens": total_tokens,
                "processing_time_seconds": processing_time,
                "embedding_provider": self.embedding_provider,
                "embedding_model": self.embedding_model_name,
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "processed_at": datetime.utcnow(),
                "media_type": media_type,
                "extraction_method": self._get_extraction_method(media_type)
            }
            
            # Update document in MongoDB
            update_data = {
                "indexing_status": "completed",
                "indexed_content": extracted_text[:5000],  # Store first 5000 chars for preview
                "chunks": embedded_chunks,
                "embeddings_processed": True,
                "embeddings_processed_at": datetime.utcnow(),
                "ingestion_stats": ingestion_stats,
                "total_chunks": len(chunks),
                "total_tokens": total_tokens,
                "embedding_provider": self.embedding_provider,
                "embedding_model": self.embedding_model_name
            }
            
            update_result = await self.collection.update_one(
                {"_id": item_id},
                {"$set": update_data}
            )
            
            if update_result.matched_count == 0:
                raise ValueError(f"Failed to update document with ID: {item_id}")
            
            logger.info(f"Successfully processed media {item_id} in {processing_time:.2f} seconds")
            
            return {
                "success": True,
                "stats": ingestion_stats
            }
            
        except Exception as e:
            logger.error(f"Error processing media {item_id}: {e}")
            
            # Update status to failed
            try:
                await self.collection.update_one(
                    {"_id": item_id},
                    {
                        "$set": {
                            "indexing_status": "failed",
                            "indexing_error": str(e),
                            "embeddings_processed_at": datetime.utcnow(),
                            "embeddings_processed": False
                        }
                    }
                )
            except Exception as update_error:
                logger.error(f"Failed to update error status: {update_error}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_extraction_method(self, media_type: str) -> str:
        """Get the extraction method used for the media type"""
        if media_type == "image":
            return "OCR (Tesseract)"
        elif media_type in ["audio", "video"]:
            return "Speech-to-Text (Whisper)"
        elif media_type == "youtube":
            return "YouTube Metadata/Captions"
        else:
            return "Metadata Only"


# Create singleton instance
media_ingestion_service = MediaIngestionService()