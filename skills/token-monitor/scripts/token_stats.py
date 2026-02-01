#!/usr/bin/env python3
"""
Token Usage Statistics Generator

Usage:
    python token_stats.py                    # Full statistics
    python token_stats.py --group-by date     # Group by date
    python token_stats.py --group-by model    # Group by model
    python token_stats.py --recent 10         # Last N conversations
    python token_stats.py --format json       # JSON output
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

def load_records(file_path):
    """Load token usage records from JSONL file."""
    if not file_path.exists():
        print("No token usage data found yet. Start a conversation first.")
        return []

    records = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records

def format_number(num):
    """Format large numbers with commas."""
    return f"{num:,}"

def format_currency(amount):
    """Format currency amount."""
    return f"${float(amount):.6f}"

def print_full_stats(records):
    """Print full statistics."""
    if not records:
        return

    total_calls = len(records)
    total_tokens = sum(r.get('totalTokens', 0) for r in records)
    total_cost = sum(r.get('cost', {}).get('total', 0) for r in records)
    avg_tokens = total_tokens / total_calls if total_calls > 0 else 0

    # Get date range
    dates = sorted(set(r.get('date', '') for r in records))
    date_range = f"{dates[0]} to {dates[-1]}" if len(dates) > 1 else dates[0]

    print("=" * 60)
    print("📊 TOKEN USAGE STATISTICS")
    print("=" * 60)
    print(f"Period:         {date_range}")
    print(f"Total Calls:     {format_number(total_calls)}")
    print(f"Total Tokens:    {format_number(total_tokens)}")
    print(f"Total Cost:      {format_currency(total_cost)}")
    print(f"Avg Tokens/Call: {avg_tokens:.2f}")
    avg_cost = total_cost / total_calls
    print(f"Avg Cost/Call:   ${avg_cost:.6f}")
    print()

    # Model breakdown
    print("-" * 60)
    print("BY MODEL")
    print("-" * 60)

    model_stats = {}
    for r in records:
        model = r.get('model', 'unknown')
        if model not in model_stats:
            model_stats[model] = {'calls': 0, 'tokens': 0, 'cost': 0}
        model_stats[model]['calls'] += 1
        model_stats[model]['tokens'] += r.get('totalTokens', 0)
        model_stats[model]['cost'] += r.get('cost', {}).get('total', 0)

    for model, stats in sorted(model_stats.items()):
        avg_t = stats['tokens'] / stats['calls']
        print(f"  {model:20} Calls: {stats['calls']:4}  Tokens: {format_number(stats['tokens']):10}  Cost: {format_currency(stats['cost']):10}  Avg/Call: {avg_t:8.1f}")

    print()

    # Top 10 conversations by token usage
    print("-" * 60)
    print("TOP 10 CONVERSATIONS (by tokens)")
    print("-" * 60)

    sorted_records = sorted(records, key=lambda r: r.get('totalTokens', 0), reverse=True)[:10]
    print(f"  {'Date':<12} {'Model':<15} {'Tokens':>12} {'Cost':>12}")
    print(f"  {'-'*12} {'-'*15} {'-'*12} {'-'*12}")
    for r in sorted_records:
        date = r.get('date', 'unknown')
        model = r.get('model', 'unknown')[:15]
        tokens = r.get('totalTokens', 0)
        cost = r.get('cost', {}).get('total', 0)
        print(f"  {date:<12} {model:<15} {format_number(tokens):>12} {format_currency(cost):>12}")

def print_grouped_stats(records, group_by):
    """Print statistics grouped by date or model."""
    if not records:
        return

    grouped = {}
    for r in records:
        key = r.get(group_by, 'unknown')
        if key not in grouped:
            grouped[key] = {'calls': 0, 'tokens': 0, 'cost': 0}
        grouped[key]['calls'] += 1
        grouped[key]['tokens'] += r.get('totalTokens', 0)
        grouped[key]['cost'] += r.get('cost', {}).get('total', 0)

    print("=" * 60)
    print(f"📊 TOKEN USAGE BY {group_by.upper()}")
    print("=" * 60)

    if group_by == 'date':
        for date in sorted(grouped.keys()):
            stats = grouped[date]
            avg_t = stats['tokens'] / stats['calls']
            print(f"  {date}:  Calls: {stats['calls']:4}  Tokens: {format_number(stats['tokens']):10}  Cost: {format_currency(stats['cost']):10}  Avg/Call: {avg_t:8.1f}")
    elif group_by == 'model':
        for model, stats in sorted(grouped.items()):
            avg_t = stats['tokens'] / stats['calls']
            print(f"  {model}:  Calls: {stats['calls']:4}  Tokens: {format_number(stats['tokens']):10}  Cost: {format_currency(stats['cost']):10}  Avg/Call: {avg_t:8.1f}")

    print()

    total = sum(g['calls'] for g in grouped.values())
    total_tokens = sum(g['tokens'] for g in grouped.values())
    total_cost = sum(g['cost'] for g in grouped.values())

    print("-" * 60)
    print(f"TOTAL: Calls: {format_number(total)}  Tokens: {format_number(total_tokens)}  Cost: {format_currency(total_cost)}")

def print_recent(records, count):
    """Print recent N conversations."""
    if not records:
        return

    recent = records[-count:] if len(records) >= count else records

    print("=" * 60)
    print(f"📊 RECENT {len(recent)} CONVERSATIONS")
    print("=" * 60)

    for r in reversed(recent):
        timestamp = r.get('timestamp', 'unknown')[:19]  # Remove milliseconds
        date = r.get('date', 'unknown')
        model = r.get('model', 'unknown')
        tokens = r.get('totalTokens', 0)
        cost = r.get('cost', {}).get('total', 0)
        print(f"  {timestamp}")
        print(f"    Model:    {model}")
        print(f"    Tokens:   {format_number(tokens)} (in:{r.get('input',0)} out:{r.get('output',0)} cache:{r.get('cacheRead',0)})")
        print(f"    Cost:     {format_currency(cost)}")
        print()

def print_json_stats(records):
    """Print statistics in JSON format."""
    if not records:
        print("{}")
        return

    total_calls = len(records)
    total_tokens = sum(r.get('totalTokens', 0) for r in records)
    total_cost = sum(r.get('cost', {}).get('total', 0) for r in records)

    stats = {
        'summary': {
            'totalCalls': total_calls,
            'totalTokens': total_tokens,
            'totalCost': total_cost,
            'avgTokensPerCall': total_tokens / total_calls if total_calls > 0 else 0,
            'dateRange': {
                'start': min(r.get('date', '') for r in records),
                'end': max(r.get('date', '') for r in records)
            }
        },
        'byModel': {},
        'byDate': {}
    }

    # Group by model
    for r in records:
        model = r.get('model', 'unknown')
        if model not in stats['byModel']:
            stats['byModel'][model] = {'calls': 0, 'tokens': 0, 'cost': 0}
        stats['byModel'][model]['calls'] += 1
        stats['byModel'][model]['tokens'] += r.get('totalTokens', 0)
        stats['byModel'][model]['cost'] += r.get('cost', {}).get('total', 0)

    # Group by date
    for r in records:
        date = r.get('date', 'unknown')
        if date not in stats['byDate']:
            stats['byDate'][date] = {'calls': 0, 'tokens': 0, 'cost': 0}
        stats['byDate'][date]['calls'] += 1
        stats['byDate'][date]['tokens'] += r.get('totalTokens', 0)
        stats['byDate'][date]['cost'] += r.get('cost', {}).get('total', 0)

    print(json.dumps(stats, indent=2))

def main():
    parser = argparse.ArgumentParser(description='Token usage statistics')
    parser.add_argument('--group-by', choices=['date', 'model'], help='Group statistics by date or model')
    parser.add_argument('--recent', type=int, help='Show recent N conversations')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')

    args = parser.parse_args()

    # Determine file path
    workspace = Path('/root/.openclaw/workspace')
    memory_dir = workspace / 'memory'
    token_file = memory_dir / 'token-usage.jsonl'

    records = load_records(token_file)

    if not records:
        sys.exit(0)

    if args.format == 'json':
        print_json_stats(records)
    elif args.group_by:
        print_grouped_stats(records, args.group_by)
    elif args.recent:
        print_recent(records, args.recent)
    else:
        print_full_stats(records)

if __name__ == '__main__':
    main()
