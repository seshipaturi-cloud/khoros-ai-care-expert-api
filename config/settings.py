from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Kafka Configuration
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_consumer_group: str = "doc_processor_group"
    kafka_document_topic: str = "doc_document"
    kafka_enabled: bool = False  # Set to True to enable Kafka consumer
    app_name: str = "Khoros Care AI Assist API"
    app_version: str = "1.0.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # MongoDB Configuration
    mongodb_uri: str = "mongodb+srv://srp:SiX3ofWhhhjzC2Bz@cluster0.badm4i9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    mongodb_url: str = "mongodb+srv://srp:SiX3ofWhhhjzC2Bz@cluster0.badm4i9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Alias for compatibility
    mongodb_database: str = "ai-care-expert"
    database_name: str = "ai-care-expert"  # Alias for our services
    
    # Security
    secret_key: str = "your-secret-key-change-this-in-production"
    jwt_secret_key: str = "your-secret-key-change-this-in-production"  # Alias
    algorithm: str = "HS256"
    jwt_algorithm: str = "HS256"  # Alias
    access_token_expire_minutes: int = 30
    
    # CORS - Allow common development ports and production ELB
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:7070,http://localhost:8000,http://localhost:8080,http://localhost:8081,http://localhost:5174,http://ac3c749e32cc5479583d5fc2b4360e97-127b53cf3f9c9c0e.elb.us-west-2.amazonaws.com,https://ac3c749e32cc5479583d5fc2b4360e97-127b53cf3f9c9c0e.elb.us-west-2.amazonaws.com"
    
    # AWS Configuration
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_session_token: str = ""
    aws_region: str = "us-west-2"
    s3_bucket_name: str = "ai-care-expert-knowledgebase-dev"
    
    # AI Model Configuration
    embedding_provider: str = "huggingface"  # huggingface (default), openai, anthropic
    llm_provider: str = "anthropic"  # anthropic (default), openai, huggingface
    
    # OpenAI Configuration
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_llm_model: str = "gpt-4-turbo-preview"
    
    # Anthropic Configuration
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5-20250929"
    
    # HuggingFace Configuration
    huggingface_api_token: str = ""
    huggingface_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    huggingface_llm_model: str = "meta-llama/Llama-2-7b-chat-hf"
    
    # Firecrawl Configuration
    firecrawl_api_key: str = ""
    use_firecrawl: bool = True  # Set to True to use Firecrawl, False for custom crawler
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()