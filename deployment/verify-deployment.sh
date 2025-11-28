#!/bin/bash

set -e

echo "======================================"
echo "Verifying API Service Deployment"
echo "======================================"

# Variables
NAMESPACE="ai-care-expert"
DEPLOYMENT_NAME="api-service"
SERVICE_NAME="api-service"
REGION="us-west-2"
EKS_CLUSTER="care-demo-qa-001"

echo "📝 Configuring kubectl for EKS cluster..."
aws eks update-kubeconfig --region $REGION --name $EKS_CLUSTER --alias $EKS_CLUSTER

echo ""
echo "🔍 Checking Deployment Status..."
echo "======================================"
kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o wide

echo ""
echo "🔍 Checking Pods..."
echo "======================================"
kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT_NAME -o wide

echo ""
echo "🔍 Checking Pod Health..."
echo "======================================"
kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT_NAME -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\t"}{.status.containerStatuses[0].ready}{"\n"}{end}' | column -t

echo ""
echo "🔍 Checking Service..."
echo "======================================"
kubectl get svc $SERVICE_NAME -n $NAMESPACE -o wide

echo ""
echo "🔍 Checking HPA (Horizontal Pod Autoscaler)..."
echo "======================================"
kubectl get hpa -n $NAMESPACE -l app=$DEPLOYMENT_NAME

echo ""
echo "🔍 Checking ConfigMap..."
echo "======================================"
kubectl get configmap ${DEPLOYMENT_NAME}-config -n $NAMESPACE

echo ""
echo "🔍 Checking Secrets..."
echo "======================================"
kubectl get secret ${DEPLOYMENT_NAME}-secrets -n $NAMESPACE

echo ""
echo "🔍 Recent Events..."
echo "======================================"
kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | tail -20

echo ""
echo "======================================"
echo "Verification Complete"
echo "======================================"
echo ""
echo "Useful commands:"
echo "  View logs: kubectl logs -f deployment/$DEPLOYMENT_NAME -n $NAMESPACE"
echo "  Describe pod: kubectl describe pod -l app=$DEPLOYMENT_NAME -n $NAMESPACE"
echo "  Get pod details: kubectl get pod -l app=$DEPLOYMENT_NAME -n $NAMESPACE -o yaml"
echo "  Restart deployment: kubectl rollout restart deployment/$DEPLOYMENT_NAME -n $NAMESPACE"
echo "  Check rollout status: kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE"
echo ""
