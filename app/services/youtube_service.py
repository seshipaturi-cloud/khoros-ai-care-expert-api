"""
YouTube video processing service
Downloads YouTube videos, extracts audio, transcribes, and ingests into vector store
"""

import logging
import os
import tempfile
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import time

# YouTube download
import yt_dlp
from pathlib import Path

# Audio transcription
whisper = None
try:
    # First try to import the OpenAI Whisper package
    import whisper
    # Check if it's the OpenAI Whisper by checking for load_model attribute
    if not hasattr(whisper, 'load_model'):
        # This is the graphite whisper package, not what we need
        print("Wrong 'whisper' package detected. Need 'openai-whisper' for audio transcription.")
        whisper = None
except ImportError:
    whisper = None
    print("OpenAI Whisper not installed. Audio transcription will not be available.")

# MongoDB and S3
from motor.motor_asyncio import AsyncIOMotorClient
import boto3
from botocore.exceptions import ClientError

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

from config.settings import settings

logger = logging.getLogger(__name__)


class YouTubeService:
    """Service for processing YouTube videos"""
    
    def __init__(self):
        # MongoDB connection
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.database_name]
        self.collection = self.db.knowledge_base_items
        
        # S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            aws_session_token=getattr(settings, 'aws_session_token', None),
            region_name=settings.aws_region
        )
        self.bucket_name = settings.s3_bucket_name
        
        # Initialize embeddings
        self.embeddings = self._initialize_embeddings()
        self.embedding_provider = settings.embedding_provider
        self.embedding_model_name = self._get_embedding_model_name()
        
        # Text splitter for transcripts
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", " ", ""]
        )
        
        # Whisper model (lazy loading)
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
            raise ImportError(
                "OpenAI Whisper is not installed or wrong package is installed. "
                "Please run: pip uninstall whisper && pip install openai-whisper"
            )
        if self.whisper_model is None:
            logger.info("Loading Whisper model for audio transcription...")
            self.whisper_model = whisper.load_model("base")
        return self.whisper_model
    
    def download_youtube_video(self, youtube_url: str, output_path: str) -> Dict[str, Any]:
        """Download YouTube video and extract metadata"""
        try:
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'best[ext=mp4]/best',  # Prefer MP4 format
                'outtmpl': output_path,
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'writesubtitles': True,  # Try to download subtitles
                'writeautomaticsub': True,  # Download auto-generated subtitles
                'subtitleslangs': ['en'],  # Prefer English subtitles
            }
            
            # Download video and extract info
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                
                # Extract metadata
                metadata = {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'channel_id': info.get('channel_id', ''),
                    'description': info.get('description', ''),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'upload_date': info.get('upload_date', ''),
                    'thumbnail': info.get('thumbnail', ''),
                    'video_id': info.get('id', ''),
                    'webpage_url': info.get('webpage_url', youtube_url),
                    'categories': info.get('categories', []),
                    'tags': info.get('tags', [])
                }
                
                # Check if subtitles were downloaded
                subtitle_file = None
                if info.get('requested_subtitles'):
                    for lang, sub_info in info['requested_subtitles'].items():
                        if sub_info and 'filepath' in sub_info:
                            subtitle_file = sub_info['filepath']
                            break
                
                metadata['subtitle_file'] = subtitle_file
                
                logger.info(f"Downloaded YouTube video: {metadata['title']}")
                return {
                    'success': True,
                    'video_path': output_path,
                    'metadata': metadata
                }
                
        except Exception as e:
            logger.error(f"Error downloading YouTube video: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def extract_audio_from_video(self, video_path: str, audio_path: str) -> bool:
        """Extract audio from video file"""
        try:
            import moviepy.editor as mp
            
            # Load video and extract audio
            video = mp.VideoFileClip(video_path)
            audio = video.audio
            
            if audio is not None:
                # Write audio to file
                audio.write_audiofile(audio_path, logger=None)
                video.close()
                logger.info(f"Extracted audio to: {audio_path}")
                return True
            else:
                video.close()
                logger.warning("Video has no audio track")
                return False
                
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return False
    
    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio using Whisper"""
        try:
            model = self._get_whisper_model()
            logger.info(f"Transcribing audio: {audio_path}")
            
            # Transcribe audio
            result = model.transcribe(audio_path)
            
            transcript = result.get("text", "")
            language = result.get("language", "unknown")
            
            logger.info(f"Transcription complete. Language: {language}, Length: {len(transcript)} chars")
            return transcript
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return ""
    
    def read_subtitle_file(self, subtitle_path: str) -> str:
        """Read and clean subtitle file content"""
        try:
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clean subtitle formatting (remove timestamps, etc.)
            lines = content.split('\n')
            cleaned_lines = []
            
            for line in lines:
                # Skip empty lines and timestamp lines
                if line.strip() and not line.strip().isdigit() and '-->' not in line:
                    # Remove HTML tags if present
                    import re
                    clean_line = re.sub('<[^<]+?>', '', line)
                    cleaned_lines.append(clean_line.strip())
            
            return ' '.join(cleaned_lines)
            
        except Exception as e:
            logger.error(f"Error reading subtitle file: {e}")
            return ""
    
    async def upload_to_s3(self, file_path: str, s3_key: str, mime_type: str = 'video/mp4') -> bool:
        """Upload file to S3"""
        try:
            with open(file_path, 'rb') as f:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=f,
                    ContentType=mime_type
                )
            
            logger.info(f"Uploaded to S3: {s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
            return False
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        return len(text) // 4
    
    async def process_youtube_video(
        self,
        item_id: str,
        youtube_url: str,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Complete YouTube video processing pipeline"""
        
        start_time = time.time()
        temp_dir = tempfile.mkdtemp()
        
        try:
            logger.info(f"Starting YouTube processing for item_id: {item_id}, URL: {youtube_url}")
            
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
            
            # 1. Download YouTube video
            video_path = os.path.join(temp_dir, f"{item_id}.mp4")
            download_result = self.download_youtube_video(youtube_url, video_path)
            
            if not download_result['success']:
                raise ValueError(f"Failed to download video: {download_result.get('error')}")
            
            metadata = download_result['metadata']
            
            # Use YouTube title if no title provided
            if not title:
                title = metadata['title']
            
            # 2. Upload video to S3
            s3_key = f"knowledge-base/media/default-brand/{datetime.utcnow().strftime('%Y/%m')}/{item_id}.mp4"
            upload_success = await self.upload_to_s3(video_path, s3_key, 'video/mp4')
            
            if not upload_success:
                raise ValueError("Failed to upload video to S3")
            
            # Get file size
            file_size = os.path.getsize(video_path)
            
            # 3. Extract transcript (from subtitles or audio)
            transcript = ""
            
            # First try to use subtitles if available
            if metadata.get('subtitle_file') and os.path.exists(metadata['subtitle_file']):
                logger.info("Using subtitles for transcript")
                transcript = self.read_subtitle_file(metadata['subtitle_file'])
            
            # If no subtitles or empty transcript, extract audio and transcribe
            if not transcript:
                logger.info("No subtitles found, extracting audio for transcription")
                audio_path = os.path.join(temp_dir, f"{item_id}.wav")
                
                if self.extract_audio_from_video(video_path, audio_path):
                    transcript = self.transcribe_audio(audio_path)
            
            if not transcript:
                # Use description as fallback
                transcript = metadata.get('description', 'No transcript available')
            
            # 4. Create full content for indexing
            full_content = f"""YouTube Video: {title}
Channel: {metadata.get('uploader', 'Unknown')}
URL: {youtube_url}
Duration: {metadata.get('duration', 0)} seconds
Views: {metadata.get('view_count', 0)}
Upload Date: {metadata.get('upload_date', 'Unknown')}

Description:
{metadata.get('description', 'No description')}

Transcript:
{transcript}"""
            
            # 5. Create document for processing
            doc = Document(
                page_content=full_content,
                metadata={
                    "source": youtube_url,
                    "media_type": "youtube_video",
                    "title": title,
                    "channel": metadata.get('uploader'),
                    "video_id": metadata.get('video_id'),
                    "duration": metadata.get('duration'),
                    "item_id": item_id
                }
            )
            
            # 6. Split text into chunks
            chunks = self.text_splitter.split_documents([doc])
            logger.info(f"Split YouTube content into {len(chunks)} chunks")
            
            # 7. Generate embeddings for each chunk
            chunk_texts = [chunk.page_content for chunk in chunks]
            embeddings_list = self.embeddings.embed_documents(chunk_texts)
            
            # 8. Prepare chunks for storage (without embeddings in chunks)
            chunk_docs = []
            for i, chunk in enumerate(chunks):
                chunk_docs.append({
                    "chunk_id": f"{item_id}_chunk_{i}",
                    "content": chunk.page_content,
                    "metadata": {
                        **chunk.metadata,
                        "chunk_index": i,
                        "item_id": item_id
                    }
                })
            
            # 9. Calculate statistics
            processing_time = time.time() - start_time
            total_tokens = self.estimate_tokens(full_content)
            
            ingestion_stats = {
                "chunks_created": len(chunks),
                "total_characters": len(full_content),
                "estimated_tokens": total_tokens,
                "processing_time_seconds": processing_time,
                "embedding_provider": self.embedding_provider,
                "embedding_model": self.embedding_model_name,
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "processed_at": datetime.utcnow(),
                "media_type": "youtube_video",
                "youtube_metadata": metadata,
                "transcript_source": "subtitles" if metadata.get('subtitle_file') else "audio_transcription"
            }
            
            # 10. Update MongoDB document
            update_data = {
                "indexing_status": "completed",
                "indexed_content": full_content[:5000],  # Store first 5000 chars for preview
                "chunks": chunk_docs,  # Chunks without embeddings
                "embeddings": embeddings_list,  # All embeddings in a single array field
                "embeddings_processed": True,
                "embeddings_processed_at": datetime.utcnow(),
                "ingestion_stats": ingestion_stats,
                "total_chunks": len(chunks),
                "total_tokens": total_tokens,
                "embedding_provider": self.embedding_provider,
                "embedding_model": self.embedding_model_name,
                "file": {
                    "name": f"{title}.mp4",
                    "size": file_size,
                    "s3_key": s3_key,
                    "s3_bucket": self.bucket_name,
                    "mime_type": "video/mp4",
                    "uploaded_at": datetime.utcnow()
                },
                "metadata": {
                    **metadata,
                    "youtube_url": youtube_url,
                    "media_type": "youtube_video"
                }
            }
            
            update_result = await self.collection.update_one(
                {"_id": item_id},
                {"$set": update_data}
            )
            
            if update_result.matched_count == 0:
                raise ValueError(f"Failed to update document with ID: {item_id}")
            
            logger.info(f"Successfully processed YouTube video {item_id} in {processing_time:.2f} seconds")
            
            return {
                "success": True,
                "stats": ingestion_stats,
                "s3_key": s3_key,
                "title": title,
                "transcript_length": len(transcript)
            }
            
        except Exception as e:
            logger.error(f"Error processing YouTube video {item_id}: {e}")
            
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
        
        finally:
            # Clean up temporary files
            try:
                import shutil
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {e}")


# Create singleton instance
youtube_service = YouTubeService()