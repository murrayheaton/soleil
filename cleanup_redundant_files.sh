#!/bin/bash
# cleanup_redundant_files.sh - Execute file deletions

echo "Starting codebase cleanup..."
echo "This will remove redundant files. Press Ctrl+C to cancel."
echo ""
echo "🔐 CRITICAL PRE-CLEANUP CHECKLIST:"
echo "[ ] Have you backed up all .env files?"
echo "[ ] Have you consolidated secrets to .env.production?"
echo "[ ] Have you tested login with the new configuration?"
echo "[ ] Have you documented all production secrets?"
echo ""
read -p "Type 'yes' to confirm you've completed ALL steps: " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled. Complete the checklist first!"
    exit 1
fi

# Create cleanup log
CLEANUP_LOG="cleanup_$(date +%Y%m%d_%H%M%S).log"

# Function to safely remove files
remove_file() {
    local file="$1"
    local reason="$2"
    
    if [ -f "$file" ]; then
        echo "Removing: $file" | tee -a "$CLEANUP_LOG"
        echo "  Reason: $reason" | tee -a "$CLEANUP_LOG"
        rm -f "$file"
    else
        echo "Already removed: $file" | tee -a "$CLEANUP_LOG"
    fi
}

# Function to safely remove directories
remove_directory() {
    local dir="$1"
    local reason="$2"
    
    if [ -d "$dir" ]; then
        echo "Removing directory: $dir" | tee -a "$CLEANUP_LOG"
        echo "  Reason: $reason" | tee -a "$CLEANUP_LOG"
        rm -rf "$dir"
    else
        echo "Already removed: $dir" | tee -a "$CLEANUP_LOG"
    fi
}

echo "Cleanup started at $(date)" | tee -a "$CLEANUP_LOG"

# Remove OAuth redundancies
cd band-platform/backend
remove_file "minimal_oauth.py" "Experimental OAuth, not used"
remove_file "oauth_only_server.py" "Partial implementation"
remove_file "simple_oauth.py" "Experimental version"
remove_file "standalone_oauth.py" "Test implementation"
remove_file "test_drive_oauth.py" "Test file"

# Archive app/main.py but keep services
if [ -f "app/main.py" ]; then
    mv app/main.py app/main.py.archived
    echo "Archived app/main.py - keeping app/services/* for reusable logic" | tee -a "$CLEANUP_LOG"
fi

# Remove redundant environment files
remove_file ".env" "Redundant with .env.example"
remove_file ".env.production.bak" "Old backup"
remove_file ".env.production.template" "Duplicate of .env.example"
remove_file ".env.test" "Not used"

# Remove macOS specific files
remove_file "Soleil_Backend.command" "macOS specific, use Docker"
remove_file "start_backend.sh" "Redundant with Docker"
remove_file "stop_backend.sh" "Redundant with Docker"

# Frontend cleanup
cd ../frontend
remove_file ".env.production.template" "Duplicate of .env.example"

# Root directory cleanup
cd ../..
remove_file "deploy-solepower.sh" "Old deployment approach"
remove_file "deploy-to-do.sh" "Task list, not a script"
remove_file "online-port.md" "Move to documentation"
remove_file "PRODUCT_VISION_2025-07-30.md" "Outdated version"
remove_file "INITIAL_google_drive_role_based_organization.md" "Initial planning doc"

# Remove band-platform specific files
cd band-platform
remove_file "Sole_Power_Live.command" "macOS specific"
remove_file "README_LAUNCHER.md" "Launcher docs for removed files"
remove_file "SOLEPOWER_DEPLOYMENT.md" "Consolidate into DEPLOYMENT_GUIDE.md"

# Remove backup directory
remove_directory "../band-platform-backup" "Old backup, use git for version control"

echo "Cleanup complete! Log saved to: $CLEANUP_LOG"
echo "Total files and directories processed: $(wc -l < "$CLEANUP_LOG")"
echo ""
echo "Next steps:"
echo "1. Review the cleanup log for any issues"
echo "2. Test authentication with the consolidated setup"
echo "3. Commit changes to git"