---
name: token-monitor
description: Monitor and track token usage for every conversation. Automatically records token consumption, model, timestamp, and provides statistical summaries.
metadata: {"openclaw":{"emoji":"📊","always":true}}
---

# Token Monitor

Monitor and track token usage for every conversation with clawdbot.

## When to use

Use this skill when:
- User asks about token usage statistics
- User wants to know API call counts
- User asks for cost analysis
- After any conversation (auto-triggered to log usage)

## Data Storage

Token usage is automatically logged to:
`/root/.openclaw/workspace/memory/token-usage.jsonl`

Each line contains:
```json
{
  "timestamp": "2026-02-01T05:14:33.277Z",
  "date": "2026-02-01",
  "provider": "zai",
  "model": "glm-4.7",
  "input": 49,
  "output": 71,
  "cacheRead": 41738,
  "cacheWrite": 0,
  "totalTokens": 41858,
  "cost": {
    "input": 0.0000294,
    "output": 0.0001562,
    "cacheRead": 0.00459118,
    "cacheWrite": 0,
    "total": 0.0047767800000000004
  }
}
```

## Commands

### Log current session token usage
After each conversation, extract and log token usage from session file:

```bash
SESSION_FILE="/root/.openclaw/agents/main/sessions/0c718610-10a1-4f90-899c-fdcf2a2fc391.jsonl"
jq -r 'select(.message.role == "assistant") | {
  timestamp: .timestamp,
  date: (.timestamp | split("T")[0]),
  provider: .message.provider,
  model: .message.model,
  input: .message.usage.input,
  output: .message.usage.output,
  cacheRead: .message.usage.cacheRead,
  cacheWrite: .message.usage.cacheWrite,
  totalTokens: .message.usage.totalTokens,
  cost: .message.usage.cost
}' "$SESSION_FILE" >> /root/.openclaw/workspace/memory/token-usage.jsonl
```

### Show token usage statistics
```bash
python {baseDir}/scripts/token_stats.py
```

### Show statistics by date
```bash
python {baseDir}/scripts/token_stats.py --group-by date
```

### Show statistics by model
```bash
python {baseDir}/scripts/token_stats.py --group-by model
```

### Show recent N conversations
```bash
tail -n 20 /root/.openclaw/workspace/memory/token-usage.jsonl | jq -r '[.date, .model, .totalTokens, .cost.total] | @tsv' | column -t
```

## Manual Query Examples

### Count total API calls
```bash
wc -l /root/.openclaw/workspace/memory/token-usage.jsonl
```

### Total tokens used
```bash
jq -s '[.[] | .totalTokens] | add' /root/.openclaw/workspace/memory/token-usage.jsonl
```

### Total cost
```bash
jq -s '[.[] | .cost.total] | add' /root/.openclaw/workspace/memory/token-usage.jsonl
```

### Average tokens per conversation
```bash
TOTAL=$(jq -s '[.[] | .totalTokens] | add' /root/.openclaw/workspace/memory/token-usage.jsonl)
COUNT=$(wc -l < /root/.openclaw/workspace/memory/token-usage.jsonl)
echo "scale=2; $TOTAL / $COUNT" | bc
```

### Usage by model
```bash
jq -s 'group_by(.model) | map({model: .[0].model, calls: length, totalTokens: [.[] | .totalTokens] | add, avgTokens: ([.[] | .totalTokens] | add / length)})' /root/.openclaw/workspace/memory/token-usage.jsonl
```

### Usage by date
```bash
jq -s 'group_by(.date) | map({date: .[0].date, calls: length, totalTokens: [.[] | .totalTokens] | add, totalCost: [.[] | .cost.total] | add})' /root/.openclaw/workspace/memory/token-usage.jsonl
```

## Notes

- This skill should be auto-invoked after each conversation to log usage
- Use the `{baseDir}` placeholder which will be replaced with the skill directory path
- The token-usage.jsonl file is append-only, never deleted automatically
- Date format is ISO 8601 (YYYY-MM-DD)
