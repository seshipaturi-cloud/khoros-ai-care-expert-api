# CLAUDE.md - Khoros Care AI Assist API

This file provides guidance to Claude Code (claude.ai/code) when working with the Khoros Care AI Assist API backend.

## Agent Identifier: ai-care-expert-api-agent

When working on this project, you are the **AI Care Expert API Agent** responsible for the FastAPI backend that powers advanced AI operations for Khoros AI Expert Care.

## Project Overview

**Khoros AI Care Expert API** - A high-performance FastAPI backend service that provides:
- Advanced AI processing and orchestration
- LLM integration and management
- Message processing pipelines
- Knowledge base vectorization and retrieval
- Real-time webhook handling
- Asynchronous task processing
- Integration with external AI services

## Tech Stack

- **Framework**: FastAPI (0.115.5)
- **Server**: Uvicorn with async support
- **Database**: MongoDB (via Motor for async operations)
- **Cloud Services**: AWS (S3, Lambda, SQS)
- **AI/ML**: Integration with OpenAI, Anthropic, and other LLM providers
- **Language**: Python 3.11+
- **Package Management**: pip/requirements.txt

## Development Commands

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --port 8000

# Run with custom host
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Format code
black app/

# Lint code
pylint app/

# Type checking
mypy app/
```

## Project Structure

```
khoros-care-ai-assist-api/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
├── app/
│   ├── __init__.py
│   ├── api/               # API layer
│   │   ├── __init__.py
│   │   ├── middleware/    # Request/response middleware
│   │   │   └── cors.py
│   │   │   └── auth.py
│   │   └── routes/        # API endpoints
│   │       ├── __init__.py
│   │       ├── health.py  # Health check endpoints
│   │       ├── items.py   # Item CRUD operations
│   │       └── users.py   # User management
│   ├── models/            # Pydantic models
│   │   ├── __init__.py
│   │   ├── item.py       # Item data models
│   │   └── user.py       # User data models
│   ├── services/          # Business logic layer
│   │   ├── __init__.py
│   │   ├── ai_service.py     # AI/LLM operations
│   │   ├── message_service.py # Message processing
│   │   └── knowledge_service.py # Knowledge base operations
│   └── utils/             # Utility functions
│       ├── __init__.py
│       ├── aws.py         # AWS service integrations
│       └── database.py    # Database connections
├── config/                # Configuration management
│   ├── __init__.py
│   └── settings.py        # Environment and app settings
└── tests/                 # Test suite
    ├── __init__.py
    ├── test_api/
    └── test_services/
```

## Core Dependencies

```python
# Framework
fastapi==0.115.5
uvicorn[standard]==0.32.1

# Database
pymongo==4.10.1
motor==3.6.0  # Async MongoDB driver

# Configuration
python-dotenv==1.0.1
pydantic==2.10.3
pydantic-settings==2.6.1

# File handling
python-multipart==0.0.17

# AWS Services
boto3==1.35.83
```

## API Architecture

### Layer Structure

1. **Routes Layer** (`app/api/routes/`)
   - HTTP endpoint definitions
   - Request validation
   - Response serialization
   - OpenAPI documentation

2. **Service Layer** (`app/services/`)
   - Business logic implementation
   - External service integration
   - Data processing
   - AI/ML operations

3. **Model Layer** (`app/models/`)
   - Pydantic data models
   - Request/response schemas
   - Validation rules
   - Type definitions

4. **Utils Layer** (`app/utils/`)
   - Database connections
   - AWS service clients
   - Helper functions
   - Common utilities

## Key Features & Endpoints

### 1. Health & Status
```python
GET /health          # Service health check
GET /status          # Detailed status information
```

### 2. AI Processing
```python
POST /ai/process     # Process message with AI
POST /ai/generate    # Generate AI response
GET /ai/models       # List available AI models
```

### 3. Knowledge Base
```python
POST /knowledge/upload    # Upload document
POST /knowledge/index     # Index content
GET /knowledge/search     # Vector search
DELETE /knowledge/{id}    # Remove document
```

### 4. Message Handling
```python
POST /messages/ingest    # Ingest social media message
GET /messages/queue      # Get message queue
PUT /messages/{id}       # Update message status
POST /messages/assign    # Assign to agent
```

### 5. User Management
```python
GET /users              # List users
POST /users             # Create user
GET /users/{id}         # Get user details
PUT /users/{id}         # Update user
DELETE /users/{id}      # Delete user
```

## Configuration Management

### Environment Variables (.env)
```bash
# Application
APP_NAME=khoros-care-ai-assist-api
APP_VERSION=1.0.0
DEBUG=true

# Database
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=khoros_care

# AWS
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET=khoros-knowledge-base

# AI Services
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Security
JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:5173", "https://app.khoros.com"]
```

### Settings Management (config/settings.py)
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str
    debug: bool
    mongodb_uri: str
    database_name: str
    # ... other settings
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## Database Schema

### MongoDB Collections

1. **users**
```json
{
  "_id": "ObjectId",
  "email": "string",
  "name": "string",
  "role": "string",
  "brand_ids": ["ObjectId"],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

2. **messages**
```json
{
  "_id": "ObjectId",
  "platform": "string",
  "content": "string",
  "author": "object",
  "ai_processed": "boolean",
  "ai_response": "string",
  "status": "string",
  "assigned_to": "ObjectId",
  "created_at": "datetime"
}
```

3. **knowledge_base**
```json
{
  "_id": "ObjectId",
  "brand_id": "ObjectId",
  "type": "document|website|media",
  "content": "string",
  "embeddings": "array",
  "metadata": "object",
  "created_at": "datetime"
}
```

## API Development Guidelines

### Creating New Endpoints

1. **Define Pydantic Models** (`app/models/`)
```python
from pydantic import BaseModel

class ItemCreate(BaseModel):
    name: str
    description: str
    
class ItemResponse(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime
```

2. **Create Service Function** (`app/services/`)
```python
async def create_item(item_data: ItemCreate) -> ItemResponse:
    # Business logic here
    result = await db.items.insert_one(item_data.dict())
    return ItemResponse(id=str(result.inserted_id), **item_data.dict())
```

3. **Define Route** (`app/api/routes/`)
```python
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/items", tags=["items"])

@router.post("/", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    try:
        return await item_service.create_item(item)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Error Handling Pattern
```python
from fastapi import HTTPException, status

class ItemNotFound(HTTPException):
    def __init__(self, item_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found"
        )
```

### Async Operations
```python
# Always use async/await for I/O operations
async def get_item(item_id: str):
    item = await db.items.find_one({"_id": ObjectId(item_id)})
    if not item:
        raise ItemNotFound(item_id)
    return item
```

## Testing Guidelines

### Unit Tests
```python
# tests/test_services/test_item_service.py
import pytest
from app.services import item_service

@pytest.mark.asyncio
async def test_create_item():
    item_data = ItemCreate(name="Test", description="Test item")
    result = await item_service.create_item(item_data)
    assert result.name == "Test"
```

### Integration Tests
```python
# tests/test_api/test_items.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_item():
    response = client.post(
        "/items/",
        json={"name": "Test", "description": "Test item"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test"
```

## Performance Optimization

1. **Use Async Operations**: All database and external API calls should be async
2. **Connection Pooling**: Motor handles MongoDB connection pooling
3. **Caching**: Implement Redis for frequently accessed data
4. **Background Tasks**: Use FastAPI BackgroundTasks for non-blocking operations
5. **Rate Limiting**: Implement rate limiting for API endpoints

## Security Best Practices

1. **Authentication**: JWT-based authentication
2. **Authorization**: Role-based access control (RBAC)
3. **Input Validation**: Pydantic models for all inputs
4. **CORS**: Configured for specific origins only
5. **Secrets Management**: Use environment variables, never commit secrets
6. **SQL Injection**: Not applicable (using MongoDB)
7. **Rate Limiting**: Implement per-endpoint limits

## Monitoring & Logging

```python
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response
```

## Deployment Considerations

### Docker Configuration
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Settings
- Use environment-specific configurations
- Enable HTTPS/TLS
- Configure proper CORS origins
- Set up monitoring (Prometheus/Grafana)
- Implement health checks
- Use production ASGI server (Gunicorn with Uvicorn workers)

## Integration with Web Application

This API serves as the backend for:
- **Khoros Care AI Assist Web** (`/Users/seshireddy/projects/khoros-care-ai-assist`)
- Provides AI processing capabilities
- Handles complex business logic
- Manages external service integrations

## Common Development Tasks

### Adding New AI Provider
1. Create provider client in `app/services/ai_providers/`
2. Add configuration in `config/settings.py`
3. Update AI service to include new provider
4. Add provider-specific endpoints if needed

### Implementing Webhook Handler
1. Create webhook model in `app/models/webhooks.py`
2. Add webhook route in `app/api/routes/webhooks.py`
3. Implement processing logic in `app/services/webhook_service.py`
4. Add webhook verification middleware

### Adding Background Task
```python
from fastapi import BackgroundTasks

@router.post("/process")
async def process_item(
    item_id: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(process_item_async, item_id)
    return {"message": "Processing started"}
```

## Troubleshooting

### Common Issues
1. **MongoDB Connection**: Check MONGODB_URI and network access
2. **AWS Credentials**: Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
3. **Import Errors**: Ensure virtual environment is activated
4. **CORS Issues**: Add frontend URL to CORS_ORIGINS

---

**Agent Role**: As the ai-care-expert-api-agent, you are responsible for all backend development, API design, database operations, AI service integrations, and performance optimization for the Khoros Care AI Assist API service.