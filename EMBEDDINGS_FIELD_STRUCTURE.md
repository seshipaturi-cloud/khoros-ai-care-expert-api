# New Embeddings Field Structure

## Overview
The system has been updated to store embeddings in a dedicated root-level `embeddings` field instead of nested within chunks. This provides better performance and easier indexing for MongoDB Atlas Vector Search.

## Previous Structure (Old)
```json
{
  "_id": "item_123",
  "title": "Document Title",
  "chunks": [
    {
      "chunk_id": "item_123_chunk_0",
      "content": "First chunk text...",
      "embedding": [0.1, 0.2, ...],  // 384 dimensions embedded in each chunk
      "metadata": {...}
    },
    {
      "chunk_id": "item_123_chunk_1", 
      "content": "Second chunk text...",
      "embedding": [0.3, 0.4, ...],  // 384 dimensions embedded in each chunk
      "metadata": {...}
    }
  ]
}
```

## New Structure (Current)
```json
{
  "_id": "item_123",
  "title": "Document Title",
  "chunks": [
    {
      "chunk_id": "item_123_chunk_0",
      "content": "First chunk text...",
      "metadata": {
        "chunk_index": 0,
        "item_id": "item_123"
      }
    },
    {
      "chunk_id": "item_123_chunk_1",
      "content": "Second chunk text...",
      "metadata": {
        "chunk_index": 1,
        "item_id": "item_123"
      }
    }
  ],
  "embeddings": [
    [0.1, 0.2, ...],  // 384 dimensions for chunk 0
    [0.3, 0.4, ...]   // 384 dimensions for chunk 1
  ],
  "embedding_provider": "huggingface",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

## Benefits

### 1. **Simplified Vector Indexing**
- Single field to index: `embeddings`
- No nested path complexity
- Better MongoDB Atlas Vector Search performance

### 2. **Reduced Storage**
- Embeddings stored once at root level
- Chunks contain only text and metadata
- Smaller document size for chunk operations

### 3. **Easier Querying**
- Direct access to embeddings array
- Simpler aggregation pipelines
- Better compatibility with vector search

### 4. **Maintenance**
- Clear separation of concerns
- Easier to update embeddings without modifying chunks
- Simpler backup and migration

## MongoDB Atlas Vector Index Configuration

### Vector Search Index
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

### Hybrid Search Index (Optional)
```json
{
  "name": "kb_hybrid_index",
  "type": "search",
  "definition": {
    "mappings": {
      "dynamic": false,
      "fields": {
        "title": {"type": "string", "analyzer": "lucene.standard"},
        "description": {"type": "string", "analyzer": "lucene.standard"},
        "indexed_content": {"type": "string", "analyzer": "lucene.standard"},
        "chunks": {
          "type": "document",
          "fields": {
            "content": {"type": "string", "analyzer": "lucene.standard"}
          }
        },
        "embeddings": {
          "type": "knnVector",
          "dimensions": 384,
          "similarity": "cosine"
        }
      }
    }
  }
}
```

## How It Works

### 1. **Document Ingestion**
```python
# Generate embeddings for all chunks
chunk_texts = [chunk.content for chunk in chunks]
embeddings_list = embeddings.embed_documents(chunk_texts)

# Store separately
document = {
    "chunks": chunk_docs,        # Text and metadata only
    "embeddings": embeddings_list # All embeddings in array
}
```

### 2. **Vector Search**
The system correlates embeddings with chunks by array index:
- `embeddings[0]` corresponds to `chunks[0]`
- `embeddings[1]` corresponds to `chunks[1]`
- And so on...

### 3. **Retrieval Process**
1. Query embedding is generated
2. Vector search finds similar embeddings
3. Corresponding chunks are retrieved using array index
4. Results include chunk content and similarity score

## Migration from Old Structure

### For Existing Documents with Nested Embeddings
If you have documents with the old structure (embeddings in chunks):

```python
# Migration script pseudo-code
for document in collection.find({"chunks.embedding": {"$exists": True}}):
    embeddings = []
    chunks_without_embeddings = []
    
    for chunk in document["chunks"]:
        embeddings.append(chunk.pop("embedding"))
        chunks_without_embeddings.append(chunk)
    
    collection.update_one(
        {"_id": document["_id"]},
        {"$set": {
            "embeddings": embeddings,
            "chunks": chunks_without_embeddings
        }}
    )
```

## API Changes

### Embedding Info Endpoint
```bash
GET /api/knowledge-base/embedding-info

Response:
{
  "index_configuration": {
    "index_name": "kb_index",
    "path": "embeddings",  # Changed from "chunks.embedding"
    "expected_dimension": 384,
    "similarity": "cosine"
  }
}
```

## Services Updated

### 1. **Ingestion Services**
- `langchain_ingestion_service.py`: Stores embeddings in root field
- `website_ingestion_service.py`: Updated to new structure
- `youtube_service.py`: Uses root embeddings field

### 2. **Search Services**
- `vector_service.py`: Searches on `embeddings` field
- `rag_service.py`: Correlates embeddings with chunks by index

### 3. **Compatibility**
- System checks for embeddings in root field first
- Falls back to checking chunks for backward compatibility
- Migration recommended for optimal performance

## Best Practices

1. **Always Maintain Order**: Embeddings array must match chunks array order
2. **Atomic Updates**: Update both chunks and embeddings together
3. **Validation**: Ensure embeddings.length === chunks.length
4. **Indexing**: Create vector index on `embeddings` field only

## Performance Impact

- **Faster Searches**: Direct array access vs nested document traversal
- **Lower Memory**: Reduced document size for chunk operations
- **Better Scaling**: Optimized for MongoDB Atlas Vector Search
- **Simpler Aggregations**: No need for $unwind on embedded arrays

## Summary

The new structure separates embeddings from chunks, storing them in a dedicated root-level array field. This provides better performance, simpler indexing, and easier maintenance while maintaining the correlation between chunks and their embeddings through array indices.