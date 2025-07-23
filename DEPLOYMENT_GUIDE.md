# MadSpark Multi-Agent System - Deployment Guide

## Prerequisites
- Docker and Docker Compose installed
- Python 3.10+ (for local development)
- Node.js 16+ (for local development)
- Google Cloud API key with Gemini API enabled

## Quick Start (Docker)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Eureka
```

### 2. Set Environment Variables
Create a `.env` file in the `web` directory:
```env
# Backend
GOOGLE_API_KEY=your-google-api-key-here
REDIS_URL=redis://redis:6379
PYTHONPATH=/app

# Frontend
REACT_APP_API_BASE_URL=http://localhost:8000
```

### 3. Deploy with Docker Compose
```bash
cd web
docker-compose up --build
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Local Development Setup

### Backend Setup
```bash
# Navigate to backend directory
cd web/backend

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_API_KEY=your-google-api-key-here
export PYTHONPATH=../../src

# Run the backend
python main.py
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd web/frontend

# Install dependencies
npm install

# Set environment variables
export REACT_APP_API_BASE_URL=http://localhost:8000

# Run development server
npm start
```

## Production Deployment

### Using Docker (Recommended)

1. **Build Production Images**:
```bash
cd web

# Build backend
docker build -f backend/Dockerfile -t madspark-backend:latest .

# Build frontend  
docker build -f frontend/Dockerfile -t madspark-frontend:latest .
```

2. **Run with Docker Compose**:
```bash
# Production configuration
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment

#### Backend Deployment
1. **Install Dependencies**:
```bash
cd web/backend
pip install -r requirements.txt
pip install gunicorn
```

2. **Run with Gunicorn**:
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Frontend Deployment
1. **Build Production Bundle**:
```bash
cd web/frontend
npm install
npm run build
```

2. **Serve with Nginx**:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /path/to/build;
        try_files $uri /index.html;
    }
    
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Cloud Platform Deployment

### Google Cloud Platform

1. **Backend on Cloud Run**:
```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT-ID/madspark-backend

# Deploy to Cloud Run
gcloud run deploy madspark-backend \
  --image gcr.io/PROJECT-ID/madspark-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=$GOOGLE_API_KEY
```

2. **Frontend on Firebase Hosting**:
```bash
# Install Firebase CLI
npm install -g firebase-tools

# Initialize Firebase
firebase init hosting

# Build and deploy
npm run build
firebase deploy
```

### AWS Deployment

1. **Backend on ECS**:
```bash
# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI
docker tag madspark-backend:latest $ECR_URI/madspark-backend:latest
docker push $ECR_URI/madspark-backend:latest

# Deploy with ECS CLI or Console
```

2. **Frontend on S3 + CloudFront**:
```bash
# Build frontend
npm run build

# Sync to S3
aws s3 sync build/ s3://your-bucket-name

# Invalidate CloudFront
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

## Environment Configuration

### Required Environment Variables

#### Backend
- `GOOGLE_API_KEY` (required): Google Cloud API key
- `REDIS_URL` (optional): Redis connection URL
- `CORS_ORIGINS` (optional): Allowed CORS origins
- `MAX_WORKERS` (optional): Number of worker processes
- `LOG_LEVEL` (optional): Logging level (INFO, DEBUG, ERROR)

#### Frontend
- `REACT_APP_API_BASE_URL` (required): Backend API URL
- `REACT_APP_WEBSOCKET_URL` (optional): WebSocket URL
- `REACT_APP_GA_TRACKING_ID` (optional): Google Analytics ID

### Recommended Production Settings

```env
# Backend Production
GOOGLE_API_KEY=your-production-key
REDIS_URL=redis://production-redis:6379
CORS_ORIGINS=["https://your-domain.com"]
MAX_WORKERS=4
LOG_LEVEL=INFO

# Frontend Production
REACT_APP_API_BASE_URL=https://api.your-domain.com
REACT_APP_WEBSOCKET_URL=wss://api.your-domain.com/ws
```

## Monitoring and Maintenance

### Health Checks
- Backend health: `GET /health`
- API metrics: `GET /metrics`
- Frontend health: Check for 200 status on root path

### Logging
- Backend logs: Check Docker logs or application logs
- Frontend errors: Browser console and error tracking service

### Backup
- Bookmark data: Stored in `data/bookmarks/`
- Redis cache: Optional, can be rebuilt

### Updates
1. Pull latest changes
2. Rebuild Docker images
3. Run database migrations (if any)
4. Deploy new version
5. Verify health checks

## Troubleshooting

### Common Issues

1. **API Connection Failed**:
   - Check CORS settings
   - Verify API_BASE_URL in frontend
   - Check network connectivity

2. **Google API Errors**:
   - Verify API key is valid
   - Check API quotas
   - Ensure Gemini API is enabled

3. **Docker Build Failures**:
   - Clear Docker cache: `docker system prune`
   - Check disk space
   - Verify Dockerfile syntax

4. **Performance Issues**:
   - Enable Redis caching
   - Increase worker processes
   - Check API rate limits

### Support
For issues and questions:
- Check the logs first
- Review error messages in browser console
- Consult API documentation at `/docs`
- File issues in the project repository