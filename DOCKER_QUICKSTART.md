# Docker Quick Start Guide

Get the ABSA API running in 5 minutes with Docker!

## Prerequisites
- Docker installed on your machine
- Basic command line knowledge

## Quick Start (3 commands)

```bash
# 1. Build the Docker image
docker-compose build

# 2. Start the API
docker-compose up -d

# 3. Check it's running
curl http://localhost:8000/health
```

That's it! 🎉

## Access Points

- **API Base:** http://localhost:8000
- **Interactive Docs:** http://localhost:8000/docs
- **API Documentation:** http://localhost:8000/redoc

## Test the API

### Using the Browser
Open: http://localhost:8000/docs

Click on any endpoint and try it out!

### Using curl

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Sentiment Analysis:**
```bash
curl -X POST "http://localhost:8000/api/v1/sentiment" \
  -H "Content-Type: application/json" \
  -d '{"text": "This place is amazing!", "rating": 5}'
```

**ABSA Analysis:**
```bash
curl -X POST "http://localhost:8000/api/v1/absa" \
  -H "Content-Type: application/json" \
  -d '{"text": "Great location but poor service", "rating": 3}'
```

**Get Statistics:**
```bash
curl http://localhost:8000/api/v1/stats
```

## Useful Commands

**View Logs:**
```bash
docker-compose logs -f
```

**Stop the API:**
```bash
docker-compose down
```

**Restart:**
```bash
docker-compose restart
```

**Rebuild (after code changes):**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Troubleshooting

**Port 8000 already in use?**
```bash
# Windows:
netstat -ano | findstr :8000
# Kill the process

# Or change port in docker-compose.yml:
ports:
  - "8080:8000"  # Use port 8080 instead
```

**Container won't start?**
```bash
# Check logs
docker-compose logs

# Check container status
docker ps -a
```

**Need to rebuild everything?**
```bash
docker-compose down -v
docker system prune -a
docker-compose up --build
```

## Next Steps

- See full deployment options: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- Deploy to cloud platforms
- Set up monitoring and scaling

## Performance Note

First request may be slow (model loading). Subsequent requests are fast (<100ms).

---

**Questions?** Check the full [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
