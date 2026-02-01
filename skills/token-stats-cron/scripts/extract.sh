#!/bin/bash
#
# Token Stats Cron Job
# Periodically extracts token usage from session files
#

WORKSPACE="/root/.openclaw/workspace"
MEMORY_DIR="$WORKSPACE/memory"
EXTRACTOR_SCRIPT="$WORKSPACE/skills/token-stats-cron/scripts/extract.py"

case "${1:-extract}" in
    extract)
        python3 "$EXTRACTOR_SCRIPT" extract
        ;;
    status)
        python3 "$EXTRACTOR_SCRIPT" status
        ;;
    *)
        echo "Usage: $0 {extract|status}"
        exit 1
        ;;
esac
