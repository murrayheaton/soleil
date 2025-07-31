#!/bin/bash

# Sole Power Live - Production Deployment Script
# This script rebuilds and deploys the frontend and restarts services

set -e

echo "🚀 Starting Sole Power Live deployment..."

# Change to project directory
cd /root/soleil/band-platform

# Build frontend
echo "📦 Building Next.js frontend..."
cd frontend
npm run build

# Copy frontend files to web directory
echo "📂 Copying frontend files..."
rm -rf /var/www/solepower.live/*
cp -r out/* /var/www/solepower.live/
chown -R www-data:www-data /var/www/solepower.live

# Restart backend service
echo "🔄 Restarting backend service..."
systemctl restart solepower-backend.service

# Reload nginx
echo "🌐 Reloading nginx..."
systemctl reload nginx

# Verify services are running
echo "✅ Checking service status..."
systemctl is-active --quiet nginx && echo "✓ Nginx is running"
systemctl is-active --quiet solepower-backend.service && echo "✓ Backend is running"

echo "🎉 Deployment complete!"
echo "🌍 Website: https://solepower.live"
echo "🔧 API: https://solepower.live/api/"

# Test endpoints
echo "🧪 Running quick tests..."
if curl -sf https://solepower.live/ > /dev/null; then
    echo "✓ Frontend is responding"
else
    echo "❌ Frontend test failed"
fi

if curl -sf https://solepower.live/api/health > /dev/null; then
    echo "✓ API is responding"
else
    echo "❌ API test failed"
fi

echo "Deployment script completed!"