#!/bin/bash
#
# Auto Backup Script for clawdbot Workspace
# Commits and pushes changes to GitHub every run
#

WORKSPACE="/root/.openclaw/workspace"

cd "$WORKSPACE" || exit 1

echo "[backup] Checking for changes..."

# Check if there are changes
if git diff --quiet && git diff --quiet --cached; then
    echo "[backup] No changes to commit"
    exit 0
fi

# Get current time for commit message
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')

# Add all changes
git add -A

# Create commit
echo "[backup] Committing changes..."
git commit -m "Auto backup: $TIMESTAMP"

# Push to GitHub
echo "[backup] Pushing to GitHub..."
git push -u origin master

if [ $? -eq 0 ]; then
    echo "[backup] ✓ Backup completed successfully"
else
    echo "[backup] ✗ Push failed with code $?"
    exit 1
fi
