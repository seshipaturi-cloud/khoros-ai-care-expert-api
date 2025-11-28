# ⚠️ ACTION REQUIRED: MongoDB Atlas Vector Index Update

## Current Situation
- **Your MongoDB Atlas Index**: Configured for **1536 dimensions** (OpenAI)
- **Your Current Embeddings**: Using **384 dimensions** (HuggingFace)
- **Result**: Vector search will **FAIL** with dimension mismatch error

## Immediate Actions Required

### Step 1: Update MongoDB Atlas Vector Index

1. **Login to MongoDB Atlas**: https://cloud.mongodb.com
2. Navigate to your cluster
3. Go to **"Search"** tab
4. Find index named **`kb_index`**
5. **DELETE** the existing index
6. **CREATE** new index with this configuration:

```json
{
  "name": "kb_index",
  "type": "vectorSearch",
  "definition": {
    "fields": [
      {
        "path": "chunks.embedding",
        "dimensions": 384,
        "similarity": "cosine",
        "type": "vector"
      }
    ]
  }
}
```

### Step 2: Re-index Existing Documents (if any)

If you have documents already in the database with 1536-dimensional embeddings:

```bash
# For each document, trigger re-ingestion
POST /api/knowledge-base/items/{item_id}/ingest
```

### Step 3: Verify Configuration

```bash
# Check embedding configuration
curl http://localhost:8000/api/knowledge-base/embedding-info

# Expected output:
{
  "provider": "huggingface",
  "model": "sentence-transformers/all-MiniLM-L6-v2",
  "dimension": 384,  # ← Must match MongoDB index
  "index_configuration": {
    "expected_dimension": 384,
    "index_name": "kb_index"
  }
}

# Check specific document compatibility
curl http://localhost:8000/api/knowledge-base/items/{item_id}/embedding-compatibility
```

## Quick Reference

| Component | Current Setting | Required Action |
|-----------|-----------------|-----------------|
| **Embedding Provider** | HuggingFace ✅ | None |
| **Embedding Model** | all-MiniLM-L6-v2 ✅ | None |
| **Embedding Dimensions** | 384 ✅ | None |
| **MongoDB Index Dimensions** | 1536 ❌ | **UPDATE TO 384** |
| **Existing Documents** | May have 1536 dims ⚠️ | **RE-INDEX ALL** |

## Why This Matters

Vector search uses cosine similarity between query embeddings and stored embeddings. If dimensions don't match:
- Query: 384 dimensions (HuggingFace)
- Index: 1536 dimensions (old OpenAI config)
- **Result**: ERROR - Cannot compute similarity

## Testing After Update

```python
# Test search query
POST /api/knowledge-base/search
{
    "query": "test search",
    "limit": 5
}

# Should return results without errors
```

## Alternative: Switch to OpenAI

If you prefer to keep the 1536-dimension index and use OpenAI:

1. Update `.env`:
```bash
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

2. Restart the service
3. Re-index all documents with OpenAI embeddings

## Support

See `MONGODB_VECTOR_INDEX_UPDATE.md` for detailed instructions.