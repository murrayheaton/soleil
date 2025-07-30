# Soleil Band Platform - Production Deployment Guide

This guide walks you through deploying Soleil to your own domain using Docker.

## Prerequisites

1. **Server Requirements**
   - VPS or cloud instance (AWS EC2, DigitalOcean, etc.)
   - Ubuntu 20.04+ or similar Linux distribution
   - At least 2GB RAM, 2 CPU cores
   - 20GB+ storage
   - Docker and Docker Compose installed

2. **Domain and DNS**
   - A registered domain name
   - DNS A records pointing to your server's IP address
   - Both `example.com` and `www.example.com` should point to your server

3. **Google Cloud Platform Setup**
   - Google Cloud Project with Drive API enabled
   - OAuth 2.0 credentials created
   - Service account with Drive access (optional)

## Deployment Steps

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add current user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Clone Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/soleil.git
cd soleil/band-platform
```

### 3. Configure Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create or select a project
3. Enable Google Drive API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `https://yourdomain.com/api/auth/google/callback`
5. Save the Client ID and Client Secret

### 4. Run Deployment Script

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment (replace with your domain and email)
./deploy.sh yourdomain.com your-email@example.com
```

### 5. Complete Configuration

After the script runs, you need to:

1. **Add Google credentials to `backend/.env.production`:**
   ```bash
   GOOGLE_CLIENT_ID=your_client_id_here
   GOOGLE_CLIENT_SECRET=your_client_secret_here
   GOOGLE_DRIVE_SOURCE_FOLDER_ID=your_folder_id_here
   ```

2. **Update frontend configuration in `frontend/.env.production`:**
   ```bash
   NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_client_id_here
   ```

3. **Restart services:**
   ```bash
   docker-compose -f docker-compose.production.yml restart backend frontend
   ```

## Manual Deployment (Alternative)

If you prefer manual deployment over the script:

### 1. Create Production Environment File

Create `.env.production` in the root:
```bash
DOMAIN=yourdomain.com
SSL_EMAIL=your-email@example.com
DB_PASSWORD=generate_secure_password_here
REDIS_PASSWORD=generate_secure_password_here
SECRET_KEY=generate_secure_key_here
```

### 2. Update Configuration Files

Replace `YOUR_DOMAIN.com` in these files with your actual domain:
- `nginx/nginx.conf`
- `backend/.env.production`
- `frontend/.env.production`

### 3. Build and Start Services

```bash
# Build and start all services
docker-compose -f docker-compose.production.yml up -d --build

# Wait for services to initialize
sleep 30

# Get SSL certificate
docker-compose -f docker-compose.production.yml run --rm certbot

# Restart nginx to load certificates
docker-compose -f docker-compose.production.yml restart nginx
```

## SSL Certificate Management

The deployment uses Let's Encrypt for free SSL certificates.

**Initial certificate:**
```bash
docker-compose -f docker-compose.production.yml run --rm certbot
```

**Renew certificate (set up as cron job):**
```bash
# Add to crontab: crontab -e
0 0 * * 0 cd /path/to/soleil/band-platform && docker-compose -f docker-compose.production.yml run --rm certbot renew && docker-compose -f docker-compose.production.yml restart nginx
```

## Monitoring and Maintenance

### View Logs
```bash
# All services
docker-compose -f docker-compose.production.yml logs -f

# Specific service
docker-compose -f docker-compose.production.yml logs -f backend
```

### Service Management
```bash
# Stop all services
docker-compose -f docker-compose.production.yml down

# Restart specific service
docker-compose -f docker-compose.production.yml restart backend

# Update and redeploy
git pull
docker-compose -f docker-compose.production.yml up -d --build
```

### Database Backup
```bash
# Create backup
docker-compose -f docker-compose.production.yml exec postgres pg_dump -U band_user band_platform > backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose -f docker-compose.production.yml exec -T postgres psql -U band_user band_platform < backup_20240101.sql
```

## Troubleshooting

### SSL Certificate Issues
- Ensure ports 80 and 443 are open in your firewall
- Check DNS propagation: `nslookup yourdomain.com`
- View Certbot logs: `docker-compose -f docker-compose.production.yml logs certbot`

### Connection Issues
- Check nginx logs: `docker-compose -f docker-compose.production.yml logs nginx`
- Verify backend health: `curl http://localhost:8000/health`
- Check frontend: `docker-compose -f docker-compose.production.yml logs frontend`

### Google OAuth Issues
- Verify redirect URI matches exactly
- Ensure domain is added to authorized domains in Google Console
- Check backend logs for specific error messages

## Security Recommendations

1. **Firewall Configuration**
   ```bash
   sudo ufw allow 22/tcp    # SSH
   sudo ufw allow 80/tcp    # HTTP
   sudo ufw allow 443/tcp   # HTTPS
   sudo ufw enable
   ```

2. **Regular Updates**
   - Keep Docker images updated
   - Apply system security updates
   - Monitor for security advisories

3. **Backup Strategy**
   - Set up automated database backups
   - Store backups off-site
   - Test restore procedures regularly

## Performance Optimization

1. **Enable Docker BuildKit**
   ```bash
   export DOCKER_BUILDKIT=1
   ```

2. **Configure swap (for low-memory servers)**
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

3. **Monitor resource usage**
   ```bash
   docker stats
   ```

## Support

For issues or questions:
- Check logs first: `docker-compose -f docker-compose.production.yml logs`
- Review the [main README](../README.md)
- Check environment variables are correctly set
- Ensure all prerequisites are met