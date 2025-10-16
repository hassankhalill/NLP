# ABSA API Deployment Guide

Complete guide for deploying the Saudi Tourism ABSA API to various platforms.

---

## 📦 Table of Contents
1. [Local Deployment](#local-deployment)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment Options](#cloud-deployment-options)
4. [AWS Deployment](#aws-deployment)
5. [Google Cloud Deployment](#google-cloud-deployment)
6. [Azure Deployment](#azure-deployment)
7. [Free Cloud Platforms](#free-cloud-platforms)
8. [Troubleshooting](#troubleshooting)

---

## 🏠 Local Deployment

### Prerequisites
- Python 3.9+
- pip package manager

### Steps

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Download NLTK Data**
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('wordnet')"
```

3. **Run the API**
```bash
# Option 1: Direct execution
python api_app.py

# Option 2: Using uvicorn
uvicorn api_app:app --host 0.0.0.0 --port 8000 --reload
```

4. **Access the API**
- API Base: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

---

## 🐳 Docker Deployment

### Prerequisites
- Docker installed ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose (included with Docker Desktop)

### Quick Start with Docker

1. **Build and Run with Docker Compose**
```bash
docker-compose up --build
```

2. **Run in Background (Detached)**
```bash
docker-compose up -d
```

3. **View Logs**
```bash
docker-compose logs -f
```

4. **Stop the Container**
```bash
docker-compose down
```

### Manual Docker Commands

1. **Build the Image**
```bash
docker build -t absa-api:latest .
```

2. **Run the Container**
```bash
docker run -d \
  --name absa-api \
  -p 8000:8000 \
  -v $(pwd)/data_with_absa.csv:/app/data_with_absa.csv:ro \
  absa-api:latest
```

3. **Check Container Status**
```bash
docker ps
docker logs absa-api
```

4. **Stop and Remove**
```bash
docker stop absa-api
docker rm absa-api
```

### Docker Image Size Optimization
Current image: ~1.5GB (with all dependencies)

**To reduce size:**
- Use `python:3.9-alpine` (smaller base)
- Multi-stage builds
- Remove unnecessary dependencies

---

## ☁️ Cloud Deployment Options

### Comparison Table

| Platform | Difficulty | Cost | Best For |
|----------|-----------|------|----------|
| Render.com | ⭐ Easy | Free tier | Quick demos |
| Railway.app | ⭐ Easy | Free tier | Simple projects |
| Heroku | ⭐⭐ Medium | Limited free | Traditional apps |
| AWS Lambda | ⭐⭐⭐ Hard | Pay-per-use | Production |
| Google Cloud Run | ⭐⭐ Medium | Free tier + pay | Serverless containers |
| Azure Functions | ⭐⭐⭐ Hard | Free tier + pay | Microsoft ecosystem |
| AWS ECS/Fargate | ⭐⭐⭐⭐ Hard | Pay-per-use | Enterprise |

---

## 🔶 AWS Deployment

### Option 1: AWS Lambda + API Gateway (Serverless)

**Pros:** Auto-scaling, pay-per-request, no server management
**Cons:** Cold start latency, 15-minute timeout

#### Steps:

1. **Install AWS CLI**
```bash
pip install awscli
aws configure
```

2. **Create Lambda Function Package**
```bash
# Create deployment package
mkdir lambda_package
cp api_app.py lambda_package/
cp text_preprocessing.py lambda_package/
cp sentiment_analysis.py lambda_package/
cp absa_model.py lambda_package/
cp data_with_absa.csv lambda_package/

# Install dependencies
pip install -r requirements.txt -t lambda_package/

# Create ZIP
cd lambda_package
zip -r ../absa-lambda.zip .
cd ..
```

3. **Create Lambda Function**
```bash
aws lambda create-function \
  --function-name absa-api \
  --runtime python3.9 \
  --handler api_app.handler \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
  --zip-file fileb://absa-lambda.zip \
  --timeout 60 \
  --memory-size 1024
```

4. **Create API Gateway**
- Go to AWS Console → API Gateway
- Create REST API
- Create resources and methods
- Deploy to stage (e.g., "prod")
- Get invoke URL

**Estimated Cost:** $0-5/month (free tier: 1M requests/month)

---

### Option 2: AWS EC2 (Traditional Server)

**Pros:** Full control, no cold starts
**Cons:** Always running (costs more), manual scaling

#### Steps:

1. **Launch EC2 Instance**
```bash
# From AWS Console:
- AMI: Ubuntu 22.04 LTS
- Instance Type: t2.micro (free tier)
- Security Group: Allow port 8000
- Key Pair: Create and download
```

2. **Connect to Instance**
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

3. **Install Dependencies**
```bash
sudo apt update
sudo apt install -y python3-pip docker.io docker-compose
sudo systemctl start docker
sudo usermod -aG docker ubuntu
```

4. **Deploy with Docker**
```bash
# Upload files
scp -i your-key.pem -r * ubuntu@your-ec2-ip:~/app/

# On EC2:
cd ~/app
docker-compose up -d
```

5. **Configure Security Group**
- Allow inbound: Port 8000 from 0.0.0.0/0

**Access:** http://your-ec2-ip:8000

**Estimated Cost:** $0 (free tier) or ~$8-10/month

---

### Option 3: AWS ECS/Fargate (Container Service)

**Pros:** Auto-scaling, no server management, production-grade
**Cons:** More complex setup, higher cost

#### Steps:

1. **Push to ECR (Elastic Container Registry)**
```bash
# Authenticate
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Create repository
aws ecr create-repository --repository-name absa-api

# Tag and push
docker tag absa-api:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/absa-api:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/absa-api:latest
```

2. **Create ECS Cluster**
```bash
aws ecs create-cluster --cluster-name absa-cluster
```

3. **Create Task Definition**
- Define container, CPU, memory
- Use Fargate launch type

4. **Create Service**
```bash
aws ecs create-service \
  --cluster absa-cluster \
  --service-name absa-service \
  --task-definition absa-task \
  --desired-count 1 \
  --launch-type FARGATE
```

**Estimated Cost:** ~$15-30/month

---

## 🟦 Google Cloud Deployment

### Google Cloud Run (Recommended)

**Pros:** Serverless, auto-scaling, generous free tier
**Cons:** Requires GCP account

#### Steps:

1. **Install Google Cloud SDK**
```bash
# Download from: https://cloud.google.com/sdk/docs/install
gcloud init
gcloud auth login
```

2. **Build and Push to Container Registry**
```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Build with Cloud Build
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/absa-api

# Or push local image
docker tag absa-api:latest gcr.io/YOUR_PROJECT_ID/absa-api
docker push gcr.io/YOUR_PROJECT_ID/absa-api
```

3. **Deploy to Cloud Run**
```bash
gcloud run deploy absa-api \
  --image gcr.io/YOUR_PROJECT_ID/absa-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --timeout 60
```

4. **Get URL**
```bash
gcloud run services describe absa-api --region us-central1 --format='value(status.url)'
```

**Estimated Cost:** Free tier (2M requests/month) + ~$1-5/month

---

## 🔷 Azure Deployment

### Azure Container Instances

#### Steps:

1. **Install Azure CLI**
```bash
# Download from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
az login
```

2. **Create Resource Group**
```bash
az group create --name absa-rg --location eastus
```

3. **Create Container Registry**
```bash
az acr create --resource-group absa-rg --name absaregistry --sku Basic
az acr login --name absaregistry
```

4. **Push Image**
```bash
docker tag absa-api:latest absaregistry.azurecr.io/absa-api:latest
docker push absaregistry.azurecr.io/absa-api:latest
```

5. **Deploy Container**
```bash
az container create \
  --resource-group absa-rg \
  --name absa-api \
  --image absaregistry.azurecr.io/absa-api:latest \
  --cpu 1 \
  --memory 2 \
  --registry-login-server absaregistry.azurecr.io \
  --registry-username YOUR_USERNAME \
  --registry-password YOUR_PASSWORD \
  --dns-name-label absa-api-unique \
  --ports 8000
```

**Estimated Cost:** ~$10-20/month

---

## 🆓 Free Cloud Platforms

### 1. Render.com (Easiest & Recommended for Students)

**Free Tier:** Yes (with limitations)

#### Steps:

1. **Sign up:** https://render.com
2. **Create New Web Service**
3. **Connect GitHub Repository** (or manual deploy)
4. **Configure:**
   - Environment: Docker
   - Build Command: `docker build -t absa-api .`
   - Start Command: (automatic from Dockerfile)
5. **Deploy**

**URL:** https://your-app.onrender.com

**Limitations:**
- Spins down after 15 min inactivity
- 750 hours/month free
- Slower cold starts

---

### 2. Railway.app

**Free Tier:** $5 credit/month (no credit card needed)

#### Steps:

1. **Sign up:** https://railway.app
2. **Create New Project**
3. **Deploy from GitHub** or click "Deploy from Dockerfile"
4. **Configure environment variables** (if needed)
5. **Deploy**

**URL:** https://your-app.up.railway.app

---

### 3. Fly.io

**Free Tier:** 3 shared-CPU VMs

#### Steps:

1. **Install flyctl**
```bash
curl -L https://fly.io/install.sh | sh
```

2. **Login**
```bash
flyctl auth login
```

3. **Launch App**
```bash
flyctl launch
# Follow prompts, select region
```

4. **Deploy**
```bash
flyctl deploy
```

**URL:** https://your-app.fly.dev

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9
```

#### 2. Docker Build Fails
```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker build --no-cache -t absa-api .
```

#### 3. API Not Responding
```bash
# Check container logs
docker logs absa-api

# Check health
curl http://localhost:8000/health
```

#### 4. Module Import Errors
```bash
# Ensure all files are copied
ls -la

# Rebuild with correct structure
docker-compose down
docker-compose build --no-cache
docker-compose up
```

#### 5. NLTK Data Missing
```bash
# Download manually in container
docker exec -it absa-api python -c "import nltk; nltk.download('all')"
```

---

## 📊 Performance Optimization

### 1. API Response Time
- Use Redis for caching frequent requests
- Implement request batching
- Load model once at startup (already done)

### 2. Docker Image Size
Current: ~1.5GB

**Reduce to <500MB:**
```dockerfile
# Use alpine base
FROM python:3.9-alpine

# Multi-stage build
FROM python:3.9 as builder
# Build wheels here

FROM python:3.9-slim
COPY --from=builder /wheels /wheels
```

### 3. Scaling
- Horizontal: Multiple containers behind load balancer
- Vertical: Increase CPU/memory
- Auto-scaling: Use cloud platform features

---

## 🔒 Security Best Practices

1. **Never commit secrets**
```bash
# Use environment variables
export API_KEY="your-key"
```

2. **Use HTTPS in production**
```bash
# Terminate SSL at load balancer or use Nginx
```

3. **Rate limiting**
```python
# Add to api_app.py
from fastapi_limiter import FastAPILimiter
```

4. **Authentication**
```python
# Add API key validation
from fastapi.security import APIKeyHeader
```

---

## 📈 Monitoring

### Production Monitoring Tools

1. **Application Monitoring**
   - New Relic
   - Datadog
   - Prometheus + Grafana

2. **Log Aggregation**
   - CloudWatch (AWS)
   - Stackdriver (GCP)
   - ELK Stack

3. **Uptime Monitoring**
   - UptimeRobot (free)
   - Pingdom
   - StatusCake

---

## 💰 Cost Estimates

### Monthly Running Costs

| Platform | Free Tier | Paid Tier |
|----------|-----------|-----------|
| Render | Free (with limits) | $7/month |
| Railway | $5 credit | $10/month |
| Fly.io | 3 VMs free | $15/month |
| AWS Lambda | 1M requests | $5-20/month |
| GCP Cloud Run | 2M requests | $5-15/month |
| AWS EC2 t2.micro | Free 12 months | $8/month |
| AWS ECS Fargate | N/A | $15-30/month |

---

## ✅ Deployment Checklist

- [ ] Code tested locally
- [ ] Docker image builds successfully
- [ ] All dependencies in requirements.txt
- [ ] Environment variables configured
- [ ] NLTK data downloaded
- [ ] API endpoints tested
- [ ] Documentation updated
- [ ] Monitoring configured
- [ ] Backup strategy in place
- [ ] Rollback plan defined

---

## 📚 Additional Resources

- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Docker Documentation](https://docs.docker.com/)
- [AWS Lambda Docs](https://docs.aws.amazon.com/lambda/)
- [Google Cloud Run Docs](https://cloud.google.com/run/docs)
- [Azure Container Instances](https://docs.microsoft.com/en-us/azure/container-instances/)

---

## 🆘 Support

For issues or questions:
1. Check logs: `docker logs absa-api`
2. Review this guide
3. Consult platform documentation
4. Open GitHub issue (if applicable)

---

**Last Updated:** 2025-01-15
**Version:** 1.0
**Author:** NLP ABSA Project Team
