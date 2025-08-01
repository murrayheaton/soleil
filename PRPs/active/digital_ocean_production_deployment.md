name: "Digital Ocean Production Deployment Script - Secure & Automated"
description: |

## Purpose
Create a production-ready deployment script for Digital Ocean droplets that handles security hardening, environment configuration, SSL setup, and Docker orchestration with proper secret management and user prompting.

## Core Principles
1. **Security First**: SSH hardening, firewall configuration, non-root user setup
2. **Secret Management**: Interactive prompts for sensitive data, never commit secrets
3. **Infrastructure as Code**: Automated setup with validation loops
4. **Production Ready**: SSL, monitoring, backups, and scaling considerations
5. **Follow CLAUDE.md**: Adhere to all project conventions and documentation standards

---

## Goal
Create a comprehensive deployment script (`deploy_to_digitalocean.sh`) that:
- Sets up a secure Digital Ocean droplet from scratch
- Configures production environment with proper secrets management
- Deploys the Soleil Band Platform with SSL and monitoring
- Handles all security hardening automatically
- Prompts user for required secrets/keys interactively

## Why
- **Security**: Current deployment has missing celery configuration and potential security gaps
- **Reproducibility**: Need consistent deployments across environments
- **Secret Management**: Secrets should never be committed to git
- **Production Readiness**: SSL, monitoring, backups must be automated
- **Developer Experience**: One-command deployment with guided secret input

## What
A production deployment script that creates a fully configured Digital Ocean environment

### Success Criteria
- [ ] Secure droplet with SSH key auth, firewall, non-root user
- [ ] Working SSL certificate for solepower.live domain  
- [ ] All Docker services running (backend, frontend, postgres, redis, celery)
- [ ] Interactive prompts for Google OAuth, database passwords, etc.
- [ ] Monitoring and backup configuration
- [ ] Zero secrets committed to repository

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://docs.digitalocean.com/products/droplets/getting-started/recommended-droplet-setup/
  why: Official DO security hardening guide
  
- url: https://medium.com/@louis_10840/from-development-to-production-deploy-your-app-using-docker-on-digitalocean-with-ease-9557cde05161
  why: Docker deployment best practices on DO
  
- file: /root/soleil/band-platform/deploy.sh
  why: Current deployment script - has structure but missing security and secrets
  
- file: /root/soleil/band-platform/docker-compose.production.yml
  why: Production configuration - shows celery module issue and service structure
  
- url: https://github.com/sunny75016/harden
  why: Security hardening scripts for Ubuntu droplets
  
- url: https://docs.digitalocean.com/products/app-platform/how-to/deploy-from-container-images/
  why: Container deployment specifics and requirements

- file: /root/soleil/CLAUDE.md
  why: Project conventions and documentation requirements
```

### Current Codebase tree (deployment-relevant files)
```bash
/root/soleil/band-platform/
├── deploy.sh                           # Current deployment script (needs security)
├── start_sole_power_live.sh            # Local development script
├── docker-compose.production.yml       # Production services (has celery issues)
├── docker-compose.yml                  # Development services
├── backend/
│   ├── Dockerfile                      # Backend container config
│   ├── requirements.txt                # Python dependencies
│   ├── .env.production                 # Environment file (may have secrets)
│   ├── .env.production.template        # Template for secrets
│   └── app/
│       ├── main.py.archived           # FastAPI entry point (archived)
│       ├── start_server.py            # Server startup
│       └── (missing celery_app.py)    # ISSUE: Celery config missing
├── frontend/
│   ├── Dockerfile                      # Frontend container config  
│   ├── package.json                    # Node.js dependencies
│   └── .env.production                 # Frontend environment
├── nginx/
│   ├── nginx.conf                      # Nginx configuration
│   └── ssl/                           # SSL certificate storage
└── storage/                           # Persistent data storage
```

### Desired Codebase tree with files to be added
```bash
/root/soleil/band-platform/
├── deploy_to_digitalocean.sh           # NEW: Comprehensive deployment script
├── scripts/
│   ├── hardening.sh                    # NEW: Security hardening script
│   ├── secrets_setup.sh               # NEW: Interactive secrets configuration
│   └── monitoring_setup.sh            # NEW: Monitoring and backup setup  
├── backend/app/
│   └── celery_app.py                   # NEW: Missing Celery configuration
├── .env.production.secure              # NEW: Generated secure environment file
└── deployment_logs/                    # NEW: Deployment logging directory
```

### Known Gotchas of our codebase & Library Quirks
```python
# CRITICAL: Celery workers failing because app.celery_app module missing
# Current error: "The module app.celery_app was not found"
# Location: docker-compose.production.yml line 128

# CRITICAL: SSL certificate setup requires interactive input
# Current issue: Certbot prompts for expand/cancel during automation
# Need: Non-interactive certbot flags

# CRITICAL: Secrets in .env files may be committed
# Risk: Google OAuth secrets, database passwords in git
# Solution: Interactive prompts + .env.production.secure generation

# CRITICAL: Digital Ocean droplet requires specific security setup
# Required: SSH key auth, non-root user, firewall rules, system updates
# Pattern: Use cloud-init user data for initial setup

# CRITICAL: Production environment needs minimum 1GB RAM for Docker
# Required: Proper droplet sizing and resource allocation
```

## Implementation Blueprint

### Data models and structure
Create secure environment configuration and service definitions:
```yaml
# Environment structure for secure deployment
secrets:
  - GOOGLE_CLIENT_ID: "Interactive prompt"
  - GOOGLE_CLIENT_SECRET: "Interactive prompt" 
  - DATABASE_PASSWORD: "Auto-generated secure"
  - REDIS_PASSWORD: "Auto-generated secure"
  - SECRET_KEY: "Auto-generated secure"
  
services:
  - postgres: "Database with encrypted storage"
  - redis: "Cache with password auth"
  - backend: "FastAPI with proper Celery config"
  - celery_worker: "Background task processing"
  - celery_beat: "Scheduled task execution"
  - frontend: "Next.js production build"
  - nginx: "Reverse proxy with SSL termination"
```

### List of tasks to be completed to fulfill the PRP in order

```yaml
Task 1 - Fix Celery Configuration:
CREATE backend/app/celery_app.py:
  - PATTERN: Follow existing FastAPI structure in app/
  - CONTENT: Celery app initialization with Redis broker
  - INTEGRATE: Import in main application startup

Task 2 - Create Security Hardening Script:  
CREATE scripts/hardening.sh:
  - PATTERN: Use Digital Ocean hardening best practices
  - FEATURES: SSH hardening, firewall setup, system updates
  - REFERENCE: https://github.com/sunny75016/harden patterns

Task 3 - Create Interactive Secrets Setup:
CREATE scripts/secrets_setup.sh:
  - FUNCTION: Prompt user for OAuth keys, generate passwords
  - OUTPUT: .env.production.secure file (git-ignored)
  - VALIDATE: Check secret format and connectivity

Task 4 - Create Monitoring Setup Script:
CREATE scripts/monitoring_setup.sh:
  - FEATURES: Log aggregation, backup configuration
  - INTEGRATE: DigitalOcean monitoring agent
  - SETUP: Automated backup schedules

Task 5 - Create Comprehensive Deployment Script:
CREATE deploy_to_digitalocean.sh:
  - ORCHESTRATE: All above scripts in proper sequence
  - VALIDATE: Each step with health checks
  - ROLLBACK: Ability to undo failed deployments
  - LOGGING: Comprehensive deployment logging

Task 6 - Update Docker Compose Configuration:
MODIFY docker-compose.production.yml:
  - FIX: Celery command references to use new celery_app.py
  - ADD: Proper environment variable handling
  - SECURE: Remove hardcoded passwords, use generated ones

Task 7 - Create Deployment Documentation:
UPDATE DEPLOYMENT_GUIDE.md:
  - DOCUMENT: Step-by-step deployment process
  - INCLUDE: Troubleshooting common issues
  - REFERENCE: All required external accounts/services
```

### Per task pseudocode with critical details

```bash
# Task 1 - Celery Configuration
# backend/app/celery_app.py
from celery import Celery
from app.config import settings  # Use existing config pattern

# CRITICAL: Use Redis URL from environment
celery_app = Celery(
    "band_platform",
    broker=settings.REDIS_URL,  # Environment variable
    include=["app.tasks"]       # Task modules location
)

# PATTERN: Match existing FastAPI configuration style
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Task 2 - Security Hardening Script  
#!/bin/bash
# scripts/hardening.sh

# CRITICAL: Must run as root initially, then create non-root user
if [[ $EUID -eq 0 ]]; then
    echo "Running initial setup as root..."
    
    # PATTERN: Follow DO recommendations
    # 1. Update system packages
    apt-get update && apt-get upgrade -y
    
    # 2. Create non-root sudo user
    read -p "Enter username for sudo user: " USERNAME
    adduser --disabled-password --gecos "" $USERNAME
    usermod -aG sudo $USERNAME
    
    # 3. Setup SSH key authentication
    mkdir -p /home/$USERNAME/.ssh
    read -p "Paste your public SSH key: " SSH_KEY
    echo "$SSH_KEY" > /home/$USERNAME/.ssh/authorized_keys
    chmod 600 /home/$USERNAME/.ssh/authorized_keys
    chown -R $USERNAME:$USERNAME /home/$USERNAME/.ssh
    
    # 4. Disable password authentication
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
    sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    systemctl restart sshd
    
    # 5. Setup UFW firewall
    ufw default deny incoming
    ufw default allow outgoing  
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
    
    echo "Hardening complete. Switch to user: $USERNAME"
fi

# Task 3 - Interactive Secrets Setup
#!/bin/bash
# scripts/secrets_setup.sh

# FUNCTION: Collect secrets securely without echoing
collect_secrets() {
    echo "=== GOOGLE OAUTH SETUP ==="
    echo "Visit: https://console.developers.google.com/apis/credentials"
    read -p "Google Client ID: " GOOGLE_CLIENT_ID
    read -s -p "Google Client Secret: " GOOGLE_CLIENT_SECRET
    echo
    
    echo "=== AUTO-GENERATING SECURE PASSWORDS ==="
    DB_PASSWORD=$(openssl rand -base64 32)
    REDIS_PASSWORD=$(openssl rand -base64 32)  
    SECRET_KEY=$(openssl rand -base64 64)
    
    # CRITICAL: Create secure env file (never commit)
    cat > .env.production.secure << EOF
# Generated: $(date)
GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET
DB_PASSWORD=$DB_PASSWORD
REDIS_PASSWORD=$REDIS_PASSWORD
SECRET_KEY=$SECRET_KEY
DOMAIN=solepower.live
SSL_EMAIL=admin@solepower.live
EOF
    
    chmod 600 .env.production.secure
    echo "✓ Secrets configured in .env.production.secure"
}

# Task 5 - Main Deployment Script Structure
#!/bin/bash
# deploy_to_digitalocean.sh

set -e  # Exit on any error

# CRITICAL: Run validation before deployment
pre_deployment_checks() {
    # Check Docker is installed
    command -v docker >/dev/null 2>&1 || { echo "Docker required"; exit 1; }
    
    # Check if running on Digital Ocean droplet
    curl -s http://169.254.169.254/metadata/v1/id >/dev/null || {
        echo "Warning: Not running on Digital Ocean droplet"
    }
    
    # Verify minimum system requirements
    MEMORY=$(free -m | awk 'NR==2{print $2}')
    if [ $MEMORY -lt 1024 ]; then
        echo "Error: Minimum 1GB RAM required, found ${MEMORY}MB"
        exit 1
    fi
}

main_deployment() {
    echo "🚀 Starting Digital Ocean Production Deployment"
    
    # Step 1: Security hardening (if needed)
    ./scripts/hardening.sh
    
    # Step 2: Configure secrets interactively
    ./scripts/secrets_setup.sh
    
    # Step 3: Deploy application stack
    docker-compose -f docker-compose.production.yml up -d --build
    
    # Step 4: Setup SSL certificates
    docker-compose -f docker-compose.production.yml run --rm certbot \
        certonly --webroot --webroot-path=/var/www/certbot \
        --email ${SSL_EMAIL} --agree-tos --no-eff-email \
        --non-interactive -d ${DOMAIN}
    
    # Step 5: Configure monitoring
    ./scripts/monitoring_setup.sh
    
    echo "✅ Deployment Complete: https://${DOMAIN}"
}
```

### Integration Points
```yaml
SYSTEM_SERVICES:
  - ufw: "Firewall configuration for ports 22, 80, 443"
  - ssh: "Hardened configuration with key-only auth"
  - docker: "Container orchestration with proper networking"
  
ENVIRONMENT_FILES:
  - create: .env.production.secure (git-ignored)
  - update: backend/.env.production (template-based)
  - update: frontend/.env.production (domain-specific)
  
DOCKER_COMPOSE:
  - fix: celery service commands to use app.celery_app
  - add: proper health checks for all services
  - secure: environment variable references
  
MONITORING:
  - install: DigitalOcean monitoring agent
  - configure: Automated backups (daily/weekly)
  - setup: Log aggregation and alerting
```

## Validation Loop

### Level 1: Pre-Deployment Validation
```bash
# Run these FIRST - ensure environment is ready
./deploy_to_digitalocean.sh --check-only

# Expected: All system requirements met, no errors
# If errors: Address each requirement before proceeding
```

### Level 2: Security Validation  
```bash
# Test SSH hardening
ssh -o PasswordAuthentication=yes user@droplet_ip
# Expected: Permission denied (publickey required)

# Test firewall configuration
nmap -p 22,80,443,8000 droplet_ip
# Expected: Only 22, 80, 443 open; 8000 filtered

# Test service isolation
docker exec backend_container netstat -tlnp
# Expected: Services only listening on expected ports
```

### Level 3: Application Validation
```bash
# Test HTTPS endpoint
curl -I https://solepower.live
# Expected: HTTP/2 200, valid SSL certificate

# Test backend API health
curl https://solepower.live/api/health
# Expected: {"status": "healthy"}

# Test all Docker services
docker-compose -f docker-compose.production.yml ps
# Expected: All services "Up" and "healthy"

# Test Celery workers
docker-compose -f docker-compose.production.yml logs celery_worker
# Expected: "Connected to redis://..." no module errors
```

### Level 4: Security Audit
```bash
# Run security audit
lynis audit system
# Expected: Score >80, no critical issues

# Check for secrets in git
git log --all --full-history -- "*.env*" | grep -i "secret\|password\|key"
# Expected: No output (no secrets committed)

# Verify backup configuration
ls -la /opt/digitalocean/backups/
# Expected: Backup scripts present and executable
```

## Final validation Checklist
- [ ] All services healthy: `docker-compose ps` shows all "Up (healthy)"
- [ ] SSL certificate valid: `openssl s_client -connect solepower.live:443`
- [ ] No secrets in git: `git secrets --scan` passes
- [ ] Security hardening complete: SSH keys only, firewall active
- [ ] Celery workers operational: No "module not found" errors
- [ ] Monitoring configured: DO agent installed, backups scheduled
- [ ] Documentation updated: DEPLOYMENT_GUIDE.md reflects new process

---

## Anti-Patterns to Avoid
- ❌ Don't commit any secrets to git repository
- ❌ Don't skip security hardening steps for "faster" deployment  
- ❌ Don't use default passwords in production
- ❌ Don't expose internal services (Redis, Postgres) to internet
- ❌ Don't ignore SSL certificate validation errors
- ❌ Don't run production services as root user
- ❌ Don't deploy without proper backup configuration

## Emergency Rollback Plan
```bash
# If deployment fails, rollback steps:
1. Stop all services: docker-compose -f docker-compose.production.yml down
2. Restore previous backup: ./scripts/restore_backup.sh <backup_id>
3. Restart with previous configuration
4. Investigate logs in deployment_logs/ directory
```

## Security Compliance Checklist
- [ ] SSH password authentication disabled
- [ ] Non-root user with sudo access created
- [ ] UFW firewall configured and active
- [ ] SSL/TLS certificates valid and auto-renewing
- [ ] Database passwords auto-generated (32+ chars)
- [ ] No secrets stored in environment variables in containers
- [ ] All services running with minimal required permissions
- [ ] System packages updated to latest versions
- [ ] Automated security updates enabled
- [ ] Monitoring and alerting configured for security events