#!/bin/bash

# SOLEil Services Stop Script
# This script stops both backend and frontend services

echo "🛑 Stopping SOLEil Band Platform Services..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Stop backend
if [ -f /tmp/soleil_backend.pid ]; then
    BACKEND_PID=$(cat /tmp/soleil_backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        echo -e "${GREEN}Backend stopped (PID: $BACKEND_PID)${NC}"
    else
        echo "Backend process not found"
    fi
    rm /tmp/soleil_backend.pid
else
    echo "Backend PID file not found. Checking for Python processes..."
    pkill -f "start_server.py"
fi

# Stop frontend
if [ -f /tmp/soleil_frontend.pid ]; then
    FRONTEND_PID=$(cat /tmp/soleil_frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        echo -e "${GREEN}Frontend stopped (PID: $FRONTEND_PID)${NC}"
    else
        echo "Frontend process not found"
    fi
    rm /tmp/soleil_frontend.pid
else
    echo "Frontend PID file not found. Checking for Next.js processes..."
    pkill -f "next dev"
fi

echo -e "${GREEN}✅ SOLEil services stopped${NC}"