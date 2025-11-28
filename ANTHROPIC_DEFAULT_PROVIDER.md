# Anthropic as Default Provider Configuration

## Overview
The system is now configured to use **Anthropic** as the default provider. Since Anthropic (Claude) doesn't provide embedding models, the system automatically handles this with intelligent fallback.

## Current Configuration

```python
# config/settings.py
embedding_provider: str = "anthropic"  # Will use HuggingFace for embeddings
llm_provider: str = "anthropic"        # Will use Claude for LLM operations
```

## How It Works

### For LLM Operations (Text Generation, Chat, Analysis)
- **Provider**: Anthropic Claude
- **Model**: claude-3-5-sonnet-20241022 (or configured model)
- **Used in**: RAG service, AI analysis, chat responses

### For Embeddings (Vector Search, Document Indexing)
- **Provider**: Automatically falls back to HuggingFace
- **Model**: sentence-transformers/all-MiniLM-L6-v2
- **Reason**: Anthropic doesn't provide embedding models
- **Used in**: Document ingestion, vector search, similarity matching

## System Behavior

When `embedding_provider = "anthropic"`:

1. **Vector Service** (`vector_service.py`):
   ```python
   # Logs: "Anthropic doesn't provide embedding models. Falling back to HuggingFace."
   # Uses: HuggingFace sentence-transformers
   ```

2. **Ingestion Services** (documents, websites, YouTube):
   ```python
   # Logs: "Anthropic doesn't provide embedding models, falling back to HuggingFace"
   # Uses: HuggingFaceEmbeddings for chunk processing
   ```

3. **RAG Service** (`rag_service.py`):
   - **Embeddings**: HuggingFace for query/document vectors
   - **LLM**: Anthropic Claude for response generation

## Benefits of This Configuration

### ✅ Best of Both Worlds
- **High-quality LLM**: Claude for intelligent responses
- **Free embeddings**: HuggingFace for vector operations
- **Cost-effective**: Only pay for LLM usage, not embeddings

### ✅ Automatic Handling
- No manual intervention needed
- System automatically uses appropriate providers
- Clear logging shows what's being used

### ✅ Consistent Experience
- All services handle the fallback uniformly
- No configuration conflicts
- Transparent to end users

## API Response

When checking embedding configuration:

```bash
GET /api/knowledge-base/embedding-info
```

Response:
```json
{
    "provider": "huggingface",  // Actual provider being used
    "model": "sentence-transformers/all-MiniLM-L6-v2",
    "dimension": 384,
    "status": "active",
    "supported_providers": ["openai", "huggingface", "anthropic"],
    "note": "Anthropic doesn't provide embedding models and will fallback to HuggingFace"
}
```

## Log Messages

You'll see these informational messages in the logs:

```
INFO: Initializing embedding provider: anthropic
WARNING: Anthropic doesn't provide embedding models. Falling back to HuggingFace.
INFO: Using HuggingFace embeddings with model: sentence-transformers/all-MiniLM-L6-v2
```

## Document Metadata

Documents will be stored with:
```json
{
    "embedding_provider": "huggingface",  // Actual provider used
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "llm_provider": "anthropic",  // For any LLM operations
    "llm_model": "claude-3-5-sonnet-20241022"
}
```

## Alternative Configurations

If you want different behaviors:

### Use OpenAI for Embeddings
```python
embedding_provider: str = "openai"  # High-quality paid embeddings
llm_provider: str = "anthropic"     # Claude for LLM
```

### Use HuggingFace Explicitly
```python
embedding_provider: str = "huggingface"  # Explicit HuggingFace
llm_provider: str = "anthropic"          # Claude for LLM
```

### Full OpenAI
```python
embedding_provider: str = "openai"  # OpenAI embeddings
llm_provider: str = "openai"        # GPT-4 for LLM
```

## Important Notes

1. **No Re-indexing Needed**: Since the actual embedding provider (HuggingFace) hasn't changed, existing document embeddings remain valid.

2. **Transparent Fallback**: The system handles the Anthropic → HuggingFace fallback automatically without errors.

3. **Cost Optimization**: This configuration optimizes costs by using free embeddings while leveraging Claude's superior LLM capabilities.

4. **Future-Ready**: If Anthropic releases embedding models in the future, the system can easily adapt.

## Verification

To verify the configuration is working:

1. **Check logs** when starting the service:
   ```
   INFO: Initializing embedding provider: anthropic
   WARNING: Anthropic doesn't provide embedding models. Falling back to HuggingFace.
   ```

2. **Test document ingestion**:
   ```bash
   # Upload a document and check the logs
   # Should show: "Using HuggingFace embeddings"
   ```

3. **Check embedding info endpoint**:
   ```bash
   curl http://localhost:8000/api/knowledge-base/embedding-info
   ```

## Summary

Setting `embedding_provider = "anthropic"` is a valid configuration that:
- Automatically uses HuggingFace for embeddings (since Anthropic doesn't provide them)
- Maintains system stability and functionality
- Provides clear logging about what's actually being used
- Prepares the system for potential future Anthropic embedding models

This configuration is **production-ready** and provides an optimal balance of capability and cost.