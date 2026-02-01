---
name: token-stats
description: View token usage statistics and cost analysis for clawdbot conversations.
homepage: https://docs.openclaw.ai/skills#token-stats
metadata: {"openclaw":{"emoji":"📊","always":true}}
---

# Token Stats

View and analyze token usage statistics for all conversations with clawdbot.

## Quick Start

The `token-stats` command is available at `~/.local/bin/token-stats`:

```bash
# Full statistics
token-stats

# Recent N conversations
token-stats --recent 5

# Grouped by date
token-stats --group-by date

# Grouped by model
token-stats --group-by model

# JSON output
token-stats --format json
```

## Data Source

Statistics are generated from `<workspace>/memory/token-usage.jsonl`, which is automatically maintained by the `token-monitor` skill and `token-logger` hook.

Each conversation entry includes:
- Timestamp and date
- Provider and model used
- Input/output/cache token counts
- Cost breakdown (input/output/cache/total)

## Available Commands

### Full Statistics

Show comprehensive statistics including:

```
token-stats
```

Output:
- Period covered (date range)
- Total API calls
- Total tokens consumed
- Total cost
- Average tokens per call
- Average cost per call
- Breakdown by model
- Top 10 conversations by token usage

### Recent Conversations

Show the last N conversations:

```bash
token-stats --recent 10
```

Output includes timestamp, model, token counts, and cost.

### Grouped Statistics

View usage grouped by date or model:

```bash
# By date
token-stats --group-by date

# By model
token-stats --group-by model
```

### JSON Output

Get statistics in JSON format for automation:

```bash
token-stats --format json
```

Output structure:
```json
{
  "summary": {
    "totalCalls": 71,
    "totalTokens": 2252566,
    "totalCost": 0.37838,
    "avgTokensPerCall": 31726.28,
    "dateRange": {
      "start": "2026-02-01",
      "end": "2026-02-01"
    }
  },
  "byModel": { ... },
  "byDate": { ... }
}
```

## Script Location

The `token-stats` wrapper script is located at:
```
<workspace>/skills/token-stats/scripts/token-stats-wrapper.sh
```

It wraps the Python script at:
```
<workspace>/skills/token-monitor/scripts/token_stats.py
```

### Migration Notes

All scripts and data are within the workspace for easy migration:

```
<workspace>/
├── skills/
│   ├── token-monitor/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── token_stats.py    # Core statistics script
│   └── token-stats/
│       ├── SKILL.md
│       └── scripts/
│           └── token-stats-wrapper.sh  # Command wrapper
└── memory/
    ├── token-usage.jsonl          # Token usage data
    └── token-logger-tracker.json  # Tracker file
```

To migrate to a new environment, copy the entire `<workspace>` directory.

### Creating System Command

For convenience, you can create a system-wide command:

```bash
# Create symlink (optional, for easy access)
ln -s /root/.openclaw/workspace/skills/token-stats/scripts/token-stats-wrapper.sh /usr/local/bin/token-stats
chmod +x /usr/local/bin/token-stats
```

Then you can run `token-stats` from anywhere.

## Integration

- **Automatic logging**: The `token-logger` hook automatically logs each conversation
- **Manual viewing**: This skill provides the `token-stats` command for analysis
- **Data persistence**: All data is stored in `<workspace>/memory/token-usage.jsonl`

## Notes

- Requires Python 3
- Requires `token-usage.jsonl` to exist (created by `token-logger` hook)
- No API calls needed - all analysis is local
- Safe to run frequently - just reads local JSONL files
