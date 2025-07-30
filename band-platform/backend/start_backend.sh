#!/bin/bash

# Soleil Band Platform - Backend Startup Script
# This script starts the backend server with proper virtual environment

echo "🎵 Starting Soleil Band Platform Backend..."

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv_linux" ]; then
    echo "❌ Virtual environment not found at venv_linux"
    echo "Please run: python3 -m venv venv_linux && source venv_linux/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    echo "Please copy .env.example to .env and configure your settings"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv_linux/bin/activate

# Check if required packages are installed
echo "📦 Checking dependencies..."
python3 -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Installing missing dependencies..."
    pip3 install -r requirements.txt
fi

# Kill any existing process on port 8000
echo "🧹 Cleaning up any existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start the server
echo "🚀 Starting backend server on http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔧 Google Auth: http://localhost:8000/api/auth/google/login"
echo ""
echo "Press Ctrl+C to stop the server"
echo "----------------------------------------"

# Try to start the full app first, fall back to simple server
if python3 -c "from app.main import app" 2>/dev/null; then
    echo "🎯 Starting full backend with all features..."
    python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
else
    echo "🎯 Starting simple backend (some advanced features may not work)..."
    python3 start_server.py
fi