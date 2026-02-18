# SKILL.md - Read File Command

## Overview
This skill provides a `/read_file` command to safely read markdown files from the workspace `docs` and `reports` directories.

## Security Features
- **Path restriction**: Only allows access to `/root/.openclaw/workspace/docs` and `/root/.openclaw/workspace/reports`
- **File type validation**: Only reads `.md` files
- **Size limit**: Maximum 50KB per file to prevent memory issues
- **Path traversal protection**: Prevents directory traversal attacks

## Command Usage
```
/read_file <filename>
```

## Examples
```
/read_file docs/AGENT-COMMUNITY-NEWS.md
/read_file reports/agent-community-news/latest.md
```

## Safety Rules
1. Always verify the requested path is within allowed directories
2. Check file extension is `.md` only
3. Validate file size before reading
4. Use absolute paths to prevent ambiguity
5. Log all file access attempts for audit