#!/bin/bash

# Deployment script for Soleil Band Platform
# Usage: ./deploy.sh [domain] [email]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Function to generate secure password
generate_password() {
    openssl rand -base64 32
}

# Create .env file with secure passwords
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

# Update environment files with domain
echo -e "${YELLOW}🔧 Updating environment files...${NC}"
sed -i.bak "s/YOUR_DOMAIN.com/$DOMAIN/g" backend/.env.production
sed -i.bak "s/YOUR_DOMAIN.com/$DOMAIN/g" frontend/.env.production
echo -e "${GREEN}✓ Environment files updated${NC}"

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
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Update Google OAuth redirect URI to: https://$DOMAIN/api/auth/google/callback"
echo "2. Add your Google Client ID and Secret to backend/.env.production"
echo "3. Add your Google Drive folder ID to backend/.env.production"
echo "4. Restart the backend container: docker-compose -f docker-compose.production.yml restart backend"
echo ""
echo -e "${YELLOW}🔍 Useful commands:${NC}"
echo "- View logs: docker-compose -f docker-compose.production.yml logs -f"
echo "- Stop services: docker-compose -f docker-compose.production.yml down"
echo "- Restart services: docker-compose -f docker-compose.production.yml restart"
echo ""
echo -e "${GREEN}💾 Your secure passwords have been saved to .env.production${NC}"
echo -e "${RED}⚠️  Keep this file secure and backed up!${NC}"