#!/bin/bash

# Wild Kratts MCP Server Deployment Script

set -e

echo "🚀 Deploying Wild Kratts MCP Server..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create logs directory
mkdir -p logs

# Build and start the container
echo "🔨 Building Docker image..."
docker-compose build

echo "🏃 Starting MCP server..."
docker-compose up -d

echo "⏳ Waiting for server to start..."
sleep 5

# Check if container is running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Wild Kratts MCP Server is running!"
    echo "📋 Container status:"
    docker-compose ps
    echo ""
    echo "📝 To view logs: docker-compose logs -f"
    echo "🛑 To stop: docker-compose down"
    echo "🔄 To restart: docker-compose restart"
else
    echo "❌ Failed to start server. Check logs:"
    docker-compose logs
    exit 1
fi