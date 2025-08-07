# 🚀 Deploy Authentication Fix to Digital Ocean

## Quick Deploy Steps

### 1. Find Your Droplet IP
Go to: https://cloud.digitalocean.com/droplets
- Look for the droplet running `solepower.live`
- Copy the IP address (something like `137.184.XX.XX`)

### 2. SSH Into Your Droplet
```bash
ssh root@YOUR_DROPLET_IP
```

### 3. Pull the Authentication Fixes
```bash
# Navigate to your project (try these paths)
cd /var/www/soleil
# OR
cd /opt/soleil
# OR
cd /home/soleil

# Pull latest changes that include auth fixes
git pull origin main

# You should see:
# - band-platform/frontend/src/contexts/AuthContext.tsx (new file)
# - band-platform/frontend/src/components/ProfileOnboarding.tsx (modified)
# - band-platform/backend/modules/auth/api/google_auth_routes.py (modified)
```

### 4. Install Backend Dependencies
```bash
cd band-platform/backend
pip3 install pyjwt
```

### 5. Rebuild Frontend
```bash
cd ../frontend
npm install  # In case of new dependencies
npm run build
```

### 6. Restart Services

#### If using PM2:
```bash
pm2 restart all
pm2 status
```

#### If using systemd:
```bash
systemctl restart soleil-backend
systemctl restart nginx
```

#### If running manually:
```bash
# Kill old backend process
pkill -f "python.*start_server.py"

# Start new backend
cd band-platform/backend
nohup python3 start_server.py > backend.log 2>&1 &

# Restart nginx
nginx -s reload
```

### 7. Verify the Fix
Visit: https://solepower.live

Test these specific fixes:
1. ✅ **Email field** in profile setup now accepts input (was readonly before)
2. ✅ **Session persists** when navigating between pages (was losing auth before)

### 8. Check Logs if Needed
```bash
# Backend logs
tail -f band-platform/backend/backend.log

# PM2 logs (if using PM2)
pm2 logs

# Nginx logs
tail -f /var/log/nginx/error.log
```

## What Changed?

### Frontend:
- **NEW**: `AuthContext.tsx` - Manages authentication state globally
- **FIXED**: `ProfileOnboarding.tsx` - Email field now editable
- **UPDATED**: `layout.tsx` - Wrapped app with AuthProvider

### Backend:
- **NEW**: `/api/auth/validate` - Session validation endpoint
- **NEW**: `/api/auth/refresh` - Token refresh endpoint
- **FIXED**: OAuth callback now sets proper JWT cookies

## Troubleshooting

### Can't find project directory?
```bash
# Search for it
find / -name "soleil" -type d 2>/dev/null
```

### Git pull fails?
```bash
# Check status
git status

# If you have local changes
git stash
git pull origin main
git stash pop
```

### Frontend build fails?
```bash
# Clear cache and rebuild
rm -rf node_modules
npm install
npm run build
```

### Backend won't start?
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill the process using it
kill -9 [PID]
```

## Success Indicators
- No errors during `git pull`
- `pyjwt` installs successfully
- Frontend builds without errors
- Services restart without errors
- Email field accepts input on profile page
- Session persists across page navigation

---

**Note**: The authentication fixes are already pushed to the main branch, so a simple `git pull` will get all the necessary changes!