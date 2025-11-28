#!/bin/bash

set -e

echo "======================================"
echo "Checking Pipeline Status"
echo "======================================"

# Variables
PIPELINE_NAME="care-demo-api-service-pipeline"
REGION="us-west-2"

echo "📝 Getting pipeline state..."
PIPELINE_STATE=$(aws codepipeline get-pipeline-state \
    --name $PIPELINE_NAME \
    --region $REGION)

echo ""
echo "Pipeline: $PIPELINE_NAME"
echo "======================================"

# Extract and display stage information
echo "$PIPELINE_STATE" | jq -r '.stageStates[] |
    "Stage: \(.stageName)\nStatus: \(.latestExecution.status // "N/A")\n"'

echo ""
echo "🔍 Latest execution details..."
LATEST_EXECUTION=$(aws codepipeline list-pipeline-executions \
    --pipeline-name $PIPELINE_NAME \
    --region $REGION \
    --max-items 1)

echo "$LATEST_EXECUTION" | jq -r '.pipelineExecutionSummaries[0] |
    "Execution ID: \(.pipelineExecutionId)\nStatus: \(.status)\nStart Time: \(.startTime)\nLast Update: \(.lastUpdateTime)"'

echo ""
echo "======================================"
echo "For detailed logs:"
echo "  AWS Console: https://console.aws.amazon.com/codesuite/codepipeline/pipelines/$PIPELINE_NAME/view"
echo ""
echo "To manually trigger:"
echo "  ./deployment/trigger-pipeline.sh"
echo ""
