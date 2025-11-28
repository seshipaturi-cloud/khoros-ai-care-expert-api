# User Context Implementation - Backend API

## Overview
This document describes the implementation of automatic user context storage in MongoDB for all API endpoints. Every create and update operation now automatically stores full user context including user information, company details, and audit trail data.

## Implementation Date
October 21, 2025

## What Was Implemented

### 1. User Context Models (`app/models/user_context.py`)
Created comprehensive models to store user and company information:

```python
class UserInfo(BaseModel):
    """User information captured from requests"""
    id, name, email, title, team_id, team_name, role_types, department, locale

class CompanyInfo(BaseModel):
    """Company information captured from requests"""
    id, key, name

class UserContext(BaseModel):
    """Complete user context for audit trails"""
    user: UserInfo
    company: CompanyInfo
    timestamp, ip_address, user_agent
```

### 2. User Context Extractor Utility (`app/utils/user_context_extractor.py`)
Created utility functions to extract user context from HTTP requests:

- `extract_user_context_from_headers(request)` - Extracts from HTTP headers sent by frontend
- `extract_user_context_from_body(body)` - Extracts from `_userContext` field in request body
- `get_user_context(request, body)` - Combined extraction from both sources
- `remove_user_context_from_body(body)` - Cleans request body for processing

## APIs Updated

### ✅ 1. LLM Providers API (COMPLETED)

**Model:** `app/models/llm_provider.py`
- Added `created_by_context: Optional[UserContext]`
- Added `updated_by_context: Optional[UserContext]`

**Service:** `app/services/llm_provider_service.py`
- Updated `create_provider()` to accept `user_context` parameter
- Updated `update_provider()` to accept `user_context` parameter
- Stores user context in MongoDB on create/update

**Routes:** `app/api/routes/llm_providers.py`
- Updated `create_provider()` endpoint to extract and pass user context
- Updated `update_provider()` endpoint to extract and pass user context

## APIs To Be Updated

### 2. AI Models API
**Files to update:**
- Model: `app/models/ai_model.py` - Add `created_by_context` and `updated_by_context`
- Service: `app/services/ai_model_service.py` (if exists) - Add user_context parameter
- Routes: `app/api/routes/ai_models.py` - Extract and pass user context

### 3. AI Features API
**Files to update:**
- Model: `app/models/ai_feature.py` - Add `created_by_context` and `updated_by_context`
- Service: `app/services/ai_feature_service.py` (if exists) - Add user_context parameter
- Routes: `app/api/routes/ai_features.py` - Extract and pass user context

### 4. Tags API
**Files to update:**
- Model: `app/models/tag.py` - Add `created_by_context` and `updated_by_context`
- Service: `app/services/tag_service.py` (if exists) - Add user_context parameter
- Routes: `app/api/routes/tags.py` - Extract and pass user context

### 5. Knowledge Base API
**Files to update:**
- Model: `app/models/knowledge_base.py` - Add `created_by_context` and `updated_by_context`
- Service: `app/services/knowledge_base_service.py` (if exists) - Add user_context parameter
- Routes: `app/api/routes/knowledge_base.py` - Extract and pass user context

### 6. Tickets API
**Files to update:**
- Model: `app/models/ticket.py` - Add `created_by_context` and `updated_by_context`
- Service: `app/services/ticket_service.py` (if exists) - Add user_context parameter
- Routes: `app/api/routes/tickets.py` - Extract and pass user context

### 7. Feedback API
**Files to update:**
- Model: `app/models/feedback.py` - Add `created_by_context` and `updated_by_context`
- Service: `app/services/feedback_service.py` (if exists) - Add user_context parameter
- Routes: `app/api/routes/feedback.py` - Extract and pass user context

### 8. AI Agents API
**Files to update:**
- Model: `app/models/ai_agent.py` - Add `created_by_context` and `updated_by_context`
- Service: `app/services/ai_agent_service.py` (if exists) - Add user_context parameter
- Routes: `app/api/routes/ai_agents.py` - Extract and pass user context

## Implementation Pattern

### Step 1: Update Model
```python
# Add to imports
from app.models.user_context import UserContext

# Add to response model
class ModelResponse(BaseModel):
    # ... existing fields ...
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None  # Deprecated
    updated_by: Optional[str] = None  # Deprecated

    # Add these fields
    created_by_context: Optional[UserContext] = None
    updated_by_context: Optional[UserContext] = None
```

### Step 2: Update Service
```python
# Add to imports
from app.models.user_context import UserContext
from typing import Optional

# Update create method
async def create_item(
    self,
    item_data: ItemCreate,
    created_by: str = "system",
    user_context: Optional[UserContext] = None  # Add this
) -> ItemResponse:
    doc = {
        # ... existing fields ...
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": created_by,
        "updated_by": created_by,
        "created_by_context": user_context.model_dump() if user_context else None,  # Add
        "updated_by_context": user_context.model_dump() if user_context else None   # Add
    }
    await self.collection.insert_one(doc)
    return ItemResponse(**doc)

# Update update method
async def update_item(
    self,
    item_id: str,
    item_data: ItemUpdate,
    updated_by: str = "system",
    user_context: Optional[UserContext] = None  # Add this
) -> Optional[ItemResponse]:
    update_doc = {
        # ... existing fields ...
        "updated_at": datetime.utcnow(),
        "updated_by": updated_by,
        "updated_by_context": user_context.model_dump() if user_context else None  # Add
    }
    await self.collection.update_one({"_id": item_id}, {"$set": update_doc})
    return await self.get_item(item_id)
```

### Step 3: Update Routes
```python
# Add to imports
from fastapi import Request
from app.utils.user_context_extractor import get_user_context

# Update create endpoint
@router.post("/", response_model=ItemResponse)
async def create_item(
    request: Request,  # Add this
    item_data: ItemCreate,
    current_user: dict = Depends(get_current_user)
):
    # Extract user context
    user_context = get_user_context(request)

    # Pass to service
    item = await item_service.create_item(
        item_data,
        created_by=current_user.get("id", "system"),
        user_context=user_context  # Add this
    )
    return item

# Update update endpoint
@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    request: Request,  # Add this
    item_id: str,
    item_data: ItemUpdate,
    current_user: dict = Depends(get_current_user)
):
    # Extract user context
    user_context = get_user_context(request)

    # Pass to service
    item = await item_service.update_item(
        item_id,
        item_data,
        updated_by=current_user.get("id", "system"),
        user_context=user_context  # Add this
    )
    return item
```

## MongoDB Storage Structure

User context is stored in MongoDB as:

```json
{
  "_id": "...",
  "...": "other fields",
  "created_at": "2025-10-21T12:00:00Z",
  "created_by": "user-id-123",
  "created_by_context": {
    "user": {
      "id": "user-id-123",
      "name": "John Doe",
      "email": "john@example.com",
      "title": "Product Manager",
      "team_id": "team-456",
      "team_name": "Product Team",
      "role_types": ["PRODUCT_MANAGER", "ADMIN"],
      "department": "Product",
      "locale": "en-US"
    },
    "company": {
      "id": "company-789",
      "key": "acme-corp",
      "name": "Acme Corporation"
    },
    "timestamp": "2025-10-21T12:00:00.123Z",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0..."
  },
  "updated_at": "2025-10-21T13:00:00Z",
  "updated_by": "user-id-456",
  "updated_by_context": {
    "user": { "..." },
    "company": { "..." },
    "timestamp": "2025-10-21T13:00:00.456Z",
    "ip_address": "192.168.1.101",
    "user_agent": "Mozilla/5.0..."
  }
}
```

## Benefits

1. **Complete Audit Trail:** Full user and company context for every create/update operation
2. **Multi-tenancy Support:** Company information enables proper data isolation and tracking
3. **Compliance:** Meets regulatory requirements for audit logging
4. **Troubleshooting:** IP address and user agent help debug issues
5. **Analytics:** Rich data for usage analytics and reporting
6. **Security:** Track who made changes from which location
7. **Backward Compatible:** Maintains `created_by` and `updated_by` for existing code

## Testing

After implementing for each API, verify:

1. **Create Operations:**
```python
# Test creating a new item
response = client.post("/api/items/",
    json={...},
    headers={
        "X-User-Id": "123",
        "X-User-Name": "John%20Doe",
        "X-User-Email": "john@example.com",
        "X-Company-Id": "456",
        "X-Company-Name": "Acme%20Corp"
    }
)

# Check MongoDB
doc = await db.items.find_one({"_id": response.json()["id"]})
assert doc["created_by_context"]["user"]["id"] == "123"
assert doc["created_by_context"]["company"]["id"] == "456"
```

2. **Update Operations:**
```python
# Test updating an item
response = client.put(f"/api/items/{item_id}",
    json={...},
    headers={...}
)

# Check MongoDB
doc = await db.items.find_one({"_id": item_id})
assert doc["updated_by_context"]["user"]["id"] == "789"
assert doc["updated_by_context"] != doc["created_by_context"]
```

## Migration (if needed)

For existing records without user context:

```python
# migration_script.py
async def migrate_add_user_context():
    """Add empty user context to existing records"""
    collections = [
        "llm_providers",
        "ai_models",
        "ai_features",
        "tags",
        "knowledge_base",
        "tickets",
        "feedback"
    ]

    for collection_name in collections:
        collection = db[collection_name]

        # Update records without user context
        await collection.update_many(
            {"created_by_context": {"$exists": False}},
            {"$set": {
                "created_by_context": None,
                "updated_by_context": None
            }}
        )

        print(f"Migrated {collection_name}")
```

## Next Steps

1. ✅ LLM Providers API - COMPLETED
2. ⏳ AI Models API - TO DO
3. ⏳ AI Features API - TO DO
4. ⏳ Tags API - TO DO
5. ⏳ Knowledge Base API - TO DO
6. ⏳ Tickets API - TO DO
7. ⏳ Feedback API - TO DO
8. ⏳ AI Agents API - TO DO

## Files Created/Modified

**Created:**
- `app/models/user_context.py`
- `app/utils/user_context_extractor.py`
- `USER_CONTEXT_IMPLEMENTATION_BACKEND.md`

**Modified (LLM Providers - Completed):**
- `app/models/llm_provider.py`
- `app/services/llm_provider_service.py`
- `app/api/routes/llm_providers.py`

**To be Modified (Remaining APIs):**
- All models in `app/models/` (7 remaining)
- All services in `app/services/` (7 remaining)
- All routes in `app/api/routes/` (7 remaining)
