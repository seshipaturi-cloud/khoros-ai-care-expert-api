# Step-by-Step Deployment Guide
## Khoros AI Care Expert API - AWS Deployment

This guide will walk you through deploying the API service step by step.

## Prerequisites Checklist

- [ ] AWS CLI installed and configured with valid credentials
- [ ] kubectl installed
- [ ] jq installed (`brew install jq` on macOS)
- [ ] Valid AWS session with admin access to account 642760139656
- [ ] Access to EKS cluster: care-demo-qa-001

## Step 1: Verify AWS Access

```bash
# Check your AWS identity
aws sts get-caller-identity

# Expected output should show account: 642760139656
```

## Step 2: Configure kubectl for EKS

```bash
# Configure kubectl to access the EKS cluster
aws eks update-kubeconfig --region us-west-2 --name care-demo-qa-001

# Verify connection
kubectl get nodes

# Check if namespace exists
kubectl get namespace ai-care-expert
```

If namespace doesn't exist:
```bash
kubectl create namespace ai-care-expert
```

## Step 3: Get MongoDB URI from Existing Secrets

```bash
# Check existing secrets in the namespace
kubectl get secrets -n ai-care-expert

# If ai-service-secrets exists, get the MongoDB URI
kubectl get secret ai-service-secrets -n ai-care-expert -o jsonpath='{.data.mongodb-uri}' | base64 -d

# Save this MongoDB URI - you'll need it for Step 8
```

## Step 4: Create ECR Repository

```bash
# Check if repository already exists
aws ecr describe-repositories --repository-names care-demo/api-service --region us-west-2

# If not exists, create it
aws ecr create-repository \
  --repository-name care-demo/api-service \
  --region us-west-2 \
  --image-scanning-configuration scanOnPush=true
```

**Expected Output:**
```json
{
    "repository": {
        "repositoryArn": "arn:aws:ecr:us-west-2:642760139656:repository/care-demo/api-service",
        "registryId": "642760139656",
        "repositoryName": "care-demo/api-service",
        "repositoryUri": "642760139656.dkr.ecr.us-west-2.amazonaws.com/care-demo/api-service"
    }
}
```

✅ **Checkpoint**: ECR repository created at `642760139656.dkr.ecr.us-west-2.amazonaws.com/care-demo/api-service`

## Step 5: Create CodeBuild BUILD Project

### 5.1: Create IAM Service Role (if needed)

Check if role exists:
```bash
aws iam get-role --role-name ai-care-expert-codebuild-role 2>/dev/null
```

If not exists, create the role:
```bash
# Create trust policy
cat > /tmp/codebuild-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codebuild.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the role
aws iam create-role \
  --role-name ai-care-expert-codebuild-role \
  --assume-role-policy-document file:///tmp/codebuild-trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name ai-care-expert-codebuild-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser

aws iam attach-role-policy \
  --role-name ai-care-expert-codebuild-role \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess

aws iam attach-role-policy \
  --role-name ai-care-expert-codebuild-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

### 5.2: Create BUILD Project

```bash
cat > /tmp/codebuild-project.json <<EOF
{
  "name": "care-demo-api-service",
  "source": {
    "type": "CODEPIPELINE",
    "buildspec": "buildspec.yml"
  },
  "artifacts": {
    "type": "CODEPIPELINE"
  },
  "environment": {
    "type": "LINUX_CONTAINER",
    "image": "aws/codebuild/standard:7.0",
    "computeType": "BUILD_GENERAL1_SMALL",
    "privilegedMode": true,
    "environmentVariables": []
  },
  "serviceRole": "arn:aws:iam::642760139656:role/ai-care-expert-codebuild-role",
  "logsConfig": {
    "cloudWatchLogs": {
      "status": "ENABLED"
    }
  }
}
EOF

# Create the project
aws codebuild create-project --cli-input-json file:///tmp/codebuild-project.json --region us-west-2
```

✅ **Checkpoint**: CodeBuild project `care-demo-api-service` created

## Step 6: Create CodeBuild DEPLOY Project

### 6.1: Update IAM Role for EKS Access

Add EKS permissions to the role:
```bash
# Create EKS policy
cat > /tmp/eks-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Create and attach policy
aws iam create-policy \
  --policy-name ai-care-expert-eks-policy \
  --policy-document file:///tmp/eks-policy.json

aws iam attach-role-policy \
  --role-name ai-care-expert-codebuild-role \
  --policy-arn arn:aws:iam::642760139656:policy/ai-care-expert-eks-policy
```

### 6.2: Grant CodeBuild Role Access to EKS

```bash
# Edit the aws-auth ConfigMap to add CodeBuild role
kubectl edit configmap aws-auth -n kube-system
```

Add this section under `mapRoles`:
```yaml
- rolearn: arn:aws:iam::642760139656:role/ai-care-expert-codebuild-role
  username: codebuild
  groups:
    - system:masters
```

### 6.3: Create DEPLOY Project

```bash
cat > /tmp/codebuild-deploy-project.json <<EOF
{
  "name": "care-demo-api-service-deploy",
  "source": {
    "type": "CODEPIPELINE",
    "buildspec": "buildspec-deploy.yml"
  },
  "secondarySources": [
    {
      "type": "CODEPIPELINE",
      "sourceIdentifier": "BuildOutput"
    }
  ],
  "artifacts": {
    "type": "CODEPIPELINE"
  },
  "environment": {
    "type": "LINUX_CONTAINER",
    "image": "aws/codebuild/standard:7.0",
    "computeType": "BUILD_GENERAL1_SMALL",
    "privilegedMode": false,
    "environmentVariables": []
  },
  "serviceRole": "arn:aws:iam::642760139656:role/ai-care-expert-codebuild-role",
  "vpcConfig": {
    "vpcId": "vpc-3d946758",
    "subnets": [
      "subnet-0a8b9c0d1e2f3g4h5",
      "subnet-1b9c0d2e3f4g5h6i7"
    ],
    "securityGroupIds": [
      "sg-0975490ae537b3000"
    ]
  },
  "logsConfig": {
    "cloudWatchLogs": {
      "status": "ENABLED"
    }
  }
}
EOF

# Create the project
aws codebuild create-project --cli-input-json file:///tmp/codebuild-deploy-project.json --region us-west-2
```

**Note**: You may need to update subnet IDs. Get them from:
```bash
aws eks describe-cluster --name care-demo-qa-001 --region us-west-2 --query 'cluster.resourcesVpcConfig.subnetIds'
```

✅ **Checkpoint**: CodeBuild project `care-demo-api-service-deploy` created

## Step 7: Create CodePipeline

```bash
cd /Users/seshireddy/projects/khoros-ai-care-expert/khoros-ai-care-expert-api

# Run the create pipeline script
./deployment/create-pipeline.sh
```

The script will:
1. Fetch GitHub OAuth token from existing ai-service pipeline
2. Create the pipeline with Source → Build → Deploy stages
3. Configure artifact passing between stages

✅ **Checkpoint**: CodePipeline `care-demo-api-service-pipeline` created

## Step 8: Setup GitHub Webhook

```bash
# Run the webhook creation script
./deployment/create-webhook.sh
```

This will:
1. Create a webhook in AWS CodePipeline
2. Register it with GitHub repository
3. Configure to trigger on pushes to `main` branch

✅ **Checkpoint**: GitHub webhook configured for automatic deployments

## Step 9: Setup Kubernetes Secrets

### 9.1: Get MongoDB URI from Existing Secret

```bash
# Get MongoDB URI from ai-service-secrets
MONGODB_URI=$(kubectl get secret ai-service-secrets -n ai-care-expert -o jsonpath='{.data.mongodb-uri}' | base64 -d)

echo "MongoDB URI: $MONGODB_URI"
```

### 9.2: Get Other Required Secrets from .env file

```bash
cd /Users/seshireddy/projects/khoros-ai-care-expert/khoros-ai-care-expert-api

# Read from your .env file
source .env

# Display the values (verify they're correct)
echo "JWT_SECRET_KEY: ${JWT_SECRET_KEY:0:10}..."
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:0:10}..."
echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:0:10}..."
```

### 9.3: Create Kubernetes Secret

```bash
# Create the secret with values
kubectl create secret generic api-service-secrets \
  --from-literal=mongodb-uri="$MONGODB_URI" \
  --from-literal=jwt-secret-key="$JWT_SECRET_KEY" \
  --from-literal=openai-api-key="${OPENAI_API_KEY:-}" \
  --from-literal=anthropic-api-key="${ANTHROPIC_API_KEY:-}" \
  --from-literal=aws-access-key-id="${AWS_ACCESS_KEY_ID:-}" \
  --from-literal=aws-secret-access-key="${AWS_SECRET_ACCESS_KEY:-}" \
  --from-literal=firecrawl-api-key="${FIRECRAWL_API_KEY:-}" \
  -n ai-care-expert
```

### 9.4: Verify Secret Creation

```bash
kubectl get secret api-service-secrets -n ai-care-expert
kubectl describe secret api-service-secrets -n ai-care-expert
```

✅ **Checkpoint**: Kubernetes secrets configured with MongoDB URI from existing secrets

## Step 10: Apply Kubernetes Manifests

```bash
cd /Users/seshireddy/projects/khoros-ai-care-expert/khoros-ai-care-expert-api

# Apply ConfigMap
kubectl apply -f deployment/k8s/configmap.yaml

# Apply Service
kubectl apply -f deployment/k8s/service.yaml

# Apply HPA
kubectl apply -f deployment/k8s/hpa.yaml
```

✅ **Checkpoint**: Kubernetes resources (ConfigMap, Service, HPA) created

## Step 11: Trigger Initial Pipeline Execution

```bash
# Trigger the pipeline manually for first deployment
./deployment/trigger-pipeline.sh
```

Or push a commit to trigger via webhook:
```bash
git commit --allow-empty -m "Trigger initial deployment"
git push origin main
```

## Step 12: Monitor Deployment

### Check Pipeline Status
```bash
./deployment/check-pipeline-status.sh
```

### Monitor CodeBuild Logs
Go to AWS Console:
- CodeBuild → Build projects → care-demo-api-service → Build history
- CodeBuild → Build projects → care-demo-api-service-deploy → Build history

### Watch Kubernetes Deployment
```bash
# Watch pods being created
kubectl get pods -n ai-care-expert -l app=api-service -w

# Check deployment status
kubectl rollout status deployment/api-service -n ai-care-expert
```

## Step 13: Verify Deployment

```bash
./deployment/verify-deployment.sh
```

This will show:
- Deployment status
- Pod health
- Service endpoints
- HPA status
- Recent events

### Check Pod Logs
```bash
kubectl logs -f deployment/api-service -n ai-care-expert
```

### Test the API
```bash
# Get the service endpoint
kubectl get svc api-service -n ai-care-expert

# If you have port-forward or ingress, test health endpoint
kubectl port-forward svc/api-service 8000:8000 -n ai-care-expert

# In another terminal
curl http://localhost:8000/api/health
```

✅ **Checkpoint**: API service deployed and healthy

## Troubleshooting

### Pipeline Fails at BUILD Stage
```bash
# Check CodeBuild logs
aws codebuild batch-get-builds \
  --ids $(aws codepipeline get-pipeline-state \
    --name care-demo-api-service-pipeline \
    --query 'stageStates[1].latestExecution.actionStates[0].latestExecution.externalExecutionId' \
    --output text) \
  --region us-west-2
```

### Pipeline Fails at DEPLOY Stage
```bash
# Check deployment events
kubectl get events -n ai-care-expert --sort-by='.lastTimestamp' | tail -20

# Check pod status
kubectl describe pod -l app=api-service -n ai-care-expert
```

### Pods Not Starting
```bash
# Check pod logs
kubectl logs -l app=api-service -n ai-care-expert --all-containers

# Check events
kubectl describe pod -l app=api-service -n ai-care-expert

# Check secrets
kubectl get secret api-service-secrets -n ai-care-expert -o yaml
```

### Update Secrets
```bash
# Delete and recreate
kubectl delete secret api-service-secrets -n ai-care-expert

# Recreate with new values
kubectl create secret generic api-service-secrets \
  --from-literal=mongodb-uri="..." \
  ...
  -n ai-care-expert

# Restart deployment
kubectl rollout restart deployment/api-service -n ai-care-expert
```

## Post-Deployment

### Monitor Application
```bash
# View logs
kubectl logs -f deployment/api-service -n ai-care-expert

# Check metrics
kubectl top pods -n ai-care-expert -l app=api-service
```

### Scale Manually (if needed)
```bash
kubectl scale deployment api-service --replicas=3 -n ai-care-expert
```

### Update Deployment
Just push to main branch - webhook will trigger automatic deployment:
```bash
git add .
git commit -m "Update API"
git push origin main
```

## Summary Checklist

- [ ] Step 1: AWS access verified
- [ ] Step 2: kubectl configured
- [ ] Step 3: MongoDB URI retrieved from existing secrets
- [ ] Step 4: ECR repository created
- [ ] Step 5: CodeBuild BUILD project created
- [ ] Step 6: CodeBuild DEPLOY project created
- [ ] Step 7: CodePipeline created
- [ ] Step 8: GitHub webhook configured
- [ ] Step 9: Kubernetes secrets created (with existing MongoDB URI)
- [ ] Step 10: Kubernetes manifests applied
- [ ] Step 11: Pipeline triggered
- [ ] Step 12: Deployment monitored
- [ ] Step 13: Deployment verified

## Quick Reference Commands

```bash
# Check pipeline status
./deployment/check-pipeline-status.sh

# Trigger deployment
./deployment/trigger-pipeline.sh

# Verify deployment
./deployment/verify-deployment.sh

# View logs
kubectl logs -f deployment/api-service -n ai-care-expert

# Restart deployment
kubectl rollout restart deployment/api-service -n ai-care-expert

# Check pod health
kubectl get pods -n ai-care-expert -l app=api-service
```

## Support

For issues, check:
1. CodeBuild logs in AWS Console
2. Kubernetes events: `kubectl get events -n ai-care-expert`
3. Pod logs: `kubectl logs -l app=api-service -n ai-care-expert`
4. Deployment README: `deployment/README.md`
