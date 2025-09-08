#!/bin/bash
# Script to stop local Docker containers when production is running

echo "🛑 Stopping local Docker containers..."

# Stop all containers
docker-compose down

# Remove stopped containers
docker container prune -f

# Remove unused images (optional)
# docker image prune -f

echo "✅ Local Docker containers stopped!"
echo "💡 Production server is now handling the bot."
echo ""
echo "To restart locally later:"
echo "  docker-compose up -d"