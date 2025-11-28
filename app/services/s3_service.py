import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import mimetypes
from config.settings import settings

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self):
        # Include session token if available (for temporary credentials)
        client_params = {
            'service_name': 's3',
            'aws_access_key_id': settings.aws_access_key_id,
            'aws_secret_access_key': settings.aws_secret_access_key,
            'region_name': settings.aws_region
        }
        
        # Add session token if it exists
        if hasattr(settings, 'aws_session_token') and settings.aws_session_token:
            client_params['aws_session_token'] = settings.aws_session_token
            
        self.s3_client = boto3.client(**client_params)
        self.bucket_name = settings.s3_bucket_name
        
    def generate_s3_key(self, brand_id: str, content_type: str, filename: str, item_id: str) -> str:
        """Generate a structured S3 key for storing files"""
        # Extract file extension
        extension = filename.split('.')[-1] if '.' in filename else ''
        
        # Ensure content_type is a simple string (not an enum)
        if hasattr(content_type, 'value'):
            content_type = content_type.value
        content_type = str(content_type).lower().replace('contenttype.', '')
        
        # Create a structured path
        timestamp = datetime.utcnow().strftime('%Y/%m')
        s3_key = f"knowledge-base/{content_type}/{brand_id}/{timestamp}/{item_id}.{extension}"
        
        return s3_key
    
    def generate_presigned_upload_url(
        self, 
        s3_key: str, 
        content_type: Optional[str] = None,
        expires_in: int = 3600,
        metadata: Dict[str, str] = None
    ) -> str:
        """Generate a presigned URL for uploading files directly to S3"""
        try:
            # Prepare parameters for presigned URL
            params = {
                'Bucket': self.bucket_name,
                'Key': s3_key,
            }
            
            # Add content type if provided
            if content_type:
                params['ContentType'] = content_type
            
            # Add metadata if provided
            if metadata:
                params['Metadata'] = metadata
            
            # Generate presigned URL
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params=params,
                ExpiresIn=expires_in
            )
            
            logger.info(f"Generated presigned URL for key: {s3_key}")
            return presigned_url
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise
    
    def generate_presigned_download_url(
        self, 
        s3_key: str, 
        expires_in: int = 3600,
        filename: Optional[str] = None,
        inline: bool = False,
        content_type: Optional[str] = None
    ) -> str:
        """Generate a presigned URL for downloading files from S3"""
        try:
            params = {
                'Bucket': self.bucket_name,
                'Key': s3_key,
            }
            
            # Add content disposition - inline for preview, attachment for download
            if filename:
                if inline:
                    params['ResponseContentDisposition'] = f'inline; filename="{filename}"'
                else:
                    params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'
            
            # Add content type if provided (helps with browser display)
            if content_type and inline:
                params['ResponseContentType'] = content_type
            
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expires_in
            )
            
            logger.info(f"Generated {'preview' if inline else 'download'} URL for key: {s3_key}, inline: {inline}")
            return presigned_url
            
        except ClientError as e:
            logger.error(f"Error generating download URL: {e}")
            raise
    
    def delete_file(self, s3_key: str) -> bool:
        """Delete a file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Deleted file from S3: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {e}")
            return False
    
    def copy_file(self, source_key: str, destination_key: str) -> bool:
        """Copy a file within S3"""
        try:
            copy_source = {'Bucket': self.bucket_name, 'Key': source_key}
            
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=destination_key
            )
            
            logger.info(f"Copied file from {source_key} to {destination_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error copying file in S3: {e}")
            return False
    
    def get_file_metadata(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a file in S3"""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return {
                'size': response.get('ContentLength'),
                'content_type': response.get('ContentType'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            logger.error(f"Error getting file metadata: {e}")
            return None
    
    def upload_file_from_bytes(
        self, 
        file_bytes: bytes, 
        s3_key: str, 
        content_type: Optional[str] = None,
        metadata: Dict[str, str] = None
    ) -> bool:
        """Upload file bytes directly to S3"""
        try:
            params = {
                'Bucket': self.bucket_name,
                'Key': s3_key,
                'Body': file_bytes
            }
            
            if content_type:
                params['ContentType'] = content_type
            
            if metadata:
                params['Metadata'] = metadata
            
            self.s3_client.put_object(**params)
            
            logger.info(f"Uploaded file to S3: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {e}")
            return False
    
    def list_files(
        self, 
        prefix: str, 
        max_keys: int = 1000
    ) -> list:
        """List files in S3 with a given prefix"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified']
                    })
            
            return files
            
        except ClientError as e:
            logger.error(f"Error listing files in S3: {e}")
            return []
    
    def create_multipart_upload(self, s3_key: str, content_type: Optional[str] = None) -> str:
        """Initiate a multipart upload for large files"""
        try:
            params = {
                'Bucket': self.bucket_name,
                'Key': s3_key
            }
            
            if content_type:
                params['ContentType'] = content_type
            
            response = self.s3_client.create_multipart_upload(**params)
            
            upload_id = response['UploadId']
            logger.info(f"Created multipart upload with ID: {upload_id}")
            
            return upload_id
            
        except ClientError as e:
            logger.error(f"Error creating multipart upload: {e}")
            raise
    
    def generate_presigned_urls_for_multipart(
        self, 
        s3_key: str, 
        upload_id: str, 
        num_parts: int,
        expires_in: int = 3600
    ) -> list:
        """Generate presigned URLs for multipart upload parts"""
        try:
            presigned_urls = []
            
            for part_number in range(1, num_parts + 1):
                presigned_url = self.s3_client.generate_presigned_url(
                    'upload_part',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': s3_key,
                        'UploadId': upload_id,
                        'PartNumber': part_number
                    },
                    ExpiresIn=expires_in
                )
                
                presigned_urls.append({
                    'part_number': part_number,
                    'url': presigned_url
                })
            
            return presigned_urls
            
        except ClientError as e:
            logger.error(f"Error generating multipart presigned URLs: {e}")
            raise


# Create a singleton instance
s3_service = S3Service()