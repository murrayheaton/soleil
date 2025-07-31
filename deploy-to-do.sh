#!/bin/bash

# Deployment script for Soleil to DigitalOcean
# Usage: ./deploy-to-do.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting deployment to DigitalOcean...${NC}"

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo -e "${RED}❌ Error: You have uncommitted changes${NC}"
    echo "Please commit or stash your changes before deploying"
    git status -s
    exit 1
fi

# Push to GitHub
echo -e "${YELLOW}📤 Pushing to GitHub...${NC}"
git push origin main

# SSH and deploy
echo -e "${YELLOW}🔄 Deploying on DigitalOcean droplet...${NC}"
ssh root@159.203.62.132 << 'EOF'
set -e
cd /soleil/band-platform

echo "📥 Pulling latest changes..."
git pull origin main

echo "🐳 Rebuilding and restarting containers..."
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d --build

echo "⏳ Waiting for services to start..."
sleep 10

echo "🔍 Checking service status..."
docker-compose -f docker-compose.production.yml ps

echo "✅ Deployment complete!"
EOF

echo -e "${GREEN}✅ Deployment successful!${NC}"
echo -e "${GREEN}🌐 Your changes are now live on your droplet${NC}"
