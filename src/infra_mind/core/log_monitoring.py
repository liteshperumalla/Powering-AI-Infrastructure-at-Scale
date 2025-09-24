"""
Real-Time Log Monitoring and Analysis System.

Provides real-time log monitoring, pattern detection, anomaly detection,
and automated alerting for production environments.
"""

import asyncio
import json
import time
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
from pathlib import Path
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
import aiofiles
import websockets
import redis
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .advanced_logging import LogCategory, LogLevel, AlertSeverity


@dataclass
class LogPattern:
    """Log pattern for monitoring."""
    name: str
    pattern: str
    category: LogCategory
    severity: AlertSeverity
    description: str
    threshold: int = 1  # Number of occurrences to trigger alert
    time_window: int = 300  # Time window in seconds
    enabled: bool = True


@dataclass
class LogAnomaly:
    """Detected log anomaly."""
    timestamp: datetime
    pattern_name: str
    message: str
    count: int
    severity: AlertSeverity
    context: Dict[str, Any]


@dataclass
class LogMetrics:
    """Log metrics for monitoring."""
    total_logs: int = 0
    error_count: int = 0
    warning_count: int = 0
    critical_count: int = 0
    logs_per_minute: float = 0.0
    error_rate: float = 0.0
    top_errors: List[Dict[str, Any]] = field(default_factory=list)
    response_times: List[float] = field(default_factory=list)
    avg_response_time: float = 0.0


class LogPatternMatcher:
    """Matches log entries against predefined patterns."""
    
    def __init__(self):
        """Initialize pattern matcher."""
        self.patterns: List[LogPattern] = []
        self.pattern_counts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.compiled_patterns: Dict[str, re.Pattern] = {}
    
    def add_pattern(self, pattern: LogPattern) -> None:
        """Add a pattern to monitor."""
        self.patterns.append(pattern)
        self.compiled_patterns[pattern.name] = re.compile(pattern.pattern, re.IGNORECASE)
    
    def check_log_entry(self, log_entry: Dict[str, Any]) -> List[LogAnomaly]:
        """Check log entry against all patterns."""
        anomalies = []
        current_time = datetime.now()
        
        for pattern in self.patterns:
            if not pattern.enabled:
                continue
            
            # Check if pattern matches
            message = log_entry.get('message')
            if self.compiled_patterns[pattern.name].search(message):
                # Record pattern match
                self.pattern_counts[pattern.name].append(current_time)
                
                # Check if threshold exceeded within time window
                cutoff_time = current_time - timedelta(seconds=pattern.time_window)
                recent_matches = [
                    t for t in self.pattern_counts[pattern.name] 
                    if t > cutoff_time
                ]
                
                if len(recent_matches) >= pattern.threshold:
                    anomaly = LogAnomaly(
                        timestamp=current_time,
                        pattern_name=pattern.name,
                        message=message,
                        count=len(recent_matches),
                        severity=pattern.severity,
                        context={
                            'pattern_description': pattern.description,
                            'time_window': pattern.time_window,
                            'threshold': pattern.threshold,
                            'log_entry': log_entry
                        }
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def get_default_patterns(self) -> List[LogPattern]:
        """Get default monitoring patterns."""
        return [
            LogPattern(
                name="high_error_rate",
                pattern=r"ERROR|CRITICAL",
                category=LogCategory.SYSTEM,
                severity=AlertSeverity.HIGH,
                description="High error rate detected",
                threshold=10,
                time_window=300
            ),
            LogPattern(
                name="authentication_failures",
                pattern=r"authentication.*failed|login.*failed|invalid.*credentials",
                category=LogCategory.SECURITY,
                severity=AlertSeverity.HIGH,
                description="Multiple authentication failures",
                threshold=5,
                time_window=300
            ),
            LogPattern(
                name="database_connection_errors",
                pattern=r"database.*connection.*failed|mongodb.*error|redis.*error",
                category=LogCategory.DATABASE,
                severity=AlertSeverity.CRITICAL,
                description="Database connection issues",
                threshold=3,
                time_window=180
            ),
            LogPattern(
                name="api_rate_limit_exceeded",
                pattern=r"rate.*limit.*exceeded|too.*many.*requests",
                category=LogCategory.API,
                severity=AlertSeverity.MEDIUM,
                description="API rate limits being exceeded",
                threshold=5,
                time_window=300
            ),
            LogPattern(
                name="slow_response_times",
                pattern=r"execution_time_seconds.*[3-9]\d+|execution_time_seconds.*\d{3,}",
                category=LogCategory.PERFORMANCE,
                severity=AlertSeverity.MEDIUM,
                description="Slow response times detected",
                threshold=5,
                time_window=300
            ),
            LogPattern(
                name="llm_api_failures",
                pattern=r"openai.*error|anthropic.*error|llm.*failed",
                category=LogCategory.LLM,
                severity=AlertSeverity.HIGH,
                description="LLM API failures",
                threshold=3,
                time_window=300
            ),
            LogPattern(
                name="cloud_api_failures",
                pattern=r"aws.*error|azure.*error|gcp.*error|cloud.*api.*failed",
                category=LogCategory.CLOUD,
                severity=AlertSeverity.HIGH,
                description="Cloud API failures",
                threshold=5,
                time_window=300
            ),
            LogPattern(
                name="memory_issues",
                pattern=r"out.*of.*memory|memory.*error|oom.*killed",
                category=LogCategory.SYSTEM,
                severity=AlertSeverity.CRITICAL,
                description="Memory issues detected",
                threshold=1,
                time_window=60
            ),
            LogPattern(
                name="disk_space_issues",
                pattern=r"disk.*full|no.*space.*left|disk.*space.*low",
                category=LogCategory.SYSTEM,
                severity=AlertSeverity.CRITICAL,
                description="Disk space issues",
                threshold=1,
                time_window=60
            ),
            LogPattern(
                name="security_violations",
                pattern=r"security.*violation|unauthorized.*access|suspicious.*activity",
                category=LogCategory.SECURITY,
                severity=AlertSeverity.CRITICAL,
                description="Security violations detected",
                threshold=1,
                time_window=60
            )
        ]


class LogFileWatcher(FileSystemEventHandler):
    """Watches log files for changes and processes new entries."""
    
    def __init__(self, log_monitor: 'RealTimeLogMonitor'):
        """Initialize file watcher."""
        self.log_monitor = log_monitor
        self.file_positions: Dict[str, int] = {}
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        file_path = event.src_path
        if not file_path.endswith('.log'):
            return
        
        self._process_log_file(file_path)
    
    def _process_log_file(self, file_path: str) -> None:
        """Process new entries in log file."""
        try:
            with open(file_path, 'r') as f:
                # Seek to last known position
                last_position = self.file_positions.get(file_path, 0)
                f.seek(last_position)
                
                # Read new lines
                new_lines = f.readlines()
                
                # Update position
                self.file_positions[file_path] = f.tell()
                
                # Process new log entries
                for line in new_lines:
                    line = line.strip()
                    if line:
                        try:
                            log_entry = json.loads(line)
                            self.log_monitor.process_log_entry(log_entry)
                        except json.JSONDecodeError:
                            # Handle non-JSON log entries
                            log_entry = {
                                'timestamp': datetime.now().isoformat(),
                                'message': line,
                                'level': 'INFO',
                                'category': 'system'
                            }
                            self.log_monitor.process_log_entry(log_entry)
        
        except Exception as e:
            logging.error(f"Error processing log file {file_path}: {e}")


class RealTimeLogMonitor:
    """Real-time log monitoring and analysis system."""
    
    def __init__(self, log_dir: str = "logs", redis_config: Optional[Dict[str, Any]] = None):
        """Initialize log monitor."""
        self.log_dir = Path(log_dir)
        self.pattern_matcher = LogPatternMatcher()
        self.metrics = LogMetrics()
        self.anomaly_callbacks: List[Callable[[LogAnomaly], None]] = []
        self.metrics_callbacks: List[Callable[[LogMetrics], None]] = []
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Redis for distributed monitoring
        self.redis_client = None
        if redis_config:
            try:
                self.redis_client = redis.Redis(**redis_config)
            except Exception as e:
                logging.warning(f"Failed to connect to Redis: {e}")
        
        # Initialize with default patterns
        for pattern in self.pattern_matcher.get_default_patterns():
            self.pattern_matcher.add_pattern(pattern)
        
        # Metrics tracking
        self.log_buffer: deque = deque(maxlen=10000)
        self.error_buffer: deque = deque(maxlen=1000)
        self.metrics_lock = threading.Lock()
        
        # File watcher
        self.observer = Observer()
        self.file_watcher = LogFileWatcher(self)
    
    def start(self) -> None:
        """Start real-time monitoring."""
        if self.running:
            return
        
        self.running = True
        
        # Start file watching
        if self.log_dir.exists():
            self.observer.schedule(self.file_watcher, str(self.log_dir), recursive=True)
            self.observer.start()
        
        # Start metrics calculation task
        self.executor.submit(self._metrics_calculation_loop)
        
        # Start Redis monitoring if available
        if self.redis_client:
            self.executor.submit(self._redis_monitoring_loop)
        
        logging.info("Real-time log monitoring started")
    
    def stop(self) -> None:
        """Stop monitoring."""
        self.running = False
        self.observer.stop()
        self.observer.join()
        self.executor.shutdown(wait=True)
        logging.info("Real-time log monitoring stopped")
    
    def add_anomaly_callback(self, callback: Callable[[LogAnomaly], None]) -> None:
        """Add callback for anomaly detection."""
        self.anomaly_callbacks.append(callback)
    
    def add_metrics_callback(self, callback: Callable[[LogMetrics], None]) -> None:
        """Add callback for metrics updates."""
        self.metrics_callbacks.append(callback)
    
    def process_log_entry(self, log_entry: Dict[str, Any]) -> None:
        """Process a single log entry."""
        try:
            # Update metrics
            self._update_metrics(log_entry)
            
            # Check for anomalies
            anomalies = self.pattern_matcher.check_log_entry(log_entry)
            
            # Notify callbacks
            for anomaly in anomalies:
                for callback in self.anomaly_callbacks:
                    try:
                        callback(anomaly)
                    except Exception as e:
                        logging.error(f"Anomaly callback failed: {e}")
        
        except Exception as e:
            logging.error(f"Error processing log entry: {e}")
    
    def _update_metrics(self, log_entry: Dict[str, Any]) -> None:
        """Update metrics with new log entry."""
        with self.metrics_lock:
            self.metrics.total_logs += 1
            
            level = log_entry.get('level').upper()
            if level == 'ERROR':
                self.metrics.error_count += 1
                self.error_buffer.append(log_entry)
            elif level == 'WARNING':
                self.metrics.warning_count += 1
            elif level == 'CRITICAL':
                self.metrics.critical_count += 1
            
            # Track response times
            perf_metrics = log_entry.get('performance_metrics', {})
            if 'execution_time_seconds' in perf_metrics:
                self.metrics.response_times.append(perf_metrics['execution_time_seconds'])
                if len(self.metrics.response_times) > 1000:
                    self.metrics.response_times = self.metrics.response_times[-1000:]
            
            # Add to buffer for rate calculations
            self.log_buffer.append({
                'timestamp': datetime.now(),
                'level': level,
                'entry': log_entry
            })
    
    def _calculate_metrics(self) -> None:
        """Calculate derived metrics."""
        with self.metrics_lock:
            current_time = datetime.now()
            one_minute_ago = current_time - timedelta(minutes=1)
            
            # Calculate logs per minute
            recent_logs = [
                log for log in self.log_buffer 
                if log['timestamp'] > one_minute_ago
            ]
            self.metrics.logs_per_minute = len(recent_logs)
            
            # Calculate error rate
            if self.metrics.total_logs > 0:
                self.metrics.error_rate = (
                    (self.metrics.error_count + self.metrics.critical_count) / 
                    self.metrics.total_logs * 100
                )
            
            # Calculate average response time
            if self.metrics.response_times:
                self.metrics.avg_response_time = sum(self.metrics.response_times) / len(self.metrics.response_times)
            
            # Get top errors
            error_counts = defaultdict(int)
            for error in self.error_buffer:
                message = error.get('message')[:100]  # Truncate for grouping
                error_counts[message] += 1
            
            self.metrics.top_errors = [
                {'message': msg, 'count': count}
                for msg, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
    
    def _metrics_calculation_loop(self) -> None:
        """Background loop for metrics calculation."""
        while self.running:
            try:
                self._calculate_metrics()
                
                # Notify metrics callbacks
                for callback in self.metrics_callbacks:
                    try:
                        callback(self.metrics)
                    except Exception as e:
                        logging.error(f"Metrics callback failed: {e}")
                
                time.sleep(30)  # Update metrics every 30 seconds
                
            except Exception as e:
                logging.error(f"Metrics calculation error: {e}")
                time.sleep(30)
    
    def _redis_monitoring_loop(self) -> None:
        """Monitor Redis log stream."""
        while self.running:
            try:
                # Get logs from Redis
                logs = self.redis_client.lrange("infra_mind_logs", 0, 99)
                
                for log_data in logs:
                    try:
                        log_entry = json.loads(log_data.decode('utf-8'))
                        self.process_log_entry(log_entry)
                    except json.JSONDecodeError:
                        continue
                
                # Remove processed logs
                if logs:
                    self.redis_client.ltrim("infra_mind_logs", len(logs), -1)
                
                time.sleep(5)  # Check Redis every 5 seconds
                
            except Exception as e:
                logging.error(f"Redis monitoring error: {e}")
                time.sleep(10)
    
    def get_current_metrics(self) -> LogMetrics:
        """Get current metrics."""
        self._calculate_metrics()
        return self.metrics
    
    def add_custom_pattern(self, pattern: LogPattern) -> None:
        """Add custom monitoring pattern."""
        self.pattern_matcher.add_pattern(pattern)
    
    def get_log_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get log summary for specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_logs = [
            log for log in self.log_buffer 
            if log['timestamp'] > cutoff_time
        ]
        
        summary = {
            'total_logs': len(recent_logs),
            'error_logs': len([log for log in recent_logs if log['level'] in ['ERROR', 'CRITICAL']]),
            'warning_logs': len([log for log in recent_logs if log['level'] == 'WARNING']),
            'time_period_hours': hours,
            'average_logs_per_hour': len(recent_logs) / hours if hours > 0 else 0
        }
        
        return summary


# WebSocket server for real-time log streaming
class LogStreamServer:
    """WebSocket server for streaming logs to clients."""
    
    def __init__(self, monitor: RealTimeLogMonitor, port: int = 8765):
        """Initialize log stream server."""
        self.monitor = monitor
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
    
    async def start(self) -> None:
        """Start WebSocket server."""
        self.server = await websockets.serve(self.handle_client, "localhost", self.port)
        
        # Add callbacks to monitor
        self.monitor.add_anomaly_callback(self.broadcast_anomaly)
        self.monitor.add_metrics_callback(self.broadcast_metrics)
        
        logging.info(f"Log stream server started on port {self.port}")
    
    async def stop(self) -> None:
        """Stop WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
    
    async def handle_client(self, websocket, path):
        """Handle WebSocket client connection."""
        self.clients.add(websocket)
        try:
            # Send current metrics on connection
            metrics = self.monitor.get_current_metrics()
            await websocket.send(json.dumps({
                'type': 'metrics',
                'data': {
                    'total_logs': metrics.total_logs,
                    'error_count': metrics.error_count,
                    'warning_count': metrics.warning_count,
                    'logs_per_minute': metrics.logs_per_minute,
                    'error_rate': metrics.error_rate,
                    'avg_response_time': metrics.avg_response_time
                }
            }))
            
            # Keep connection alive
            await websocket.wait_closed()
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
    
    def broadcast_anomaly(self, anomaly: LogAnomaly) -> None:
        """Broadcast anomaly to all clients."""
        if not self.clients:
            return
        
        message = json.dumps({
            'type': 'anomaly',
            'data': {
                'timestamp': anomaly.timestamp.isoformat(),
                'pattern_name': anomaly.pattern_name,
                'message': anomaly.message,
                'count': anomaly.count,
                'severity': anomaly.severity.value
            }
        })
        
        # Send to all clients
        asyncio.create_task(self._broadcast_message(message))
    
    def broadcast_metrics(self, metrics: LogMetrics) -> None:
        """Broadcast metrics to all clients."""
        if not self.clients:
            return
        
        message = json.dumps({
            'type': 'metrics',
            'data': {
                'total_logs': metrics.total_logs,
                'error_count': metrics.error_count,
                'warning_count': metrics.warning_count,
                'logs_per_minute': metrics.logs_per_minute,
                'error_rate': metrics.error_rate,
                'avg_response_time': metrics.avg_response_time,
                'top_errors': metrics.top_errors[:5]  # Send top 5 errors
            }
        })
        
        asyncio.create_task(self._broadcast_message(message))
    
    async def _broadcast_message(self, message: str) -> None:
        """Broadcast message to all connected clients."""
        if not self.clients:
            return
        
        # Send to all clients, remove disconnected ones
        disconnected = set()
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
        
        # Remove disconnected clients
        self.clients -= disconnected