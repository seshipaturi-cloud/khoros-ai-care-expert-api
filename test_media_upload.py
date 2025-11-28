#!/usr/bin/env python3
"""
Test script for media upload functionality
"""

import requests
import json
from PIL import Image
import io
import base64

# API endpoint
API_BASE = "http://localhost:8000/api"

# Create a simple test image
def create_test_image():
    """Create a simple test image"""
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()

def test_media_upload():
    """Test uploading a media file"""
    
    # Create test image
    image_data = create_test_image()
    
    # First, upload the file via server proxy
    files = {'file': ('test_image.png', image_data, 'image/png')}
    data = {'content_type': 'media'}
    
    response = requests.post(
        f"{API_BASE}/knowledge-base/upload-via-server-proxy",
        files=files,
        data=data
    )
    
    if response.status_code != 200:
        print(f"Upload failed: {response.status_code}")
        print(response.text)
        return
    
    upload_result = response.json()
    print(f"File uploaded successfully: {upload_result}")
    
    # Create knowledge base item for the media
    item_data = {
        "title": "Test Image",
        "description": "A test image for media processing",
        "content_type": "media",
        "brand_id": "default-brand",
        "agent_ids": [],
        "s3_key": upload_result['s3_key'],
        "file_name": "test_image.png",
        "file_size": len(image_data),
        "mime_type": "image/png",
        "metadata": {
            "media_type": "image",
            "file_extension": "png",
            "original_filename": "test_image.png"
        },
        "processing_options": {
            "auto_index": True,
            "extract_text_from_images": True,
            "generate_embeddings": True
        }
    }
    
    response = requests.post(
        f"{API_BASE}/knowledge-base/items",
        json=item_data
    )
    
    if response.status_code != 200:
        print(f"Item creation failed: {response.status_code}")
        print(response.text)
        return
    
    item_result = response.json()
    print(f"Knowledge base item created: {item_result}")
    
    # Check processing status
    item_id = item_result['_id']
    
    # Wait a moment for processing
    import time
    time.sleep(2)
    
    # Check the item status
    response = requests.get(f"{API_BASE}/knowledge-base/items/{item_id}")
    if response.status_code == 200:
        item_status = response.json()
        print(f"Item status: {item_status.get('indexing_status')}")
        if item_status.get('indexing_error'):
            print(f"Processing error: {item_status.get('indexing_error')}")
    
    return item_id

if __name__ == "__main__":
    print("Testing media upload functionality...")
    item_id = test_media_upload()
    if item_id:
        print(f"Test completed. Item ID: {item_id}")