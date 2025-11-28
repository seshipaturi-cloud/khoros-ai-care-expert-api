#!/usr/bin/env python3
"""
Bulk update script to add user context to all remaining APIs
Run this to quickly update AI Features, Tags, Knowledge Base, Tickets, and Feedback APIs
"""

import os
import re

# Models to update with their file paths
MODELS_TO_UPDATE = [
    "app/models/ai_feature.py",
    "app/models/tag.py",
    "app/models/knowledge_base.py",
    "app/models/ticket.py",
    "app/models/feedback.py"
]

# Routes to update
ROUTES_TO_UPDATE = [
    "app/api/routes/ai_features.py",
    "app/api/routes/tags.py",
    "app/api/routes/knowledge_base.py",
    "app/api/routes/tickets.py",
    "app/api/routes/feedback.py"
]

def update_model_file(filepath):
    """Add user context import and fields to model file"""
    with open(filepath, 'r') as f:
        content = f.read()

    # Add import if not present
    if 'from app.models.user_context import UserContext' not in content:
        # Find the imports section
        import_pattern = r'(from pydantic import.*?\n)'
        replacement = r'\1from app.models.user_context import UserContext\n'
        content = re.sub(import_pattern, replacement, content, count=1)

    # Find and update the Response class timestamps section
    pattern = r'(    # Timestamps\n    created_at: datetime\n    updated_at: datetime\n    created_by: Optional\[str\] = None\n    updated_by: Optional\[str\] = None)'

    replacement = '''    # Timestamps
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None  # Deprecated: Use created_by_context
    updated_by: Optional[str] = None  # Deprecated: Use updated_by_context

    # User context for audit trails
    created_by_context: Optional[UserContext] = None
    updated_by_context: Optional[UserContext] = None'''

    content = re.sub(pattern, replacement, content)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"✅ Updated model: {filepath}")

def update_route_file(filepath):
    """Add user context extraction to route file"""
    with open(filepath, 'r') as f:
        content = f.read()

    # Add imports if not present
    if 'from fastapi import' in content and 'Request' not in content:
        content = content.replace('from fastapi import ', 'from fastapi import Request, ')

    if 'from app.utils.user_context_extractor import get_user_context' not in content:
        # Add import after other app imports
        pattern = r'(from app\.services\..+?\n)'
        replacement = r'\1from app.utils.user_context_extractor import get_user_context\n'
        content = re.sub(pattern, replacement, content, count=1)

    # Update create endpoint signatures
    content = re.sub(
        r'async def create_(\w+)\(\s*(\w+_data:)',
        r'async def create_\1(\n    request: Request,\n    \2',
        content
    )

    # Update update endpoint signatures
    content = re.sub(
        r'async def update_(\w+)\(\s*(\w+_id: str)',
        r'async def update_\1(\n    request: Request,\n    \2',
        content
    )

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"✅ Updated routes: {filepath}")

def main():
    print("Starting bulk update of APIs with user context...\n")

    # Update models
    print("Updating models...")
    for model_path in MODELS_TO_UPDATE:
        if os.path.exists(model_path):
            try:
                update_model_file(model_path)
            except Exception as e:
                print(f"❌ Error updating {model_path}: {e}")
        else:
            print(f"⚠️  File not found: {model_path}")

    print("\nUpdating routes...")
    for route_path in ROUTES_TO_UPDATE:
        if os.path.exists(route_path):
            try:
                update_route_file(route_path)
            except Exception as e:
                print(f"❌ Error updating {route_path}: {e}")
        else:
            print(f"⚠️  File not found: {route_path}")

    print("\n✅ Bulk update complete!")
    print("\nNote: You still need to manually:")
    print("1. Update service files to accept user_context parameter")
    print("2. Add user_context extraction in route handlers")
    print("3. Pass user_context to service calls")

if __name__ == "__main__":
    main()
