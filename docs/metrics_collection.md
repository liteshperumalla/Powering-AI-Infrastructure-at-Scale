# Metrics Collection System

This document describes the metrics collection system implemented for the Infra Mind platform as part of task 12.1.

## Overview

The metrics collection system provides comprehensive monitoring of system performance, user engagement, and system health. It is designed to be lightweight, scalable, and integrated with all major components of the platform.

## Key Features

### System Performance Monitoring

- **CPU Usage**: Tracks CPU utilization percentage
- **Memory Usage**: Monitors memory consumption and availability
- **Disk Usage**: Tracks disk space utilization
- **Network Connections**: Monitors active network connections
- **Process Metrics**: Tracks application process resource usage
- **Response Times**: Measures API response times and latency

### User Engagement Tracking

- **Active Sessions**: Tracks number of active user sessions
- **User Actions**: Records user interactions with the platform
- **Assessment Metrics**: Monitors assessment starts and completions
- **Report Generation**: Tracks report generation and downloads
- **Session Duration**: Measures average user session duration
- **Action Patterns**: Analyzes user behavior patterns

### System Health Monitoring

- **Health Status**: Overall system health status (healthy, warning, critical)
- **Error Rates**: Tracks API and processing error rates
- **Uptime Tracking**: Monitors system uptime and availability
- **Health Scores**: Calculates composite health scores based on multiple metrics
- **Service Status**: Monitors status of dependent services (database, cache, etc.)

## Architecture

The metrics collection system consists of the following components:

1. **MetricsCollector**: Core service that collects and manages metrics
2. **Metric Models**: MongoDB document models for storing metrics data
3. **Middleware Components**: FastAPI middleware for automatic request tracking
4. **Agent Integration**: Performance tracking in the agent framework
5. **Health Endpoints**: API endpoints for system health monitoring

## Usage

### Automatic Collection

Metrics are automatically collected through:

- FastAPI middleware for all API requests
- Agent execution monitoring
- Periodic system metrics collection (every 60 seconds)

### Manual Tracking

```python
# Get metrics collector
from infra_mind.core.metrics_collector import get_metrics_collector
collector = get_metrics_collector()

# Track API request
collector.track_request(response_time_ms=150.5, success=True)

# Track user action
collector.track_user_action(
    user_id="user123",
    action_type="assessment_started",
    metadata={"source": "web"}
)

# Track operation with context manager
async with collector.track_operation("database_query"):
    # Operation code here
    result = await db.find_one({"id": "123"})

# Record agent performance
await collector.record_agent_performance(
    agent_name="cto_agent",
    execution_time=2.5,
    success=True,
    confidence_score=0.85,
    recommendations_count=3,
    assessment_id="assessment123"
)
```

### Health Monitoring

```python
# Get system health status
health = await collector.get_system_health()
print(f"System status: {health.status}")
print(f"CPU usage: {health.cpu_usage_percent}%")
print(f"Memory usage: {health.memory_usage_percent}%")

# Get user engagement metrics
engagement = await collector.get_user_engagement_summary()
print(f"Active users: {engagement.active_users_count}")
print(f"Assessments started: {engagement.assessments_started}")
```

## API Endpoints

The system provides the following API endpoints:

- **/health**: Returns current system health status
- **/metrics**: Returns comprehensive metrics data

## Integration Points

The metrics collection system integrates with:

- **FastAPI Application**: Through middleware components
- **Agent Framework**: Through the BaseAgent class
- **MongoDB**: For metrics storage and retrieval
- **Frontend**: Through health and metrics endpoints

## Future Enhancements

Potential future enhancements include:

- Real-time metrics dashboard
- Advanced analytics and trend analysis
- Alerting system for critical metrics
- Custom metric definitions
- Metrics visualization components

## Implementation Details

The metrics collection system is implemented in the following files:

- `src/infra_mind/core/metrics_collector.py`: Core metrics collection service
- `src/infra_mind/models/metrics.py`: Metrics data models
- `src/infra_mind/core/metrics_middleware.py`: FastAPI middleware components
- `api/app.py`: API integration
- `src/infra_mind/agents/base.py`: Agent framework integration