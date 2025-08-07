#!/bin/bash

# SOLEil Authentication Fix Deployment Script
# Deploys only the necessary auth fixes to your Digital Ocean droplet

echo "🚀 Deploying authentication fixes to Digital Ocean droplet..."
echo "=================================================="

# Configuration
# IMPORTANT: Replace the X's with your actual droplet IP address
# You can find this in your Digital Ocean dashboard
DROPLET_IP="159.203.62.132"  # <-- REPLACE WITH YOUR DROPLET IP!
DROPLET_USER="root"            # Default for Digital Ocean
PROJECT_PATH="/root/soleil" # Actual deployment path on your droplet

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# IP is now configured - ready to deploy!

echo -e "${YELLOW}📋 Step 1: Connect to droplet and pull latest code${NC}"
echo "Connecting to solepower.live droplet..."
ssh $DROPLET_USER@$DROPLET_IP << 'ENDSSH'
    # Navigate to project directory
    if [ -d "/root/soleil" ]; then
        cd /root/soleil
    elif [ -d "/var/www/soleil" ]; then
        cd /root/soleil
    elif [ -d "/opt/soleil" ]; then
        cd /opt/soleil
    else
        echo "❌ Could not find project directory. Checking common locations..."
        find / -maxdepth 3 -name "soleil" -type d 2>/dev/null | head -5
        exit 1
    fi
    echo "Current directory: $(pwd)"
    
    # Pull latest changes from main
    echo "Pulling latest changes..."
    git pull origin main
    
    # Check if pull was successful
    if [ $? -eq 0 ]; then
        echo "✅ Successfully pulled latest changes"
    else
        echo "❌ Failed to pull changes. Check git status"
        git status
        exit 1
    fi
ENDSSH

echo -e "${YELLOW}📋 Step 2: Install backend dependencies${NC}"
ssh $DROPLET_USER@$DROPLET_IP << 'ENDSSH'
    cd /root/soleil/band-platform/backend
    
    # Install PyJWT for authentication
    echo "Installing PyJWT..."
    pip3 install pyjwt
    
    echo "✅ Backend dependencies installed"
ENDSSH

echo -e "${YELLOW}📋 Step 3: Build frontend${NC}"
ssh $DROPLET_USER@$DROPLET_IP << 'ENDSSH'
    cd /root/soleil/band-platform/frontend
    
    # Install any new dependencies
    echo "Installing frontend dependencies..."
    npm install
    
    # Build production version
    echo "Building frontend..."
    npm run build
    
    if [ $? -eq 0 ]; then
        echo "✅ Frontend built successfully"
    else
        echo "❌ Frontend build failed"
        exit 1
    fi
ENDSSH

echo -e "${YELLOW}📋 Step 4: Restart services${NC}"
ssh $DROPLET_USER@$DROPLET_IP << 'ENDSSH'
    # Restart backend
    echo "Restarting backend service..."
    sudo systemctl restart soleil-backend || pm2 restart soleil-backend || {
        echo "Manual restart needed - killing old process"
        pkill -f "python.*start_server.py"
        cd /root/soleil/band-platform/backend
        nohup python3 start_server.py > backend.log 2>&1 &
    }
    
    # Restart frontend (if using PM2 or systemd)
    echo "Restarting frontend service..."
    sudo systemctl restart soleil-frontend || pm2 restart soleil-frontend || {
        echo "Frontend served statically - no restart needed"
    }
    
    # Restart nginx
    echo "Restarting nginx..."
    sudo systemctl reload nginx
    
    echo "✅ Services restarted"
ENDSSH

echo -e "${YELLOW}📋 Step 5: Verify deployment${NC}"
ssh $DROPLET_USER@$DROPLET_IP << 'ENDSSH'
    # Check if backend is running
    echo "Checking backend status..."
    curl -s http://localhost:8000/api/auth/validate || echo "Backend check failed"
    
    # Check latest commit
    cd /root/soleil
    echo "Latest commit on server:"
    git log --oneline -1
ENDSSH

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Test the authentication fixes:"
echo "1. Visit https://solepower.live"
echo "2. Click 'Sign in with Google'"
echo "3. Verify email field accepts input"
echo "4. Complete profile setup"
echo "5. Navigate around - session should persist"
echo ""
echo "If issues occur, check logs:"
echo "  ssh $DROPLET_USER@$DROPLET_IP"
echo "  tail -f /var/www/soleil/band-platform/backend/backend.log"