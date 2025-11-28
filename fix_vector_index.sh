#!/bin/bash

# MongoDB Atlas Vector Index Fix Script
# This script uses MongoDB Atlas CLI to fix vector search indexes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load configuration from .env file
if [ -f .env ]; then
    echo -e "${GREEN}Loading configuration from .env file...${NC}"
    # Export all variables from .env file
    set -a
    source .env
    set +a
else
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please ensure you're in the khoros-ai-care-expert-api directory"
    exit 1
fi

# Parse MongoDB URI to extract cluster information
if [ -z "$MONGODB_URI" ]; then
    echo -e "${RED}❌ MONGODB_URI not found in .env file${NC}"
    exit 1
fi

# Extract cluster name from MongoDB URI
# Format: mongodb+srv://username:password@cluster-name.xxxxx.mongodb.net/database
if [[ $MONGODB_URI =~ mongodb\+srv://[^@]+@([^.]+)\.([^/]+)/?(.*) ]]; then
    CLUSTER_NAME="${BASH_REMATCH[1]}"
    CLUSTER_DOMAIN="${BASH_REMATCH[2]}"
    URI_DATABASE="${BASH_REMATCH[3]}"
elif [[ $MONGODB_URI =~ mongodb://[^@]+@([^:]+):([^/]+)/?(.*) ]]; then
    # For standard mongodb:// URIs
    echo -e "${YELLOW}⚠️  Using standard MongoDB URI. Atlas Search requires MongoDB Atlas.${NC}"
    CLUSTER_NAME="local-cluster"
fi

# Use database from env or extracted from URI
DATABASE="${MONGODB_DATABASE:-${URI_DATABASE:-ai-care-expert}}"

# For PROJECT_ID, we need user input or environment variable
PROJECT_ID="${ATLAS_PROJECT_ID:-}"

# If PROJECT_ID is not set, try to get it from Atlas CLI config
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(atlas config get project_id 2>/dev/null)
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}MongoDB Atlas Vector Index Fix Script${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if Atlas CLI is installed
if ! command -v atlas &> /dev/null; then
    echo -e "${RED}❌ MongoDB Atlas CLI is not installed${NC}"
    echo "Please install it first: https://www.mongodb.com/docs/atlas/cli/stable/install-atlas-cli/"
    exit 1
fi

echo -e "\n${GREEN}Configuration loaded from .env:${NC}"
echo -e "  MongoDB URI: ${MONGODB_URI:0:30}..."
echo -e "  Cluster: ${CLUSTER_NAME}"
echo -e "  Database: ${DATABASE}"

# Check if PROJECT_ID is available
if [ -z "$PROJECT_ID" ]; then
    echo -e "\n${YELLOW}MongoDB Atlas Project ID is required.${NC}"
    echo -e "You can find it in MongoDB Atlas UI (URL contains it) or run:"
    echo -e "  ${BLUE}atlas projects list${NC}"
    echo -e "\n${YELLOW}Please enter your MongoDB Atlas Project ID:${NC}"
    read -r PROJECT_ID
    
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}❌ Project ID is required${NC}"
        exit 1
    fi
    
    # Optionally save it for future use
    echo -e "\n${YELLOW}Save this Project ID to .env file? (y/n)${NC}"
    read -r SAVE_CHOICE
    if [[ $SAVE_CHOICE == "y" ]]; then
        echo -e "\n# MongoDB Atlas Project ID" >> .env
        echo "ATLAS_PROJECT_ID=${PROJECT_ID}" >> .env
        echo -e "${GREEN}✅ Project ID saved to .env${NC}"
    fi
else
    echo -e "  Project: ${PROJECT_ID}"
fi

echo -e "\n${GREEN}Ready to proceed with fixing vector indexes${NC}"
echo -e "Press Enter to continue or Ctrl+C to exit..."
read

# Set the project
echo -e "\n${BLUE}Setting project...${NC}"
atlas config set project_id $PROJECT_ID

# Step 1: List existing search indexes
echo -e "\n${BLUE}Step 1: Listing existing search indexes...${NC}"
echo -e "\n${YELLOW}Indexes on knowledge_base_items:${NC}"
atlas clusters search indexes list \
    --clusterName $CLUSTER_NAME \
    --db $DATABASE \
    --collection knowledge_base_items \
    --output json | jq -r '.[] | "\(.id): \(.name) (Status: \(.status))"' 2>/dev/null || echo "No indexes found or jq not installed"

echo -e "\n${YELLOW}Indexes on knowledge_base_vectors:${NC}"
atlas clusters search indexes list \
    --clusterName $CLUSTER_NAME \
    --db $DATABASE \
    --collection knowledge_base_vectors \
    --output json | jq -r '.[] | "\(.id): \(.name) (Status: \(.status))"' 2>/dev/null || echo "No indexes found or jq not installed"

# Step 2: Ask if user wants to delete old indexes
echo -e "\n${YELLOW}Do you want to delete existing indexes? (y/n)${NC}"
read -r DELETE_CHOICE

if [[ $DELETE_CHOICE == "y" ]]; then
    echo -e "${YELLOW}Enter the index ID to delete (or press Enter to skip):${NC}"
    read -r INDEX_ID
    
    if [[ ! -z $INDEX_ID ]]; then
        echo -e "${RED}Deleting index $INDEX_ID...${NC}"
        atlas clusters search indexes delete $INDEX_ID --clusterName $CLUSTER_NAME --force
        echo -e "${GREEN}✅ Index deleted${NC}"
        sleep 2
    fi
fi

# Step 3: Create vector index configuration files
echo -e "\n${BLUE}Step 2: Creating index configuration files...${NC}"

# Create vector index for knowledge_base_items
cat > vector_index_items.json << 'EOF'
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
EOF
echo -e "${GREEN}✅ Created vector_index_items.json${NC}"

# Create vector index for knowledge_base_vectors
cat > vector_index_vectors.json << 'EOF'
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
EOF
echo -e "${GREEN}✅ Created vector_index_vectors.json${NC}"

# Create hybrid index configuration
cat > hybrid_index.json << 'EOF'
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
        "company_id": {
          "type": "string"
        },
        "brand_ids": {
          "type": "string"
        },
        "ai_agent_ids": {
          "type": "string"
        }
      }
    }
  }
}
EOF
echo -e "${GREEN}✅ Created hybrid_index.json${NC}"

# Step 4: Create new indexes
echo -e "\n${BLUE}Step 3: Creating new search indexes...${NC}"

echo -e "\n${YELLOW}Create vector index for knowledge_base_items? (y/n)${NC}"
read -r CREATE_ITEMS

if [[ $CREATE_ITEMS == "y" ]]; then
    echo -e "${BLUE}Creating vector index for knowledge_base_items...${NC}"
    atlas clusters search indexes create \
        --clusterName $CLUSTER_NAME \
        --db $DATABASE \
        --collection knowledge_base_items \
        --file vector_index_items.json
    echo -e "${GREEN}✅ Vector index creation initiated for knowledge_base_items${NC}"
fi

echo -e "\n${YELLOW}Create vector index for knowledge_base_vectors? (y/n)${NC}"
read -r CREATE_VECTORS

if [[ $CREATE_VECTORS == "y" ]]; then
    echo -e "${BLUE}Creating vector index for knowledge_base_vectors...${NC}"
    atlas clusters search indexes create \
        --clusterName $CLUSTER_NAME \
        --db $DATABASE \
        --collection knowledge_base_vectors \
        --file vector_index_vectors.json
    echo -e "${GREEN}✅ Vector index creation initiated for knowledge_base_vectors${NC}"
fi

echo -e "\n${YELLOW}Create hybrid search index? (y/n)${NC}"
read -r CREATE_HYBRID

if [[ $CREATE_HYBRID == "y" ]]; then
    echo -e "${BLUE}Creating hybrid search index...${NC}"
    atlas clusters search indexes create \
        --clusterName $CLUSTER_NAME \
        --db $DATABASE \
        --collection knowledge_base_items \
        --file hybrid_index.json
    echo -e "${GREEN}✅ Hybrid index creation initiated${NC}"
fi

# Step 5: Check index status
echo -e "\n${BLUE}Step 4: Checking index status...${NC}"
echo -e "${YELLOW}Waiting for indexes to become active (this may take 2-5 minutes)...${NC}"
echo -e "${YELLOW}Press Ctrl+C to exit (indexes will continue building)${NC}"

while true; do
    sleep 10
    echo -e "\n${BLUE}Current index status:${NC}"
    
    echo -e "${YELLOW}knowledge_base_items:${NC}"
    atlas clusters search indexes list \
        --clusterName $CLUSTER_NAME \
        --db $DATABASE \
        --collection knowledge_base_items \
        --output json | jq -r '.[] | "  \(.name): \(.status)"' 2>/dev/null
    
    echo -e "${YELLOW}knowledge_base_vectors:${NC}"
    atlas clusters search indexes list \
        --clusterName $CLUSTER_NAME \
        --db $DATABASE \
        --collection knowledge_base_vectors \
        --output json | jq -r '.[] | "  \(.name): \(.status)"' 2>/dev/null
    
    # Check if all indexes are active
    ITEMS_ACTIVE=$(atlas clusters search indexes list --clusterName $CLUSTER_NAME --db $DATABASE --collection knowledge_base_items --output json | jq -r '.[] | select(.name=="kb_index") | .status' 2>/dev/null)
    VECTORS_ACTIVE=$(atlas clusters search indexes list --clusterName $CLUSTER_NAME --db $DATABASE --collection knowledge_base_vectors --output json | jq -r '.[] | select(.name=="kb_vectors_index") | .status' 2>/dev/null)
    
    if [[ $ITEMS_ACTIVE == "READY" ]] && [[ $VECTORS_ACTIVE == "READY" ]]; then
        echo -e "\n${GREEN}✅ All indexes are active!${NC}"
        break
    fi
done

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Vector Index Fix Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "\nNext steps:"
echo -e "1. Test vector search with: python fix_vector_index.py"
echo -e "2. Update app/services/vector_service.py to remove fallback code"
echo -e "3. Restart your application"

# Cleanup
echo -e "\n${YELLOW}Clean up configuration files? (y/n)${NC}"
read -r CLEANUP

if [[ $CLEANUP == "y" ]]; then
    rm -f vector_index_items.json vector_index_vectors.json hybrid_index.json
    echo -e "${GREEN}✅ Configuration files removed${NC}"
fi