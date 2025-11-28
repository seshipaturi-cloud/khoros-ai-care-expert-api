from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import json
from config import settings
from app.utils import connect_to_mongo, close_mongo_connection
from app.api.routes import health, users, items, knowledge_base, knowledge_base_public, ai_agents, search_stats, companies, brands, llm_providers, auth, roles, admin, teams, templates, tags, tickets, feedback, setup
# Import new routes separately to handle errors
try:
    from app.api.routes import ai_features, ai_models
    AI_FEATURES_AVAILABLE = True
    AI_MODELS_AVAILABLE = True
except Exception as e:
    print(f"⚠️  Warning: Could not import ai_features or ai_models: {e}")
    AI_FEATURES_AVAILABLE = False
    AI_MODELS_AVAILABLE = False

# Import Kafka consumer if enabled
if settings.kafka_enabled:
    from app.services.kafka_consumer import start_kafka_consumer, stop_kafka_consumer
    logger_kafka = logging.getLogger("kafka_consumer")
    logger_kafka.info("Kafka consumer enabled in settings")

logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start MongoDB connection
    await connect_to_mongo()
    
    # Start Kafka consumer if enabled
    if settings.kafka_enabled:
        logger.info("Starting Kafka consumer service...")
        try:
            start_kafka_consumer()
            logger.info("✅ Kafka consumer started successfully")
        except Exception as e:
            logger.error(f"❌ Failed to start Kafka consumer: {e}")
    
    yield
    
    # Stop Kafka consumer if enabled
    if settings.kafka_enabled:
        logger.info("Stopping Kafka consumer service...")
        try:
            stop_kafka_consumer()
            logger.info("✅ Kafka consumer stopped successfully")
        except Exception as e:
            logger.error(f"❌ Failed to stop Kafka consumer: {e}")
    
    # Close MongoDB connection
    await close_mongo_connection()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_chat_requests(request: Request, call_next):
    """Log incoming chat requests to see what frontend sends"""
    # Only log POST requests to chat endpoint
    if request.method == "POST" and "chat" in str(request.url.path):
        # Read body
        body_bytes = await request.body()
        # Create new request with body
        async def receive():
            return {"type": "http.request", "body": body_bytes}
        request._receive = receive
        
        try:
            body_json = json.loads(body_bytes) if body_bytes else {}
            logger.info("=" * 80)
            logger.info(f"📥 FRONTEND REQUEST TO: {request.url.path}")
            logger.info(f"Request Body:")
            logger.info(json.dumps(body_json, indent=2))
            # Specifically log company_id and brand_id
            if 'company_id' in body_json:
                logger.info(f"✅ company_id: {body_json['company_id']}")
            else:
                logger.info("❌ company_id: NOT SENT")
            if 'brand_id' in body_json:
                logger.info(f"✅ brand_id: {body_json['brand_id']}")  
            else:
                logger.info("❌ brand_id: NOT SENT")
            logger.info("=" * 80)
        except Exception as e:
            logger.error(f"Error logging request: {e}")
    
    response = await call_next(request)
    return response

app.include_router(auth.router)
app.include_router(roles.router)
app.include_router(admin.router)
app.include_router(teams.router, prefix="/api/teams", tags=["teams"])
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(items.router, prefix="/api/items", tags=["items"])
app.include_router(knowledge_base.router, prefix="/api/knowledge-base", tags=["knowledge-base"])
app.include_router(knowledge_base_public.router, prefix="/api/aicareexpert/knowledge-base", tags=["knowledge-base-public"])
app.include_router(ai_agents.router)
app.include_router(search_stats.router, prefix="/api", tags=["search-stats"])
app.include_router(companies.router)
app.include_router(brands.router)
app.include_router(llm_providers.router)
app.include_router(templates.router)
app.include_router(tags.router)
app.include_router(tickets.router)
app.include_router(feedback.router, prefix="/api/aicareexpert", tags=["feedback"])
app.include_router(setup.router, tags=["setup"])

# Include new AI routes if successfully imported
if AI_FEATURES_AVAILABLE:
    app.include_router(ai_features.router)
    print("✅ AI Features API routes registered")
else:
    print("⚠️  AI Features API not available")

if AI_MODELS_AVAILABLE:
    app.include_router(ai_models.router)
    print("✅ AI Models API routes registered")
else:
    print("⚠️  AI Models API not available")


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )