"""
Production-Ready Metrics Collection Service for Infra Mind.

Implements comprehensive metrics collection for system performance, user engagement,
business metrics, and real-time monitoring with dashboard capabilities.
"""

import asyncio
import time
import psutil
import logging
import json
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
import threading
import websockets
import aiohttp

from ..models.metrics import Metric, AgentMetrics, MetricType, MetricCategory
from ..core.config import get_settings


logger = logging.getLogger(__name__)


@dataclass
class SystemHealthStatus:
    """System health status data structure."""
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    active_connections: int
    response_time_ms: float
    error_rate_percent: float
    uptime_seconds: float
    status: str = "healthy"  # healthy, warning, critical
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserEngagementMetrics:
    """User engagement metrics data structure."""
    active_users_count: int
    new_users_count: int
    assessments_started: int
    assessments_completed: int
    reports_generated: int
    average_session_duration_minutes: float
    bounce_rate_percent: float
    page_views: int
    unique_visitors: int
    conversion_rate: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BusinessMetrics:
    """Business metrics data structure."""
    total_assessments: int
    completed_assessments: int
    total_reports: int
    total_recommendations: int
    user_satisfaction_score: float
    revenue_impact: float
    cost_savings_identified: float
    compliance_score: float
    agent_efficiency_score: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RealTimeMetrics:
    """Real-time metrics data structure."""
    requests_per_second: float
    active_connections: int
    queue_depth: int
    cache_hit_rate: float
    database_connections: int
    llm_requests_per_minute: int
    cloud_api_calls_per_minute: int
    error_rate_last_minute: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class MetricsCollector:
    """
    Production-ready central metrics collection service.
    
    Handles collection of system performance, user engagement,
    business metrics, and real-time monitoring with dashboard capabilities.
    """
    
    def __init__(self, redis_config: Optional[Dict[str, Any]] = None):
        """Initialize metrics collector."""
        self.settings = get_settings()
        self.start_time = datetime.utcnow()
        self.collection_interval = 30  # seconds for more frequent collection
        self.is_collecting = False
        self._collection_task: Optional[asyncio.Task] = None
        self._real_time_task: Optional[asyncio.Task] = None
        self._database_available = True  # Track database availability
        
        # Performance tracking
        self._request_times: deque = deque(maxlen=10000)
        self._error_count = 0
        self._request_count = 0
        self._requests_per_second = deque(maxlen=60)  # Last 60 seconds
        
        # User engagement tracking
        self._active_sessions: Dict[str, datetime] = {}
        self._user_actions: List[Dict[str, Any]] = []
        self._page_views: deque = deque(maxlen=10000)
        self._unique_visitors: set = set()
        
        # Business metrics tracking
        self._assessments_data: Dict[str, Any] = defaultdict(int)
        self._reports_data: Dict[str, Any] = defaultdict(int)
        self._recommendations_data: Dict[str, Any] = defaultdict(int)
        self._user_feedback: List[Dict[str, Any]] = []
        
        # Real-time metrics
        self._real_time_metrics = RealTimeMetrics(
            requests_per_second=0.0,
            active_connections=0,
            queue_depth=0,
            cache_hit_rate=0.0,
            database_connections=0,
            llm_requests_per_minute=0,
            cloud_api_calls_per_minute=0,
            error_rate_last_minute=0.0
        )
        
        # Thread safety
        self._metrics_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Redis for distributed metrics
        self.redis_client = None
        if redis_config:
            try:
                self.redis_client = redis.Redis(**redis_config)
                self.redis_client.ping()  # Test connection
            except Exception as e:
                logging.warning(f"Failed to connect to Redis for metrics: {e}")
        
        # Callbacks for real-time updates
        self._metrics_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._websocket_clients: set = set()
        
        # Cache for expensive calculations
        self._metrics_cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = 30  # seconds
    
    async def _safe_record_metric(self, **kwargs) -> bool:
        """Safely record a metric, handling database unavailability."""
        try:
            await Metric.record_metric(**kwargs)
            return True
        except Exception as e:
            if not self._database_available:
                logger.debug(f"Database not available, skipping metric: {kwargs.get('name', 'unknown')}")
            else:
                logger.debug(f"Failed to record metric {kwargs.get('name', 'unknown')}: {e}")
                self._database_available = False
            return False
    
    async def start_collection(self) -> None:
        """Start automatic metrics collection."""
        if self.is_collecting:
            logger.warning("Metrics collection already started")
            return
        
        self.is_collecting = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        self._real_time_task = asyncio.create_task(self._real_time_loop())
        logger.info("Started comprehensive metrics collection")
    
    async def stop_collection(self) -> None:
        """Stop automatic metrics collection."""
        if not self.is_collecting:
            return
        
        self.is_collecting = False
        
        # Cancel collection tasks
        for task in [self._collection_task, self._real_time_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Shutdown executor
        self._executor.shutdown(wait=True)
        
        logger.info("Stopped metrics collection")
    
    async def _collection_loop(self) -> None:
        """Main collection loop."""
        while self.is_collecting:
            try:
                await self.collect_system_metrics()
                await self.collect_health_metrics()
                await self.collect_user_engagement_metrics()
                await self.collect_business_metrics()
                await self._update_redis_metrics()
                await self._notify_callbacks()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _real_time_loop(self) -> None:
        """Real-time metrics collection loop."""
        while self.is_collecting:
            try:
                await self._collect_real_time_metrics()
                await self._broadcast_real_time_metrics()
                await asyncio.sleep(5)  # Update every 5 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in real-time metrics loop: {e}")
                await asyncio.sleep(5)
    
    async def _collect_real_time_metrics(self) -> None:
        """Collect real-time metrics."""
        try:
            current_time = datetime.utcnow()
            
            # Calculate requests per second
            recent_requests = [
                req for req in self._requests_per_second
                if (current_time - req).total_seconds() <= 60
            ]
            rps = len(recent_requests) / 60.0
            
            # Get system metrics - handle permission issues gracefully
            try:
                connections = len(psutil.net_connections())
            except (psutil.AccessDenied, PermissionError):
                # On macOS, this requires elevated permissions
                connections = 0
                logger.debug("Network connections unavailable due to permissions")
            
            # Calculate error rate for last minute
            minute_ago = current_time - timedelta(minutes=1)
            recent_errors = sum(
                1 for action in self._user_actions
                if (action.get('timestamp', current_time) > minute_ago and 
                    action.get('type') == 'error')
            )
            recent_total = len([
                action for action in self._user_actions
                if action.get('timestamp', current_time) > minute_ago
            ])
            error_rate = (recent_errors / max(recent_total, 1)) * 100
            
            # Update real-time metrics
            with self._metrics_lock:
                self._real_time_metrics = RealTimeMetrics(
                    requests_per_second=rps,
                    active_connections=connections,
                    queue_depth=0,  # TODO: Implement queue monitoring
                    cache_hit_rate=self._calculate_cache_hit_rate(),
                    database_connections=self._get_database_connections(),
                    llm_requests_per_minute=self._count_llm_requests_last_minute(),
                    cloud_api_calls_per_minute=self._count_cloud_api_calls_last_minute(),
                    error_rate_last_minute=error_rate
                )
            
        except Exception as e:
            logger.error(f"Error collecting real-time metrics: {e}", exc_info=True)
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        # TODO: Implement actual cache hit rate calculation
        return 85.0  # Placeholder
    
    def _get_database_connections(self) -> int:
        """Get current database connections."""
        # TODO: Implement actual database connection monitoring
        return 5  # Placeholder
    
    def _count_llm_requests_last_minute(self) -> int:
        """Count LLM requests in the last minute."""
        minute_ago = datetime.utcnow() - timedelta(minutes=1)
        return len([
            action for action in self._user_actions
            if (action.get('timestamp', datetime.utcnow()) > minute_ago and
                action.get('type', '').startswith('llm_'))
        ])
    
    def _count_cloud_api_calls_last_minute(self) -> int:
        """Count cloud API calls in the last minute."""
        minute_ago = datetime.utcnow() - timedelta(minutes=1)
        return len([
            action for action in self._user_actions
            if (action.get('timestamp', datetime.utcnow()) > minute_ago and
                action.get('type', '').startswith('cloud_api_'))
        ])
    
    async def collect_system_metrics(self) -> None:
        """Collect system performance metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            await self._safe_record_metric(
                name="system.cpu.usage_percent",
                value=cpu_percent,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.TECHNICAL,
                unit="percent",
                source="system_monitor"
            )
            
            # Memory metrics
            memory = psutil.virtual_memory()
            await self._safe_record_metric(
                name="system.memory.usage_percent",
                value=memory.percent,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.TECHNICAL,
                unit="percent",
                source="system_monitor",
                dimensions={
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2)
                }
            )
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            await self._safe_record_metric(
                name="system.disk.usage_percent",
                value=disk_percent,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.TECHNICAL,
                unit="percent",
                source="system_monitor",
                dimensions={
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2)
                }
            )
            
            # Network connections - handle permission issues gracefully
            try:
                connections = len(psutil.net_connections())
            except (psutil.AccessDenied, PermissionError):
                # On macOS, this requires elevated permissions
                connections = 0
                logger.debug("Network connections unavailable due to permissions")
            
            await self._safe_record_metric(
                name="system.network.active_connections",
                value=connections,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.TECHNICAL,
                unit="count",
                source="system_monitor"
            )
            
            # Process metrics
            process = psutil.Process()
            await self._safe_record_metric(
                name="system.process.memory_mb",
                value=process.memory_info().rss / (1024 * 1024),
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.TECHNICAL,
                unit="mb",
                source="system_monitor"
            )
            
            logger.debug("Collected system performance metrics")
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}", exc_info=True)
    
    async def collect_health_metrics(self) -> None:
        """Collect system health monitoring metrics."""
        try:
            # Calculate uptime
            uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
            await self._safe_record_metric(
                name="system.uptime_seconds",
                value=uptime_seconds,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.OPERATIONAL,
                unit="seconds",
                source="health_monitor"
            )
            
            # Calculate error rate
            error_rate = 0.0
            if self._request_count > 0:
                error_rate = (self._error_count / self._request_count) * 100
            
            await self._safe_record_metric(
                name="system.error_rate_percent",
                value=error_rate,
                metric_type=MetricType.ERROR_TRACKING,
                category=MetricCategory.OPERATIONAL,
                unit="percent",
                source="health_monitor",
                dimensions={
                    "total_requests": self._request_count,
                    "total_errors": self._error_count
                }
            )
            
            # Calculate average response time
            avg_response_time = 0.0
            if self._request_times:
                avg_response_time = sum(self._request_times) / len(self._request_times)
            
            await self._safe_record_metric(
                name="system.avg_response_time_ms",
                value=avg_response_time,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.TECHNICAL,
                unit="ms",
                source="health_monitor",
                dimensions={
                    "sample_count": len(self._request_times)
                }
            )
            
            # Determine health status
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            health_score = 100.0
            if cpu_percent > 80:
                health_score -= 30
            elif cpu_percent > 60:
                health_score -= 15
            
            if memory_percent > 85:
                health_score -= 30
            elif memory_percent > 70:
                health_score -= 15
            
            if error_rate > 5:
                health_score -= 25
            elif error_rate > 1:
                health_score -= 10
            
            await self._safe_record_metric(
                name="system.health_score",
                value=health_score,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.OPERATIONAL,
                unit="score",
                source="health_monitor",
                dimensions={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "error_rate": error_rate
                }
            )
            
            # Reset counters periodically
            if len(self._request_times) > 1000:
                self._request_times = self._request_times[-500:]
            
            logger.debug("Collected health monitoring metrics")
            
        except Exception as e:
            logger.error(f"Error collecting health metrics: {e}", exc_info=True)
    
    async def collect_user_engagement_metrics(self) -> None:
        """Collect enhanced user engagement tracking metrics."""
        try:
            now = datetime.utcnow()
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)
            
            # Active sessions count
            active_sessions = sum(
                1 for last_activity in self._active_sessions.values()
                if (now - last_activity).total_seconds() < 1800  # 30 minutes
            )
            
            await self._safe_record_metric(
                name="user.active_sessions",
                value=active_sessions,
                metric_type=MetricType.USER_ENGAGEMENT,
                category=MetricCategory.USER_EXPERIENCE,
                unit="count",
                source="engagement_tracker"
            )
            
            # Page views in the last hour
            recent_page_views = [
                view for view in self._page_views
                if view.get('timestamp', now) > hour_ago
            ]
            
            await self._safe_record_metric(
                name="user.page_views_per_hour",
                value=len(recent_page_views),
                metric_type=MetricType.USER_ENGAGEMENT,
                category=MetricCategory.USER_EXPERIENCE,
                unit="count",
                source="engagement_tracker"
            )
            
            # Unique visitors in the last day
            daily_visitors = len([
                visitor for visitor in self._unique_visitors
                # Note: This is simplified - in production, you'd track visitor timestamps
            ])
            
            await self._safe_record_metric(
                name="user.unique_visitors_daily",
                value=daily_visitors,
                metric_type=MetricType.USER_ENGAGEMENT,
                category=MetricCategory.USER_EXPERIENCE,
                unit="count",
                source="engagement_tracker"
            )
            
            # User actions in the last hour
            recent_actions = [
                action for action in self._user_actions
                if action.get('timestamp', now) > hour_ago
            ]
            
            await self._safe_record_metric(
                name="user.actions_per_hour",
                value=len(recent_actions),
                metric_type=MetricType.USER_ENGAGEMENT,
                category=MetricCategory.USER_EXPERIENCE,
                unit="count",
                source="engagement_tracker"
            )
            
            # Action type breakdown
            action_types = defaultdict(int)
            for action in recent_actions:
                action_type = action.get('type', 'unknown')
                action_types[action_type] += 1
            
            for action_type, count in action_types.items():
                await self._safe_record_metric(
                    name=f"user.action.{action_type}",
                    value=count,
                    metric_type=MetricType.USER_ENGAGEMENT,
                    category=MetricCategory.USER_EXPERIENCE,
                    unit="count",
                    source="engagement_tracker",
                    tags=[action_type]
                )
            
            # Calculate conversion rate (assessments completed / assessments started)
            assessments_started = action_types.get('assessment_started', 0)
            assessments_completed = action_types.get('assessment_completed', 0)
            conversion_rate = (assessments_completed / max(assessments_started, 1)) * 100
            
            await self._safe_record_metric(
                name="user.conversion_rate",
                value=conversion_rate,
                metric_type=MetricType.USER_ENGAGEMENT,
                category=MetricCategory.BUSINESS,
                unit="percent",
                source="engagement_tracker"
            )
            
            # Clean up old data
            self._user_actions = [
                action for action in self._user_actions
                if action.get('timestamp', now) > day_ago
            ]
            
            # Clean up old page views
            self._page_views = deque([
                view for view in self._page_views
                if view.get('timestamp', now) > day_ago
            ], maxlen=10000)
            
            logger.debug("Collected enhanced user engagement metrics")
            
        except Exception as e:
            logger.error(f"Error collecting user engagement metrics: {e}", exc_info=True)
    
    async def collect_business_metrics(self) -> None:
        """Collect business-specific metrics."""
        try:
            now = datetime.utcnow()
            
            # Assessment metrics
            total_assessments = self._assessments_data.get('total', 0)
            completed_assessments = self._assessments_data.get('completed', 0)
            
            await self._safe_record_metric(
                name="business.assessments.total",
                value=total_assessments,
                metric_type=MetricType.BUSINESS_KPI,
                category=MetricCategory.BUSINESS,
                unit="count",
                source="business_tracker"
            )
            
            await self._safe_record_metric(
                name="business.assessments.completed",
                value=completed_assessments,
                metric_type=MetricType.BUSINESS_KPI,
                category=MetricCategory.BUSINESS,
                unit="count",
                source="business_tracker"
            )
            
            # Report metrics
            total_reports = self._reports_data.get('total', 0)
            await self._safe_record_metric(
                name="business.reports.generated",
                value=total_reports,
                metric_type=MetricType.BUSINESS_KPI,
                category=MetricCategory.BUSINESS,
                unit="count",
                source="business_tracker"
            )
            
            # Recommendation metrics
            total_recommendations = self._recommendations_data.get('total', 0)
            await self._safe_record_metric(
                name="business.recommendations.generated",
                value=total_recommendations,
                metric_type=MetricType.BUSINESS_KPI,
                category=MetricCategory.BUSINESS,
                unit="count",
                source="business_tracker"
            )
            
            # User satisfaction score (from feedback)
            if self._user_feedback:
                satisfaction_scores = [
                    feedback.get('score', 0) for feedback in self._user_feedback
                    if feedback.get('timestamp', now) > now - timedelta(days=30)
                ]
                avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0
                
                await self._safe_record_metric(
                    name="business.user_satisfaction_score",
                    value=avg_satisfaction,
                    metric_type=MetricType.BUSINESS_KPI,
                    category=MetricCategory.BUSINESS,
                    unit="score",
                    source="business_tracker",
                    dimensions={
                        "sample_size": len(satisfaction_scores)
                    }
                )
            
            # Cost savings identified (from recommendations)
            cost_savings = self._recommendations_data.get('cost_savings_total', 0.0)
            await self._safe_record_metric(
                name="business.cost_savings_identified",
                value=cost_savings,
                metric_type=MetricType.BUSINESS_KPI,
                category=MetricCategory.BUSINESS,
                unit="usd",
                source="business_tracker"
            )
            
            # Compliance score
            compliance_score = self._assessments_data.get('avg_compliance_score', 0.0)
            await self._safe_record_metric(
                name="business.compliance_score",
                value=compliance_score,
                metric_type=MetricType.BUSINESS_KPI,
                category=MetricCategory.BUSINESS,
                unit="score",
                source="business_tracker"
            )
            
            logger.debug("Collected business metrics")
            
        except Exception as e:
            logger.error(f"Error collecting business metrics: {e}", exc_info=True)
    
    async def _update_redis_metrics(self) -> None:
        """Update metrics in Redis for distributed access."""
        if not self.redis_client:
            return
        
        try:
            # Get current metrics
            health_status = await self.get_system_health()
            engagement_metrics = await self.get_user_engagement_summary()
            business_metrics = await self.get_business_metrics_summary()
            
            # Store in Redis with expiration
            metrics_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'system_health': asdict(health_status),
                'user_engagement': asdict(engagement_metrics),
                'business_metrics': asdict(business_metrics),
                'real_time_metrics': asdict(self._real_time_metrics)
            }
            
            self.redis_client.setex(
                'infra_mind:metrics:current',
                300,  # 5 minutes expiration
                json.dumps(metrics_data, default=str)
            )
            
            # Store time-series data
            timestamp = int(time.time())
            self.redis_client.zadd(
                'infra_mind:metrics:timeseries',
                {json.dumps(metrics_data, default=str): timestamp}
            )
            
            # Keep only last 24 hours of time-series data
            cutoff = timestamp - (24 * 60 * 60)
            self.redis_client.zremrangebyscore('infra_mind:metrics:timeseries', 0, cutoff)
            
        except Exception as e:
            logger.error(f"Error updating Redis metrics: {e}")
    
    async def _notify_callbacks(self) -> None:
        """Notify registered callbacks with current metrics."""
        if not self._metrics_callbacks:
            return
        
        try:
            metrics_data = {
                'system_health': asdict(await self.get_system_health()),
                'user_engagement': asdict(await self.get_user_engagement_summary()),
                'business_metrics': asdict(await self.get_business_metrics_summary()),
                'real_time_metrics': asdict(self._real_time_metrics),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            for callback in self._metrics_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(metrics_data)
                    else:
                        self._executor.submit(callback, metrics_data)
                except Exception as e:
                    logger.error(f"Metrics callback failed: {e}")
                    
        except Exception as e:
            logger.error(f"Error notifying metrics callbacks: {e}")
    
    async def _update_redis_metrics(self) -> None:
        """Update metrics in Redis for distributed access."""
        if not self.redis_client:
            return
        
        try:
            # Get current metrics
            health_status = await self.get_system_health()
            engagement_metrics = await self.get_user_engagement_summary()
            business_metrics = await self.get_business_metrics_summary()
            
            # Store in Redis with expiration
            metrics_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'system_health': asdict(health_status),
                'user_engagement': asdict(engagement_metrics),
                'business_metrics': asdict(business_metrics),
                'real_time_metrics': asdict(self._real_time_metrics)
            }
            
            self.redis_client.setex(
                'infra_mind:metrics:current',
                300,  # 5 minutes expiration
                json.dumps(metrics_data, default=str)
            )
            
            # Store time-series data
            timestamp = int(time.time())
            self.redis_client.zadd(
                'infra_mind:metrics:timeseries',
                {json.dumps(metrics_data, default=str): timestamp}
            )
            
            # Keep only last 24 hours of time-series data
            cutoff = timestamp - (24 * 60 * 60)
            self.redis_client.zremrangebyscore('infra_mind:metrics:timeseries', 0, cutoff)
            
        except Exception as e:
            logger.error(f"Error updating Redis metrics: {e}")
    
    async def _notify_callbacks(self) -> None:
        """Notify registered callbacks with current metrics."""
        if not self._metrics_callbacks:
            return
        
        try:
            metrics_data = {
                'system_health': asdict(await self.get_system_health()),
                'user_engagement': asdict(await self.get_user_engagement_summary()),
                'business_metrics': asdict(await self.get_business_metrics_summary()),
                'real_time_metrics': asdict(self._real_time_metrics),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            for callback in self._metrics_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(metrics_data)
                    else:
                        self._executor.submit(callback, metrics_data)
                except Exception as e:
                    logger.error(f"Metrics callback failed: {e}")
                    
        except Exception as e:
            logger.error(f"Error notifying metrics callbacks: {e}")
    
    async def _broadcast_real_time_metrics(self) -> None:
        """Broadcast real-time metrics to WebSocket clients."""
        if not self._websocket_clients:
            return
        
        try:
            message = json.dumps({
                'type': 'real_time_metrics',
                'data': asdict(self._real_time_metrics),
                'timestamp': datetime.utcnow().isoformat()
            }, default=str)
            
            # Send to all connected clients
            disconnected_clients = set()
            for client in self._websocket_clients:
                try:
                    await client.send(message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.add(client)
                except Exception as e:
                    logger.error(f"Error sending to WebSocket client: {e}")
                    disconnected_clients.add(client)
            
            # Remove disconnected clients
            self._websocket_clients -= disconnected_clients
            
        except Exception as e:
            logger.error(f"Error broadcasting real-time metrics: {e}")
    
    # API tracking methods
    
    def track_request(self, response_time_ms: float, success: bool = True) -> None:
        """Track API request metrics."""
        with self._metrics_lock:
            self._request_times.append(response_time_ms)
            self._request_count += 1
            self._requests_per_second.append(datetime.utcnow())
            
            if not success:
                self._error_count += 1
    
    def track_user_action(
        self,
        user_id: str,
        action_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track user engagement action."""
        now = datetime.utcnow()
        
        with self._metrics_lock:
            self._active_sessions[user_id] = now
            self._unique_visitors.add(user_id)
            
            action = {
                'user_id': user_id,
                'type': action_type,
                'timestamp': now,
                'metadata': metadata or {}
            }
            self._user_actions.append(action)
            
            # Track specific business actions
            if action_type == 'assessment_started':
                self._assessments_data['total'] += 1
            elif action_type == 'assessment_completed':
                self._assessments_data['completed'] += 1
            elif action_type == 'report_generated':
                self._reports_data['total'] += 1
            elif action_type == 'recommendations_generated':
                self._recommendations_data['total'] += 1
    
    def track_page_view(self, user_id: str, page_path: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Track page view for engagement metrics."""
        now = datetime.utcnow()
        
        with self._metrics_lock:
            self._page_views.append({
                'user_id': user_id,
                'page_path': page_path,
                'timestamp': now,
                'metadata': metadata or {}
            })
            
            self._unique_visitors.add(user_id)
    
    def track_user_feedback(self, user_id: str, score: float, feedback_type: str, 
                           comments: Optional[str] = None) -> None:
        """Track user feedback for satisfaction metrics."""
        now = datetime.utcnow()
        
        with self._metrics_lock:
            self._user_feedback.append({
                'user_id': user_id,
                'score': score,
                'feedback_type': feedback_type,
                'comments': comments,
                'timestamp': now
            })
    
    def track_business_impact(self, impact_type: str, value: float, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Track business impact metrics."""
        with self._metrics_lock:
            if impact_type == 'cost_savings':
                self._recommendations_data['cost_savings_total'] += value
            elif impact_type == 'compliance_score':
                # Update running average
                current_total = self._assessments_data.get('compliance_score_total', 0.0)
                current_count = self._assessments_data.get('compliance_score_count', 0)
                
                self._assessments_data['compliance_score_total'] = current_total + value
                self._assessments_data['compliance_score_count'] = current_count + 1
                self._assessments_data['avg_compliance_score'] = (
                    self._assessments_data['compliance_score_total'] / 
                    self._assessments_data['compliance_score_count']
                )
    
    def add_metrics_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Add callback for metrics updates."""
        self._metrics_callbacks.append(callback)
    
    def add_websocket_client(self, websocket) -> None:
        """Add WebSocket client for real-time updates."""
        self._websocket_clients.add(websocket)
    
    def remove_websocket_client(self, websocket) -> None:
        """Remove WebSocket client."""
        self._websocket_clients.discard(websocket)
    
    async def record_agent_performance(
        self,
        agent_name: str,
        execution_time: float,
        success: bool,
        confidence_score: Optional[float] = None,
        recommendations_count: int = 0,
        assessment_id: Optional[str] = None
    ) -> None:
        """Record agent performance metrics."""
        try:
            # Create agent metrics record
            agent_metrics = await AgentMetrics.create_for_agent(
                agent_name=agent_name,
                agent_version="1.0.0",  # TODO: Get from agent
                started_at=datetime.utcnow() - timedelta(seconds=execution_time),
                assessment_id=assessment_id
            )
            
            # Update performance data
            agent_metrics.update_performance(
                execution_time=execution_time,
                api_calls=1  # Basic tracking
            )
            
            if confidence_score is not None:
                agent_metrics.update_quality(confidence_score=confidence_score)
            
            agent_metrics.update_output(recommendations=recommendations_count)
            
            if not success:
                agent_metrics.record_error()
            
            await agent_metrics.save()
            
            # Also record as general metrics
            await Metric.record_metric(
                name=f"agent.{agent_name}.execution_time",
                value=execution_time,
                metric_type=MetricType.AGENT_PERFORMANCE,
                category=MetricCategory.TECHNICAL,
                unit="seconds",
                source=f"agent_{agent_name}",
                dimensions={
                    "success": success,
                    "recommendations_count": recommendations_count
                }
            )
            
            if confidence_score is not None:
                await Metric.record_metric(
                    name=f"agent.{agent_name}.confidence_score",
                    value=confidence_score,
                    metric_type=MetricType.AGENT_PERFORMANCE,
                    category=MetricCategory.BUSINESS,
                    unit="score",
                    source=f"agent_{agent_name}"
                )
            
        except Exception as e:
            logger.error(f"Error recording agent performance: {e}")
    
    async def record_error(self, error_type: str, error_category: str, severity: str,
                          component: str, agent_name: Optional[str] = None,
                          workflow_id: Optional[str] = None, is_recoverable: bool = True) -> None:
        """Record error metrics."""
        try:
            await Metric.record_metric(
                name="system.error_event",
                value=1.0,
                metric_type=MetricType.ERROR_TRACKING,
                category=MetricCategory.OPERATIONAL,
                unit="count",
                source="error_handler",
                dimensions={
                    "error_type": error_type,
                    "error_category": error_category,
                    "severity": severity,
                    "component": component,
                    "agent_name": agent_name,
                    "workflow_id": workflow_id,
                    "is_recoverable": is_recoverable
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to record error metric: {str(e)}")
    
    async def record_alert(self, alert_id: str, rule_name: str, level: str,
                          metric_value: float, threshold: float) -> None:
        """Record alert metrics."""
        try:
            await Metric.record_metric(
                name="system.alert",
                value=1.0,
                metric_type=MetricType.ERROR_TRACKING,
                category=MetricCategory.OPERATIONAL,
                unit="count",
                source="alert_manager",
                dimensions={
                    "alert_id": alert_id,
                    "rule_name": rule_name,
                    "level": level,
                    "metric_value": metric_value,
                    "threshold": threshold
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to record alert metric: {str(e)}")
    
    async def record_monitoring_metric(self, metric_name: str, value: float, unit: str) -> None:
        """Record monitoring metrics."""
        try:
            await Metric.record_metric(
                name=f"monitoring.{metric_name}",
                value=value,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.OPERATIONAL,
                unit=unit,
                source="error_monitor"
            )
            
        except Exception as e:
            logger.error(f"Failed to record monitoring metric: {str(e)}")
    
    async def get_error_metrics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get error metrics for the specified time window."""
        try:
            # This would query the actual metrics storage
            # For now, return basic data based on tracked errors
            return {
                "total_errors": self._error_count,
                "error_rate": (self._error_count / max(self._request_count, 1)) * 100,
                "recovery_rate": 1.0,  # Would be calculated from actual recovery data
                "error_categories": {},
                "time_window_hours": time_window_hours
            }
        except Exception as e:
            logger.error(f"Failed to get error metrics: {str(e)}")
            return {}
    
    async def get_system_health(self) -> SystemHealthStatus:
        """Get current system health status."""
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            connections = len(psutil.net_connections())
            
            # Calculate response time
            avg_response_time = 0.0
            if self._request_times:
                avg_response_time = sum(self._request_times[-10:]) / min(len(self._request_times), 10)
            
            # Calculate error rate
            error_rate = 0.0
            if self._request_count > 0:
                error_rate = (self._error_count / self._request_count) * 100
            
            # Determine status
            status = "healthy"
            if cpu_usage > 80 or memory.percent > 85 or error_rate > 5:
                status = "critical"
            elif cpu_usage > 60 or memory.percent > 70 or error_rate > 1:
                status = "warning"
            
            return SystemHealthStatus(
                cpu_usage_percent=cpu_usage,
                memory_usage_percent=memory.percent,
                disk_usage_percent=(disk.used / disk.total) * 100,
                active_connections=connections,
                response_time_ms=avg_response_time,
                error_rate_percent=error_rate,
                uptime_seconds=(datetime.utcnow() - self.start_time).total_seconds(),
                status=status
            )
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return SystemHealthStatus(
                cpu_usage_percent=0,
                memory_usage_percent=0,
                disk_usage_percent=0,
                active_connections=0,
                response_time_ms=0,
                error_rate_percent=100,
                uptime_seconds=0,
                status="critical"
            )
    
    async def get_user_engagement_summary(self) -> UserEngagementMetrics:
        """Get enhanced user engagement metrics summary."""
        cache_key = 'user_engagement_summary'
        if self._is_cache_valid(cache_key):
            return self._metrics_cache[cache_key]
        
        try:
            now = datetime.utcnow()
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)
            
            with self._metrics_lock:
                # Count active sessions
                active_users = sum(
                    1 for last_activity in self._active_sessions.values()
                    if (now - last_activity).total_seconds() < 1800
                )
                
                # Count new users (users who first appeared in last 24 hours)
                new_users = len([
                    user_id for user_id, first_seen in self._active_sessions.items()
                    if first_seen > day_ago
                ])
                
                # Count recent actions
                recent_actions = [
                    action for action in self._user_actions
                    if action.get('timestamp', now) > hour_ago
                ]
                
                # Count specific action types
                assessments_started = sum(
                    1 for action in recent_actions
                    if action.get('type') == 'assessment_started'
                )
                
                assessments_completed = sum(
                    1 for action in recent_actions
                    if action.get('type') == 'assessment_completed'
                )
                
                reports_generated = sum(
                    1 for action in recent_actions
                    if action.get('type') == 'report_generated'
                )
                
                # Count page views
                recent_page_views = [
                    view for view in self._page_views
                    if view.get('timestamp', now) > hour_ago
                ]
                
                # Calculate conversion rate
                conversion_rate = (assessments_completed / max(assessments_started, 1)) * 100
                
                # Calculate bounce rate (simplified)
                single_page_sessions = sum(
                    1 for user_id in self._active_sessions.keys()
                    if len([view for view in self._page_views if view.get('user_id') == user_id]) == 1
                )
                bounce_rate = (single_page_sessions / max(len(self._active_sessions), 1)) * 100
                
                # Calculate average session duration
                session_durations = []
                for user_id, last_activity in self._active_sessions.items():
                    user_views = [
                        view for view in self._page_views
                        if view.get('user_id') == user_id
                    ]
                    if len(user_views) > 1:
                        first_view = min(user_views, key=lambda x: x.get('timestamp', now))
                        duration = (last_activity - first_view.get('timestamp', now)).total_seconds() / 60
                        session_durations.append(max(duration, 0))
                
                avg_session_duration = sum(session_durations) / len(session_durations) if session_durations else 0
                
                result = UserEngagementMetrics(
                    active_users_count=active_users,
                    new_users_count=new_users,
                    assessments_started=assessments_started,
                    assessments_completed=assessments_completed,
                    reports_generated=reports_generated,
                    average_session_duration_minutes=avg_session_duration,
                    bounce_rate_percent=bounce_rate,
                    page_views=len(recent_page_views),
                    unique_visitors=len(self._unique_visitors),
                    conversion_rate=conversion_rate
                )
                
                # Cache result
                self._metrics_cache[cache_key] = result
                self._cache_timestamps[cache_key] = now
                
                return result
            
        except Exception as e:
            logger.error(f"Error getting user engagement summary: {e}")
            return UserEngagementMetrics(
                active_users_count=0,
                new_users_count=0,
                assessments_started=0,
                assessments_completed=0,
                reports_generated=0,
                average_session_duration_minutes=0,
                bounce_rate_percent=0,
                page_views=0,
                unique_visitors=0,
                conversion_rate=0
            )
    
    async def get_business_metrics_summary(self) -> BusinessMetrics:
        """Get business metrics summary."""
        cache_key = 'business_metrics_summary'
        if self._is_cache_valid(cache_key):
            return self._metrics_cache[cache_key]
        
        try:
            now = datetime.utcnow()
            
            with self._metrics_lock:
                # Calculate user satisfaction score
                recent_feedback = [
                    feedback for feedback in self._user_feedback
                    if feedback.get('timestamp', now) > now - timedelta(days=30)
                ]
                avg_satisfaction = (
                    sum(f.get('score', 0) for f in recent_feedback) / len(recent_feedback)
                    if recent_feedback else 0.0
                )
                
                # Calculate agent efficiency (simplified)
                total_actions = len(self._user_actions)
                successful_actions = len([
                    action for action in self._user_actions
                    if action.get('metadata', {}).get('success', True)
                ])
                agent_efficiency = (successful_actions / max(total_actions, 1)) * 100
                
                result = BusinessMetrics(
                    total_assessments=self._assessments_data.get('total', 0),
                    completed_assessments=self._assessments_data.get('completed', 0),
                    total_reports=self._reports_data.get('total', 0),
                    total_recommendations=self._recommendations_data.get('total', 0),
                    user_satisfaction_score=avg_satisfaction,
                    revenue_impact=0.0,  # TODO: Implement revenue tracking
                    cost_savings_identified=self._recommendations_data.get('cost_savings_total', 0.0),
                    compliance_score=self._assessments_data.get('avg_compliance_score', 0.0),
                    agent_efficiency_score=agent_efficiency
                )
                
                # Cache result
                self._metrics_cache[cache_key] = result
                self._cache_timestamps[cache_key] = now
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting business metrics summary: {e}")
            return BusinessMetrics(
                total_assessments=0,
                completed_assessments=0,
                total_reports=0,
                total_recommendations=0,
                user_satisfaction_score=0.0,
                revenue_impact=0.0,
                cost_savings_identified=0.0,
                compliance_score=0.0,
                agent_efficiency_score=0.0
            )
    
    def get_real_time_metrics(self) -> RealTimeMetrics:
        """Get current real-time metrics."""
        with self._metrics_lock:
            return self._real_time_metrics
    
    async def get_system_health(self) -> SystemHealthStatus:
        """Get current system health status."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Handle network connections with permission issues
            try:
                connections = len(psutil.net_connections())
            except (psutil.AccessDenied, PermissionError):
                # On macOS, this requires elevated permissions
                connections = 0
                logger.debug("Network connections unavailable due to permissions")
            
            # Calculate uptime
            uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
            
            # Calculate error rate
            error_rate = 0.0
            if self._request_count > 0:
                error_rate = (self._error_count / self._request_count) * 100
            
            # Calculate average response time
            avg_response_time = 0.0
            if self._request_times:
                avg_response_time = sum(self._request_times) / len(self._request_times)
            
            # Determine health status
            status = "healthy"
            if cpu_percent > 80 or memory.percent > 85 or error_rate > 5:
                status = "critical"
            elif cpu_percent > 60 or memory.percent > 70 or error_rate > 1:
                status = "warning"
            
            return SystemHealthStatus(
                cpu_usage_percent=cpu_percent,
                memory_usage_percent=memory.percent,
                disk_usage_percent=(disk.used / disk.total) * 100,
                active_connections=connections,
                response_time_ms=avg_response_time,
                error_rate_percent=error_rate,
                uptime_seconds=uptime_seconds,
                status=status
            )
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}", exc_info=True)
            return SystemHealthStatus(
                cpu_usage_percent=0.0,
                memory_usage_percent=0.0,
                disk_usage_percent=0.0,
                active_connections=0,
                response_time_ms=0.0,
                error_rate_percent=0.0,
                uptime_seconds=0.0,
                status="error"
            )
    
    async def get_system_health(self) -> SystemHealthStatus:
        """Get current system health status."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Handle network connections with permission issues
            try:
                connections = len(psutil.net_connections())
            except (psutil.AccessDenied, PermissionError):
                # On macOS, this requires elevated permissions
                connections = 0
                logger.debug("Network connections unavailable due to permissions")
            
            # Calculate uptime
            uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
            
            # Calculate error rate
            error_rate = 0.0
            if self._request_count > 0:
                error_rate = (self._error_count / self._request_count) * 100
            
            # Calculate average response time
            avg_response_time = 0.0
            if self._request_times:
                avg_response_time = sum(self._request_times) / len(self._request_times)
            
            # Determine health status
            status = "healthy"
            if cpu_percent > 80 or memory.percent > 85 or error_rate > 5:
                status = "critical"
            elif cpu_percent > 60 or memory.percent > 70 or error_rate > 1:
                status = "warning"
            
            return SystemHealthStatus(
                cpu_usage_percent=cpu_percent,
                memory_usage_percent=memory.percent,
                disk_usage_percent=(disk.used / disk.total) * 100,
                active_connections=connections,
                response_time_ms=avg_response_time,
                error_rate_percent=error_rate,
                uptime_seconds=uptime_seconds,
                status=status
            )
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            logger.error(f"Error getting system health: {e}", exc_info=True)
            return SystemHealthStatus(
                cpu_usage_percent=0.0,
                memory_usage_percent=0.0,
                disk_usage_percent=0.0,
                active_connections=0,
                response_time_ms=0.0,
                error_rate_percent=0.0,
                uptime_seconds=0.0,
                status="error"
            )
    
    async def get_user_engagement_summary(self) -> UserEngagementMetrics:
        """Get user engagement metrics summary."""
        try:
            now = datetime.utcnow()
            hour_ago = now - timedelta(hours=1)
            
            # Active sessions count
            active_sessions = sum(
                1 for last_activity in self._active_sessions.values()
                if (now - last_activity).total_seconds() < 1800  # 30 minutes
            )
            
            # Recent actions
            recent_actions = [
                action for action in self._user_actions
                if action.get('timestamp', now) > hour_ago
            ]
            
            # Count action types
            assessments_started = len([a for a in recent_actions if a.get('type') == 'assessment_started'])
            assessments_completed = len([a for a in recent_actions if a.get('type') == 'assessment_completed'])
            reports_generated = len([a for a in recent_actions if a.get('type') == 'report_generated'])
            
            # Calculate conversion rate
            conversion_rate = (assessments_completed / max(assessments_started, 1)) * 100
            
            # Calculate average session duration (simplified)
            avg_session_duration = 15.0  # Placeholder - would need proper session tracking
            
            # Calculate bounce rate (simplified)
            bounce_rate = 25.0  # Placeholder
            
            return UserEngagementMetrics(
                active_users_count=active_sessions,
                new_users_count=len(self._unique_visitors),  # Simplified
                assessments_started=assessments_started,
                assessments_completed=assessments_completed,
                reports_generated=reports_generated,
                average_session_duration_minutes=avg_session_duration,
                bounce_rate_percent=bounce_rate,
                page_views=len(self._page_views),
                unique_visitors=len(self._unique_visitors),
                conversion_rate=conversion_rate
            )
            
        except Exception as e:
            logger.error(f"Error getting user engagement summary: {e}")
            return UserEngagementMetrics(
                active_users_count=0,
                new_users_count=0,
                assessments_started=0,
                assessments_completed=0,
                reports_generated=0,
                average_session_duration_minutes=0.0,
                bounce_rate_percent=0.0,
                page_views=0,
                unique_visitors=0,
                conversion_rate=0.0
            )
    
    async def get_business_metrics_summary(self) -> BusinessMetrics:
        """Get business metrics summary."""
        try:
            # Calculate user satisfaction score
            satisfaction_score = 0.0
            if self._user_feedback:
                scores = [f.get('score', 0) for f in self._user_feedback]
                satisfaction_score = sum(scores) / len(scores) if scores else 0.0
            
            # Calculate agent efficiency (simplified)
            agent_efficiency = 85.0  # Placeholder
            
            return BusinessMetrics(
                total_assessments=self._assessments_data.get('total', 0),
                completed_assessments=self._assessments_data.get('completed', 0),
                total_reports=self._reports_data.get('total', 0),
                total_recommendations=self._recommendations_data.get('total', 0),
                user_satisfaction_score=satisfaction_score,
                revenue_impact=0.0,  # Placeholder
                cost_savings_identified=self._recommendations_data.get('cost_savings_total', 0.0),
                compliance_score=self._assessments_data.get('avg_compliance_score', 0.0),
                agent_efficiency_score=agent_efficiency
            )
            
        except Exception as e:
            logger.error(f"Error getting business metrics summary: {e}")
            return BusinessMetrics(
                total_assessments=0,
                completed_assessments=0,
                total_reports=0,
                total_recommendations=0,
                user_satisfaction_score=0.0,
                revenue_impact=0.0,
                cost_savings_identified=0.0,
                compliance_score=0.0,
                agent_efficiency_score=0.0
            )
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached result is still valid."""
        if cache_key not in self._metrics_cache:
            return False
        
        cache_time = self._cache_timestamps.get(cache_key)
        if not cache_time:
            return False
        
        return (datetime.utcnow() - cache_time).total_seconds() < self._cache_ttl
    
    async def get_metrics_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive metrics data for dashboard."""
        try:
            return {
                'system_health': asdict(await self.get_system_health()),
                'user_engagement': asdict(await self.get_user_engagement_summary()),
                'business_metrics': asdict(await self.get_business_metrics_summary()),
                'real_time_metrics': asdict(self.get_real_time_metrics()),
                'timestamp': datetime.utcnow().isoformat(),
                'collection_status': {
                    'is_collecting': self.is_collecting,
                    'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
                    'redis_connected': self.redis_client is not None,
                    'active_callbacks': len(self._metrics_callbacks),
                    'websocket_clients': len(self._websocket_clients)
                }
            }
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @asynccontextmanager
    async def track_operation(self, operation_name: str):
        """Context manager to track operation performance."""
        start_time = time.time()
        success = True
        
        try:
            yield
        except Exception as e:
            success = False
            logger.error(f"Operation {operation_name} failed: {e}")
            raise
        finally:
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            self.track_request(execution_time, success)
            
            # Record operation-specific metric
            await self._safe_record_metric(
                name=f"operation.{operation_name}.duration",
                value=execution_time,
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                category=MetricCategory.TECHNICAL,
                unit="ms",
                source="operation_tracker",
                dimensions={"success": success}
            )
    
    async def _broadcast_real_time_metrics(self) -> None:
        """Broadcast real-time metrics to WebSocket clients."""
        if not self._websocket_clients:
            return
        
        try:
            message = json.dumps({
                'type': 'real_time_metrics',
                'data': asdict(self._real_time_metrics),
                'timestamp': datetime.utcnow().isoformat()
            }, default=str)
            
            # Send to all connected clients
            disconnected_clients = set()
            for client in self._websocket_clients:
                try:
                    await client.send(message)
                except Exception as e:
                    logger.error(f"Error sending to WebSocket client: {e}")
                    disconnected_clients.add(client)
            
            # Remove disconnected clients
            self._websocket_clients -= disconnected_clients
            
        except Exception as e:
            logger.error(f"Error broadcasting real-time metrics: {e}")


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


async def initialize_metrics_collection() -> None:
    """Initialize and start metrics collection."""
    collector = get_metrics_collector()
    await collector.start_collection()
    logger.info("Metrics collection initialized")


async def shutdown_metrics_collection() -> None:
    """Shutdown metrics collection."""
    collector = get_metrics_collector()
    await collector.stop_collection()
    logger.info("Metrics collection shutdown")