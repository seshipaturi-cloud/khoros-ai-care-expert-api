// MongoDB Atlas Vector Index Fix Script
// Run this in MongoDB Atlas Data Explorer or MongoDB Shell

// Switch to the correct database
use("ai-care-expert");

// ============================================
// STEP 1: Check Current Search Indexes
// ============================================
print("=== Checking Current Search Indexes ===");

// Note: You cannot list Atlas Search indexes via MongoDB Shell
// You must use Atlas UI or Atlas CLI for this
print("Please check Atlas UI -> Search tab for existing indexes");
print("Look for index named 'kb_index' and delete it if it exists");

// ============================================
// STEP 2: Check Sample Documents
// ============================================
print("\n=== Checking Sample Documents ===");

// Check knowledge_base_items collection
print("\n📋 Sample from knowledge_base_items:");
let itemSample = db.knowledge_base_items.findOne({embeddings: {$exists: true}});
if (itemSample) {
    print("  Found document with embeddings");
    if (itemSample.embeddings && itemSample.embeddings.length > 0) {
        print(`  Number of embedding vectors: ${itemSample.embeddings.length}`);
        if (Array.isArray(itemSample.embeddings[0])) {
            print(`  Embedding dimensions: ${itemSample.embeddings[0].length}`);
        }
    }
    print(`  Embedding provider: ${itemSample.embedding_provider || 'Unknown'}`);
    print(`  Embedding model: ${itemSample.embedding_model || 'Unknown'}`);
} else {
    print("  No documents with embeddings found");
}

// Check knowledge_base_vectors collection
print("\n📋 Sample from knowledge_base_vectors:");
let vectorSample = db.knowledge_base_vectors.findOne({embeddings: {$exists: true}});
if (vectorSample) {
    print("  Found vector document");
    if (vectorSample.embeddings) {
        print(`  Embedding dimensions: ${vectorSample.embeddings.length}`);
    }
    print(`  Embedding provider: ${vectorSample.embedding_provider || 'Unknown'}`);
    print(`  Embedding model: ${vectorSample.embedding_model || 'Unknown'}`);
} else {
    print("  No vector documents found");
}

// ============================================
// STEP 3: Create Regular Indexes (not vector)
// ============================================
print("\n=== Creating Regular Indexes ===");

// Create indexes for knowledge_base_items
print("\n Creating indexes for knowledge_base_items...");
db.knowledge_base_items.createIndex({company_id: 1});
db.knowledge_base_items.createIndex({ai_agent_ids: 1});
db.knowledge_base_items.createIndex({brand_ids: 1});
db.knowledge_base_items.createIndex({indexing_status: 1});
db.knowledge_base_items.createIndex({content_type: 1});
db.knowledge_base_items.createIndex({
    title: "text",
    description: "text",
    indexed_content: "text"
});
print("  ✅ Created regular indexes for knowledge_base_items");

// Create indexes for knowledge_base_vectors
print("\n Creating indexes for knowledge_base_vectors...");
db.knowledge_base_vectors.createIndex({knowledge_item_id: 1});
db.knowledge_base_vectors.createIndex({company_id: 1});
db.knowledge_base_vectors.createIndex({ai_agent_ids: 1});
db.knowledge_base_vectors.createIndex({brand_ids: 1});
db.knowledge_base_vectors.createIndex({chunk_index: 1});
db.knowledge_base_vectors.createIndex({
    chunk_text: "text"
});
print("  ✅ Created regular indexes for knowledge_base_vectors");

// ============================================
// STEP 4: Vector Index Configuration
// ============================================
print("\n=== Vector Index Configuration ===");
print("\n⚠️  IMPORTANT: Vector Search indexes must be created via Atlas UI or CLI");
print("\nGo to MongoDB Atlas UI -> Search Tab -> Create Search Index");
print("\nFor knowledge_base_items collection, use this JSON:");
print(`
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
`);

print("\nFor knowledge_base_vectors collection, use this JSON:");
print(`
{
  "name": "kb_vectors_index",
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
`);

// ============================================
// STEP 5: Test Queries (after index creation)
// ============================================
print("\n=== Test Queries (run after creating vector indexes) ===");

print("\nTest query for vector search (will only work after index is created):");
print(`
db.knowledge_base_vectors.aggregate([
  {
    $vectorSearch: {
      index: "kb_vectors_index",
      path: "embeddings",
      queryVector: [/* 384 numbers here */],
      numCandidates: 100,
      limit: 5
    }
  },
  {
    $project: {
      chunk_text: 1,
      score: {$meta: "vectorSearchScore"}
    }
  }
])
`);

// ============================================
// STEP 6: Summary
// ============================================
print("\n" + "=".repeat(60));
print("SUMMARY OF REQUIRED ACTIONS:");
print("=".repeat(60));
print("\n1. Go to MongoDB Atlas UI -> Your Cluster -> Search Tab");
print("2. Delete any existing 'kb_index' (if present)");
print("3. Create new Vector Search indexes using the JSON above");
print("4. Wait 2-5 minutes for indexes to become Active");
print("5. Test vector search with the sample query");
print("\n✅ Regular indexes have been created successfully!");
print("⏳ Vector indexes need manual creation in Atlas UI");

// Count documents
let itemCount = db.knowledge_base_items.countDocuments();
let vectorCount = db.knowledge_base_vectors.countDocuments();
print(`\n📊 Statistics:`);
print(`  knowledge_base_items: ${itemCount} documents`);
print(`  knowledge_base_vectors: ${vectorCount} documents`);