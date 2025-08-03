"""
Production-Ready Advanced Logging System for Multi-Agent Workflows.

Provides comprehensive logging for all agent interactions, decisions,
and workflow execution with structured logging, correlation IDs,
real log aggregation, and alerting capabilities.
"""

import logging
import logging.handlers
import json
import sys
import time
import os
import socket
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextlib import contextmanager
import threading
import uuid
import traceback
from pathlib import Path
import gzip
import shutil
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiohttp
import redis
from concurrent.futures import ThreadPoolExecutor

from ..core.config import get_settings


class LogLevel(str, Enum):
    """Enhanced log levels."""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(str, Enum):
    """Log categories for filtering and analysis."""
    WORKFLOW = "workflow"
    AGENT = "agent"
    SYSTEM = "system"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USER = "user"
    API = "api"
    DATABASE = "database"
    CLOUD = "cloud"
    LLM = "llm"
    MONITORING = "monitoring"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LogAggregationConfig:
    """Configuration for log aggregation services."""
    enabled: bool = False
    service_type: str = "elasticsearch"  # elasticsearch, splunk, datadog, etc.
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    index_name: str = "infra-mind-logs"
    batch_size: int = 100
    flush_interval: int = 30  # seconds
    
    
@dataclass
class AlertConfig:
    """Configuration for alerting."""
    enabled: bool = False
    email_enabled: bool = False
    webhook_enabled: bool = False
    slack_enabled: bool = False
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    alert_recipients: List[str] = field(default_factory=list)
    webhook_url: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    alert_cooldown: int = 300  # seconds between similar alerts


@dataclass
class LogContext:
    """Structured log context for correlation."""
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: Optional[str] = None
    agent_name: Optional[str] = None
    step_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class StructuredLogRecord:
    """Structured log record with enhanced metadata."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    level: LogLevel = LogLevel.INFO
    category: LogCategory = LogCategory.SYSTEM
    message: str = ""
    logger_name: str = ""
    module: str = ""
    function: str = ""
    line_number: int = 0
    context: LogContext = field(default_factory=LogContext)
    data: Dict[str, Any] = field(default_factory=dict)
    exception: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    hostname: str = field(default_factory=socket.gethostname)
    process_id: int = field(default_factory=os.getpid)
    thread_id: int = field(default_factory=threading.get_ident)
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log record to dictionary."""
        record = {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "category": self.category.value,
            "message": self.message,
            "logger": self.logger_name,
            "module": self.module,
            "function": self.function,
            "line": self.line_number,
            "context": self.context.to_dict(),
            "data": self.data,
            "hostname": self.hostname,
            "process_id": self.process_id,
            "thread_id": self.thread_id,
            "environment": self.environment
        }
        
        if self.exception:
            record["exception"] = self.exception
        
        if self.performance_metrics:
            record["performance"] = self.performance_metrics
        
        return record
    
    def to_json(self) -> str:
        """Convert log record to JSON string."""
        return json.dumps(self.to_dict(), default=str)
    
    def should_alert(self) -> bool:
        """Determine if this log record should trigger an alert."""
        return (
            self.level in [LogLevel.ERROR, LogLevel.CRITICAL] or
            self.category == LogCategory.SECURITY or
            (self.performance_metrics and 
             self.performance_metrics.get('execution_time_seconds', 0) > 30)
        )


class LogAggregator:
    """Handles log aggregation to external services."""
    
    def __init__(self, config: LogAggregationConfig):
        """Initialize log aggregator."""
        self.config = config
        self.log_buffer: List[Dict[str, Any]] = []
        self.buffer_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.last_flush = time.time()
        
        if config.enabled:
            # Start background flush task
            self._start_flush_task()
    
    def add_log(self, log_record: StructuredLogRecord) -> None:
        """Add log record to buffer for aggregation."""
        if not self.config.enabled:
            return
            
        with self.buffer_lock:
            self.log_buffer.append(log_record.to_dict())
            
            # Flush if buffer is full or time interval exceeded
            if (len(self.log_buffer) >= self.config.batch_size or
                time.time() - self.last_flush >= self.config.flush_interval):
                self._flush_logs()
    
    def _flush_logs(self) -> None:
        """Flush logs to aggregation service."""
        if not self.log_buffer:
            return
            
        logs_to_send = self.log_buffer.copy()
        self.log_buffer.clear()
        self.last_flush = time.time()
        
        # Send logs asynchronously
        self.executor.submit(self._send_logs, logs_to_send)
    
    def _send_logs(self, logs: List[Dict[str, Any]]) -> None:
        """Send logs to aggregation service."""
        try:
            if self.config.service_type == "elasticsearch":
                self._send_to_elasticsearch(logs)
            elif self.config.service_type == "datadog":
                self._send_to_datadog(logs)
            elif self.config.service_type == "splunk":
                self._send_to_splunk(logs)
            else:
                # Generic HTTP endpoint
                self._send_to_http_endpoint(logs)
        except Exception as e:
            # Log aggregation failure shouldn't break the application
            print(f"Log aggregation failed: {e}", file=sys.stderr)
    
    def _send_to_elasticsearch(self, logs: List[Dict[str, Any]]) -> None:
        """Send logs to Elasticsearch."""
        import requests
        
        bulk_data = []
        for log in logs:
            # Elasticsearch bulk format
            bulk_data.append(json.dumps({
                "index": {"_index": self.config.index_name}
            }))
            bulk_data.append(json.dumps(log))
        
        bulk_body = "\n".join(bulk_data) + "\n"
        
        headers = {
            "Content-Type": "application/x-ndjson",
            "Authorization": f"ApiKey {self.config.api_key}"
        }
        
        response = requests.post(
            f"{self.config.endpoint}/_bulk",
            headers=headers,
            data=bulk_body,
            timeout=30
        )
        response.raise_for_status()
    
    def _send_to_datadog(self, logs: List[Dict[str, Any]]) -> None:
        """Send logs to Datadog."""
        import requests
        
        headers = {
            "Content-Type": "application/json",
            "DD-API-KEY": self.config.api_key
        }
        
        for log in logs:
            response = requests.post(
                f"{self.config.endpoint}/v1/input/{self.config.api_key}",
                headers=headers,
                json=log,
                timeout=30
            )
            response.raise_for_status()
    
    def _send_to_http_endpoint(self, logs: List[Dict[str, Any]]) -> None:
        """Send logs to generic HTTP endpoint."""
        import requests
        
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        response = requests.post(
            self.config.endpoint,
            headers=headers,
            json={"logs": logs},
            timeout=30
        )
        response.raise_for_status()
    
    def _start_flush_task(self) -> None:
        """Start background task to flush logs periodically."""
        def flush_periodically():
            while True:
                time.sleep(self.config.flush_interval)
                with self.buffer_lock:
                    if self.log_buffer:
                        self._flush_logs()
        
        flush_thread = threading.Thread(target=flush_periodically, daemon=True)
        flush_thread.start()


class AlertManager:
    """Manages alerting for critical log events."""
    
    def __init__(self, config: AlertConfig):
        """Initialize alert manager."""
        self.config = config
        self.alert_cache: Dict[str, float] = {}  # Alert cooldown cache
        self.cache_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    def process_log_record(self, log_record: StructuredLogRecord) -> None:
        """Process log record and send alerts if necessary."""
        if not self.config.enabled or not log_record.should_alert():
            return
        
        # Create alert key for cooldown
        alert_key = f"{log_record.level}:{log_record.category}:{log_record.message[:100]}"
        
        with self.cache_lock:
            last_alert_time = self.alert_cache.get(alert_key, 0)
            current_time = time.time()
            
            if current_time - last_alert_time < self.config.alert_cooldown:
                return  # Still in cooldown period
            
            self.alert_cache[alert_key] = current_time
        
        # Send alert asynchronously
        self.executor.submit(self._send_alert, log_record)
    
    def _send_alert(self, log_record: StructuredLogRecord) -> None:
        """Send alert for log record."""
        try:
            alert_data = self._create_alert_data(log_record)
            
            if self.config.email_enabled:
                self._send_email_alert(alert_data)
            
            if self.config.webhook_enabled:
                self._send_webhook_alert(alert_data)
            
            if self.config.slack_enabled:
                self._send_slack_alert(alert_data)
                
        except Exception as e:
            print(f"Alert sending failed: {e}", file=sys.stderr)
    
    def _create_alert_data(self, log_record: StructuredLogRecord) -> Dict[str, Any]:
        """Create alert data from log record."""
        severity = AlertSeverity.CRITICAL if log_record.level == LogLevel.CRITICAL else AlertSeverity.HIGH
        
        return {
            "timestamp": log_record.timestamp.isoformat(),
            "severity": severity.value,
            "level": log_record.level.value,
            "category": log_record.category.value,
            "message": log_record.message,
            "hostname": log_record.hostname,
            "environment": log_record.environment,
            "context": log_record.context.to_dict(),
            "data": log_record.data,
            "exception": log_record.exception,
            "performance_metrics": log_record.performance_metrics
        }
    
    def _send_email_alert(self, alert_data: Dict[str, Any]) -> None:
        """Send email alert."""
        if not self.config.alert_recipients:
            return
        
        subject = f"[{alert_data['severity'].upper()}] Infra Mind Alert - {alert_data['category']}"
        
        body = f"""
        Alert Details:
        - Timestamp: {alert_data['timestamp']}
        - Severity: {alert_data['severity']}
        - Level: {alert_data['level']}
        - Category: {alert_data['category']}
        - Message: {alert_data['message']}
        - Hostname: {alert_data['hostname']}
        - Environment: {alert_data['environment']}
        
        Context: {json.dumps(alert_data['context'], indent=2)}
        
        Additional Data: {json.dumps(alert_data['data'], indent=2)}
        """
        
        if alert_data['exception']:
            body += f"\n\nException: {json.dumps(alert_data['exception'], indent=2)}"
        
        msg = MIMEMultipart()
        msg['From'] = self.config.smtp_username
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
            server.starttls()
            server.login(self.config.smtp_username, self.config.smtp_password)
            
            for recipient in self.config.alert_recipients:
                msg['To'] = recipient
                server.send_message(msg)
                del msg['To']
    
    def _send_webhook_alert(self, alert_data: Dict[str, Any]) -> None:
        """Send webhook alert."""
        import requests
        
        response = requests.post(
            self.config.webhook_url,
            json=alert_data,
            timeout=30
        )
        response.raise_for_status()
    
    def _send_slack_alert(self, alert_data: Dict[str, Any]) -> None:
        """Send Slack alert."""
        import requests
        
        color = {
            AlertSeverity.LOW: "good",
            AlertSeverity.MEDIUM: "warning", 
            AlertSeverity.HIGH: "danger",
            AlertSeverity.CRITICAL: "danger"
        }.get(AlertSeverity(alert_data['severity']), "danger")
        
        slack_payload = {
            "attachments": [{
                "color": color,
                "title": f"Infra Mind Alert - {alert_data['category']}",
                "text": alert_data['message'],
                "fields": [
                    {"title": "Severity", "value": alert_data['severity'], "short": True},
                    {"title": "Level", "value": alert_data['level'], "short": True},
                    {"title": "Hostname", "value": alert_data['hostname'], "short": True},
                    {"title": "Environment", "value": alert_data['environment'], "short": True},
                ],
                "timestamp": int(datetime.fromisoformat(alert_data['timestamp'].replace('Z', '+00:00')).timestamp())
            }]
        }
        
        response = requests.post(
            self.config.slack_webhook_url,
            json=slack_payload,
            timeout=30
        )
        response.raise_for_status()


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with aggregation and alerting."""
    
    def __init__(self, aggregator: Optional[LogAggregator] = None, 
                 alert_manager: Optional[AlertManager] = None):
        """Initialize formatter with optional aggregator and alert manager."""
        super().__init__()
        self.aggregator = aggregator
        self.alert_manager = alert_manager
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Get context from thread local storage
        context = getattr(_context_storage, 'context', LogContext())
        
        # Create structured record
        structured_record = StructuredLogRecord(
            level=LogLevel(record.levelname),
            category=getattr(record, 'category', LogCategory.SYSTEM),
            message=record.getMessage(),
            logger_name=record.name,
            module=record.module if hasattr(record, 'module') else '',
            function=record.funcName,
            line_number=record.lineno,
            context=context,
            data=getattr(record, 'data', {}),
            performance_metrics=getattr(record, 'performance_metrics', None)
        )
        
        # Add exception info if present
        if record.exc_info:
            structured_record.exception = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Send to aggregator
        if self.aggregator:
            self.aggregator.add_log(structured_record)
        
        # Process for alerts
        if self.alert_manager:
            self.alert_manager.process_log_record(structured_record)
        
        return structured_record.to_json()


class AgentDecisionLogger:
    """Specialized logger for agent decisions and reasoning."""
    
    def __init__(self, agent_name: str):
        """
        Initialize agent decision logger.
        
        Args:
            agent_name: Name of the agent
        """
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agent.{agent_name}")
    
    def log_decision(self, decision: str, reasoning: str, 
                    confidence: float, alternatives: List[str],
                    context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an agent decision with full reasoning.
        
        Args:
            decision: The decision made
            reasoning: Reasoning behind the decision
            confidence: Confidence score (0-1)
            alternatives: Alternative options considered
            context: Additional context data
        """
        self.logger.info(
            f"Agent decision: {decision}",
            extra={
                'category': LogCategory.AGENT,
                'data': {
                    'agent_name': self.agent_name,
                    'decision': decision,
                    'reasoning': reasoning,
                    'confidence': confidence,
                    'alternatives': alternatives,
                    'context': context or {}
                }
            }
        )
    
    def log_recommendation(self, recommendation_type: str, 
                         recommendation: Dict[str, Any],
                         supporting_data: Dict[str, Any]) -> None:
        """
        Log an agent recommendation.
        
        Args:
            recommendation_type: Type of recommendation
            recommendation: The recommendation data
            supporting_data: Data supporting the recommendation
        """
        self.logger.info(
            f"Agent recommendation: {recommendation_type}",
            extra={
                'category': LogCategory.AGENT,
                'data': {
                    'agent_name': self.agent_name,
                    'recommendation_type': recommendation_type,
                    'recommendation': recommendation,
                    'supporting_data': supporting_data
                }
            }
        )
    
    def log_tool_usage(self, tool_name: str, input_data: Dict[str, Any],
                      output_data: Dict[str, Any], execution_time: float) -> None:
        """
        Log agent tool usage.
        
        Args:
            tool_name: Name of the tool used
            input_data: Input data to the tool
            output_data: Output data from the tool
            execution_time: Tool execution time in seconds
        """
        self.logger.debug(
            f"Tool usage: {tool_name}",
            extra={
                'category': LogCategory.AGENT,
                'data': {
                    'agent_name': self.agent_name,
                    'tool_name': tool_name,
                    'input_data': input_data,
                    'output_data': output_data
                },
                'performance_metrics': {
                    'execution_time_seconds': execution_time
                }
            }
        )
    
    def log_llm_interaction(self, prompt: str, response: str,
                          model: str, tokens_used: int,
                          response_time: float) -> None:
        """
        Log LLM interaction.
        
        Args:
            prompt: The prompt sent to LLM
            response: The response from LLM
            model: Model used
            tokens_used: Number of tokens used
            response_time: Response time in seconds
        """
        self.logger.debug(
            f"LLM interaction with {model}",
            extra={
                'category': LogCategory.AGENT,
                'data': {
                    'agent_name': self.agent_name,
                    'model': model,
                    'prompt_length': len(prompt),
                    'response_length': len(response),
                    'tokens_used': tokens_used,
                    # Don't log full prompt/response in production for privacy
                    'prompt_preview': prompt[:200] + "..." if len(prompt) > 200 else prompt,
                    'response_preview': response[:200] + "..." if len(response) > 200 else response
                },
                'performance_metrics': {
                    'response_time_seconds': response_time,
                    'tokens_per_second': tokens_used / response_time if response_time > 0 else 0
                }
            }
        )


class WorkflowLogger:
    """Specialized logger for workflow execution."""
    
    def __init__(self):
        """Initialize workflow logger."""
        self.logger = logging.getLogger("workflow")
    
    def log_workflow_started(self, workflow_id: str, workflow_name: str,
                           steps: List[str], context: Dict[str, Any]) -> None:
        """Log workflow start."""
        self.logger.info(
            f"Workflow started: {workflow_name}",
            extra={
                'category': LogCategory.WORKFLOW,
                'data': {
                    'workflow_id': workflow_id,
                    'workflow_name': workflow_name,
                    'total_steps': len(steps),
                    'steps': steps,
                    'context': context
                }
            }
        )
    
    def log_workflow_completed(self, workflow_id: str, workflow_name: str,
                             execution_time: float, results: Dict[str, Any]) -> None:
        """Log workflow completion."""
        self.logger.info(
            f"Workflow completed: {workflow_name}",
            extra={
                'category': LogCategory.WORKFLOW,
                'data': {
                    'workflow_id': workflow_id,
                    'workflow_name': workflow_name,
                    'results': results
                },
                'performance_metrics': {
                    'execution_time_seconds': execution_time
                }
            }
        )
    
    def log_workflow_failed(self, workflow_id: str, workflow_name: str,
                          error: str, failed_step: Optional[str] = None) -> None:
        """Log workflow failure."""
        self.logger.error(
            f"Workflow failed: {workflow_name}",
            extra={
                'category': LogCategory.WORKFLOW,
                'data': {
                    'workflow_id': workflow_id,
                    'workflow_name': workflow_name,
                    'error': error,
                    'failed_step': failed_step
                }
            }
        )
    
    def log_step_started(self, workflow_id: str, step_id: str,
                        step_name: str, agent_name: str) -> None:
        """Log workflow step start."""
        self.logger.info(
            f"Step started: {step_name}",
            extra={
                'category': LogCategory.WORKFLOW,
                'data': {
                    'workflow_id': workflow_id,
                    'step_id': step_id,
                    'step_name': step_name,
                    'agent_name': agent_name
                }
            }
        )
    
    def log_step_completed(self, workflow_id: str, step_id: str,
                         step_name: str, agent_name: str,
                         execution_time: float, result: Dict[str, Any]) -> None:
        """Log workflow step completion."""
        self.logger.info(
            f"Step completed: {step_name}",
            extra={
                'category': LogCategory.WORKFLOW,
                'data': {
                    'workflow_id': workflow_id,
                    'step_id': step_id,
                    'step_name': step_name,
                    'agent_name': agent_name,
                    'result': result
                },
                'performance_metrics': {
                    'execution_time_seconds': execution_time
                }
            }
        )


class PerformanceLogger:
    """Logger for performance metrics and monitoring."""
    
    def __init__(self):
        """Initialize performance logger."""
        self.logger = logging.getLogger("performance")
    
    def log_performance_metric(self, metric_name: str, value: float,
                             unit: str, context: Dict[str, Any]) -> None:
        """Log a performance metric."""
        self.logger.info(
            f"Performance metric: {metric_name} = {value} {unit}",
            extra={
                'category': LogCategory.PERFORMANCE,
                'data': {
                    'metric_name': metric_name,
                    'value': value,
                    'unit': unit,
                    'context': context
                }
            }
        )
    
    def log_resource_usage(self, cpu_percent: float, memory_percent: float,
                         disk_percent: float, network_connections: int) -> None:
        """Log system resource usage."""
        self.logger.info(
            "System resource usage",
            extra={
                'category': LogCategory.PERFORMANCE,
                'data': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'disk_percent': disk_percent,
                    'network_connections': network_connections
                }
            }
        )


# Thread-local storage for log context
_context_storage = threading.local()


@contextmanager
def log_context(**kwargs):
    """Context manager for setting log context."""
    # Get current context or create new one
    current_context = getattr(_context_storage, 'context', LogContext())
    
    # Create new context with updates
    new_context = LogContext(**{
        **asdict(current_context),
        **{k: v for k, v in kwargs.items() if v is not None}
    })
    
    # Set new context
    old_context = getattr(_context_storage, 'context', None)
    _context_storage.context = new_context
    
    try:
        yield new_context
    finally:
        # Restore old context
        if old_context:
            _context_storage.context = old_context
        else:
            if hasattr(_context_storage, 'context'):
                delattr(_context_storage, 'context')


class LogRotationHandler(logging.handlers.TimedRotatingFileHandler):
    """Custom log rotation handler with compression and retention."""
    
    def __init__(self, filename: str, when: str = 'midnight', interval: int = 1,
                 backup_count: int = 30, compress: bool = True, **kwargs):
        """Initialize rotation handler."""
        super().__init__(filename, when, interval, backup_count, **kwargs)
        self.compress = compress
    
    def doRollover(self) -> None:
        """Perform log rotation with compression."""
        super().doRollover()
        
        if self.compress:
            # Compress rotated log files
            log_dir = Path(self.baseFilename).parent
            for log_file in log_dir.glob(f"{Path(self.baseFilename).name}.*"):
                if not log_file.name.endswith('.gz') and log_file.is_file():
                    self._compress_file(log_file)
    
    def _compress_file(self, file_path: Path) -> None:
        """Compress a log file."""
        try:
            with open(file_path, 'rb') as f_in:
                with gzip.open(f"{file_path}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            file_path.unlink()  # Remove original file
        except Exception as e:
            print(f"Failed to compress log file {file_path}: {e}", file=sys.stderr)


def setup_production_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    enable_console: bool = True,
    enable_structured: bool = True,
    enable_rotation: bool = True,
    aggregation_config: Optional[LogAggregationConfig] = None,
    alert_config: Optional[AlertConfig] = None,
    redis_config: Optional[Dict[str, Any]] = None
) -> None:
    """
    Set up production-ready logging configuration.
    
    Args:
        log_level: Logging level
        log_dir: Directory for log files
        enable_console: Enable console logging
        enable_structured: Enable structured JSON logging
        enable_rotation: Enable log rotation
        aggregation_config: Configuration for log aggregation
        alert_config: Configuration for alerting
        redis_config: Redis configuration for distributed logging
    """
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize aggregator and alert manager
    aggregator = LogAggregator(aggregation_config) if aggregation_config else None
    alert_manager = AlertManager(alert_config) if alert_config else None
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    if enable_structured:
        formatter = StructuredFormatter(aggregator, alert_manager)
        console_formatter = StructuredFormatter()  # No aggregation for console
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = formatter
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)
    
    # File handlers with rotation
    if enable_rotation:
        # Main application log
        app_handler = LogRotationHandler(
            filename=str(log_path / "infra_mind.log"),
            when='midnight',
            interval=1,
            backup_count=30,
            compress=True
        )
        app_handler.setFormatter(formatter)
        app_handler.setLevel(logging.INFO)
        root_logger.addHandler(app_handler)
        
        # Error log
        error_handler = LogRotationHandler(
            filename=str(log_path / "errors.log"),
            when='midnight',
            interval=1,
            backup_count=90,
            compress=True
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
        
        # Performance log
        perf_handler = LogRotationHandler(
            filename=str(log_path / "performance.log"),
            when='midnight',
            interval=1,
            backup_count=30,
            compress=True
        )
        perf_handler.setFormatter(formatter)
        perf_handler.addFilter(lambda record: getattr(record, 'category', None) == LogCategory.PERFORMANCE)
        root_logger.addHandler(perf_handler)
        
        # Security log
        security_handler = LogRotationHandler(
            filename=str(log_path / "security.log"),
            when='midnight',
            interval=1,
            backup_count=365,  # Keep security logs for 1 year
            compress=True
        )
        security_handler.setFormatter(formatter)
        security_handler.addFilter(lambda record: getattr(record, 'category', None) == LogCategory.SECURITY)
        root_logger.addHandler(security_handler)
    
    # Set up specific loggers
    loggers = [
        'workflow',
        'agent',
        'performance',
        'system',
        'api',
        'database',
        'cloud',
        'llm',
        'monitoring'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, log_level.upper()))
    
    # Set up Redis logging if configured
    if redis_config:
        setup_redis_logging(redis_config)
    
    logging.info("Production logging system initialized")


def setup_redis_logging(redis_config: Dict[str, Any]) -> None:
    """Set up Redis-based distributed logging."""
    try:
        redis_client = redis.Redis(**redis_config)
        
        class RedisLogHandler(logging.Handler):
            """Redis log handler for distributed logging."""
            
            def __init__(self, redis_client: redis.Redis, key: str = "infra_mind_logs"):
                super().__init__()
                self.redis_client = redis_client
                self.key = key
            
            def emit(self, record: logging.LogRecord) -> None:
                """Emit log record to Redis."""
                try:
                    log_entry = self.format(record)
                    self.redis_client.lpush(self.key, log_entry)
                    # Keep only last 10000 log entries
                    self.redis_client.ltrim(self.key, 0, 9999)
                except Exception:
                    # Don't let Redis failures break logging
                    pass
        
        redis_handler = RedisLogHandler(redis_client)
        redis_handler.setFormatter(StructuredFormatter())
        
        root_logger = logging.getLogger()
        root_logger.addHandler(redis_handler)
        
        logging.info("Redis logging configured")
        
    except Exception as e:
        logging.warning(f"Failed to configure Redis logging: {e}")


def setup_advanced_logging(log_level: str = "INFO", 
                         log_file: Optional[str] = None,
                         enable_console: bool = True,
                         enable_structured: bool = True) -> None:
    """
    Set up advanced logging configuration (legacy function for compatibility).
    
    Args:
        log_level: Logging level
        log_file: Optional log file path
        enable_console: Enable console logging
        enable_structured: Enable structured JSON logging
    """
    # Use production logging setup
    log_dir = Path(log_file).parent if log_file else Path("logs")
    setup_production_logging(
        log_level=log_level,
        log_dir=str(log_dir),
        enable_console=enable_console,
        enable_structured=enable_structured
    )


def get_agent_logger(agent_name: str) -> AgentDecisionLogger:
    """Get agent decision logger for specific agent."""
    return AgentDecisionLogger(agent_name)


def get_workflow_logger() -> WorkflowLogger:
    """Get workflow logger."""
    return WorkflowLogger()


def get_performance_logger() -> PerformanceLogger:
    """Get performance logger."""
    return PerformanceLogger()


# Performance timing decorator
def log_performance(operation_name: str, category: LogCategory = LogCategory.PERFORMANCE):
    """Decorator to log operation performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger = logging.getLogger("performance")
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.info(
                    f"Operation completed: {operation_name}",
                    extra={
                        'category': category,
                        'data': {
                            'operation': operation_name,
                            'function': func.__name__,
                            'success': True
                        },
                        'performance_metrics': {
                            'execution_time_seconds': execution_time
                        }
                    }
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                logger.error(
                    f"Operation failed: {operation_name}",
                    extra={
                        'category': category,
                        'data': {
                            'operation': operation_name,
                            'function': func.__name__,
                            'success': False,
                            'error': str(e)
                        },
                        'performance_metrics': {
                            'execution_time_seconds': execution_time
                        }
                    },
                    exc_info=True
                )
                
                raise
        
        return wrapper
    return decorator


# Async version of performance decorator
def log_async_performance(operation_name: str, category: LogCategory = LogCategory.PERFORMANCE):
    """Decorator to log async operation performance."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            logger = logging.getLogger("performance")
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.info(
                    f"Async operation completed: {operation_name}",
                    extra={
                        'category': category,
                        'data': {
                            'operation': operation_name,
                            'function': func.__name__,
                            'success': True
                        },
                        'performance_metrics': {
                            'execution_time_seconds': execution_time
                        }
                    }
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                logger.error(
                    f"Async operation failed: {operation_name}",
                    extra={
                        'category': category,
                        'data': {
                            'operation': operation_name,
                            'function': func.__name__,
                            'success': False,
                            'error': str(e)
                        },
                        'performance_metrics': {
                            'execution_time_seconds': execution_time
                        }
                    },
                    exc_info=True
                )
                
                raise
        
        return wrapper
    return decorator