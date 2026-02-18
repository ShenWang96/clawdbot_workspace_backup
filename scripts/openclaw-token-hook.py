#!/usr/bin/env python3
"""
OpenClaw Token Hook - 实时Token监控集成
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenClawTokenHook:
    """OpenClaw Token Hook处理器"""
    
    def __init__(self, hook_config: Dict):
        self.hook_config = hook_config
        self.enabled = hook_config.get('enabled', True)
        self.prometheus_enabled = hook_config.get('prometheus', {}).get('enabled', False)
        self.prometheus_url = hook_config.get('prometheus', {}).get('url', 'http://localhost:9090')
        
        if not self.enabled:
            logger.info("Token Hook is disabled")
            return
        
        # 初始化Prometheus客户端（如果启用）
        if self.prometheus_enabled:
            try:
                from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
                self.prometheus_client = self._init_prometheus_client()
                logger.info("Prometheus metrics enabled")
            except ImportError:
                logger.warning("Prometheus client not available, metrics disabled")
                self.prometheus_enabled = False
        else:
            logger.info("Prometheus metrics disabled")
        
        # 确保日志目录存在
        self.log_dir = Path('/var/log/clawdbot')
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("OpenClaw Token Hook initialized")
    
    def _init_prometheus_client(self):
        """初始化Prometheus客户端"""
        from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
        
        registry = CollectorRegistry()
        
        tokens_total = Counter(
            'clawdbot_tokens_total',
            'Total tokens consumed',
            ['provider', 'model', 'channel', 'status'],
            registry=registry
        )
        
        tokens_input = Counter(
            'clawdbot_tokens_input_total',
            'Input tokens consumed',
            ['provider', 'model', 'channel'],
            registry=registry
        )
        
        tokens_output = Counter(
            'clawdbot_tokens_output_total',
            'Output tokens consumed',
            ['provider', 'model', 'channel'],
            registry=registry
        )
        
        api_calls = Counter(
            'clawdbot_api_calls_total',
            'Total API calls',
            ['provider', 'model', 'channel', 'status'],
            registry=registry
        )
        
        api_duration = Histogram(
            'clawdbot_api_call_duration_seconds',
            'API call duration',
            ['provider', 'model'],
            registry=registry
        )
        
        cost_total = Counter(
            'clawdbot_cost_total_usd',
            'Total cost in USD',
            ['provider', 'model', 'channel'],
            registry=registry
        )
        
        return {
            'registry': registry,
            'tokens_total': tokens_total,
            'tokens_input': tokens_input,
            'tokens_output': tokens_output,
            'api_calls': api_calls,
            'api_duration': api_duration,
            'cost_total': cost_total
        }
    
    def process_message_completion(self, message_data: Dict, usage_data: Optional[Dict] = None):
        """处理消息完成事件"""
        if not self.enabled:
            return
        
        try:
            # 提取基本信息
            provider = message_data.get('provider', 'unknown')
            model = message_data.get('model', 'unknown')
            channel = message_data.get('channel', 'unknown')
            session_id = message_data.get('session_id', 'unknown')
            
            # 提取token使用数据
            if usage_data:
                input_tokens = usage_data.get('input', 0) or 0
                output_tokens = usage_data.get('output', 0) or 0
                cache_read = usage_data.get('cacheRead', 0) or 0
                cache_write = usage_data.get('cacheWrite', 0) or 0
                total_tokens = usage_data.get('totalTokens', 0) or (input_tokens + output_tokens + cache_read)
                cost_data = usage_data.get('cost', {})
                
                # 记录到Prometheus
                if self.prometheus_enabled:
                    self._record_to_prometheus(
                        provider=provider,
                        model=model,
                        channel=channel,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=total_tokens,
                        cost_data=cost_data,
                        status='success',
                        session_id=session_id
                    )
                
                # 记录到本地文件
                self._record_to_log(
                    provider=provider,
                    model=model,
                    channel=channel,
                    session_id=session_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    cost_data=cost_data,
                    status='success'
                )
            
            logger.info(f"Processed token metrics for {provider}/{model} in {channel}")
            
        except Exception as e:
            logger.error(f"Error processing token metrics: {e}")
    
    def _record_to_prometheus(self, **kwargs):
        """记录到Prometheus指标"""
        try:
            data = {
                'provider': kwargs.get('provider', 'unknown'),
                'model': kwargs.get('model', 'unknown'),
                'channel': kwargs.get('channel', 'unknown'),
                'input_tokens': kwargs.get('input_tokens', 0),
                'output_tokens': kwargs.get('output_tokens', 0),
                'total_tokens': kwargs.get('total_tokens', 0),
                'cost_data': kwargs.get('cost_data', {}),
                'status': kwargs.get('status', 'success')
            }
            
            client = self.prometheus_client
            
            # 记录token指标
            client['tokens_total'].labels(
                provider=data['provider'],
                model=data['model'],
                channel=data['channel'],
                status=data['status']
            ).inc(data['total_tokens'])
            
            client['tokens_input'].labels(
                provider=data['provider'],
                model=data['model'],
                channel=data['channel']
            ).inc(data['input_tokens'])
            
            client['tokens_output'].labels(
                provider=data['provider'],
                model=data['model'],
                channel=data['channel']
            ).inc(data['output_tokens'])
            
            # 记录API调用
            client['api_calls'].labels(
                provider=data['provider'],
                model=data['model'],
                channel=data['channel'],
                status=data['status']
            ).inc(1)
            
            # 记录成本
            if data['cost_data']:
                total_cost = data['cost_data'].get('total', 0) or 0
                if total_cost > 0:
                    client['cost_total'].labels(
                        provider=data['provider'],
                        model=data['model'],
                        channel=data['channel']
                    ).inc(total_cost)
            
            logger.debug(f"Recorded to Prometheus: {data['provider']}/{data['model']} - {data['total_tokens']} tokens")
            
        except Exception as e:
            logger.error(f"Error recording to Prometheus: {e}")
    
    def _record_to_log(self, **kwargs):
        """记录到本地日志文件"""
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'provider': kwargs.get('provider', 'unknown'),
                'model': kwargs.get('model', 'unknown'),
                'channel': kwargs.get('channel', 'unknown'),
                'session_id': kwargs.get('session_id', 'unknown'),
                'input_tokens': kwargs.get('input_tokens', 0),
                'output_tokens': kwargs.get('output_tokens', 0),
                'total_tokens': kwargs.get('total_tokens', 0),
                'cost_data': kwargs.get('cost_data', {}),
                'status': kwargs.get('status', 'success')
            }
            
            log_file = self.log_dir / 'token-metrics.log'
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
            
        except Exception as e:
            logger.error(f"Error writing to log file: {e}")
    
    def get_metrics_text(self) -> str:
        """获取Prometheus格式的指标文本"""
        if not self.prometheus_enabled:
            return ""
        
        try:
            from prometheus_client import generate_latest
            return generate_latest(self.prometheus_client['registry']).decode('utf-8')
        except Exception as e:
            logger.error(f"Error generating metrics text: {e}")
            return ""


def load_config() -> Dict:
    """加载配置文件"""
    config_path = Path('/root/.openclaw/workspace/config/token-hook-config.json')
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    # 返回默认配置
    return {
        'enabled': True,
        'prometheus': {
            'enabled': True,
            'url': 'http://localhost:9090'
        }
    }


def main():
    """主函数"""
    try:
        # 加载配置
        config = load_config()
        
        # 创建Hook实例
        hook = OpenClawTokenHook(config)
        
        # 测试数据
        test_message = {
            'provider': 'zai',
            'model': 'glm-4.7',
            'channel': 'telegram',
            'session_id': 'test-session-123'
        }
        
        test_usage = {
            'input': 1500,
            'output': 750,
            'cacheRead': 0,
            'cacheWrite': 0,
            'totalTokens': 2250,
            'cost': {
                'input': 0.0015,
                'output': 0.0075,
                'total': 0.009
            }
        }
        
        # 处理测试数据
        hook.process_message_completion(test_message, test_usage)
        
        # 输出指标文本
        metrics_text = hook.get_metrics_text()
        if metrics_text:
            print("=== Prometheus Metrics ===")
            print(metrics_text)
        
        logger.info("Hook processing completed successfully")
        
    except Exception as e:
        logger.error(f"Hook processing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()