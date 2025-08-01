#!/bin/bash
# fix_and_merge_auth.sh - Handle remote changes and merge to main

echo "🔐 Fixing Remote Conflicts and Merging to Main"
echo "============================================="
echo ""

# Navigate to project directory
cd /Users/murrayheaton/Documents/GitHub/soleil

# 1. Get current branch
current_branch=$(git branch --show-current)
echo "📍 Current branch: $current_branch"

# 2. Pull remote changes and merge
echo ""
echo "📥 Pulling remote changes..."
git pull origin "$current_branch" --rebase

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Merge conflicts detected!"
    echo "Please resolve conflicts manually, then run this script again."
    echo ""
    echo "To resolve:"
    echo "1. Edit conflicted files"
    echo "2. git add <resolved-files>"
    echo "3. git rebase --continue"
    exit 1
fi

# 3. Push updated branch
echo ""
echo "📤 Pushing updated branch..."
git push origin "$current_branch"

if [ $? -ne 0 ]; then
    echo "❌ Push failed. Check error messages above."
    exit 1
fi

# 4. Pre-merge checklist
echo ""
echo "✅ Pre-Merge Checklist:"
echo "[ ] Authentication tested locally"
echo "[ ] Production site (solepower.live) still accessible"
echo "[ ] .env.production has real credentials (not placeholders)"
echo "[ ] Backup of auth data created (user_profiles.json, google_token.json)"
echo "[ ] No placeholder values in config files"
echo ""
read -p "Have you verified ALL items above? (yes/no): " verified

if [ "$verified" != "yes" ]; then
    echo "❌ Complete checklist before merging!"
    exit 1
fi

# 5. Switch to main and update
echo ""
echo "🔄 Switching to main branch..."
git checkout main

if [ $? -ne 0 ]; then
    echo "❌ Failed to switch to main. You may have uncommitted changes."
    exit 1
fi

git pull origin main

# 6. Merge the fix
echo ""
echo "🔀 Merging authentication fixes..."
git merge "$current_branch" --no-ff -m "Merge branch '$current_branch' into main

Authentication system consolidated and production-ready
- Single auth implementation via start_server.py
- Removed 20+ redundant files
- Robust session management
- Comprehensive error handling"

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Merge conflicts with main!"
    echo "Please resolve conflicts, then:"
    echo "1. git add <resolved-files>"
    echo "2. git commit"
    echo "3. git push origin main"
    exit 1
fi

# 7. Quick verification
echo ""
echo "🧪 Verifying critical files..."
if [ -f "band-platform/backend/start_server.py" ]; then
    echo "✅ start_server.py exists"
else
    echo "❌ ERROR: start_server.py missing!"
    exit 1
fi

# 8. Final confirmation before push
echo ""
echo "⚠️  FINAL CONFIRMATION"
echo "This will push to main and affect production!"
echo ""
read -p "Push to main now? (yes/no): " push_confirm

if [ "$push_confirm" != "yes" ]; then
    echo ""
    echo "📌 Merge complete locally. When ready to push:"
    echo "   git push origin main"
    exit 0
fi

# 9. Push to main
git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully merged to main!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Deploy to production:"
    echo "   ssh root@YOUR_SERVER_IP"
    echo "   cd /root/soleil"
    echo "   git pull origin main"
    echo "   cd band-platform"
    echo "   docker-compose -f docker-compose.production.yml up -d --build"
    echo ""
    echo "2. Test production:"
    echo "   https://solepower.live"
    echo ""
    echo "3. Clean up branch (optional):"
    echo "   git branch -d $current_branch"
    echo "   git push origin --delete $current_branch"
else
    echo "❌ Push to main failed!"
fi