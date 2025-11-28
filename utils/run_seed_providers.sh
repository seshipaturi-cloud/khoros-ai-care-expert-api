#!/bin/bash

# Script to run the LLM providers seeding utility
# Usage: ./utils/run_seed_providers.sh

echo "🚀 Starting LLM Providers Seeding Script"
echo "========================================"

# Set environment variables if needed
export API_BASE_URL=${API_BASE_URL:-"http://localhost:8000"}
export API_TOKEN=${API_TOKEN:-""}  # Add your auth token if required

# Navigate to the project root
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
fi

# Run the seeding script
echo "🌱 Running seed script..."
python utils/seed_llm_providers.py

echo "✅ Done!"