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