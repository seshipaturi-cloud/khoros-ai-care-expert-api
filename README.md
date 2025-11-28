# Python API Project

A standard Python API built with FastAPI and MongoDB.

## Features

- FastAPI framework for high-performance async API
- MongoDB integration with Motor (async driver)
- Environment-based configuration
- CORS middleware support
- Structured project layout
- Health check endpoints
- Basic CRUD operations for Users and Items

## Project Structure

```
.
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── users.py
│   │   │   └── items.py
│   │   └── middleware/
│   ├── models/
│   │   ├── user.py
│   │   └── item.py
│   ├── services/
│   └── utils/
│       └── database.py
├── config/
│   └── settings.py
├── tests/
├── .env
├── .env.example
├── .gitignore
├── main.py
├── requirements.txt
└── README.md
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start MongoDB:
```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or use your local MongoDB installation
```

4. Run the application:
```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload
```

## API Documentation

Once the application is running, you can access:
- Interactive API docs: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc
- Health check: http://localhost:8000/api/health

## API Endpoints

### Health
- `GET /api/health` - Application health check
- `GET /api/health/db` - Database connection health check

### Users
- `POST /api/users` - Create a new user
- `GET /api/users` - List all users
- `GET /api/users/{user_id}` - Get a specific user
- `PUT /api/users/{user_id}` - Update a user
- `DELETE /api/users/{user_id}` - Delete a user

### Items
- `POST /api/items` - Create a new item
- `GET /api/items` - List all items (with optional filters)
- `GET /api/items/{item_id}` - Get a specific item
- `PUT /api/items/{item_id}` - Update an item
- `DELETE /api/items/{item_id}` - Delete an item

## Environment Variables

See `.env.example` for all available configuration options:
- `APP_NAME` - Application name
- `APP_VERSION` - Application version
- `DEBUG` - Debug mode (True/False)
- `HOST` - Server host
- `PORT` - Server port
- `MONGODB_URL` - MongoDB connection URL
- `MONGODB_DATABASE` - MongoDB database name
- `SECRET_KEY` - Secret key for security
- `CORS_ORIGINS` - Allowed CORS origins

## Development

The application includes:
- Automatic reload in debug mode
- Comprehensive error handling
- Request validation with Pydantic
- Async/await support throughout
- Proper MongoDB connection management
- CORS configuration for frontend integration