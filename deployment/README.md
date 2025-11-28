# Khoros AI Care Expert API - AWS Deployment

This directory contains all the configuration files and scripts needed to deploy the Khoros AI Care Expert API to AWS using CodePipeline, CodeBuild, ECR, and EKS.

## Architecture Overview

```
GitHub (main branch)
    ↓
AWS CodePipeline: care-demo-api-service-pipeline
    ├─ SOURCE Stage: GitHub webhook trigger
    ├─ BUILD Stage: CodeBuild builds Docker image → ECR
    └─ DEPLOY Stage: CodeBuild deploys to EKS cluster
        ↓
    EKS Cluster: care-demo-qa-001
    Namespace: ai-care-expert
    Service: api-service (2-10 replicas with auto-scaling)
```

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **kubectl** installed and configured
3. **jq** for JSON processing
4. AWS account access with permissions for:
   - CodePipeline
   - CodeBuild
   - ECR
   - EKS
   - S3
   - IAM

## Directory Structure

```
deployment/
├── README.md                    # This file
├── Dockerfile                   # Multi-stage Docker build
├── .dockerignore               # Files to exclude from Docker build
├── buildspec.yml               # CodeBuild BUILD stage configuration
├── buildspec-deploy.yml        # CodeBuild DEPLOY stage configuration
├── pipeline.json               # CodePipeline definition
├── k8s/                        # Kubernetes manifests
│   ├── deployment.yaml         # Kubernetes Deployment
│   ├── service.yaml           # Kubernetes Service (ClusterIP)
│   ├── configmap.yaml         # Non-sensitive configuration
│   ├── hpa.yaml               # Horizontal Pod Autoscaler
│   └── secret.yaml.template   # Template for secrets
├── create-pipeline.sh         # Create/update CodePipeline
├── create-webhook.sh          # Setup GitHub webhook
├── setup-secrets.sh           # Create Kubernetes secrets
├── verify-deployment.sh       # Verify EKS deployment
├── check-pipeline-status.sh   # Check pipeline status
└── trigger-pipeline.sh        # Manually trigger pipeline
```

## Setup Instructions

### Step 1: Create ECR Repository

```bash
aws ecr create-repository \
  --repository-name care-demo/api-service \
  --region us-west-2
```

### Step 2: Create CodeBuild Projects

#### BUILD Project

Create a CodeBuild project with these settings:
- **Name**: `care-demo-api-service`
- **Source**: AWS CodePipeline
- **Environment**:
  - Image: `aws/codebuild/standard:7.0`
  - Privileged mode: ✅ Enabled (for Docker)
  - Service role: Create or use existing with ECR permissions
- **Buildspec**: Use buildspec file: `buildspec.yml`

#### DEPLOY Project

Create a CodeBuild project with these settings:
- **Name**: `care-demo-api-service-deploy`
- **Source**: AWS CodePipeline
- **Environment**:
  - Image: `aws/codebuild/standard:7.0`
  - Service role: Requires EKS access permissions
- **VPC**: `vpc-3d946758` (qa VPC)
- **Security Group**: `sg-0975490ae537b3000`
- **Buildspec**: Use buildspec file: `buildspec-deploy.yml`

### Step 3: Create CodePipeline

```bash
cd /Users/seshireddy/projects/khoros-ai-care-expert/khoros-ai-care-expert-api
./deployment/create-pipeline.sh
```

This script will:
- Fetch GitHub OAuth token from existing pipeline
- Create/update the pipeline with Source → Build → Deploy stages
- Configure automatic artifact passing between stages

### Step 4: Setup GitHub Webhook

```bash
./deployment/create-webhook.sh
```

This configures automatic pipeline triggers on pushes to the `main` branch.

### Step 5: Setup Kubernetes Secrets

```bash
./deployment/setup-secrets.sh
```

You'll be prompted to enter:
- MongoDB URI
- OpenAI API Key (optional)
- Anthropic API Key (optional)
- JWT Secret Key
- AWS credentials (optional)
- Firecrawl API Key (optional)

### Step 6: Verify Deployment

```bash
./deployment/verify-deployment.sh
```

## Configuration

### Environment Variables

#### ConfigMap (Non-Sensitive)
Configured in `k8s/configmap.yaml`:
- `log-level`: Logging level (info, debug, warning)
- `mongodb-database`: MongoDB database name
- `aws-region`: AWS region
- `s3-bucket`: S3 bucket for storage
- `cors-origins`: Allowed CORS origins
- `kafka-enabled`: Enable/disable Kafka consumer

#### Secrets (Sensitive)
Configured via `setup-secrets.sh`:
- `mongodb-uri`: MongoDB connection string
- `openai-api-key`: OpenAI API key
- `anthropic-api-key`: Anthropic API key
- `jwt-secret-key`: JWT signing secret
- `aws-access-key-id`: AWS credentials
- `aws-secret-access-key`: AWS credentials
- `firecrawl-api-key`: Firecrawl API key

### Resource Limits

Configured in `k8s/deployment.yaml`:
- **Requests**: 512Mi memory, 250m CPU
- **Limits**: 1Gi memory, 1000m CPU

### Auto-Scaling

Configured in `k8s/hpa.yaml`:
- **Min Replicas**: 2
- **Max Replicas**: 10
- **CPU Target**: 70% utilization
- **Memory Target**: 80% utilization

## Deployment Scripts

### create-pipeline.sh
Creates or updates the AWS CodePipeline with all stages configured.

**Usage**:
```bash
./deployment/create-pipeline.sh
```

### create-webhook.sh
Sets up GitHub webhook for automatic pipeline triggers.

**Usage**:
```bash
./deployment/create-webhook.sh
```

### setup-secrets.sh
Interactive script to create Kubernetes secrets.

**Usage**:
```bash
./deployment/setup-secrets.sh
```

### verify-deployment.sh
Checks the status of all Kubernetes resources.

**Usage**:
```bash
./deployment/verify-deployment.sh
```

### check-pipeline-status.sh
Shows the current status of the CodePipeline.

**Usage**:
```bash
./deployment/check-pipeline-status.sh
```

### trigger-pipeline.sh
Manually triggers a pipeline execution.

**Usage**:
```bash
./deployment/trigger-pipeline.sh
```

## Monitoring and Troubleshooting

### View Pod Logs
```bash
kubectl logs -f deployment/api-service -n ai-care-expert
```

### Describe Pod
```bash
kubectl describe pod -l app=api-service -n ai-care-expert
```

### Check Pod Status
```bash
kubectl get pods -n ai-care-expert -l app=api-service
```

### Restart Deployment
```bash
kubectl rollout restart deployment/api-service -n ai-care-expert
```

### View Rollout Status
```bash
kubectl rollout status deployment/api-service -n ai-care-expert
```

### View Recent Events
```bash
kubectl get events -n ai-care-expert --sort-by='.lastTimestamp' | tail -20
```

### Check HPA Status
```bash
kubectl get hpa api-service-hpa -n ai-care-expert
```

### View CodeBuild Logs
Navigate to AWS Console:
- CodeBuild → Build projects → care-demo-api-service → Build history

## AWS Resources

### ECR Repository
- **URI**: `642760139656.dkr.ecr.us-west-2.amazonaws.com/care-demo/api-service`
- **Region**: us-west-2

### EKS Cluster
- **Name**: `care-demo-qa-001`
- **Region**: us-west-2
- **Namespace**: `ai-care-expert`

### CodeBuild Projects
- **Build**: `care-demo-api-service`
- **Deploy**: `care-demo-api-service-deploy`

### CodePipeline
- **Name**: `care-demo-api-service-pipeline`
- **Stages**: Source → Build → Deploy

### S3 Artifact Store
- **Bucket**: `care-demo-codepipeline-artifacts-us-west-2`

## Health Checks

The deployment includes both liveness and readiness probes:

**Liveness Probe**:
- Endpoint: `/api/health`
- Initial delay: 30s
- Period: 10s

**Readiness Probe**:
- Endpoint: `/api/health`
- Initial delay: 10s
- Period: 5s

## Updating Configuration

### Update ConfigMap
```bash
kubectl edit configmap api-service-config -n ai-care-expert
kubectl rollout restart deployment/api-service -n ai-care-expert
```

### Update Secrets
```bash
./deployment/setup-secrets.sh
kubectl rollout restart deployment/api-service -n ai-care-expert
```

### Update Deployment
```bash
kubectl apply -f deployment/k8s/deployment.yaml
```

## CI/CD Workflow

1. **Developer pushes to main branch**
2. **GitHub webhook triggers CodePipeline**
3. **SOURCE stage**: Fetches code from GitHub
4. **BUILD stage**:
   - Builds Docker image using `deployment/Dockerfile`
   - Tags image with commit hash and build number
   - Pushes to ECR
   - Creates `imagedefinitions.json` artifact
5. **DEPLOY stage**:
   - Reads image URI from artifact
   - Updates Kubernetes deployment.yaml
   - Applies manifests to EKS cluster
   - Waits for rollout completion
6. **Kubernetes performs rolling update**
   - Zero-downtime deployment
   - Health checks verify new pods
   - Old pods terminated after new ones are ready

## Security Considerations

1. **Non-root Container**: Runs as user `appuser` (UID 1001)
2. **Secret Management**: Sensitive data in Kubernetes secrets
3. **Network Policies**: Consider implementing network policies
4. **RBAC**: Ensure proper Kubernetes RBAC configuration
5. **Image Scanning**: Enable ECR image scanning
6. **VPC**: Deploy stage runs in VPC for security

## Cost Optimization

1. **Auto-scaling**: HPA scales based on actual load
2. **Resource Limits**: Prevents resource overconsumption
3. **Build Caching**: Docker layer caching for faster builds
4. **Spot Instances**: Consider using spot instances for worker nodes

## Support and Maintenance

### AWS Console Links
- **CodePipeline**: https://console.aws.amazon.com/codesuite/codepipeline/pipelines
- **ECR**: https://console.aws.amazon.com/ecr/repositories
- **EKS**: https://console.aws.amazon.com/eks/home
- **CodeBuild**: https://console.aws.amazon.com/codesuite/codebuild

### Common Issues

**Pipeline fails at BUILD stage**:
- Check CodeBuild logs
- Verify ECR permissions
- Ensure Dockerfile is valid

**Pipeline fails at DEPLOY stage**:
- Check EKS cluster connectivity
- Verify kubectl configuration
- Check namespace and secret existence
- Review pod logs for application errors

**Pods not starting**:
- Check image pull errors: `kubectl describe pod`
- Verify secrets are created
- Check resource availability
- Review application logs

## Contact

For issues or questions, please contact the infrastructure team or refer to the project documentation.
