#!/bin/bash
# merge_auth_fix_to_main.sh - Safely merge authentication fixes to main

echo "🔐 Authentication Fix Merge to Main"
echo "=================================="
echo ""

# Navigate to project directory
cd /Users/murrayheaton/Documents/GitHub/soleil

# 1. Check current branch and status
echo "📍 Current Status:"
git branch --show-current
git status --short

echo ""
read -p "Are all changes committed? (yes/no): " committed

if [ "$committed" != "yes" ]; then
    echo ""
    echo "📝 Committing current changes..."
    git add -A
    git commit -m "fix: complete authentication consolidation and cleanup

- Consolidated authentication to single implementation (start_server.py)
- Removed redundant OAuth files and old environment configs
- Updated Docker configuration to use correct entry point
- Added robust session management and token refresh
- Cleaned up 20+ obsolete files
- Restructured documentation for clarity
- Maintained all frontend styling unchanged
- Added comprehensive troubleshooting guide

BREAKING CHANGE: Requires .env.production with correct Google OAuth credentials"
fi

# 2. Push current branch
echo ""
echo "📤 Pushing branch to origin..."
current_branch=$(git branch --show-current)
git push origin "$current_branch"

# 3. Pre-merge checklist
echo ""
echo "✅ Pre-Merge Checklist:"
echo "[ ] Authentication tested locally"
echo "[ ] Production site still accessible"
echo "[ ] .env.production has real credentials"
echo "[ ] Backup of auth data created"
echo "[ ] No placeholder values in config"
echo ""
read -p "Have you verified ALL items above? (yes/no): " verified

if [ "$verified" != "yes" ]; then
    echo "❌ Complete checklist before merging!"
    exit 1
fi

# 4. Switch to main and update
echo ""
echo "🔄 Switching to main branch..."
git checkout main
git pull origin main

# 5. Merge the fix
echo ""
echo "🔀 Merging authentication fixes..."
git merge "$current_branch" --no-ff -m "Merge branch '$current_branch' into main

Authentication system consolidated and production-ready"

# 6. Run quick verification
echo ""
echo "🧪 Quick verification..."
if [ -f "band-platform/backend/start_server.py" ]; then
    echo "✅ start_server.py exists"
else
    echo "❌ ERROR: start_server.py missing!"
    exit 1
fi

if [ -f "band-platform/backend/.env.production" ]; then
    echo "✅ .env.production exists"
else
    echo "⚠️  WARNING: .env.production missing - ensure it's on production server"
fi

# 7. Push to main
echo ""
echo "📤 Pushing to main..."
read -p "Ready to push to main? This will update production! (yes/no): " push_confirm

if [ "$push_confirm" != "yes" ]; then
    echo "Push cancelled. When ready, run: git push origin main"
    exit 0
fi

git push origin main

# 8. Post-merge actions
echo ""
echo "✅ Merge Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Deploy to production:"
echo "   ssh root@YOUR_SERVER_IP"
echo "   cd /root/soleil"
echo "   git pull origin main"
echo "   cd band-platform"
echo "   docker-compose -f docker-compose.production.yml up -d --build"
echo ""
echo "2. Monitor production logs:"
echo "   docker-compose -f docker-compose.production.yml logs -f backend"
echo ""
echo "3. Test production auth:"
echo "   https://solepower.live"
echo ""
echo "4. Optional: Delete merged branch:"
echo "   git branch -d $current_branch"
echo "   git push origin --delete $current_branch"
echo ""
echo "🎉 Authentication consolidation successfully merged to main!"