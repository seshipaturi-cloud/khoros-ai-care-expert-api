# RAG Answer Generation Implementation

## Overview
Implemented a RAG (Retrieval Augmented Generation) answer endpoint that returns synthesized answers from the knowledge base instead of raw documents.

## Changes Made

### 1. New API Endpoint
**`POST /api/knowledge-base/answer/internal`**
- Internal endpoint for RAG-based answer generation
- No authentication required (for service-to-service communication)
- Returns synthesized answer with sources

### 2. RAG Service Updates
- Updated `vector_search` method to use the improved `vector_service`
- Simplified text_search to use vector search with lower threshold
- Fixed field mapping (`chunk_content` instead of `content`)
- Removed old deprecated search code

### 3. AI Service Integration
- Updated `search_knowledge_base_with_context` method in `api_client.py`
- Added `use_rag_answer` parameter (default=True)
- Calls new `/answer/internal` endpoint for RAG answers
- Falls back to document search if RAG fails

## API Usage

### Request
```bash
POST /api/knowledge-base/answer/internal
Content-Type: application/json

{
    "query": "What are the key features of AI Expert Care?",
    "company_id": "1",
    "agent_ids": ["agent1"],
    "limit": 5,
    "similarity_threshold": 0.4
}
```

### Response
```json
{
    "answer": "Based on the knowledge base, here are the key features...",
    "sources": [
        {
            "title": "AI Expert Care - Product Specification",
            "score": 0.95,
            "content_type": "document"
        }
    ],
    "success": true,
    "search_type": "rag_answer"
}
```

## Integration with AI Service

The AI service now calls this endpoint by default when searching the knowledge base:

```python
# In AI service
kb_search_result = await api_client.search_knowledge_base_with_context(
    current_message="user question",
    parent_messages=["context1", "context2"],
    company_id="1",
    use_rag_answer=True  # New parameter - returns answer instead of documents
)

# Response contains
# kb_search_result["knowledge_context"] = "The synthesized answer..."
# kb_search_result["results"] = [list of source documents]
```

## Benefits

1. **Better User Experience**: Returns direct answers instead of requiring the AI service to process raw documents
2. **Reduced Latency**: Single LLM call for answer generation at the API level
3. **Consistent Answers**: Uses the same RAG pipeline for all knowledge base queries
4. **Source Attribution**: Includes sources for transparency and verification
5. **Fallback Support**: Can fall back to document search if needed

## Configuration

### Environment Variables
- `ANTHROPIC_API_KEY`: For Claude-based answer generation (primary)
- `OPENAI_API_KEY`: Fallback LLM for answer generation
- `EMBEDDING_PROVIDER`: "huggingface" (default) or "openai"

### Search Parameters
- `similarity_threshold`: 0.3-0.7 (lower = more results)
- `limit`: Number of documents to retrieve (default: 5)
- `search_type`: "vector", "text", or "hybrid"

## Error Handling

- Returns friendly error message if answer generation fails
- Falls back to document search if RAG endpoint fails
- Always returns structured response even on error

## Performance

- Vector search with company_id='1' searches across all companies
- Typical response time: 2-5 seconds for answer generation
- Handles queries up to 1000 characters
- Returns answers of 200-1000 words typically

## Testing

```bash
# Test RAG answer generation
curl -X POST "http://localhost:8000/api/knowledge-base/answer/internal" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the features?",
    "company_id": "1",
    "limit": 5
  }'
```

## Next Steps

1. Add caching for frequent queries
2. Implement conversation history context
3. Add support for follow-up questions
4. Optimize embedding generation
5. Add response streaming for long answers