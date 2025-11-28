#!/usr/bin/env python3
"""
Update S3 bucket CORS configuration to allow browser access
"""

import boto3
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

def update_cors_configuration():
    """Update S3 bucket CORS configuration"""
    
    # Create S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
        region_name=AWS_REGION
    )
    
    # Define CORS configuration
    cors_configuration = {
        'CORSRules': [
            {
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
                'AllowedOrigins': [
                    'http://localhost:3000',
                    'http://localhost:5173',
                    'http://localhost:5174',
                    'http://localhost:8080',
                    'http://localhost:8081',
                    'https://*.lovable.app',
                    'https://*.vercel.app'
                ],
                'ExposeHeaders': [
                    'ETag',
                    'Content-Length',
                    'Content-Type',
                    'x-amz-request-id',
                    'x-amz-id-2'
                ],
                'MaxAgeSeconds': 3600
            }
        ]
    }
    
    try:
        # Get current CORS configuration
        try:
            current_cors = s3_client.get_bucket_cors(Bucket=S3_BUCKET_NAME)
            print("Current CORS configuration:")
            print(json.dumps(current_cors['CORSRules'], indent=2))
        except Exception as e:
            if 'NoSuchCORSConfiguration' in str(e):
                print("No CORS configuration found on bucket")
            else:
                print(f"Error getting current CORS: {e}")
        
        # Update CORS configuration
        print(f"\nUpdating CORS configuration for bucket: {S3_BUCKET_NAME}")
        s3_client.put_bucket_cors(
            Bucket=S3_BUCKET_NAME,
            CORSConfiguration=cors_configuration
        )
        
        print("✅ CORS configuration updated successfully!")
        print("\nNew CORS configuration:")
        print(json.dumps(cors_configuration['CORSRules'], indent=2))
        
    except Exception as e:
        print(f"❌ Error updating CORS configuration: {e}")
        print("\nTroubleshooting:")
        print("1. Check if the bucket name is correct")
        print("2. Verify AWS credentials have permission to update bucket CORS")
        print("3. Ensure the bucket exists in the specified region")

def check_bucket_policy():
    """Check and suggest bucket policy for public read access to presigned URLs"""
    
    print("\n" + "="*50)
    print("RECOMMENDED: S3 Bucket Policy for Presigned URLs")
    print("="*50)
    
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowPresignedUrlAccess",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{S3_BUCKET_NAME}/*",
                "Condition": {
                    "StringLike": {
                        "aws:Referer": [
                            "http://localhost:*",
                            "https://*.lovable.app/*",
                            "https://*.vercel.app/*"
                        ]
                    }
                }
            }
        ]
    }
    
    print("\nConsider adding this bucket policy if images still don't display:")
    print(json.dumps(policy, indent=2))
    print("\nNote: This policy allows GET access only from specified referrer URLs")

if __name__ == "__main__":
    print("S3 CORS Configuration Updater")
    print("="*50)
    
    if not S3_BUCKET_NAME:
        print("❌ Error: S3_BUCKET_NAME not found in environment variables")
        exit(1)
    
    update_cors_configuration()
    check_bucket_policy()