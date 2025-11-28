#!/bin/bash

set -e

echo "======================================"
echo "Kubernetes Secrets Setup for API Service"
echo "======================================"

# Variables
NAMESPACE="ai-care-expert"
SECRET_NAME="api-service-secrets"
REGION="us-west-2"
EKS_CLUSTER="care-demo-qa-001"

echo "📝 Configuring kubectl for EKS cluster..."
aws eks update-kubeconfig --region $REGION --name $EKS_CLUSTER

echo "🔍 Checking if namespace exists..."
if ! kubectl get namespace $NAMESPACE &>/dev/null; then
    echo "📦 Creating namespace $NAMESPACE..."
    kubectl create namespace $NAMESPACE
    echo "✅ Namespace created"
else
    echo "✅ Namespace $NAMESPACE already exists"
fi

echo ""
echo "Please provide the following secrets:"
echo "======================================"

# Prompt for secrets
echo -n "MongoDB URI: "
read -s MONGODB_URI
echo ""

echo -n "OpenAI API Key (optional, press Enter to skip): "
read -s OPENAI_API_KEY
echo ""

echo -n "Anthropic API Key (optional, press Enter to skip): "
read -s ANTHROPIC_API_KEY
echo ""

echo -n "JWT Secret Key: "
read -s JWT_SECRET_KEY
echo ""

echo -n "AWS Access Key ID (optional, press Enter to skip): "
read -s AWS_ACCESS_KEY_ID
echo ""

echo -n "AWS Secret Access Key (optional, press Enter to skip): "
read -s AWS_SECRET_ACCESS_KEY
echo ""

echo -n "Firecrawl API Key (optional, press Enter to skip): "
read -s FIRECRAWL_API_KEY
echo ""

echo ""
echo "🔍 Checking if secret already exists..."
if kubectl get secret $SECRET_NAME -n $NAMESPACE &>/dev/null; then
    echo "⚠️  Secret $SECRET_NAME already exists"
    echo "Do you want to delete and recreate it? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "🗑️  Deleting existing secret..."
        kubectl delete secret $SECRET_NAME -n $NAMESPACE
    else
        echo "ℹ️  Keeping existing secret. Exiting."
        exit 0
    fi
fi

echo "🔐 Creating Kubernetes secret..."

# Build the kubectl create secret command
CMD="kubectl create secret generic $SECRET_NAME -n $NAMESPACE"
CMD="$CMD --from-literal=mongodb-uri=\"$MONGODB_URI\""
CMD="$CMD --from-literal=jwt-secret-key=\"$JWT_SECRET_KEY\""

if [ ! -z "$OPENAI_API_KEY" ]; then
    CMD="$CMD --from-literal=openai-api-key=\"$OPENAI_API_KEY\""
fi

if [ ! -z "$ANTHROPIC_API_KEY" ]; then
    CMD="$CMD --from-literal=anthropic-api-key=\"$ANTHROPIC_API_KEY\""
fi

if [ ! -z "$AWS_ACCESS_KEY_ID" ]; then
    CMD="$CMD --from-literal=aws-access-key-id=\"$AWS_ACCESS_KEY_ID\""
fi

if [ ! -z "$AWS_SECRET_ACCESS_KEY" ]; then
    CMD="$CMD --from-literal=aws-secret-access-key=\"$AWS_SECRET_ACCESS_KEY\""
fi

if [ ! -z "$FIRECRAWL_API_KEY" ]; then
    CMD="$CMD --from-literal=firecrawl-api-key=\"$FIRECRAWL_API_KEY\""
fi

# Execute the command
eval $CMD

echo "✅ Secret created successfully"

echo ""
echo "======================================"
echo "Secrets Configuration Complete"
echo "======================================"
echo "Secret Name: $SECRET_NAME"
echo "Namespace: $NAMESPACE"
echo ""
echo "To verify:"
echo "  kubectl get secret $SECRET_NAME -n $NAMESPACE"
echo ""
echo "To update deployment with new secrets:"
echo "  kubectl rollout restart deployment/api-service -n $NAMESPACE"
echo ""
