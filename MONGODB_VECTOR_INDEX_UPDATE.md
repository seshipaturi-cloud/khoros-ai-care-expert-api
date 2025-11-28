# MongoDB Atlas Vector Index Configuration Update

## Current Issue
- **Current Index**: Configured for 1536 dimensions (OpenAI embeddings)
- **Actual Embeddings**: Using 384 dimensions (HuggingFace)
- **Result**: Vector search will fail due to dimension mismatch

## Required Actions

### 1. Delete Existing Index (if exists)

In MongoDB Atlas:
1. Go to your cluster in Atlas
2. Navigate to "Search" tab
3. Find index named `kb_index`
4. Delete it

### 2. Create New Vector Search Index

#### Option A: Atlas UI Method

1. In MongoDB Atlas, go to "Search" tab
2. Click "Create Search Index"
3. Select "JSON Editor"
4. Use this configuration:

```json
{
  "name": "kb_index",
  "type": "vectorSearch",
  "definition": {
    "fields": [
      {
        "path": "embeddings",
        "dimensions": 384,
        "similarity": "cosine",
        "type": "vector"
      }
    ]
  }
}
```

#### Option B: Atlas CLI Method

```bash
atlas clusters search indexes create \
  --clusterName <your-cluster-name> \
  --collection knowledge_base_items \
  --db ai-care-expert \
  --type vectorSearch \
  --file vector_index.json
```

Where `vector_index.json` contains:
```json
{
  "name": "kb_index",
  "type": "vectorSearch",
  "definition": {
    "fields": [
      {
        "path": "embeddings",
        "dimensions": 384,
        "similarity": "cosine",
        "type": "vector"
      }
    ]
  }
}
```

### 3. Create Hybrid Search Index (Optional but Recommended)

For better search quality, also create a hybrid index:

```json
{
  "name": "kb_hybrid_index",
  "type": "search",
  "definition": {
    "mappings": {
      "dynamic": false,
      "fields": {
        "title": {
          "type": "string",
          "analyzer": "lucene.standard"
        },
        "description": {
          "type": "string",
          "analyzer": "lucene.standard"
        },
        "indexed_content": {
          "type": "string",
          "analyzer": "lucene.standard"
        },
        "chunks": {
          "type": "document",
          "fields": {
            "content": {
              "type": "string",
              "analyzer": "lucene.standard"
            }
          }
        },
        "embeddings": {
          "type": "knnVector",
          "dimensions": 384,
          "similarity": "cosine"
        },
        "company_id": {
          "type": "string"
        },
        "brand_id": {
          "type": "string"
        },
        "ai_agent_ids": {
          "type": "string"
        }
      }
    }
  }
}
```

## Verification Steps

### 1. Check Index Status
In MongoDB Atlas:
- Go to "Search" tab
- Look for `kb_index`
- Status should be "Active"
- Dimensions should show "384"

### 2. Test with MongoDB Compass or Shell

```javascript
// Test query
db.knowledge_base_items.aggregate([
  {
    $search: {
      index: "kb_index",
      knnBeta: {
        vector: [/* 384-dimensional array */],
        path: "embeddings",
        k: 10
      }
    }
  },
  {
    $limit: 5
  }
])
```

### 3. Test via API

```bash
# Check embedding configuration
curl http://localhost:8000/api/knowledge-base/embedding-info

# Should return:
{
  "provider": "huggingface",
  "model": "sentence-transformers/all-MiniLM-L6-v2",
  "dimension": 384,  # ← This should match index
  "status": "active"
}
```

## Important Notes

### ⚠️ Re-indexing Required
If you have existing documents with 1536-dimensional embeddings:
1. You MUST re-process all documents
2. Use the `/api/knowledge-base/items/{item_id}/ingest` endpoint
3. Or create a batch re-indexing script

### Dimension Compatibility

| Embedding Provider | Model | Dimensions | Index Config |
|-------------------|-------|------------|--------------|
| HuggingFace | all-MiniLM-L6-v2 | 384 | `"dimensions": 384` |
| OpenAI | text-embedding-3-small | 1536 | `"dimensions": 1536` |
| OpenAI | text-embedding-3-large | 3072 | `"dimensions": 3072` |

### Current System Status
- **Embedding Provider**: HuggingFace (default)
- **Model**: sentence-transformers/all-MiniLM-L6-v2
- **Dimensions**: 384
- **All new documents**: Will use 384-dimensional embeddings

## Troubleshooting

### Error: "Vector dimension mismatch"
**Cause**: Index expects different dimension than provided
**Solution**: Ensure index dimensions match embedding provider

### Error: "Index not found"
**Cause**: Index doesn't exist or wrong name
**Solution**: Create index with exact name `kb_index`

### Error: "No results found"
**Cause**: Documents not re-indexed with new embeddings
**Solution**: Re-process all documents after index update

## Performance Considerations

### HuggingFace (384 dimensions)
- ✅ Smaller index size (75% reduction)
- ✅ Faster searches
- ✅ Lower memory usage
- ⚠️ Slightly lower accuracy than OpenAI

### OpenAI (1536 dimensions)
- ✅ Higher accuracy
- ⚠️ 4x larger index size
- ⚠️ Slower searches
- ⚠️ Higher memory usage

## Migration Script

If you need to re-index all documents:

```python
# Python script to re-index all documents
import asyncio
from app.services.knowledge_base_service import knowledge_base_service
from app.services.langchain_ingestion_service import langchain_ingestion_service

async def reindex_all():
    # Get all items
    items = await knowledge_base_service.list_items(limit=1000)
    
    for item in items:
        if item.get('s3_key'):
            print(f"Re-indexing {item['_id']}: {item.get('title')}")
            await langchain_ingestion_service.process_document(
                item_id=item['_id'],
                s3_key=item['s3_key'],
                mime_type=item.get('mime_type', 'text/plain')
            )
    
    print("Re-indexing complete!")

# Run the migration
asyncio.run(reindex_all())
```

## Summary

1. **Delete** old 1536-dimension index
2. **Create** new 384-dimension index
3. **Re-process** existing documents (if any)
4. **Verify** with test queries

The system is already configured to use HuggingFace embeddings (384 dimensions), so once the index is updated, vector search will work correctly.