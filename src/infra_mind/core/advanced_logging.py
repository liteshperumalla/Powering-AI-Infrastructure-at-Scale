"""
Advanced Logging System for Multi-Agent Workflows.

Provides comprehensive logging for all agent interactions, decisions,
and workflow execution with structured logging and correlation IDs.
"""

import logging
import json
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextlib import contextmanager
import threading
import uuid
import traceback
from pathlib import Path

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
            "data": self.data
        }
        
        if self.exception:
            record["exception"] = self.exception
        
        if self.performance_metrics:
            record["performance"] = self.performance_metrics
        
        return record
    
    def to_json(self) -> str:
        """Convert log record to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
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


def setup_advanced_logging(log_level: str = "INFO", 
                         log_file: Optional[str] = None,
                         enable_console: bool = True,
                         enable_structured: bool = True) -> None:
    """
    Set up advanced logging configuration.
    
    Args:
        log_level: Logging level
        log_file: Optional log file path
        enable_console: Enable console logging
        enable_structured: Enable structured JSON logging
    """
    # Create logs directory if needed
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    if enable_structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set up specific loggers
    loggers = [
        'workflow',
        'agent',
        'performance',
        'system',
        'api',
        'database'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, log_level.upper()))
    
    logging.info("Advanced logging system initialized")


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