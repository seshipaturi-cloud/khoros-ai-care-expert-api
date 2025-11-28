# Document Ingestion & Embedding Analysis

## Current Embedding Usage in Document Ingestion

### Services Using Embeddings

The Khoros AI Care Expert system uses embeddings in multiple services for document ingestion and retrieval:

1. **langchain_ingestion_service.py** - Primary document processor
2. **website_ingestion_service.py** - Website crawling and processing
3. **youtube_service.py** - YouTube video transcription and processing
4. **media_ingestion_service.py** - Media file processing
5. **rag_service.py** - Retrieval-augmented generation for chat
6. **vector_service.py** - Direct vector operations (newly updated)

### Current Configuration

All services are configured to use the **same embedding provider** specified in `settings.embedding_provider`:

```python
# From config/settings.py
embedding_provider: str = "huggingface"  # Default: huggingface, openai, anthropic
```

### Embedding Providers in Use

#### 1. LangChain Ingestion Service (Documents)
```python
# Line 59-62, 72-93
self.embeddings = self._initialize_embeddings()
self.embedding_provider = settings.embedding_provider

# Initialization logic:
- If provider == "openai": Uses OpenAIEmbeddings from langchain_openai
- If provider == "anthropic": Falls back to HuggingFace (Anthropic has no embeddings)
- If provider == "huggingface": Uses HuggingFaceEmbeddings
```

**Usage in document processing (Line 306):**
```python
embeddings = self.embeddings.embed_documents(chunk_texts)
```

#### 2. Website Ingestion Service
- **Same initialization pattern** as langchain_ingestion_service
- Uses identical `_initialize_embeddings()` method
- Processes website content into chunks and generates embeddings

#### 3. YouTube Service
- **Same initialization pattern** as other services
- Processes video transcripts into chunks
- Generates embeddings using configured provider

#### 4. RAG Service (Retrieval)
- **Same initialization pattern** for consistency
- Uses embeddings for query processing:
```python
query_embedding = self.embeddings.embed_query(query)
```

### Embedding Models Used

Based on provider configuration:

| Provider | Model | Dimensions | Library |
|----------|-------|------------|---------|
| **HuggingFace** (Default) | sentence-transformers/all-MiniLM-L6-v2 | 384 | langchain_community.embeddings.HuggingFaceEmbeddings |
| **OpenAI** | text-embedding-3-small | 1536 | langchain_openai.OpenAIEmbeddings |
| **Anthropic** | N/A - Falls back to HuggingFace | 384 | N/A |

### Document Ingestion Flow

1. **File Upload** → Knowledge Base Item created
2. **Background Task** → `langchain_ingestion_service.process_document()`
3. **Processing Steps:**
   - Download from S3
   - Load document with appropriate loader (PDF, DOCX, etc.)
   - Split into chunks (1000 chars, 200 overlap)
   - **Generate embeddings** using configured provider
   - Store chunks with embeddings in MongoDB

### Metadata Stored

Each ingested document stores:
```python
{
    "embedding_provider": "huggingface",  # or "openai"
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "chunks": [
        {
            "chunk_id": "...",
            "content": "...",
            "embedding": [...],  # Vector array
            "metadata": {...}
        }
    ],
    "ingestion_stats": {
        "embedding_provider": "...",
        "embedding_model": "...",
        "chunks_created": 10,
        "processing_time_seconds": 2.5
    }
}
```

## Key Findings

### ✅ Consistent Embedding Usage
- All services use the **same embedding provider** configuration
- Centralized configuration via `settings.embedding_provider`
- Consistent initialization pattern across all services

### ✅ Current Default: HuggingFace
- Default provider is **HuggingFace** (free, local)
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- 384-dimensional embeddings

### ✅ Flexible Architecture
- Easy to switch providers via configuration
- All services automatically use the new provider
- Fallback mechanism if provider fails

### ⚠️ Important Considerations

1. **Embedding Consistency**: All documents in the knowledge base should use the same embedding model for proper similarity search
2. **Re-indexing Required**: When switching embedding providers, all documents need to be re-processed
3. **Dimension Mismatch**: Different models have different dimensions (384 vs 1536), making them incompatible

## How to Change Embedding Provider

### 1. Update Configuration

Edit `.env` or `config/settings.py`:
```bash
# For OpenAI
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# For HuggingFace (default)
EMBEDDING_PROVIDER=huggingface
HUGGINGFACE_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### 2. Restart Services
```bash
uvicorn main:app --reload
```

### 3. Re-index All Documents
**CRITICAL**: You must re-process all existing documents when switching providers:

```python
# Trigger re-ingestion for all items
POST /api/knowledge-base/items/{item_id}/ingest
```

## Vector Service Update

The `vector_service.py` has been updated to support multiple embedding providers:
- Now reads from `settings.embedding_provider`
- Supports OpenAI and HuggingFace
- Provides fallback mechanisms
- Includes `get_embedding_info()` method for status checking

## Recommendations

1. **Production**: Use OpenAI for better quality embeddings
2. **Development**: Use HuggingFace to save costs
3. **Consistency**: Don't mix embeddings from different providers
4. **Monitoring**: Check embedding configuration via `/api/knowledge-base/embedding-info`
5. **Documentation**: Track which embedding model was used for each batch of documents

## API Endpoints

### Check Current Configuration
```bash
GET /api/knowledge-base/embedding-info
```

Response:
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

### Trigger Document Ingestion
```bash
POST /api/knowledge-base/items/{item_id}/ingest
```

## Conclusion

The system currently uses **HuggingFace embeddings by default** across all ingestion services. The architecture supports easy switching between providers through configuration, but requires re-indexing of all documents when changing providers to maintain consistency.