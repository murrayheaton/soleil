# Solepower.live Deployment Instructions

This guide is specifically for deploying Soleil to solepower.live using Squarespace DNS.

## Prerequisites Checklist

- [ ] Domain purchased (solepower.live) ✓
- [ ] VPS server (DigitalOcean, AWS, etc.)
- [ ] Google Cloud account with OAuth credentials
- [ ] Your server's IP address
- [ ] SSH access to your server

## Quick Start Commands

After getting your server and updating DNS in Squarespace:

```bash
# Connect to your server
ssh root@YOUR_SERVER_IP

# Run this one-liner to set everything up:
curl -fsSL https://raw.githubusercontent.com/murrayheaton/soleil/main/band-platform/setup-server.sh | bash -s solepower.live your-email@example.com

# Or do it manually:
apt update && apt upgrade -y
curl -fsSL https://get.docker.com | sh
apt install docker-compose git -y
git clone https://github.com/murrayheaton/soleil.git
cd soleil/band-platform
chmod +x deploy.sh
./deploy.sh solepower.live your-email@example.com
```

## Squarespace DNS Configuration

1. Log into Squarespace
2. Navigate to: Settings → Domains → solepower.live → DNS Settings
3. Delete any existing A records for @ and www
4. Add these records exactly:

| Type | Host | Points to | TTL |
|------|------|-----------|-----|
| A | @ | YOUR_SERVER_IP | 3600 |
| A | www | YOUR_SERVER_IP | 3600 |

Wait 5-30 minutes for DNS propagation.

## Google OAuth Configuration

1. Go to: https://console.cloud.google.com
2. Select your project (or create new)
3. Navigate to: APIs & Services → Credentials
4. Edit your OAuth 2.0 Client ID
5. Add to Authorized redirect URIs:
   - `https://solepower.live/api/auth/google/callback`
6. Add to Authorized JavaScript origins:
   - `https://solepower.live`
   - `https://www.solepower.live`

## Verify Deployment

Once DNS has propagated and deployment is complete:

1. **Check DNS propagation:**
   ```bash
   nslookup solepower.live
   ```

2. **Test the site:**
   - HTTP redirect: http://solepower.live (should redirect to HTTPS)
   - Main site: https://solepower.live
   - API health: https://solepower.live/api/health

3. **View logs if needed:**
   ```bash
   cd /root/soleil/band-platform
   docker-compose -f docker-compose.production.yml logs -f
   ```

## Troubleshooting

### "Connection refused" or site not loading
- DNS hasn't propagated yet (wait up to 24 hours)
- Firewall blocking ports: `ufw allow 80/tcp && ufw allow 443/tcp`
- Server not running: Check with `docker ps`

### SSL Certificate errors
- Let's Encrypt rate limited: Wait 1 hour
- DNS not pointing correctly: Verify with `dig solepower.live`

### Google OAuth not working
- Redirect URI must match EXACTLY
- Clear browser cookies/cache
- Check backend logs: `docker-compose -f docker-compose.production.yml logs backend`

## Maintenance Commands

```bash
# Go to project directory
cd /root/soleil/band-platform

# View all logs
docker-compose -f docker-compose.production.yml logs -f

# Restart services
docker-compose -f docker-compose.production.yml restart

# Update code
git pull
docker-compose -f docker-compose.production.yml up -d --build

# Backup database
docker-compose -f docker-compose.production.yml exec postgres pg_dump -U band_user band_platform > backup_$(date +%Y%m%d).sql
```

## Server Recommendations

For solepower.live, recommended specs:
- **DigitalOcean**: $12/month droplet (2GB RAM, 1 CPU)
- **Region**: NYC or SFO (assuming US audience)
- **OS**: Ubuntu 22.04 LTS

## Support

If you encounter issues:
1. Check the logs first
2. Verify DNS settings in Squarespace
3. Ensure Google OAuth is configured correctly
4. Server firewall allows ports 80 and 443