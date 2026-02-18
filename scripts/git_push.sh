#!/bin/bash

# Configuration
COMMIT_MSG="$1"
if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="Auto-backup: $(date '+%Y-%m-%d %H:%M:%S')"
fi

# Navigate to workspace
cd /root/.openclaw/workspace || exit 1

# Check for changes
if [[ -z $(git status -s) ]]; then
    echo "No changes to commit."
    exit 0
fi

# Add, commit, and push
git add .
git commit -m "$COMMIT_MSG"
git push origin master

echo "Backup complete: $COMMIT_MSG"
