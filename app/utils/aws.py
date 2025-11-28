import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from config import settings
import logging

logger = logging.getLogger(__name__)


class AWSClient:
    _s3_client = None
    _dynamodb_client = None
    _dynamodb_resource = None
    
    @classmethod
    def get_s3_client(cls):
        if cls._s3_client is None:
            cls._s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                aws_session_token=settings.aws_session_token,
                region_name=settings.aws_region
            )
            logger.info("S3 client initialized")
        return cls._s3_client
    
    @classmethod
    def get_dynamodb_client(cls):
        if cls._dynamodb_client is None:
            cls._dynamodb_client = boto3.client(
                'dynamodb',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                aws_session_token=settings.aws_session_token,
                region_name=settings.aws_region
            )
            logger.info("DynamoDB client initialized")
        return cls._dynamodb_client
    
    @classmethod
    def get_dynamodb_resource(cls):
        if cls._dynamodb_resource is None:
            cls._dynamodb_resource = boto3.resource(
                'dynamodb',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                aws_session_token=settings.aws_session_token,
                region_name=settings.aws_region
            )
            logger.info("DynamoDB resource initialized")
        return cls._dynamodb_resource


async def upload_to_s3(bucket_name: str, key: str, file_content: bytes, content_type: str = None):
    """Upload a file to S3"""
    try:
        s3_client = AWSClient.get_s3_client()
        
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=file_content,
            **extra_args
        )
        
        logger.info(f"File uploaded successfully to s3://{bucket_name}/{key}")
        return f"s3://{bucket_name}/{key}"
        
    except NoCredentialsError:
        logger.error("AWS credentials not found")
        raise
    except ClientError as e:
        logger.error(f"Failed to upload to S3: {e}")
        raise


async def download_from_s3(bucket_name: str, key: str):
    """Download a file from S3"""
    try:
        s3_client = AWSClient.get_s3_client()
        
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        content = response['Body'].read()
        
        logger.info(f"File downloaded successfully from s3://{bucket_name}/{key}")
        return content
        
    except NoCredentialsError:
        logger.error("AWS credentials not found")
        raise
    except ClientError as e:
        logger.error(f"Failed to download from S3: {e}")
        raise


async def list_s3_objects(bucket_name: str, prefix: str = ""):
    """List objects in an S3 bucket"""
    try:
        s3_client = AWSClient.get_s3_client()
        
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix
        )
        
        objects = []
        if 'Contents' in response:
            for obj in response['Contents']:
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified']
                })
        
        return objects
        
    except NoCredentialsError:
        logger.error("AWS credentials not found")
        raise
    except ClientError as e:
        logger.error(f"Failed to list S3 objects: {e}")
        raise