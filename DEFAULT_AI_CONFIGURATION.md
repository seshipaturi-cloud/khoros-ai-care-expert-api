# Default AI Configuration

## Current Default Settings

The system is configured with optimal defaults for cost-effectiveness and performance:

```python
# config/settings.py
embedding_provider: str = "huggingface"  # For vector embeddings (FREE)
llm_provider: str = "anthropic"          # For text generation (Claude)
```

## Default Models

### Embeddings (Vector Operations)
- **Provider**: HuggingFace
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensions**: 384
- **Cost**: FREE (runs locally)
- **Used for**: Document chunking, vector search, similarity matching

### LLM (Text Generation)
- **Provider**: Anthropic
- **Model**: `claude-3-5-sonnet-20241022`
- **Cost**: Pay per token
- **Used for**: Chat responses, AI analysis, content generation

## Why This Configuration?

### ✅ Cost Optimization
- **Free embeddings** via HuggingFace (no API costs)
- **Pay only for LLM** usage when generating responses
- Ideal for development and production with budget constraints

### ✅ Performance Balance
- **Fast local embeddings** (no network latency)
- **High-quality LLM** responses from Claude
- Best combination of speed and intelligence

### ✅ Simplicity
- No embedding API keys needed
- Only requires Anthropic API key for LLM
- Works out of the box

## Service Usage

### Document Ingestion Services
All ingestion services use this configuration:

| Service | Embedding Provider | LLM Provider |
|---------|-------------------|--------------|
| `langchain_ingestion_service.py` | HuggingFace | - |
| `website_ingestion_service.py` | HuggingFace | - |
| `youtube_service.py` | HuggingFace | - |
| `media_ingestion_service.py` | HuggingFace | - |
| `vector_service.py` | HuggingFace | - |
| `rag_service.py` | HuggingFace | Anthropic |

### RAG (Retrieval-Augmented Generation)
- **Query Embedding**: HuggingFace
- **Document Retrieval**: Vector search using HuggingFace embeddings
- **Response Generation**: Anthropic Claude

## Environment Variables

### Minimal Required Configuration
```bash
# Only need Anthropic for LLM
ANTHROPIC_API_KEY=your-anthropic-api-key

# Optional: Specific Anthropic model
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### Optional Overrides
```bash
# Switch to OpenAI embeddings (paid)
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=your-openai-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Switch to OpenAI LLM
LLM_PROVIDER=openai
OPENAI_LLM_MODEL=gpt-4-turbo-preview
```

## API Endpoints

### Check Embedding Configuration
```bash
GET /api/knowledge-base/embedding-info
```

Expected Response:
```json
{
    "provider": "huggingface",
    "model": "sentence-transformers/all-MiniLM-L6-v2",
    "dimension": 384,
    "status": "active",
    "supported_providers": ["openai", "huggingface", "anthropic"],
    "note": "Anthropic doesn't provide embedding models and will fallback to HuggingFace"
}
```

## Document Processing Flow

1. **Upload Document** → API endpoint
2. **Process with HuggingFace**:
   - Split into chunks
   - Generate embeddings locally
   - Store in MongoDB
3. **Query Time**:
   - Embed query with HuggingFace
   - Search similar chunks
   - Generate response with Anthropic Claude

## Stored Metadata

Documents are stored with clear provider information:

```json
{
    "embedding_provider": "huggingface",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "embedding_dimension": 384,
    "chunks": [...],
    "ingestion_stats": {
        "embedding_provider": "huggingface",
        "chunks_created": 10,
        "processing_time_seconds": 1.5
    }
}
```

## Switching Providers

### To Use OpenAI Embeddings
```python
# config/settings.py or .env
embedding_provider: str = "openai"
openai_api_key: str = "sk-..."
```

**Note**: Requires re-indexing all documents due to dimension change (384 → 1536)

### To Use Different LLM
```python
# config/settings.py or .env
llm_provider: str = "openai"  # or "huggingface"
```

## Performance Characteristics

### HuggingFace Embeddings
- **Latency**: 10-50ms per chunk (local)
- **Throughput**: Limited by CPU
- **Quality**: Good for most use cases
- **Cost**: $0 (free)

### Anthropic Claude LLM
- **Latency**: 1-3 seconds per request
- **Quality**: Excellent reasoning and generation
- **Cost**: ~$3 per million input tokens

## Best Practices

1. **Development**: Use current defaults (HuggingFace + Anthropic)
2. **Production with Budget**: Keep current defaults
3. **Production Premium**: Consider OpenAI embeddings for better quality
4. **Monitoring**: Track embedding/LLM usage in document metadata

## Verification Commands

### Test Document Ingestion
```bash
# Upload a test document
curl -X POST http://localhost:8000/api/knowledge-base/items \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "content": "Test content"}'

# Check logs for:
# "Using HuggingFace embeddings with model: sentence-transformers/all-MiniLM-L6-v2"
```

### Test RAG Query
```bash
# Query the knowledge base
curl -X POST http://localhost:8000/api/knowledge-base/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the content about?"}'

# Should use HuggingFace for embedding and Claude for response
```

## Summary

The current configuration provides:
- ✅ **Free embeddings** with HuggingFace
- ✅ **Premium LLM** with Anthropic Claude
- ✅ **No unnecessary API costs**
- ✅ **Production-ready** setup
- ✅ **Easy to upgrade** when needed

This is the **recommended default configuration** for most use cases.