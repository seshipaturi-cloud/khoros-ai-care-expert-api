#!/bin/bash

set -e

echo "======================================"
echo "Creating CodePipeline for API Service"
echo "======================================"

# Set variables
PIPELINE_NAME="care-demo-api-service-pipeline"
REGION="us-west-2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE_JSON="$SCRIPT_DIR/pipeline.json"

# Check if pipeline.json exists
if [ ! -f "$PIPELINE_JSON" ]; then
    echo "❌ Error: pipeline.json not found at $PIPELINE_JSON"
    exit 1
fi

echo "📝 Fetching GitHub OAuth token from existing pipeline..."
# Try to get OAuth token from an existing pipeline (ai-service pipeline)
OAUTH_TOKEN=$(aws codepipeline get-pipeline \
    --name care-demo-ai-service-pipeline \
    --region $REGION \
    --query 'pipeline.stages[0].actions[0].configuration.OAuthToken' \
    --output text 2>/dev/null || echo "")

if [ -z "$OAUTH_TOKEN" ] || [ "$OAUTH_TOKEN" == "None" ]; then
    echo "⚠️  Warning: Could not fetch OAuth token from existing pipeline"
    echo "Please enter your GitHub OAuth token manually:"
    read -s OAUTH_TOKEN
    if [ -z "$OAUTH_TOKEN" ]; then
        echo "❌ Error: OAuth token is required"
        exit 1
    fi
fi

echo "✅ OAuth token obtained"

# Create temporary pipeline JSON with OAuth token
TEMP_PIPELINE_JSON=$(mktemp)
cat "$PIPELINE_JSON" | jq --arg token "$OAUTH_TOKEN" \
    '.pipeline.stages[0].actions[0].configuration.OAuthToken = $token' \
    > "$TEMP_PIPELINE_JSON"

echo "🔍 Checking if pipeline already exists..."
if aws codepipeline get-pipeline --name "$PIPELINE_NAME" --region "$REGION" &>/dev/null; then
    echo "⚠️  Pipeline $PIPELINE_NAME already exists"
    echo "Do you want to update it? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "🔄 Updating pipeline..."
        aws codepipeline update-pipeline \
            --cli-input-json file://"$TEMP_PIPELINE_JSON" \
            --region "$REGION"
        echo "✅ Pipeline updated successfully"
    else
        echo "ℹ️  Pipeline update cancelled"
    fi
else
    echo "🚀 Creating new pipeline..."
    aws codepipeline create-pipeline \
        --cli-input-json file://"$TEMP_PIPELINE_JSON" \
        --region "$REGION"
    echo "✅ Pipeline created successfully"
fi

# Clean up temp file
rm -f "$TEMP_PIPELINE_JSON"

echo ""
echo "======================================"
echo "Pipeline Configuration Complete"
echo "======================================"
echo "Pipeline Name: $PIPELINE_NAME"
echo "Region: $REGION"
echo ""
echo "Next steps:"
echo "1. Create webhook: ./deployment/create-webhook.sh"
echo "2. Setup secrets: ./deployment/setup-secrets.sh"
echo "3. Verify pipeline: ./deployment/check-pipeline-status.sh"
echo ""
