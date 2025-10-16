# ABSA API Deployment Guide

## Overview
This deployment package contains a production-ready ABSA (Aspect-Based Sentiment Analysis) API for tourism reviews in Arabic and English.

## Prerequisites
- Docker and Docker Compose installed
- At least 4GB RAM available
- Port 8000 available

## Quick Start

### Using Docker Compose (Recommended)
```bash
# Build and start the service
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop the service
docker-compose down
```

### Using Docker directly
```bash
# Build the image
docker build -t absa-api .

# Run the container
docker run -d -p 8000:8000 --name absa-api absa-api

# Check logs
docker logs -f absa-api
```

### Using Python directly (Development)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the API
python api.py

# Or use uvicorn directly
uvicorn api:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Analyze Single Review
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "The hotel was amazing! Great service and beautiful rooms.",
    "language": "eng",
    "review_id": "review_001"
  }'
```

### Analyze Batch
```bash
curl -X POST "http://localhost:8000/analyze-batch" \
  -H "Content-Type: application/json" \
  -d '{
    "reviews": [
      {"content": "Great experience!", "language": "eng"},
      {"content": "تجربة رائعة", "language": "ara"}
    ]
  }'
```

### Get Supported Aspects
```bash
curl http://localhost:8000/aspects
```

### Get Model Info
```bash
curl http://localhost:8000/model-info
```

## API Documentation
Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Model Information
- **Arabic Model**: Fine-tuned AraBERT v2
- **English Model**: Fine-tuned DistilBERT
- **Aspects**: 39 tourism-specific aspects
- **Sentiments**: Positive, Neutral, Negative

## Deployment Options

### AWS Deployment
1. Push Docker image to ECR
2. Deploy using ECS/Fargate or EC2
3. Use Application Load Balancer

### GCP Deployment
1. Push Docker image to GCR
2. Deploy using Cloud Run or GKE
3. Use Cloud Load Balancer

### Azure Deployment
1. Push Docker image to ACR
2. Deploy using Container Instances or AKS
3. Use Azure Load Balancer

## Monitoring
- Health endpoint: `/health`
- Metrics endpoint: `/model-info`
- Logs: Check Docker logs or `./logs` directory

## Troubleshooting

### Container won't start
```bash
docker logs absa-api
```

### Out of memory
Increase Docker memory limit or reduce batch size

### Models not loading
Ensure `./models/production` directory exists with trained models

## Support
For issues, check logs and model metadata
