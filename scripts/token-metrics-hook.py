# Token 监控系统重构方案：基于 Hook 的优雅实现

## 🎯 用户需求分析

### 当前痛点
1. **性能问题**: Session日志体量巨大，定时扫描heavy
2. **实时性差**: 每小时一次，无法及时监控
3. **覆盖不全**: 只能处理某些channel的sessions
4. **可靠性低**: 依赖解析复杂的JSON日志文件

### 理想目标
- ✅ **实时监控**: 每次模型调用立即记录
- ✅ **统一上报**: 标准化的指标收集
- ✅ **轻量高效**: 无需解析大文件
- ✅ **完整覆盖**: 支持所有provider和channel
- ✅ **易于扩展**: 支持多种监控后端

## 🏗️ Hook 系统架构设计

### 1. OpenClaw Hook 架构分析

OpenClaw已经有hook机制，支持：
```json
{
  "hooks": {
    "internal": {
      "enabled": true,
      "entries": {
        "token-logger": {
          "enabled": true
        },
        "session-memory": {
          "enabled": true
        },
        "boot-md": {
          "enabled": true
        },
        "command-logger": {
          "enabled": true
        }
      }
    }
  }
}
```

### 2. 理想的 Hook 实现点

#### 2.1 消息级别 Hook
在每次消息处理完成后，立即记录token消耗：
```python
# 伪代码示例
def on_message_complete(message, usage_stats):
    token_metrics_collector.record(
        provider=message.provider,
        model=message.model,
        input_tokens=usage_stats.input,
        output_tokens=usage_stats.output,
        cache_read=usage_stats.cache_read,
        cache_write=usage_stats.cache_write,
        total_tokens=usage_stats.totalTokens,
        cost=usage_stats.cost,
        timestamp=message.timestamp,
        session_id=message.session_id
    )
```

#### 2.2 Provider级别 Hook
在API调用级别进行拦截：
```python
# 伪代码示例
def before_api_call(provider, model, request):
    start_time = time.time()
    return {"start_time": start_time, "request_id": generate_id()}

def after_api_call(provider, model, response, context):
    duration = time.time() - context["start_time"]
    token_metrics_collector.record_api_call(
        provider=provider,
        model=model,
        duration=duration,
        tokens=response.usage,
        success=response.ok
    )
```

## 📊 指标设计方案

### 1. Prometheus 指标结构

```python
# 定义指标
class TokenMetrics:
    # Counter 指标
    TOKEN_TOTAL = Counter(
        'clawdbot_tokens_total',
        'Total tokens consumed',
        ['provider', 'model', 'session_type', 'status']
    )
    
    # Histogram 指标
    TOKEN_DURATION = Histogram(
        'clawdbot_api_call_duration_seconds',
        'API call duration',
        ['provider', 'model']
    )
    
    # Gauge 指标
    TOKEN_RATE = Gauge(
        'clawdbot_tokens_per_second',
        'Current token consumption rate'
    )
    
    COST_TOTAL = Counter(
        'clawdbot_cost_total_usd',
        'Total cost in USD',
        ['provider', 'model']
    )
```

### 2. 指标维度

| 指标名称 | 标签 | 说明 |
|---------|------|------|
| `clawdbot_tokens_total` | `provider`, `model`, `session_type`, `status` | 总token消耗 |
| `clawdbot_api_call_duration` | `provider`, `model` | API调用时长 |
| `clawdbot_cost_total` | `provider`, `model` | 总成本 |
| `clawdbot_tokens_rate` | - | 实时token速率 |

### 3. 指标示例

```json
# 示例指标数据
{
  "clawdbot_tokens_total": {
    "value": 1543200,
    "labels": {
      "provider": "zai",
      "model": "glm-4.7", 
      "session_type": "telegram",
      "status": "success"
    }
  },
  "clawdbot_cost_total": {
    "value": 0.087,
    "labels": {
      "provider": "zai",
      "model": "glm-4.7"
    }
  }
}
```

## 🔧 具体实现方案

### 方案1: OpenClaw Internal Hook (推荐)

#### 1.1 创建 Token Metrics Hook
<tool_call>write
<arg_key>content</arg_key>
<arg_value>#!/usr/bin/env python3
"""
Token Metrics Hook for OpenClaw
实时收集和上报token消耗指标到Prometheus
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest

class TokenMetricsHook:
    """Token消耗指标收集Hook"""
    
    def __init__(self, registry=None):
        if registry is None:
            registry = CollectorRegistry()
            
        self.registry = registry
        
        # 定义指标
        self.tokens_total = Counter(
            'clawdbot_tokens_total',
            'Total tokens consumed by all models',
            ['provider', 'model', 'channel', 'status'],
            registry=self.registry
        )
        
        self.tokens_input = Counter(
            'clawdbot_tokens_input_total',
            'Input tokens consumed',
            ['provider', 'model', 'channel'],
            registry=self.registry
        )
        
        self.tokens_output = Counter(
            'clawdbot_tokens_output_total',
            'Output tokens consumed',
            ['provider', 'model', 'channel'],
            registry=self.registry
        )
        
        self.api_calls_total = Counter(
            'clawdbot_api_calls_total',
            'Total API calls made',
            ['provider', 'model', 'channel', 'status'],
            registry=self.registry
        )
        
        self.api_duration = Histogram(
            'clawdbot_api_call_duration_seconds',
            'Duration of API calls',
            ['provider', 'model'],
            registry=self.registry
        )
        
        self.cost_total = Counter(
            'clawdbot_cost_total_usd',
            'Total cost in USD',
            ['provider', 'model', 'channel'],
            registry=self.registry
        )
        
        self.registry.register(self)
    
    def record_token_usage(self, 
                          provider: str, 
                          model: str, 
                          channel: str,
                          input_tokens: int,
                          output_tokens: int,
                          cache_read: int = 0,
                          cache_write: int = 0,
                          total_tokens: int = 0,
                          cost: Optional[Dict] = None,
                          status: str = 'success',
                          duration: Optional[float] = None):
        """记录token使用情况"""
        
        # 确保total_tokens有值
        if total_tokens == 0:
            total_tokens = input_tokens + output_tokens + cache_read
        
        # 记录token指标
        self.tokens_total.labels(provider=provider, model=model, channel=channel, status=status).inc(total_tokens)
        self.tokens_input.labels(provider=provider, model=model, channel=channel).inc(input_tokens)
        self.tokens_output.labels(provider=provider, model=model, channel=channel).inc(output_tokens)
        
        # 记录API调用
        self.api_calls_total.labels(provider=provider, model=model, channel=channel, status=status).inc(1)
        
        # 记录成本
        if cost:
            total_cost = cost.get('total', 0)
            if total_cost > 0:
                self.cost_total.labels(provider=provider, model=model, channel=channel).inc(total_cost)
        
        # 记录duration
        if duration:
            self.api_duration.labels(provider=provider, model=model).observe(duration)
        
        # 记录到日志文件（可选）
        self._log_token_event(provider, model, channel, input_tokens, output_tokens, total_tokens, cost, status)
    
    def _log_token_event(self, 
                         provider: str, 
                         model: str, 
                         channel: str,
                         input_tokens: int,
                         output_tokens: int,
                         total_tokens: int,
                         cost: Optional[Dict],
                         status: str):
        """记录到本地日志文件"""
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'provider': provider,
            'model': model,
            'channel': channel,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens,
            'cost': cost or {},
            'status': status
        }
        
        log_file = Path('/tmp/clawdbot-token-events.log')
        
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"[TokenMetricsHook] Error writing to log file: {e}")
    
    def get_metrics_text(self) -> str:
        """获取Prometheus格式的指标文本"""
        return generate_latest(self.registry).decode('utf-8')
    
    def export_to_file(self, file_path: str):
        """导出指标到文件"""
        metrics_text = self.get_metrics_text()
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(metrics_text)


class TokenMetricsCollector:
    """全局Token指标收集器"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = TokenMetricsHook()
        return cls._instance
    
    @classmethod
    def record_token_usage(cls, **kwargs):
        """记录token使用情况的快捷方法"""
        return cls.get_instance().record_token_usage(**kwargs)


def create_token_hook():
    """创建Token Hook的工厂函数"""
    return TokenMetricsHook()


# 测试代码
if __name__ == "__main__":
    # 测试指标收集
    collector = TokenMetricsCollector.get_instance()
    
    # 模拟一些token使用
    collector.record_token_usage(
        provider="zai",
        model="glm-4.7", 
        channel="telegram",
        input_tokens=1000,
        output_tokens=500,
        total_tokens=1500,
        cost={"total": 0.0015},
        status="success",
        duration=1.5
    )
    
    collector.record_token_usage(
        provider="moonshot",
        model="kimi-k2.5",
        channel="feishu", 
        input_tokens=2000,
        output_tokens=800,
        total_tokens=2800,
        cost={"total": 0.0028},
        status="success",
        duration=2.1
    )
    
    # 输出指标
    print(collector.get_metrics_text())