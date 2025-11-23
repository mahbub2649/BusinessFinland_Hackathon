#!/bin/bash
# Simple script to run the dockerized application

echo "🐳 Starting Smart Funding Advisor with Docker..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cat > .env << EOF
XAI_API_KEY=your-api-key-here
USE_XAI_FUNDING_DISCOVERY=true
REACT_APP_BACKEND_URL=http://localhost:8000
GENERATE_SOURCEMAP=false
BROWSER=none
EOF
    echo "✅ Created .env file. Please edit it with your XAI_API_KEY"
    exit 1
fi

# Check which docker compose command is available
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Neither 'docker-compose' nor 'docker compose' found. Please install Docker Compose."
    exit 1
fi

echo "Using: $DOCKER_COMPOSE"

# Build and start containers
echo "🔨 Building and starting containers..."
$DOCKER_COMPOSE up --build

# To run in background: docker-compose up -d --build
# To stop: docker-compose down
# To view logs: docker-compose logs -f
