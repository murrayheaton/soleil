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

# Add missing BLUE color
BLUE='\033[0;34m'

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

# Create and update environment files with domain
echo -e "${YELLOW}🔧 Creating and updating environment files...${NC}"
cp backend/.env.production.template backend/.env.production
cp frontend/.env.production.template frontend/.env.production
sed -i.bak "s/YOUR_DOMAIN.com/$DOMAIN/g" backend/.env.production
sed -i.bak "s/YOUR_DOMAIN.com/$DOMAIN/g" frontend/.env.production
echo -e "${GREEN}✓ Environment files created and updated${NC}"

# OAuth Credentials Setup - AFTER environment files are created
echo -e "${BLUE}🔑 OAuth Credentials Setup${NC}"
echo "Do you need to configure OAuth credentials?"
echo "1) Enter credentials interactively"
echo "2) Import encrypted credentials file"
echo "3) Skip (credentials already configured)"
read -p "Select option (1-3): " OAUTH_OPTION

case $OAUTH_OPTION in
    1)
        # Make script executable and run
        chmod +x scripts/oauth_credentials_manager.sh
        ./scripts/oauth_credentials_manager.sh
        ;;
    2)
        # Import encrypted credentials
        chmod +x scripts/credentials_transfer.sh
        ./scripts/credentials_transfer.sh import
        ;;
    3)
        echo -e "${YELLOW}⚠️  Skipping OAuth setup. Ensure credentials are configured!${NC}"
        ;;
    *)
        echo -e "${RED}Invalid option. Continuing without OAuth setup.${NC}"
        ;;
esac

# Validate OAuth configuration before proceeding
echo -e "${YELLOW}🔍 Validating OAuth configuration...${NC}"
if ./scripts/validate_oauth.sh; then
    echo -e "${GREEN}✓ OAuth configuration valid${NC}"
else
    echo -e "${RED}❌ OAuth configuration invalid!${NC}"
    echo -e "${YELLOW}Please configure OAuth credentials before continuing.${NC}"
    exit 1
fi

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
echo "1. Ensure Google OAuth redirect URI is set to: https://$DOMAIN/api/auth/google/callback"
echo "2. Verify your OAuth credentials are working by visiting: https://$DOMAIN"
echo ""
echo -e "${YELLOW}🔍 Useful commands:${NC}"
echo "- View logs: docker-compose -f docker-compose.production.yml logs -f"
echo "- Stop services: docker-compose -f docker-compose.production.yml down"
echo "- Restart services: docker-compose -f docker-compose.production.yml restart"
echo ""
echo -e "${GREEN}💾 Your secure passwords have been saved to .env.production${NC}"
echo -e "${RED}⚠️  Keep this file secure and backed up!${NC}"