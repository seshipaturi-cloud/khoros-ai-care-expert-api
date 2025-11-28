#!/bin/bash

set -e

echo "======================================"
echo "Creating GitHub Webhook for Pipeline"
echo "======================================"

# Variables
PIPELINE_NAME="care-demo-api-service-pipeline"
REGION="us-west-2"
GITHUB_OWNER="seshipaturi-cloud"
GITHUB_REPO="khoros-ai-care-expert-api"

echo "📝 Getting GitHub OAuth token from pipeline..."
OAUTH_TOKEN=$(aws codepipeline get-pipeline \
    --name $PIPELINE_NAME \
    --region $REGION \
    --query 'pipeline.stages[0].actions[0].configuration.OAuthToken' \
    --output text)

if [ -z "$OAUTH_TOKEN" ] || [ "$OAUTH_TOKEN" == "None" ]; then
    echo "❌ Error: Could not retrieve OAuth token from pipeline"
    exit 1
fi

echo "✅ OAuth token obtained"

echo "🔍 Checking if webhook already exists..."
WEBHOOK_ARN=$(aws codepipeline list-webhooks \
    --region $REGION \
    --query "webhooks[?definition.name=='${PIPELINE_NAME}-webhook'].arn" \
    --output text)

if [ ! -z "$WEBHOOK_ARN" ]; then
    echo "⚠️  Webhook already exists with ARN: $WEBHOOK_ARN"
    echo "Do you want to delete and recreate it? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "🗑️  Deleting existing webhook..."
        aws codepipeline delete-webhook \
            --name "${PIPELINE_NAME}-webhook" \
            --region $REGION
        echo "✅ Webhook deleted"
    else
        echo "ℹ️  Keeping existing webhook"
        exit 0
    fi
fi

echo "🚀 Creating new webhook..."
WEBHOOK_OUTPUT=$(aws codepipeline put-webhook \
    --region $REGION \
    --cli-input-json '{
        "webhook": {
            "name": "'${PIPELINE_NAME}'-webhook",
            "targetPipeline": "'${PIPELINE_NAME}'",
            "targetAction": "SourceAction",
            "filters": [
                {
                    "jsonPath": "$.ref",
                    "matchEquals": "refs/heads/main"
                }
            ],
            "authentication": "GITHUB_HMAC",
            "authenticationConfiguration": {
                "SecretToken": "'${OAUTH_TOKEN}'"
            }
        }
    }')

WEBHOOK_URL=$(echo $WEBHOOK_OUTPUT | jq -r '.webhook.url')

echo "✅ Webhook created successfully"
echo "Webhook URL: $WEBHOOK_URL"

echo ""
echo "🔗 Registering webhook with GitHub..."
aws codepipeline register-webhook-with-third-party \
    --webhook-name "${PIPELINE_NAME}-webhook" \
    --region $REGION

echo "✅ Webhook registered with GitHub"

echo ""
echo "======================================"
echo "Webhook Configuration Complete"
echo "======================================"
echo "Webhook Name: ${PIPELINE_NAME}-webhook"
echo "Webhook URL: $WEBHOOK_URL"
echo "GitHub Repo: $GITHUB_OWNER/$GITHUB_REPO"
echo "Trigger Branch: main"
echo ""
echo "The pipeline will now automatically trigger on pushes to the main branch"
echo ""
