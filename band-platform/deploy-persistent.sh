#!/bin/bash

# Deployment script for Soleil Band Platform with Persistent Credentials
# Usage: ./deploy-persistent.sh [domain] [email]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if domain and email are provided
if [ $# -lt 2 ]; then
    echo -e "${RED}Error: Domain and email required${NC}"
    echo "Usage: $0 <domain> <email>"
    echo "Example: $0 example.com admin@example.com"
    exit 1
fi

DOMAIN=$1
EMAIL=$2

echo -e "${GREEN}🚀 Starting deployment for domain: $DOMAIN${NC}"

# Function to check persistent credentials
check_persistent_credentials() {
    if [ -f "/etc/soleil/oauth.env" ]; then
        echo -e "${GREEN}✓ Persistent OAuth credentials found${NC}"
        return 0
    else
        echo -e "${RED}❌ No persistent credentials found!${NC}"
        echo -e "${YELLOW}Please run: ./scripts/setup_persistent_credentials.sh${NC}"
        return 1
    fi
}

# Check for persistent credentials early
if ! check_persistent_credentials; then
    echo -e "${RED}Cannot proceed without OAuth credentials${NC}"
    exit 1
fi

# Function to generate secure password
generate_password() {
    openssl rand -base64 32
}

# Create .env file with secure passwords (no OAuth credentials)
echo -e "${YELLOW}📝 Creating production environment file...${NC}"
cat > .env.production << EOF
# Domain configuration
DOMAIN=$DOMAIN
SSL_EMAIL=$EMAIL

# Secure passwords (auto-generated)
DB_PASSWORD=$(generate_password)
REDIS_PASSWORD=$(generate_password)
SECRET_KEY=$(generate_password)
EOF

echo -e "${GREEN}✓ Environment file created${NC}"

# Update nginx configuration with domain
echo -e "${YELLOW}🔧 Updating nginx configuration...${NC}"
sed -i.bak "s/YOUR_DOMAIN.com/$DOMAIN/g" nginx/nginx.conf
echo -e "${GREEN}✓ Nginx configuration updated${NC}"

# Create backend environment file (without OAuth credentials)
echo -e "${YELLOW}🔧 Creating backend environment file...${NC}"
cat > backend/.env.production << EOF
# SOLEil Production Environment Configuration
# OAuth credentials are loaded from /etc/soleil/oauth.env

# Frontend URLs
FRONTEND_URL=https://$DOMAIN

# API Configuration
DEBUG=False
HOST=0.0.0.0
PORT=8000

# CORS Origins
CORS_ORIGINS=["https://$DOMAIN", "https://www.$DOMAIN"]

# Session Secret (preserve existing or generate new)
SESSION_SECRET=$(generate_password)

# JWT Configuration (legacy, keeping for compatibility)
JWT_SECRET_KEY=$(generate_password)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Settings
APP_NAME="SOLEil"
LOG_LEVEL=INFO
EOF

# Create frontend environment file (without OAuth credentials)
echo -e "${YELLOW}🔧 Creating frontend environment file...${NC}"
cat > frontend/.env.production << EOF
# Frontend environment variables
# OAuth credentials are loaded from /etc/soleil/oauth.env

# Base URL of the backend API
NEXT_PUBLIC_API_URL=https://$DOMAIN/api

# WebSocket endpoint for live features
NEXT_PUBLIC_WS_URL=wss://$DOMAIN/ws
EOF

echo -e "${GREEN}✓ Environment files created${NC}"

# Build and start containers
echo -e "${YELLOW}🐳 Building and starting Docker containers...${NC}"
docker-compose -f docker-compose.production.yml up -d --build

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 30

# Get SSL certificate
echo -e "${YELLOW}🔒 Obtaining SSL certificate...${NC}"
docker-compose -f docker-compose.production.yml run --rm certbot

# Restart nginx to load certificate
docker-compose -f docker-compose.production.yml restart nginx

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${GREEN}🌐 Your application should be available at: https://$DOMAIN${NC}"
echo ""
echo -e "${YELLOW}📋 OAuth Credentials:${NC}"
echo "OAuth credentials are loaded from: /etc/soleil/oauth.env"
echo "To manage credentials: ./scripts/manage_persistent_credentials.sh {show|edit|backup|validate}"
echo ""
echo -e "${YELLOW}🔍 Useful commands:${NC}"
echo "- View logs: docker-compose -f docker-compose.production.yml logs -f"
echo "- Stop services: docker-compose -f docker-compose.production.yml down"
echo "- Restart services: docker-compose -f docker-compose.production.yml restart"
echo ""
echo -e "${GREEN}💾 Your secure passwords have been saved to .env.production${NC}"
echo -e "${RED}⚠️  Keep this file secure and backed up!${NC}"