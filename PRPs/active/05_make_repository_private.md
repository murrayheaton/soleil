name: "Convert Repository to Private While Maintaining Functionality"
description: |
  Convert the soleil GitHub repository from public to private while ensuring all deployments,
  CI/CD pipelines, and production functionality continue working without interruption.

priority: HIGH
impact: Security & Intellectual Property

---

## Pre-Implementation Requirements

Before starting implementation, Claude Code MUST:

1. **Read deployment documentation**:
   - DEPLOYMENT_GUIDE.md - Current deployment process
   - docker-compose.production.yml - Production configuration
   - .github/workflows/* (if any) - CI/CD pipelines

2. **Backup critical information**:
   ```bash
   # Document current remote URLs
   cd ~/Documents/LocalCode/claude-code/soleil
   git remote -v > git_remotes_backup.txt
   
   # Check for any hardcoded repo references
   grep -r "github.com/.*soleil" . --exclude-dir=.git > repo_references.txt
   ```

3. **Verify production access**:
   ```bash
   # Ensure you have production server credentials documented
   echo "Production server IP: YOUR_SERVER_IP" > deployment_credentials.txt
   ```

---

## Goal
Convert the soleil repository to private on GitHub while ensuring zero downtime and maintaining all deployment capabilities.

## Why
- **Intellectual Property**: Protect your band management platform code
- **Security**: Prevent unauthorized access to implementation details
- **Business**: Maintain competitive advantage if commercializing
- **Privacy**: Keep band-specific configurations private

## Success Criteria
- [ ] Repository is private on GitHub
- [ ] Production site (solepower.live) continues working
- [ ] Deployment from local machine still works
- [ ] No hardcoded public repo references remain
- [ ] SSH key authentication configured for server
- [ ] Documentation updated for private repo workflow

---

## Investigation Tasks

### Task 1: Audit Repository References
```bash
# Search for hardcoded GitHub references
cd ~/Documents/LocalCode/claude-code/soleil

# Check for public repo URLs
echo "=== Checking for GitHub URLs ==="
grep -r "github.com" . --exclude-dir=.git --exclude-dir=node_modules --exclude="*.log"

# Check for repo cloning commands
echo "=== Checking for git clone commands ==="
grep -r "git clone" . --exclude-dir=.git --exclude-dir=node_modules

# Check deployment scripts
echo "=== Checking deployment scripts ==="
grep -r "git@github.com\|https://github.com" band-platform/deploy.sh deployment_credentials.txt

# Check Docker files for repo references
echo "=== Checking Docker configurations ==="
grep -r "github" band-platform/docker-compose*.yml band-platform/*/Dockerfile
```

### Task 2: Document Current Deployment Method
```bash
# How is code currently deployed to production?
# Option A: Git pull on server (needs SSH key)
# Option B: Local build and SCP (no server GitHub access needed)
# Option C: CI/CD pipeline (needs token update)

# Check if production server has git access
ssh root@YOUR_SERVER_IP "cd /root/soleil && git remote -v"
```

---

## Implementation Tasks

### Task 1: Set Up SSH Keys for Private Repo Access

#### Option A: If Server Pulls from GitHub
```bash
# On production server
ssh root@YOUR_SERVER_IP

# Generate SSH key for server (if not exists)
if [ ! -f ~/.ssh/id_ed25519 ]; then
  ssh-keygen -t ed25519 -C "soleil-production-server" -f ~/.ssh/id_ed25519 -N ""
fi

# Display public key to add to GitHub
cat ~/.ssh/id_ed25519.pub

# Add to ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Configure SSH for GitHub
cat > ~/.ssh/config << EOF
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519
  StrictHostKeyChecking accept-new
EOF

# Test connection (after adding key to GitHub)
ssh -T git@github.com
```

#### Option B: If Deploying from Local Machine
```bash
# Ensure your local SSH key is set up
cat ~/.ssh/id_ed25519.pub || cat ~/.ssh/id_rsa.pub

# Test GitHub SSH access
ssh -T git@github.com

# Update deployment scripts to use SSH
cd ~/Documents/LocalCode/claude-code/soleil
```

### Task 2: Update Repository References

#### Update Deployment Script
```bash
# band-platform/deploy.sh - Update if it contains repo references

#!/bin/bash
# ... existing script ...

# If the script does git operations on the server, update to use SSH:
# OLD: git clone https://github.com/username/soleil.git
# NEW: git clone git@github.com:username/soleil.git

# Better approach - deploy without server GitHub access:
echo "Deployment now uses local build and rsync approach"
```

#### Create New Deployment Script (Recommended)
```bash
# band-platform/deploy_private.sh - New deployment without server GitHub access

#!/bin/bash
set -e

DOMAIN=${1:-solepower.live}
SERVER_USER="root"
SERVER_IP="YOUR_SERVER_IP"
REMOTE_PATH="/root/soleil"

echo "Deploying to $DOMAIN..."

# Build locally
echo "Building Docker images locally..."
docker-compose -f docker-compose.production.yml build

# Save images
echo "Saving Docker images..."
docker save band-platform_backend:latest > backend.tar
docker save band-platform_frontend:latest > frontend.tar

# Copy to server
echo "Copying to server..."
scp backend.tar frontend.tar $SERVER_USER@$SERVER_IP:/tmp/

# Copy necessary files
rsync -avz --exclude='.git' --exclude='node_modules' --exclude='.env' \
  band-platform/ $SERVER_USER@$SERVER_IP:$REMOTE_PATH/band-platform/

# Load and start on server
ssh $SERVER_USER@$SERVER_IP << 'EOF'
cd /root/soleil/band-platform
docker load < /tmp/backend.tar
docker load < /tmp/frontend.tar
docker-compose -f docker-compose.production.yml up -d
rm /tmp/*.tar
EOF

echo "Deployment complete!"
```

### Task 3: Remove Public Repository References

#### Update Documentation
```markdown
# README.md - Update installation instructions

## Installation

```bash
# Clone the repository (requires access)
git clone git@github.com:YOUR_USERNAME/soleil.git

# Or if you have been granted access:
# Request access from the repository owner
```

## Deployment

This is a private repository. Deployment requires:
1. SSH access to the production server
2. Repository access (for development)
3. Production environment variables
```

#### Update Any Public Links
```bash
# Find and update any public documentation links
find . -name "*.md" -exec grep -l "github.com.*soleil" {} \; | \
  xargs sed -i '' 's|https://github.com/.*/soleil|[private repository]|g'
```

### Task 4: GitHub Repository Settings

#### Steps to Make Repository Private

1. **On GitHub.com**:
   ```
   1. Go to https://github.com/YOUR_USERNAME/soleil
   2. Click "Settings" (repository settings, not account)
   3. Scroll to "Danger Zone"
   4. Click "Change visibility"
   5. Select "Make private"
   6. Type repository name to confirm
   7. Click "I understand, change repository visibility"
   ```

2. **Add Deploy Key (if server needs access)**:
   ```
   1. In repository settings, go to "Deploy keys"
   2. Click "Add deploy key"
   3. Title: "Production Server Read-Only"
   4. Key: [paste server's public key from Task 1]
   5. Allow write access: NO (read-only for safety)
   6. Click "Add key"
   ```

3. **Update Team Access** (if needed):
   ```
   1. Settings → Manage access
   2. Add any collaborators who need access
   ```

### Task 5: Update Local Repository URL

```bash
# After making repo private, update local remote
cd ~/Documents/LocalCode/claude-code/soleil

# Check current remote
git remote -v

# Update to SSH URL (if not already)
git remote set-url origin git@github.com:YOUR_USERNAME/soleil.git

# Verify change
git remote -v

# Test access
git fetch origin
```

### Task 6: Create Secure Environment Template

```bash
# .env.example.private - New template without sensitive data

# This is a template for required environment variables
# Copy to .env.production and fill in your values
# NEVER commit .env.production to the repository

# Google OAuth (get from Google Cloud Console)
GOOGLE_CLIENT_ID=your-client-id-here
GOOGLE_CLIENT_SECRET=your-secret-here
GOOGLE_REDIRECT_URI=https://yourdomain.com/api/auth/google/callback
GOOGLE_DRIVE_SOURCE_FOLDER_ID=your-folder-id

# Session Configuration
SESSION_SECRET=generate-random-string-here

# Domain Configuration
DOMAIN=yourdomain.com
SSL_EMAIL=your-email@example.com

# Production Flags
DEBUG=False
NODE_ENV=production
```

---

## Testing & Validation

### Pre-Private Testing
```bash
# 1. Test current deployment method
cd ~/Documents/LocalCode/claude-code/soleil/band-platform
./deploy.sh solepower.live

# 2. Document exactly how deployment works
echo "Current deployment method: [describe]" > deployment_method.txt

# 3. Ensure production is stable
curl https://solepower.live/health
```

### Post-Private Testing
```bash
# 1. Verify local access
git fetch origin
git pull origin main

# 2. Test deployment with new private setup
./deploy_private.sh solepower.live

# 3. Verify production still works
curl https://solepower.live/health

# 4. Test clone with SSH
cd /tmp
git clone git@github.com:YOUR_USERNAME/soleil.git test-clone
rm -rf test-clone
```

### Validation Checklist
- [ ] Repository shows as "Private" on GitHub
- [ ] Local development can pull/push
- [ ] Deployment completes successfully
- [ ] Production site remains accessible
- [ ] No public references in documentation
- [ ] Deploy keys configured (if needed)
- [ ] Collaborator access granted (if needed)

---

## Rollback Plan

If issues occur after making repository private:

1. **Make Repository Public Again**:
   ```
   GitHub → Settings → Danger Zone → Change visibility → Make public
   ```

2. **Revert Remote URLs** (if changed):
   ```bash
   git remote set-url origin https://github.com/YOUR_USERNAME/soleil.git
   ```

3. **Use Backup Deployment Method**:
   ```bash
   # If new deployment fails, use the old method
   # Check deployment_method.txt for original approach
   ```

---

## Post-Implementation

1. **Update Documentation**:
   - Add "Private Repository" note to README
   - Update CONTRIBUTING.md with access request process
   - Document SSH key setup in DEVELOPMENT.md

2. **Secure Cleanup**:
   ```bash
   # Remove any temporary files with sensitive data
   rm -f git_remotes_backup.txt
   rm -f repo_references.txt
   rm -f deployment_credentials.txt
   shred -v backend.tar frontend.tar 2>/dev/null || true
   ```

3. **Monitor for Issues**:
   - Check deployment logs for authentication errors
   - Verify team members can access repository
   - Ensure automated backups still work (if configured)

4. **Best Practices Going Forward**:
   - Never commit .env.production
   - Use deploy keys for server access (read-only)
   - Rotate secrets periodically
   - Document access procedures for new team members

---

## Alternative: GitHub Private with Public Deployment

If you want to keep some deployment artifacts public:

1. Create a separate `soleil-deploy` public repository
2. Use GitHub Actions to build and publish Docker images
3. Keep source code private but deployment artifacts public
4. Update deployment to pull from public Docker registry

This hybrid approach maintains source privacy while simplifying deployment.