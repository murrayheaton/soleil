#!/bin/bash

# Quick validation script to check frontend OAuth setup
echo "🔍 Validating Frontend OAuth Configuration..."

# Check if we're in the right directory
if [ ! -f "docker-compose.production.yml" ]; then
    echo "❌ Error: Must run from band-platform directory"
    exit 1
fi

# Check frontend .env.production
if [ -f "frontend/.env.production" ]; then
    CLIENT_ID=$(grep "^NEXT_PUBLIC_GOOGLE_CLIENT_ID=" frontend/.env.production | cut -d= -f2)
    
    if [ -z "$CLIENT_ID" ] || [[ "$CLIENT_ID" == *"your_google_client_id_here"* ]]; then
        echo "❌ Frontend: OAuth Client ID not configured properly"
        echo "   Found: $CLIENT_ID"
        exit 1
    else
        echo "✓ Frontend: OAuth Client ID configured"
        echo "   Client ID: ${CLIENT_ID:0:20}..."
    fi
else
    echo "❌ Frontend: .env.production file not found"
    exit 1
fi

# Check if frontend container can see the variable
if docker-compose -f docker-compose.production.yml ps | grep -q "frontend.*Up"; then
    echo "🐳 Checking running frontend container..."
    
    # Try to get the env var from the running container
    CONTAINER_CLIENT_ID=$(docker-compose -f docker-compose.production.yml exec -T frontend sh -c 'echo $NEXT_PUBLIC_GOOGLE_CLIENT_ID' 2>/dev/null || echo "")
    
    if [ -n "$CONTAINER_CLIENT_ID" ] && [ "$CONTAINER_CLIENT_ID" != "your_google_client_id_here" ]; then
        echo "✓ Frontend container has OAuth credentials"
    else
        echo "⚠️  Frontend container may not have OAuth credentials"
        echo "   You may need to rebuild: docker-compose -f docker-compose.production.yml up -d --build frontend"
    fi
else
    echo "ℹ️  Frontend container not running, skipping runtime check"
fi

echo "✅ Frontend OAuth validation complete!"