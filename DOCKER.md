# Docker Setup Guide

## Quick Start

### 1. Prerequisites
- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (included with Docker Desktop)
- XAI API Key

### 2. Configure Environment

Your `.env` file is already configured. Make sure it contains:
```bash
XAI_API_KEY=your-actual-api-key-here
USE_XAI_FUNDING_DISCOVERY=true
REACT_APP_BACKEND_URL=http://localhost:8000
```

### 3. Run with Docker Compose

```bash
# Make script executable
chmod +x docker-run.sh

# Start everything (builds on first run)
./docker-run.sh

# Or use docker-compose directly
docker-compose up

# Or run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything
docker-compose down
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Individual Container Commands

### Build Images
```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build backend
docker-compose build frontend
```

### Run Individual Services
```bash
# Backend only
docker-compose up backend

# Frontend only  
docker-compose up frontend
```

### Execute Commands in Running Containers
```bash
# Backend shell
docker-compose exec backend bash

# Frontend shell
docker-compose exec frontend sh

# Run Python commands
docker-compose exec backend python -c "print('Hello from Docker!')"

# Install new Python package
docker-compose exec backend pip install package-name
```

## Production Deployment

### Option 1: Single Container (Backend + Static Frontend)
```bash
# Build production image
docker build -t smart-funding-advisor:latest .

# Run production container
docker run -d \
  -p 8000:8000 \
  -e XAI_API_KEY=your-key \
  -v $(pwd)/backend/cache:/app/backend/cache \
  --name funding-advisor \
  smart-funding-advisor:latest

# Access at http://localhost:8000
```

### Option 2: Push to Container Registry
```bash
# Tag image
docker tag smart-funding-advisor:latest your-registry/smart-funding-advisor:latest

# Push to registry
docker push your-registry/smart-funding-advisor:latest
```

## Troubleshooting

### Clear Everything and Rebuild
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Check Container Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Container Not Starting
```bash
# Check status
docker-compose ps

# Inspect specific container
docker-compose exec backend env

# Check resource usage
docker stats
```

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000
# or
netstat -tuln | grep 8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Cache Issues
```bash
# Clear Python cache
docker-compose exec backend find . -type d -name __pycache__ -exec rm -rf {} +

# Clear application cache
docker-compose exec backend rm -rf backend/cache/*

# Restart services
docker-compose restart
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `XAI_API_KEY` | Your xAI API key | Required |
| `USE_XAI_FUNDING_DISCOVERY` | Enable AI funding discovery | `true` |
| `REACT_APP_BACKEND_URL` | Backend API URL | `http://localhost:8000` |
| `PYTHONUNBUFFERED` | Python output buffering | `1` |

## Volume Mounts

- `./backend/cache` - Persistent cache for funding data
- `./backend` - Backend source code (development, hot reload)
- `./frontend` - Frontend source code (development, hot reload)
- `/app/node_modules` - Node modules (prevents local override)

## Health Checks

Backend includes automatic health checks:
```bash
# Check if backend is healthy
curl http://localhost:8000/

# Check Docker health status
docker-compose ps
```

## Development vs Production

### Development (Current Setup)
- ✅ Hot reload enabled for both frontend and backend
- ✅ Source code mounted as volumes
- ✅ Separate frontend dev server
- ✅ Debug logging enabled
- ✅ Easy debugging

### Production (Single Container)
- ✅ Static frontend served by backend
- ✅ No volume mounts
- ✅ Optimized builds
- ✅ Smaller image size
- ✅ Better performance

## Common Commands Cheat Sheet

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart specific service
docker-compose restart backend

# View logs
docker-compose logs -f backend

# Rebuild after code changes
docker-compose up --build

# Remove all containers and volumes
docker-compose down -v

# Execute command in container
docker-compose exec backend python manage.py

# Access backend shell
docker-compose exec backend bash

# Access frontend shell
docker-compose exec frontend sh

# Check running containers
docker-compose ps

# Check resource usage
docker stats

# Remove unused images
docker image prune -a
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Build Docker Image

on:
  push:
    branches: [ main, dev2 ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker image
        run: docker build -t smart-funding-advisor .
      
      - name: Test container
        run: |
          docker run -d -p 8000:8000 \
            -e XAI_API_KEY=${{ secrets.XAI_API_KEY }} \
            smart-funding-advisor
          sleep 10
          curl http://localhost:8000/
```

## Tips & Best Practices

1. **Use .env file** for sensitive data (never commit it!)
2. **Run in background** with `-d` flag for development
3. **Check logs regularly** with `docker-compose logs -f`
4. **Rebuild after changes** to requirements.txt or package.json
5. **Use volumes** for persistent data (cache directory)
6. **Monitor resources** with `docker stats`
7. **Clean up regularly** with `docker system prune`

## Troubleshooting Specific Issues

### "Port already allocated"
```bash
docker-compose down
# Change port in docker-compose.yml or kill process using the port
```

### "Cannot connect to backend from frontend"
```bash
# Check backend is running
docker-compose ps
# Check backend logs
docker-compose logs backend
# Verify REACT_APP_BACKEND_URL in .env
```

### "Module not found" errors
```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### "Permission denied" on Linux
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again
```
