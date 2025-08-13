#!/bin/bash

# SOLEil Services Startup Script
# This script starts both backend and frontend services

echo "🎸 Starting SOLEil Band Platform Services..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Start backend
echo -e "${BLUE}Starting backend server...${NC}"
cd band-platform/backend

# Check if port 8000 is already in use
if check_port 8000; then
    echo -e "${RED}Port 8000 is already in use. Backend might already be running.${NC}"
else
    # Start backend in background
    python3 start_server.py &
    BACKEND_PID=$!
    echo -e "${GREEN}Backend started with PID: $BACKEND_PID${NC}"
    echo $BACKEND_PID > /tmp/soleil_backend.pid
fi

# Give backend time to start
sleep 3

# Start frontend
echo -e "${BLUE}Starting frontend server...${NC}"
cd ../frontend

# Check if port 3000 is already in use
if check_port 3000; then
    echo -e "${RED}Port 3000 is already in use. Frontend might already be running.${NC}"
else
    # Start frontend
    npm run dev &
    FRONTEND_PID=$!
    echo -e "${GREEN}Frontend started with PID: $FRONTEND_PID${NC}"
    echo $FRONTEND_PID > /tmp/soleil_frontend.pid
fi

echo ""
echo -e "${GREEN}🎵 SOLEil services are starting!${NC}"
echo ""
echo "Access the application at:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Google OAuth Configuration:"
echo "  Client ID: ${GOOGLE_CLIENT_ID:0:20}..."
echo "  Redirect URI: https://solepower.live/api/auth/google/callback"
echo ""
echo "To authenticate with Google Drive:"
echo "  1. Visit: http://localhost:8000/api/auth/google/url"
echo "  2. Follow the OAuth flow"
echo "  3. Charts will then be accessible"
echo ""
echo "To stop services, run: ./stop_services.sh"