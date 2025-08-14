# Deployment Checklist

# 🚀 Authentication Fix Deployment Checklist

## Pre-Deployment Verification

### Frontend Changes
- [x] AuthContext created at `frontend/src/contexts/AuthContext.tsx`
- [x] ProfileOnboarding email field fixed (removed readOnly)
- [x] App layout wrapped with AuthProvider
- [x] Session persistence logic implemented
- [x] Token refresh mechanism added

### Backend Changes
- [x] Auth validation endpoint created at `/api/auth/validate`
- [x] Token refresh endpoint created at `/api/auth/refresh`
- [x] OAuth callback updated to set proper cookies
- [x] Session cookies configured with correct settings
- [x] JWT token implementation added

### Testing
- [x] Test suite created for auth flow
- [x] OAuth callback tests
- [x] Session validation tests
- [x] Token refresh tests
- [x] Profile setup tests

## Deployment Steps

### 1. Install Dependencies
```bash
# Backend
cd band-platform/backend
pip install pyjwt

# Frontend - no new dependencies needed
```

### 2. Environment Variables
Add to `.env`:
```
JWT_SECRET=your-secure-secret-key-here
FRONTEND_URL=http://localhost:3000
```

### 3. Start Services
```bash
# Backend
cd band-platform/backend
python start_server.py

# Frontend
cd band-platform/frontend
npm run dev
```

### 4. Test Authentication Flow
1. Navigate to http://localhost:3000
2. Click "Sign in with Google"
3. Complete OAuth flow
4. **Verify email field accepts input** ✅
5. Complete profile setup
6. Navigate to different pages
7. **Verify session persists** ✅
8. Refresh page
9. **Verify still logged in** ✅

## Post-Deployment Monitoring

### Success Metrics
- [ ] 100% OAuth completion rate
- [ ] 0% unexpected logouts
- [ ] Email field accepts input
- [ ] Session persists across navigation
- [ ] Token refresh works automatically

### Rollback Plan
If issues occur:
```bash
git revert HEAD
git push origin main
```

## Known Issues Fixed
1. ✅ **Email field not accepting input** - Removed `readOnly` attribute
2. ✅ **Session not persisting** - Added AuthContext with proper cookie management
3. ✅ **Navigation returns to login** - Implemented session validation on mount
4. ✅ **No token refresh** - Added automatic token refresh every 10 minutes

## Production Considerations
- Change `JWT_SECRET` to secure value
- Set `secure: true` for cookies in production
- Use HTTPS for all endpoints
- Configure proper CORS origins
- Add rate limiting to auth endpoints

## Next Steps
1. Monitor error logs for auth failures
2. Track user completion rates
3. Gather feedback on auth experience
4. Consider adding social login options


---

# Droplet Update Checklist

# Droplet Update Checklist for soleil-working-prototype

## Pre-Update Checks
- [ ] Backup current working state if needed
- [ ] Note current branch: `git branch`
- [ ] Check for uncommitted changes: `git status`

## Update Process
```bash
# 1. Stash any local changes
git stash

# 2. Fetch and checkout working prototype
git fetch --all
git checkout soleil-working-prototype
git pull origin soleil-working-prototype

# 3. Backend update
cd band-platform/backend
source venv_linux/bin/activate
pip install -r requirements.txt

# 4. Frontend update
cd ../frontend
npm install
npm run build

# 5. Environment setup
cd ../backend
# Ensure .env has all required values from .env.production
```

## Environment Variables to Verify
Ensure these are set in your `.env` file:
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI` (should be https://solepower.live/api/auth/google/callback)
- `GOOGLE_DRIVE_SOURCE_FOLDER_ID`
- `DATABASE_URL` (if using PostgreSQL)
- `CORS_ORIGINS` (should include https://solepower.live)

## Service Restart Commands
```bash
# Option 1: If using systemd
sudo systemctl restart soleil-backend
sudo systemctl status soleil-backend

# Option 2: If using PM2
pm2 restart soleil-backend
pm2 logs soleil-backend

# Option 3: If running directly
# Kill existing process
pkill -f "python.*start_server.py"
# Start new process
nohup python start_server.py > server.log 2>&1 &

# Reload nginx
sudo nginx -t
sudo systemctl reload nginx
```

## Post-Update Verification
- [ ] Check backend is running: `curl http://localhost:8000/api/health`
- [ ] Check frontend is accessible: `curl http://localhost:3000`
- [ ] Verify public access: Visit https://solepower.live
- [ ] Test login functionality
- [ ] Check logs for any errors

## Rollback if Needed
```bash
# If something goes wrong, switch back to main
git checkout main
git pull origin main
# Rebuild and restart services
```


---

# SSH Setup

# 🔧 Fix SSH Access to Digital Ocean Droplet

## Common SSH Key Issues & Solutions

### Option 1: Generate New SSH Key (Recommended)
```bash
# 1. Generate a new SSH key pair
ssh-keygen -t ed25519 -C "your-email@example.com" -f ~/.ssh/id_ed25519_digitalocean

# 2. Add the key to your SSH agent
ssh-add ~/.ssh/id_ed25519_digitalocean

# 3. Display your public key to add to Digital Ocean
cat ~/.ssh/id_ed25519_digitalocean.pub
```

### Option 2: Use Password Authentication (Temporary)
```bash
# Connect with password (if enabled on droplet)
ssh root@159.203.62.132

# You'll be prompted for the root password
```

### Option 3: Add SSH Key to Digital Ocean

1. **Get your public key:**
```bash
# If you have an existing key
cat ~/.ssh/id_rsa.pub
# OR
cat ~/.ssh/id_ed25519.pub
```

2. **Add to Digital Ocean:**
- Go to https://cloud.digitalocean.com/account/security
- Click "Add SSH Key"
- Paste your public key
- Give it a name

3. **Add to your droplet:**
- Go to your droplet page
- Click "Access" → "Reset Root Password" (this will email you)
- OR use the Console to add your key manually

### Option 4: Use Digital Ocean Console (No SSH Needed)

1. Go to https://cloud.digitalocean.com/droplets
2. Click on your droplet
3. Click "Access" → "Launch Droplet Console"
4. Login with root credentials
5. Add your SSH key manually:
```bash
# In the console
mkdir -p ~/.ssh
echo "YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### Option 5: Manual Deployment Without SSH

If SSH is broken, you can still deploy by:

1. **Using Digital Ocean Console:**
```bash
# In the web console
cd /var/www/soleil
git pull origin main
cd band-platform/backend
pip3 install pyjwt
pip3 install -r requirements.txt
cd ../frontend
npm install
npm run build
# Restart services
pm2 restart all
# OR
systemctl restart nginx
```

### Quick SSH Config Fix

Create/edit `~/.ssh/config`:
```bash
Host digitalocean
    HostName 159.203.62.132
    User root
    IdentityFile ~/.ssh/id_ed25519_digitalocean
    StrictHostKeyChecking no
```

Then connect with:
```bash
ssh digitalocean
```

### Test SSH Connection
```bash
# Test with verbose output to see what's wrong
ssh -vvv root@159.203.62.132

# This will show you:
# - Which key it's trying to use
# - Why authentication is failing
# - What methods are available
```

### If All Else Fails - Recovery Mode

1. **Reset via Digital Ocean:**
   - Go to your droplet
   - Power → Power Off
   - Access → Reset Root Password
   - Power → Power On
   - Check email for new password

2. **Use Recovery Console:**
   - Access → Recovery → Boot from Recovery ISO
   - Mount your disk and fix SSH keys

## Deploy Without SSH (Alternative)

Since your code is already on GitHub, the droplet can pull it:

1. Use Digital Ocean web console
2. Run these commands:
```bash
cd /var/www/soleil
git pull origin main
pip3 install pyjwt
cd band-platform/frontend
npm run build
pm2 restart all
```

## Common Error Messages

- **Permission denied (publickey)**: Your key isn't authorized
- **Host key verification failed**: Remove old key with `ssh-keygen -R 159.203.62.132`
- **Connection refused**: SSH service might be down
- **No supported authentication methods**: Password auth disabled, need key

## Get Help

If you're still stuck:
1. Share the output of `ssh -vvv root@159.203.62.132`
2. Check Digital Ocean support
3. Use the web console as a fallback
