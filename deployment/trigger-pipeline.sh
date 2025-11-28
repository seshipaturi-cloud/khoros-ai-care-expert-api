#!/bin/bash

set -e

echo "======================================"
echo "Manually Triggering Pipeline"
echo "======================================"

# Variables
PIPELINE_NAME="care-demo-api-service-pipeline"
REGION="us-west-2"

echo "🚀 Starting pipeline execution..."
EXECUTION_OUTPUT=$(aws codepipeline start-pipeline-execution \
    --name $PIPELINE_NAME \
    --region $REGION)

EXECUTION_ID=$(echo $EXECUTION_OUTPUT | jq -r '.pipelineExecutionId')

echo "✅ Pipeline execution started"
echo ""
echo "Execution ID: $EXECUTION_ID"
echo ""
echo "======================================"
echo "Monitor the pipeline:"
echo "  ./deployment/check-pipeline-status.sh"
echo ""
echo "AWS Console:"
echo "  https://console.aws.amazon.com/codesuite/codepipeline/pipelines/$PIPELINE_NAME/view"
echo ""
