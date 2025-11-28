#!/usr/bin/env python3
"""
Add request logging middleware to see what frontend is sending
"""

import json

print("""
Add this middleware to your main.py file to log incoming requests:

========== ADD THIS TO main.py AFTER THE IMPORTS ==========

from fastapi import Request
import json

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Only log POST requests to chat endpoint
    if request.method == "POST" and "chat" in request.url.path:
        # Get the body
        body = await request.body()
        request._body = body  # Store for later use
        
        try:
            body_json = json.loads(body) if body else {}
            print("=" * 80)
            print(f"📥 INCOMING REQUEST TO: {request.url.path}")
            print(f"Method: {request.method}")
            print(f"Headers: {dict(request.headers)}")
            print(f"Body: {json.dumps(body_json, indent=2)}")
            print("=" * 80)
        except:
            print(f"📥 Request to {request.url.path} (non-JSON body)")
    
    response = await call_next(request)
    return response

# Override body getter to return stored body
async def receive_body(request: Request):
    return {"type": "http.request", "body": request._body}

========== END OF MIDDLEWARE CODE ==========

After adding this, restart your API server and make a request from the frontend.
You'll see exactly what company_id and brand_id values are being sent.
""")