---
name: token-stats-cron
description: Cron job to periodically extract token usage from session files.
metadata: {"openclaw":{"emoji":"⏰","always":true}}
---

# Token Stats Cron

Periodically extracts token usage from session files and appends to `token-usage.jsonl`.

## How It Works

This cron job runs periodically to:
1. Read the current session file
2. Find the last assistant message
3. Extract token usage data
4. Check if already logged (via timestamp)
5. Append to `token-usage.jsonl` if new

## Usage

Run manually to extract token usage:
```bash
token-stats-cron extract
```

The cron configuration will run this automatically.

## Data File

`<workspace>/memory/token-usage.jsonl`

Same format as token-monitor hook.

## Frequency

Recommended: Every 10 minutes

## Notes

- Fallback solution while OpenClaw implements `message:sent` hooks
- Safe to run frequently - checks for new messages and skips duplicates
