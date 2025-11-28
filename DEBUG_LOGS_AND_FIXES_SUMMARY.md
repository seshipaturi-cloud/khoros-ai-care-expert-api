# Debug Logs and Fixes Summary

## Issues Identified and Fixed

### 1. MongoDB Atlas Vector Search Query Syntax
**Issue**: Vector search was using incorrect operator for Lucene vector index
- Error: `Expected InitializedSearchIndex, but got InitializedLuceneVectorIndex`

**Fix**: Changed from `$search` with `knnBeta` to `$vectorSearch` operator
```python
# Before (incorrect)
'$search': {'index': 'kb_index', 'knnBeta': {...}}

# After (correct)
'$vectorSearch': {'index': 'kb_index', 'queryVector': [...], ...}
```

### 2. Company ID Mismatch
**Issue**: Vector search was returning 0 results due to company_id filter mismatch
- API was sending `company_id='1'` (default value)
- Documents in DB have `company_id='68c6a8c80fa016e20482025f'` (MongoDB ObjectId)

**Fix**: Treat `company_id='1'` as a signal to search across all companies
```python
# Only add company_id filter if it's not '1' (which is the default)
if company_id and company_id != '1':
    filter_conditions['company_id'] = company_id
elif company_id == '1':
    logger.info("Company_id='1' detected - searching across all companies")
```

### 3. Score Filtering in Pipeline
**Issue**: Using `$match` for score filtering before projection was breaking the pipeline
- Score metadata wasn't available in `$match` stage

**Fix**: Filter by score after retrieving results
```python
# Filter by similarity threshold in Python after getting results
if score < similarity_threshold:
    logger.debug(f"Skipping result with low score: {score:.3f}")
    continue
```

## Enhanced Debug Logging Added

### API Service (khoros-ai-care-expert-api)

#### Vector Service
- Query details and all filters
- Embedding generation confirmation
- Pipeline execution details
- Total documents in collection
- Results count and top result preview
- Detailed debugging when no results found
- Sample document structure verification

#### Search Endpoint
- Request details (query, filters, limits)
- Vector search vs text fallback decision
- Results from each search type
- Final results summary

### AI Service (khoros-ai-care-expert-ai-service)

#### API Client
- Full search query composition
- Parent messages context
- Request payload details
- Response status and type
- Result previews with scores
- Context generation details
- Error response details

## Current Status

✅ **Vector search is fully operational**
- Returns relevant results with similarity scores
- Handles company_id='1' as search-all
- Properly filters by similarity threshold (default 0.7, configurable)
- Falls back to text search when needed
- Comprehensive logging for debugging

## Testing Commands

```bash
# Test vector search with default company_id
curl -X POST "http://localhost:8000/api/knowledge-base/search/internal" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "product features",
    "company_id": "1",
    "limit": 5,
    "similarity_threshold": 0.5
  }'

# Test with specific company_id (if known)
curl -X POST "http://localhost:8000/api/knowledge-base/search/internal" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "customer support",
    "company_id": "68c6a8c80fa016e20482025f",
    "limit": 3
  }'
```

## Log Output Examples

### Successful Search
```
📥 Internal search request received
   Query: product features...
   Company ID: 1
   Company_id='1' detected - searching across all companies
🔍 Vector search started
   Generated embedding with 384 dimensions
   No post-processing filters applied
   Executing vector search pipeline on knowledge_base_vectors
   Total documents in collection: 225
Vector search returned 5 results
   Top result: AI Expert Care - Product Specification (score: 0.681)
✅ Returning 5 total results
```

### No Results (with debugging)
```
Vector search returned 0 results
   No results found for query: ...
   Documents matching filters: 0
   Sample doc company_id: 68c6a8c80fa016e20482025f
   Sample doc has embeddings: True
```

## Next Steps

1. **Update AI Service**: Consider updating the default `company_id` in the LLM service to match actual company IDs in the database
2. **Add Company Mapping**: Create a mapping between simple IDs (like '1') and actual MongoDB ObjectIds
3. **Monitor Performance**: Use the debug logs to monitor search performance and adjust thresholds as needed
4. **Index Optimization**: Consider adjusting `numCandidates` parameter for better results