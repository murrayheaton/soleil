#!/bin/bash

# Soleil Band Platform - Backend Stop Script
# This script stops the backend server

echo "🛑 Stopping Soleil Band Platform Backend..."

# Find and kill processes on port 8000
PIDS=$(lsof -ti:8000)

if [ -z "$PIDS" ]; then
    echo "✅ No backend processes found running on port 8000"
else
    echo "🔍 Found processes: $PIDS"
    echo "⏹️  Stopping backend processes..."
    echo "$PIDS" | xargs kill -TERM
    
    # Wait a bit for graceful shutdown
    sleep 2
    
    # Force kill if still running
    REMAINING=$(lsof -ti:8000)
    if [ ! -z "$REMAINING" ]; then
        echo "💀 Force stopping remaining processes..."
        echo "$REMAINING" | xargs kill -9
    fi
    
    echo "✅ Backend stopped successfully"
fi

echo "🎵 Soleil backend is now offline"