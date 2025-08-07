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