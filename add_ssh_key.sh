#!/bin/bash

# Your SSH public key
PUBLIC_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAry4M+75lJSQGqWkNm3eG+ItROJNZGsffSt3k192tsk murray@soleil"

echo "======================================"
echo "SSH Key Setup for Digital Ocean Droplet"
echo "======================================"
echo ""
echo "Since password authentication is disabled, you'll need to:"
echo ""
echo "Option 1: Use Digital Ocean Console (RECOMMENDED)"
echo "-------------------------------------------------"
echo "1. Go to: https://cloud.digitalocean.com/droplets"
echo "2. Click on your droplet"
echo "3. Click 'Access' → 'Launch Droplet Console'"
echo "4. Login with:"
echo "   Username: root"
echo "   Password: pypsyv-kumxen-jIkm4y"
echo ""
echo "5. Once logged in, run these commands:"
echo ""
echo "mkdir -p ~/.ssh"
echo "echo '$PUBLIC_KEY' >> ~/.ssh/authorized_keys"
echo "chmod 600 ~/.ssh/authorized_keys"
echo "chmod 700 ~/.ssh"
echo ""
echo "Option 2: Reset Root Password"
echo "------------------------------"
echo "1. Go to your droplet in Digital Ocean"
echo "2. Click 'Access' → 'Reset Root Password'"
echo "3. Check your email for the new password"
echo "4. Try SSH again with the new password"
echo ""
echo "Option 3: Deploy via Console"
echo "-----------------------------"
echo "If you just need to deploy the auth fixes, use the console and run:"
echo ""
echo "cd /var/www/soleil"
echo "git pull origin main"
echo "cd band-platform/backend"
echo "pip3 install pyjwt"
echo "cd ../frontend"
echo "npm run build"
echo "pm2 restart all"
echo ""
echo "======================================"
echo "Testing SSH connection now..."
echo "======================================"

# Test the connection
ssh -o ConnectTimeout=5 root@159.203.62.132 "echo 'SSH connection successful!'" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ SSH connection is working!"
else
    echo "❌ SSH connection failed. Please use one of the options above."
fi