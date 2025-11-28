# Embedding Providers Configuration

## Overview
The vector service now supports multiple embedding providers that can be configured dynamically through environment variables or settings.

## Supported Providers

### 1. OpenAI (Recommended for Production)
High-quality embeddings with good performance for semantic search.

**Configuration:**
```bash
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # or text-embedding-3-large
```

**Available Models:**
- `text-embedding-3-small` - 1536 dimensions, good balance of quality and cost
- `text-embedding-3-large` - 3072 dimensions, highest quality
- `text-embedding-ada-002` - 1536 dimensions, legacy model

**Pros:**
- High quality embeddings
- Good semantic understanding
- Fast API response times
- Well-maintained and reliable

**Cons:**
- Requires API key and costs money
- Network dependency

### 2. HuggingFace (Default, Free)
Open-source models that run locally or via HuggingFace API.

**Configuration:**
```bash
EMBEDDING_PROVIDER=huggingface
HUGGINGFACE_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
# Optional: HUGGINGFACE_API_TOKEN=your-token
```

**Available Models:**
- `sentence-transformers/all-MiniLM-L6-v2` - 384 dimensions, fast and efficient
- `sentence-transformers/all-mpnet-base-v2` - 768 dimensions, better quality
- `sentence-transformers/all-MiniLM-L12-v2` - 384 dimensions, balanced

**Pros:**
- Free to use
- Can run locally without network
- Good performance for most use cases
- Many models to choose from

**Cons:**
- Slightly lower quality than OpenAI
- Local models use system resources
- First load can be slow

### 3. Anthropic (Not Supported)
⚠️ **Note:** Anthropic (Claude) does not currently provide embedding models. If configured, the system will automatically fallback to HuggingFace.

**Configuration:**
```bash
EMBEDDING_PROVIDER=anthropic  # Will fallback to HuggingFace
```

## Configuration in settings.py

Edit `/config/settings.py` or set environment variables:

```python
# In settings.py or .env file
embedding_provider: str = "huggingface"  # Options: huggingface, openai, anthropic

# OpenAI settings (if using OpenAI)
openai_api_key: str = "sk-..."
openai_embedding_model: str = "text-embedding-3-small"

# HuggingFace settings (if using HuggingFace)
huggingface_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
huggingface_api_token: str = ""  # Optional, for using HF Inference API
```

## How It Works

1. **Initialization:** When `VectorService` starts, it reads the `embedding_provider` configuration
2. **Provider Setup:** Based on the provider, it initializes the appropriate client
3. **Fallback Logic:** If a provider fails (missing API key, library not installed), it falls back to HuggingFace
4. **Embedding Generation:** The `generate_embeddings()` method handles provider-specific logic

## Switching Providers

To switch embedding providers:

1. **Update Configuration:**
   ```bash
   export EMBEDDING_PROVIDER=openai
   export OPENAI_API_KEY=your-key
   ```

2. **Restart the Service:**
   ```bash
   uvicorn main:app --reload
   ```

3. **Re-index Content (Important!):**
   When switching providers, you should re-index existing content as embedding dimensions and representations differ between models.

## API Usage

The API automatically uses the configured provider:

```python
from app.services.vector_service import vector_service

# Get current embedding configuration
info = vector_service.get_embedding_info()
print(info)
# Output: {'provider': 'openai', 'model': 'text-embedding-3-small', 'dimension': 1536, 'status': 'active'}

# Generate embeddings (uses configured provider)
embeddings = await vector_service.generate_embeddings("Your text here")
```

## Performance Considerations

### OpenAI
- **Latency:** 50-200ms per request
- **Throughput:** Rate limited by API tier
- **Cost:** ~$0.02 per 1M tokens

### HuggingFace (Local)
- **Latency:** 10-100ms per request (after model load)
- **Throughput:** Limited by CPU/GPU
- **Cost:** Free (uses local resources)

## Troubleshooting

### Issue: "OpenAI API key not configured. Falling back to HuggingFace."
**Solution:** Set the `OPENAI_API_KEY` environment variable or in settings.py

### Issue: "sentence-transformers library not installed"
**Solution:** Install the required library:
```bash
pip install sentence-transformers
```

### Issue: Different embedding dimensions after switching
**Solution:** Re-index all documents when switching between providers as they produce different dimensional embeddings:
- OpenAI: 1536 or 3072 dimensions
- HuggingFace: 384 or 768 dimensions (model dependent)

## Best Practices

1. **Production:** Use OpenAI for best quality and reliability
2. **Development/Testing:** Use HuggingFace to save costs
3. **Consistency:** Don't mix embeddings from different providers in the same index
4. **Monitoring:** Check `vector_service.get_embedding_info()` to verify configuration
5. **Re-indexing:** Always re-index when changing providers or models

## Future Enhancements

Potential providers to add:
- Cohere embeddings
- Google Vertex AI embeddings
- Amazon Bedrock embeddings
- Custom fine-tuned models