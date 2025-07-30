#!/bin/bash

# Sole Power Live - Full Platform Launcher
# This script starts both backend and frontend with a fresh state

echo "🎺 Starting Sole Power Live Platform..."
echo "===================================="

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to cleanup on exit
cleanup() {
    echo -e "\n${BLUE}Shutting down Sole Power Live...${NC}"
    
    # Kill backend processes
    pkill -f "start_server.py" 2>/dev/null
    pkill -f "uvicorn" 2>/dev/null
    
    # Kill frontend processes
    lsof -ti:3000 | xargs kill -9 2>/dev/null
    pkill -f "next dev" 2>/dev/null
    
    echo -e "${GREEN}✓ Sole Power Live shut down successfully${NC}"
    exit 0
}

# Set up trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Step 1: Kill any existing processes
echo -e "${BLUE}1. Cleaning up any existing processes...${NC}"
pkill -f "start_server.py" 2>/dev/null
pkill -f "uvicorn" 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
pkill -f "next dev" 2>/dev/null
sleep 2
echo -e "${GREEN}✓ Cleanup complete${NC}"

# Step 2: Clear Google token for fresh authentication
echo -e "\n${BLUE}2. Clearing cached Google authentication...${NC}"
cd "$SCRIPT_DIR/backend"
if [ -f "google_token.json" ]; then
    rm -f google_token.json
    echo -e "${GREEN}✓ Cleared old Google token${NC}"
else
    echo "No existing Google token found"
fi

# Step 3: Start Backend
echo -e "\n${BLUE}3. Starting Backend API...${NC}"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Using existing Python virtual environment..."
    source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
elif [ -d "venv_linux" ]; then
    echo "Using existing Python virtual environment (venv_linux)..."
    source venv_linux/bin/activate 2>/dev/null
fi

# Start backend in background
nohup python3 start_server.py > backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to be ready
echo -n "Waiting for backend to start"
for i in {1..10}; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo -e "\n${GREEN}✓ Backend is running on http://localhost:8000${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

if ! curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "\n${RED}✗ Backend failed to start. Check backend.log for errors.${NC}"
    exit 1
fi

# Step 4: Clear frontend cache and start frontend
echo -e "\n${BLUE}4. Starting Frontend...${NC}"
cd "$SCRIPT_DIR/frontend"

# Clear Next.js cache for fresh start
rm -rf .next 2>/dev/null
echo "Cleared Next.js cache..."

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start frontend in background
nohup npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to be ready
echo -n "Waiting for frontend to start"
for i in {1..15}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "\n${GREEN}✓ Frontend is running on http://localhost:3000${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Step 5: Open browser
echo -e "\n${BLUE}5. Opening Sole Power Live in browser...${NC}"
sleep 2

# Open the platform in default browser
if command -v open &> /dev/null; then
    open http://localhost:3000
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
else
    echo "Please open http://localhost:3000 in your browser"
fi

# Step 6: Show status
echo -e "\n${GREEN}===================================="
echo -e "🎺 Sole Power Live is running!"
echo -e "====================================${NC}"
echo -e "Frontend: ${BLUE}http://localhost:3000${NC}"
echo -e "Backend API: ${BLUE}http://localhost:8000${NC}"
echo -e "\n${BLUE}Authentication:${NC}"
echo -e "Enter your Google account email and password when prompted - seamless login experience."
echo -e "\nPress ${RED}Ctrl+C${NC} to stop the platform"
echo -e "\nLogs:"
echo -e "  Backend: ${BLUE}$SCRIPT_DIR/backend/backend.log${NC}"
echo -e "  Frontend: ${BLUE}$SCRIPT_DIR/frontend/frontend.log${NC}"

# Keep script running
while true; do
    sleep 1
done