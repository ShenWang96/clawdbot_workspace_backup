#!/usr/bin/env python3
"""
Token Stats Reporter - 增强版
输出详细的 token 使用统计结果
"""

import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

WORKSPACE = Path("/root/.openclaw/workspace")
LOG_FILE = WORKSPACE / "memory" / "token-usage.jsonl"


def load_records():
    """加载 token 使用记录"""
    if not LOG_FILE.exists():
        return []
    
    records = []
    with open(LOG_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def format_number(num):
    """格式化数字"""
    return f"{num:,}"


def format_currency(amount):
    """格式化货币"""
    if amount == 0:
        return "$0.000000"
    return f"${float(amount):.6f}"


def format_percent(value, total):
    """格式化百分比"""
    if total == 0:
        return "0.0%"
    return f"{value/total*100:.1f}%"


def print_summary_stats(records):
    """打印汇总统计"""
    total_calls = len(records)
    total_tokens = sum(r.get('totalTokens', 0) for r in records)
    total_input = sum(r.get('input', 0) for r in records)
    total_output = sum(r.get('output', 0) for r in records)
    total_cache_read = sum(r.get('cacheRead', 0) for r in records)
    total_cost = sum(r.get('cost', {}).get('total', 0) for r in records)
    
    avg_tokens = total_tokens / total_calls if total_calls > 0 else 0
    avg_cost = total_cost / total_calls if total_calls > 0 else 0
    
    # 输入输出比例
    io_ratio = total_input / total_output if total_output > 0 else 0
    
    # 日期范围
    dates = sorted(set(r.get('date', '') for r in records if r.get('date')))
    date_range = f"{dates[0]} 至 {dates[-1]}" if len(dates) > 1 else (dates[0] if dates else "N/A")
    
    print("=" * 70)
    print("📊 TOKEN 使用统计汇总")
    print("=" * 70)
    print(f"统计周期:      {date_range}")
    print(f"总调用次数:    {format_number(total_calls)}")
    print(f"总 Token 数:   {format_number(total_tokens)}")
    print(f"  └─ 输入:     {format_number(total_input)} ({format_percent(total_input, total_tokens)})")
    print(f"  └─ 输出:     {format_number(total_output)} ({format_percent(total_output, total_tokens)})")
    print(f"  └─ 缓存读取: {format_number(total_cache_read)} ({format_percent(total_cache_read, total_tokens)})")
    print(f"输入/输出比:   {io_ratio:.2f}:1")
    print(f"总成本:        {format_currency(total_cost)}")
    print(f"平均 Tokens/次: {format_number(int(avg_tokens))}")
    print(f"平均成本/次:   {format_currency(avg_cost)}")
    print()


def print_daily_trend(records):
    """打印每日趋势"""
    print("-" * 70)
    print("📅 每日使用趋势")
    print("-" * 70)
    
    by_date = defaultdict(lambda: {'calls': 0, 'tokens': 0, 'cost': 0})
    for r in records:
        date = r.get('date', 'unknown')
        by_date[date]['calls'] += 1
        by_date[date]['tokens'] += r.get('totalTokens', 0)
        by_date[date]['cost'] += r.get('cost', {}).get('total', 0)
    
    print(f"  {'日期':<12} {'调用':>8} {'Tokens':>14} {'成本':>14} {'占比':>8}")
    print(f"  {'-'*12} {'-'*8} {'-'*14} {'-'*14} {'-'*8}")
    
    total_tokens = sum(r.get('totalTokens', 0) for r in records)
    for date in sorted(by_date.keys()):
        stats = by_date[date]
        pct = stats['tokens'] / total_tokens * 100 if total_tokens > 0 else 0
        print(f"  {date:<12} {stats['calls']:>8} {format_number(stats['tokens']):>14} {format_currency(stats['cost']):>14} {pct:>7.1f}%")
    print()


def print_model_stats(records):
    """打印按模型统计"""
    print("-" * 70)
    print("🤖 按模型统计")
    print("-" * 70)
    
    by_model = defaultdict(lambda: {
        'calls': 0, 'tokens': 0, 'input': 0, 'output': 0, 
        'cache_read': 0, 'cost': 0
    })
    
    for r in records:
        model = r.get('model', 'unknown')
        by_model[model]['calls'] += 1
        by_model[model]['tokens'] += r.get('totalTokens', 0)
        by_model[model]['input'] += r.get('input', 0)
        by_model[model]['output'] += r.get('output', 0)
        by_model[model]['cache_read'] += r.get('cacheRead', 0)
        by_model[model]['cost'] += r.get('cost', {}).get('total', 0)
    
    print(f"  {'模型':<25} {'调用':>6} {'Tokens':>12} {'输入':>10} {'输出':>10} {'缓存':>10} {'成本':>12}")
    print(f"  {'-'*25} {'-'*6} {'-'*12} {'-'*10} {'-'*10} {'-'*10} {'-'*12}")
    
    for model in sorted(by_model.keys()):
        s = by_model[model]
        model_short = model[:25] if len(model) <= 25 else model[:22] + "..."
        print(f"  {model_short:<25} {s['calls']:>6} {format_number(s['tokens']):>12} "
              f"{format_number(s['input']):>10} {format_number(s['output']):>10} "
              f"{format_number(s['cache_read']):>10} {format_currency(s['cost']):>12}")
    print()


def print_cost_analysis(records):
    """打印成本分析"""
    print("-" * 70)
    print("💰 成本分析")
    print("-" * 70)
    
    total_cost = sum(r.get('cost', {}).get('total', 0) for r in records)
    if total_cost == 0:
        print("  暂无成本数据（可能使用的是免费模型）")
        print()
        return
    
    by_model = defaultdict(lambda: {'cost': 0, 'tokens': 0, 'calls': 0})
    for r in records:
        model = r.get('model', 'unknown')
        by_model[model]['cost'] += r.get('cost', {}).get('total', 0)
        by_model[model]['tokens'] += r.get('totalTokens', 0)
        by_model[model]['calls'] += 1
    
    print(f"  {'模型':<25} {'成本':>14} {'占比':>8} {'$/1K Tokens':>12} {'$/调用':>10}")
    print(f"  {'-'*25} {'-'*14} {'-'*8} {'-'*12} {'-'*10}")
    
    for model in sorted(by_model.keys(), key=lambda x: by_model[x]['cost'], reverse=True):
        s = by_model[model]
        pct = s['cost'] / total_cost * 100 if total_cost > 0 else 0
        cost_per_1k = s['cost'] / s['tokens'] * 1000 if s['tokens'] > 0 else 0
        cost_per_call = s['cost'] / s['calls'] if s['calls'] > 0 else 0
        model_short = model[:25] if len(model) <= 25 else model[:22] + "..."
        print(f"  {model_short:<25} {format_currency(s['cost']):>14} {pct:>7.1f}% "
              f"${cost_per_1k:>10.6f} ${cost_per_call:>8.6f}")
    
    print(f"  {'-'*25} {'-'*14} {'-'*8} {'-'*12} {'-'*10}")
    print(f"  {'总计':<25} {format_currency(total_cost):>14} {'100.0%':>8}")
    print()


def print_top_conversations(records, n=10):
    """打印 TOP N 对话"""
    print("-" * 70)
    print(f"🏆 TOP {n} 对话（按 Token 数）")
    print("-" * 70)
    
    sorted_records = sorted(records, key=lambda r: r.get('totalTokens', 0), reverse=True)[:n]
    
    print(f"  {'排名':<4} {'日期':<12} {'模型':<20} {'Tokens':>12} {'成本':>12}")
    print(f"  {'-'*4} {'-'*12} {'-'*20} {'-'*12} {'-'*12}")
    
    for i, r in enumerate(sorted_records, 1):
        date = r.get('date', 'unknown')
        model = r.get('model', 'unknown')[:20]
        tokens = r.get('totalTokens', 0)
        cost = r.get('cost', {}).get('total', 0)
        print(f"  {i:<4} {date:<12} {model:<20} {format_number(tokens):>12} {format_currency(cost):>12}")
    print()


def print_recent_conversations(records, count):
    """打印最近 N 次调用"""
    print("=" * 70)
    print(f"📋 最近 {count} 次调用详情")
    print("=" * 70)
    
    recent = records[-count:] if len(records) >= count else records
    
    for r in reversed(recent):
        timestamp = r.get('timestamp', 'unknown')[:19] if len(r.get('timestamp', '')) > 19 else r.get('timestamp', 'unknown')
        date = r.get('date', 'unknown')
        model = r.get('model', 'unknown')
        provider = r.get('provider', 'unknown')
        
        tokens = r.get('totalTokens', 0)
        input_t = r.get('input', 0)
        output_t = r.get('output', 0)
        cache_t = r.get('cacheRead', 0)
        cost = r.get('cost', {}).get('total', 0)
        
        print(f"  🕐 {timestamp}")
        print(f"     提供商: {provider} | 模型: {model}")
        print(f"     Tokens: {format_number(tokens)} (输入:{format_number(input_t)} 输出:{format_number(output_t)} 缓存:{format_number(cache_t)})")
        print(f"     成本: {format_currency(cost)}")
        print()


def print_full_stats(records):
    """打印完整统计信息"""
    print_summary_stats(records)
    print_daily_trend(records)
    print_model_stats(records)
    print_cost_analysis(records)
    print_top_conversations(records, 10)


def print_grouped_stats(records, group_by):
    """按指定字段分组统计"""
    if not records:
        print("暂无数据")
        return

    grouped = defaultdict(lambda: {'calls': 0, 'tokens': 0, 'cost': 0, 'input': 0, 'output': 0})
    
    for r in records:
        key = r.get(group_by, 'unknown')
        grouped[key]['calls'] += 1
        grouped[key]['tokens'] += r.get('totalTokens', 0)
        grouped[key]['cost'] += r.get('cost', {}).get('total', 0)
        grouped[key]['input'] += r.get('input', 0)
        grouped[key]['output'] += r.get('output', 0)

    print("=" * 70)
    print(f"📊 按 {group_by.upper()} 统计")
    print("=" * 70)
    print(f"  {'分组':<20} {'调用':>8} {'Tokens':>14} {'输入':>10} {'输出':>10} {'成本':>14}")
    print(f"  {'-'*20} {'-'*8} {'-'*14} {'-'*10} {'-'*10} {'-'*14}")

    for key in sorted(grouped.keys()):
        s = grouped[key]
        key_short = key[:20] if len(key) <= 20 else key[:17] + "..."
        print(f"  {key_short:<20} {s['calls']:>8} {format_number(s['tokens']):>14} "
              f"{format_number(s['input']):>10} {format_number(s['output']):>10} {format_currency(s['cost']):>14}")

    print()
    total = sum(g['calls'] for g in grouped.values())
    total_tokens = sum(g['tokens'] for g in grouped.values())
    total_cost = sum(g['cost'] for g in grouped.values())

    print("-" * 70)
    print(f"  {'总计':<20} {total:>8} {format_number(total_tokens):>14} {'':>10} {'':>10} {format_currency(total_cost):>14}")


def print_json_stats(records):
    """以 JSON 格式输出统计"""
    if not records:
        print("{}")
        return

    total_calls = len(records)
    total_tokens = sum(r.get('totalTokens', 0) for r in records)
    total_cost = sum(r.get('cost', {}).get('total', 0) for r in records)
    total_input = sum(r.get('input', 0) for r in records)
    total_output = sum(r.get('output', 0) for r in records)
    total_cache = sum(r.get('cacheRead', 0) for r in records)

    stats = {
        'summary': {
            'totalCalls': total_calls,
            'totalTokens': total_tokens,
            'totalInput': total_input,
            'totalOutput': total_output,
            'totalCacheRead': total_cache,
            'totalCost': total_cost,
            'avgTokensPerCall': total_tokens / total_calls if total_calls > 0 else 0,
            'avgCostPerCall': total_cost / total_calls if total_calls > 0 else 0,
            'inputOutputRatio': total_input / total_output if total_output > 0 else 0,
            'dateRange': {
                'start': min((r.get('date', '') for r in records), default=''),
                'end': max((r.get('date', '') for r in records), default='')
            }
        },
        'byModel': {},
        'byDate': {}
    }

    # 按模型分组
    for r in records:
        model = r.get('model', 'unknown')
        if model not in stats['byModel']:
            stats['byModel'][model] = {'calls': 0, 'tokens': 0, 'input': 0, 'output': 0, 'cacheRead': 0, 'cost': 0}
        stats['byModel'][model]['calls'] += 1
        stats['byModel'][model]['tokens'] += r.get('totalTokens', 0)
        stats['byModel'][model]['input'] += r.get('input', 0)
        stats['byModel'][model]['output'] += r.get('output', 0)
        stats['byModel'][model]['cacheRead'] += r.get('cacheRead', 0)
        stats['byModel'][model]['cost'] += r.get('cost', {}).get('total', 0)

    # 按日期分组
    for r in records:
        date = r.get('date', 'unknown')
        if date not in stats['byDate']:
            stats['byDate'][date] = {'calls': 0, 'tokens': 0, 'input': 0, 'output': 0, 'cost': 0}
        stats['byDate'][date]['calls'] += 1
        stats['byDate'][date]['tokens'] += r.get('totalTokens', 0)
        stats['byDate'][date]['input'] += r.get('input', 0)
        stats['byDate'][date]['output'] += r.get('output', 0)
        stats['byDate'][date]['cost'] += r.get('cost', {}).get('total', 0)

    print(json.dumps(stats, indent=2))


def main():
    parser = argparse.ArgumentParser(description='Token 使用统计 - 增强版')
    parser.add_argument('--group-by', choices=['date', 'model'], help='按日期或模型分组')
    parser.add_argument('--recent', type=int, help='显示最近 N 次调用')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='输出格式')
    parser.add_argument('--simple', action='store_true', help='仅显示简化统计')

    args = parser.parse_args()

    records = load_records()

    if not records:
        print("暂无 token 使用数据。请先运行扫描。")
        return 0

    if args.format == 'json':
        print_json_stats(records)
    elif args.group_by:
        print_grouped_stats(records, args.group_by)
    elif args.recent:
        print_recent_conversations(records, args.recent)
    elif args.simple:
        print_summary_stats(records)
    else:
        print_full_stats(records)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
