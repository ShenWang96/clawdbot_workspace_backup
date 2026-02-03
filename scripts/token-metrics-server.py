#!/usr/bin/env python3
"""
Prometheus Exporter for Token Metrics
启动HTTP服务器暴露Token指标给Prometheus
"""

import argparse
import os
import signal
import sys
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# 导入我们的指标收集器
from token_metrics_hook import TokenMetricsCollector


class TokenMetricsHandler(BaseHTTPRequestHandler):
    """处理Prometheus指标请求的HTTP处理器"""
    
    def __init__(self, *args, **kwargs):
        self.collector = TokenMetricsCollector.get_instance()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/metrics':
            self._handle_metrics()
        elif self.path == '/health':
            self._handle_health()
        elif self.path == '/':
            self._handle_index()
        else:
            self._handle_404()
    
    def _handle_metrics(self):
        """处理/metrics端点"""
        try:
            metrics_text = self.collector.get_metrics_text()
            self._send_response(200, metrics_text, 'text/plain')
        except Exception as e:
            self._send_response(500, f"Error generating metrics: {str(e)}", 'text/plain')
    
    def _handle_health(self):
        """处理/health端点"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'version': '1.0.0'
        }
        self._send_response(200, json.dumps(health_status), 'application/json')
    
    def _handle_index(self):
        """处理根路径"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Clawdbot Token Metrics</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .metric { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .label { color: #666; font-size: 0.9em; }
            </style>
        </head>
        <body>
            <h1>🤖 Clawdbot Token Metrics</h1>
            <p><a href="/metrics">Prometheus Metrics</a></p>
            <p><a href="/health">Health Check</a></p>
            <h2>Recent Token Events</h2>
            <pre id="events"></pre>
            
            <script>
                async function loadEvents() {
                    try {
                        const response = await fetch('/recent-events');
                        const events = await response.text();
                        document.getElementById('events').textContent = events;
                    } catch (error) {
                        document.getElementById('events').textContent = 'Error loading events';
                    }
                    setTimeout(loadEvents, 5000); // 每5秒刷新
                }
                loadEvents();
            </script>
        </body>
        </html>
        """
        self._send_response(200, html_content, 'text/html')
    
    def _handle_404(self):
        """处理404错误"""
        self._send_response(404, "Not Found", 'text/plain')
    
    def _send_response(self, status_code, content, content_type):
        """发送响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def log_message(self, format, *args):
        """自定义日志消息"""
        print(f"[TokenMetricsServer] {format % args}")


class TokenMetricsServer:
    """Token Metrics HTTP服务器"""
    
    def __init__(self, host='0.0.0.0', port=9095):
        self.host = host
        self.port = port
        self.server = None
        self.collector = TokenMetricsCollector.get_instance()
        self.running = False
        
        # 启动日志读取线程
        self._start_log_monitor()
    
    def _start_log_monitor(self):
        """启动日志监控线程"""
        def monitor_log():
            log_file = Path('/tmp/clawdbot-token-events.log')
            if not log_file.exists():
                return
                
            with open(log_file, 'r', encoding='utf-8') as f:
                # 移动到文件末尾
                f.seek(0, 2)
                
                while self.running:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    
                    try:
                        event = json.loads(line.strip())
                        print(f"[TokenMetricsServer] New event: {event.get('provider')}/{event.get('model')} - {event.get('total_tokens')} tokens")
                    except json.JSONDecodeError:
                        continue
        
        thread = threading.Thread(target=monitor_log, daemon=True)
        thread.start()
    
    def start(self):
        """启动服务器"""
        try:
            self.server = HTTPServer((self.host, self.port), TokenMetricsHandler)
            self.running = True
            
            print(f"🚀 Token Metrics Server started on http://{self.host}:{self.port}")
            print(f"📊 Metrics available at: http://{self.host}:{self.port}/metrics")
            print(f"🔍 Health check at: http://{self.host}:{self.port}/health")
            
            # 设置信号处理
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            
            # 启动服务器
            self.server.serve_forever()
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            sys.exit(1)
    
    def stop(self):
        """停止服务器"""
        self.running = False
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        print("🛑 Token Metrics Server stopped")
    
    def _signal_handler(self, signum, frame):
        """处理终止信号"""
        print(f"\n📥 Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description='Clawdbot Token Metrics Prometheus Exporter')
    parser.add_argument('--host', default='0.0.0.0', help='Server host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=9095, help='Server port (default: 9095)')
    parser.add_argument('--disable-events', action='store_true', help='Disable event log monitoring')
    
    args = parser.parse_args()
    
    # 检查依赖
    try:
        import prometheus_client
    except ImportError:
        print("❌ prometheus_client not installed. Please run:")
        print("   pip install prometheus_client")
        sys.exit(1)
    
    # 创建并启动服务器
    server = TokenMetricsServer(host=args.host, port=args.port)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n👋 Received keyboard interrupt")
        server.stop()


if __name__ == "__main__":
    main()