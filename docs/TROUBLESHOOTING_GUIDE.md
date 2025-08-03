# Troubleshooting Guide

## Overview

This guide provides detailed troubleshooting procedures for common issues in the Infra Mind production environment. Each section includes symptoms, diagnostic steps, and resolution procedures.

## Table of Contents

1. [API and Application Issues](#api-and-application-issues)
2. [Database Problems](#database-problems)
3. [Agent Orchestration Issues](#agent-orchestration-issues)
4. [External API Integration Problems](#external-api-integration-problems)
5. [Authentication and Security Issues](#authentication-and-security-issues)
6. [Performance Problems](#performance-problems)
7. [Frontend Issues](#frontend-issues)
8. [Infrastructure Problems](#infrastructure-problems)
9. [Monitoring and Logging Issues](#monitoring-and-logging-issues)
10. [Emergency Procedures](#emergency-procedures)

## API and Application Issues

### Issue: High API Response Times

**Symptoms:**
- API responses taking > 5 seconds
- Timeout errors in frontend
- User complaints about slow performance
- High CPU/memory usage on API pods

**Diagnostic Steps:**
```bash
# Check API response times
curl -w "@curl-format.txt" -o /dev/null -s "http://api.infra-mind.com/health"

# Check API pod status
kubectl get pods -n infra-mind-prod -l app=infra-mind-api

# Check resource usage
kubectl top pods -n infra-mind-prod

# Check API logs for errors
kubectl logs -f deployment/infra-mind-api -n infra-mind-prod --tail=100

# Check database connection pool
python scripts/check_db_connections.py

# Check Redis performance
redis-cli --latency-history -i 1
```

**Resolution Steps:**
1. **Scale API instances:**
   ```bash
   kubectl scale deployment infra-mind-api --replicas=5 -n infra-mind-prod
   ```

2. **Check and optimize database queries:**
   ```bash
   # Check slow queries
   mongo --eval "db.setProfilingLevel(2, {slowms: 1000})"
   mongo --eval "db.system.profile.find().sort({ts: -1}).limit(5)"
   ```

3. **Clear Redis cache if needed:**
   ```bash
   redis-cli FLUSHDB
   python scripts/warm_cache.py
   ```

4. **Restart API pods if memory leak suspected:**
   ```bash
   kubectl rollout restart deployment/infra-mind-api -n infra-mind-prod
   ```

### Issue: API Returning 500 Errors

**Symptoms:**
- Internal server errors in API responses
- Error rate > 1% in monitoring
- Failed requests in application logs

**Diagnostic Steps:**
```bash
# Check API logs for stack traces
kubectl logs deployment/infra-mind-api -n infra-mind-prod | grep -A 10 "ERROR"

# Check database connectivity
python scripts/test_db_connection.py

# Check external API status
python scripts/check_external_apis.py

# Check configuration
python scripts/validate-config.py
```

**Resolution Steps:**
1. **Check database connection:**
   ```bash
   # Test MongoDB connection
   mongo --eval "db.runCommand({ping: 1})"
   
   # Test Redis connection
   redis-cli ping
   ```

2. **Verify environment variables:**
   ```bash
   kubectl get secret infra-mind-secrets -n infra-mind-prod -o yaml
   ```

3. **Check external API credentials:**
   ```bash
   # Test AWS credentials
   aws sts get-caller-identity
   
   # Test Azure credentials
   az account show
   
   # Test GCP credentials
   gcloud auth list
   ```

4. **Restart services if needed:**
   ```bash
   kubectl rollout restart deployment/infra-mind-api -n infra-mind-prod
   ```

### Issue: Memory Leaks in API

**Symptoms:**
- Gradually increasing memory usage
- Out of memory errors
- Pod restarts due to memory limits

**Diagnostic Steps:**
```bash
# Monitor memory usage over time
kubectl top pods -n infra-mind-prod --sort-by=memory

# Check memory limits
kubectl describe pod <pod-name> -n infra-mind-prod

# Profile memory usage
python scripts/memory_profiler.py
```

**Resolution Steps:**
1. **Increase memory limits temporarily:**
   ```bash
   kubectl patch deployment infra-mind-api -n infra-mind-prod -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","resources":{"limits":{"memory":"4Gi"}}}]}}}}'
   ```

2. **Identify memory leaks:**
   ```bash
   # Use memory profiling tools
   pip install memory-profiler
   python -m memory_profiler scripts/profile_api.py
   ```

3. **Implement fixes and redeploy:**
   ```bash
   # After fixing code
   ./scripts/build-production.sh
   ./scripts/deploy-k8s.sh production
   ```

## Database Problems

### Issue: MongoDB Connection Failures

**Symptoms:**
- "Connection refused" errors
- Database timeout errors
- Unable to read/write data

**Diagnostic Steps:**
```bash
# Check MongoDB pod status
kubectl get pods -n infra-mind-prod -l app=mongodb

# Check MongoDB logs
kubectl logs mongodb-0 -n infra-mind-prod

# Test connection from API pod
kubectl exec -it deployment/infra-mind-api -n infra-mind-prod -- python -c "
import pymongo
client = pymongo.MongoClient('mongodb://mongodb:27017/')
print(client.admin.command('ping'))
"

# Check replica set status
kubectl exec -it mongodb-0 -n infra-mind-prod -- mongo --eval "rs.status()"
```

**Resolution Steps:**
1. **Restart MongoDB pods:**
   ```bash
   kubectl rollout restart statefulset/mongodb -n infra-mind-prod
   ```

2. **Check disk space:**
   ```bash
   kubectl exec -it mongodb-0 -n infra-mind-prod -- df -h
   ```

3. **Repair replica set if needed:**
   ```bash
   kubectl exec -it mongodb-0 -n infra-mind-prod -- mongo --eval "
   rs.initiate({
     _id: 'rs0',
     members: [
       {_id: 0, host: 'mongodb-0.mongodb:27017'},
       {_id: 1, host: 'mongodb-1.mongodb:27017'},
       {_id: 2, host: 'mongodb-2.mongodb:27017'}
     ]
   })
   "
   ```

### Issue: Slow Database Queries

**Symptoms:**
- Database queries taking > 5 seconds
- High CPU usage on MongoDB pods
- Query timeout errors

**Diagnostic Steps:**
```bash
# Enable profiling
kubectl exec -it mongodb-0 -n infra-mind-prod -- mongo --eval "
db.setProfilingLevel(2, {slowms: 1000})
"

# Check slow queries
kubectl exec -it mongodb-0 -n infra-mind-prod -- mongo --eval "
db.system.profile.find().sort({ts: -1}).limit(10).pretty()
"

# Check indexes
kubectl exec -it mongodb-0 -n infra-mind-prod -- mongo --eval "
db.assessments.getIndexes()
"
```

**Resolution Steps:**
1. **Create missing indexes:**
   ```bash
   kubectl exec -it mongodb-0 -n infra-mind-prod -- mongo --eval "
   db.assessments.createIndex({user_id: 1, created_at: -1})
   db.reports.createIndex({assessment_id: 1})
   db.users.createIndex({email: 1}, {unique: true})
   "
   ```

2. **Optimize queries in application code:**
   - Review N+1 query patterns
   - Use aggregation pipelines
   - Implement proper pagination

3. **Scale MongoDB if needed:**
   ```bash
   # Add more replica set members
   kubectl scale statefulset mongodb --replicas=5 -n infra-mind-prod
   ```

### Issue: Redis Cache Problems

**Symptoms:**
- Cache miss rate > 50%
- Redis connection errors
- Slow cache operations

**Diagnostic Steps:**
```bash
# Check Redis status
kubectl get pods -n infra-mind-prod -l app=redis

# Check Redis info
kubectl exec -it redis-0 -n infra-mind-prod -- redis-cli info

# Check cache hit rate
kubectl exec -it redis-0 -n infra-mind-prod -- redis-cli info stats | grep hit

# Test Redis performance
kubectl exec -it redis-0 -n infra-mind-prod -- redis-cli --latency-history
```

**Resolution Steps:**
1. **Restart Redis cluster:**
   ```bash
   kubectl rollout restart statefulset/redis -n infra-mind-prod
   ```

2. **Clear and warm cache:**
   ```bash
   kubectl exec -it redis-0 -n infra-mind-prod -- redis-cli FLUSHALL
   python scripts/warm_cache.py
   ```

3. **Optimize cache configuration:**
   ```bash
   # Update Redis configuration
   kubectl exec -it redis-0 -n infra-mind-prod -- redis-cli CONFIG SET maxmemory-policy allkeys-lru
   ```

## Agent Orchestration Issues

### Issue: Agents Not Executing

**Symptoms:**
- Assessments stuck in "processing" state
- No agent activity in logs
- Workflow timeouts

**Diagnostic Steps:**
```bash
# Check agent orchestrator status
python scripts/check_agent_status.py

# Check LangGraph state
python scripts/check_langgraph_state.py

# Check agent logs
kubectl logs deployment/infra-mind-api -n infra-mind-prod | grep -i agent

# Check workflow state in database
mongo --eval "db.workflow_states.find({status: 'running'}).count()"
```

**Resolution Steps:**
1. **Restart agent orchestrator:**
   ```bash
   kubectl rollout restart deployment/infra-mind-api -n infra-mind-prod
   ```

2. **Clear stuck workflows:**
   ```bash
   python scripts/clear_stuck_workflows.py
   ```

3. **Reset agent state:**
   ```bash
   python scripts/reset_agent_state.py
   ```

### Issue: Agent Execution Timeouts

**Symptoms:**
- Agents timing out during execution
- Incomplete assessments
- Timeout errors in logs

**Diagnostic Steps:**
```bash
# Check agent execution times
python scripts/analyze_agent_performance.py

# Check external API response times
python scripts/check_api_latency.py

# Check resource limits
kubectl describe pod <api-pod> -n infra-mind-prod
```

**Resolution Steps:**
1. **Increase timeout values:**
   ```yaml
   # Update agent configuration
   agent_config:
     timeout: 300  # 5 minutes
     retry_attempts: 3
   ```

2. **Optimize agent code:**
   - Implement async operations
   - Add progress checkpoints
   - Optimize LLM calls

3. **Scale resources:**
   ```bash
   kubectl patch deployment infra-mind-api -n infra-mind-prod -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","resources":{"limits":{"cpu":"2000m","memory":"4Gi"}}}]}}}}'
   ```

## External API Integration Problems

### Issue: Cloud Provider API Rate Limiting

**Symptoms:**
- "Rate limit exceeded" errors
- Failed cloud API calls
- Incomplete pricing data

**Diagnostic Steps:**
```bash
# Check API call rates
python scripts/check_api_rates.py

# Check rate limit headers
curl -I -H "Authorization: Bearer $AWS_TOKEN" https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/index.json

# Check API usage metrics
python scripts/analyze_api_usage.py
```

**Resolution Steps:**
1. **Implement exponential backoff:**
   ```python
   # Update retry logic in cloud providers
   @retry(
       stop=stop_after_attempt(5),
       wait=wait_exponential(multiplier=1, min=4, max=60)
   )
   def api_call():
       # API call implementation
   ```

2. **Distribute API calls:**
   ```bash
   # Use multiple API keys/accounts
   export AWS_ACCESS_KEY_ID_2=$AWS_ACCESS_KEY_ID_2
   export AWS_SECRET_ACCESS_KEY_2=$AWS_SECRET_ACCESS_KEY_2
   ```

3. **Increase cache duration:**
   ```python
   # Update cache TTL
   CACHE_TTL = {
       'pricing_data': 3600,  # 1 hour
       'service_catalog': 7200,  # 2 hours
   }
   ```

### Issue: LLM API Failures

**Symptoms:**
- LLM API timeout errors
- Invalid responses from LLM
- High LLM costs

**Diagnostic Steps:**
```bash
# Check LLM API status
python scripts/check_llm_status.py

# Check token usage
python scripts/analyze_token_usage.py

# Test LLM providers
python scripts/test_llm_providers.py
```

**Resolution Steps:**
1. **Switch to backup LLM provider:**
   ```python
   # Update LLM configuration
   LLM_CONFIG = {
       'primary': 'openai',
       'fallback': 'anthropic',
       'fallback_threshold': 3  # failures before switching
   }
   ```

2. **Optimize prompts:**
   ```python
   # Reduce token usage
   def optimize_prompt(prompt):
       # Remove unnecessary context
       # Use more concise language
       return optimized_prompt
   ```

3. **Implement response caching:**
   ```python
   # Cache similar LLM responses
   @cache_llm_response(ttl=3600)
   def generate_response(prompt, context):
       return llm.generate(prompt, context)
   ```

## Authentication and Security Issues

### Issue: JWT Token Problems

**Symptoms:**
- Users unable to authenticate
- "Invalid token" errors
- Frequent re-authentication required

**Diagnostic Steps:**
```bash
# Check JWT secret
kubectl get secret infra-mind-secrets -n infra-mind-prod -o jsonpath='{.data.JWT_SECRET_KEY}' | base64 -d

# Test token generation
python scripts/test_jwt_tokens.py

# Check token expiration
python scripts/analyze_token_expiry.py
```

**Resolution Steps:**
1. **Regenerate JWT secret:**
   ```bash
   # Generate new secret
   NEW_SECRET=$(openssl rand -base64 32)
   kubectl patch secret infra-mind-secrets -n infra-mind-prod -p '{"data":{"JWT_SECRET_KEY":"'$(echo -n $NEW_SECRET | base64)'"}}'
   
   # Restart API to pick up new secret
   kubectl rollout restart deployment/infra-mind-api -n infra-mind-prod
   ```

2. **Adjust token expiration:**
   ```python
   # Update token configuration
   JWT_CONFIG = {
       'access_token_expire_minutes': 60,
       'refresh_token_expire_days': 30
   }
   ```

### Issue: RBAC Permission Errors

**Symptoms:**
- Users unable to access certain features
- "Permission denied" errors
- Incorrect role assignments

**Diagnostic Steps:**
```bash
# Check user roles
mongo --eval "db.users.find({}, {email: 1, role: 1})"

# Check permission mappings
python scripts/check_rbac_permissions.py

# Test user permissions
python scripts/test_user_permissions.py --user-id=<user_id>
```

**Resolution Steps:**
1. **Update user roles:**
   ```bash
   # Update user role in database
   mongo --eval "db.users.updateOne({email: 'user@example.com'}, {\$set: {role: 'admin'}})"
   ```

2. **Fix permission mappings:**
   ```python
   # Update RBAC configuration
   ROLE_PERMISSIONS = {
       'admin': ['read', 'write', 'delete', 'manage_users'],
       'user': ['read', 'write'],
       'viewer': ['read']
   }
   ```

## Performance Problems

### Issue: High Memory Usage

**Symptoms:**
- Memory usage > 85%
- Out of memory errors
- Pod restarts

**Diagnostic Steps:**
```bash
# Check memory usage
kubectl top pods -n infra-mind-prod --sort-by=memory

# Check memory limits
kubectl describe pods -n infra-mind-prod | grep -A 5 "Limits:"

# Profile memory usage
python scripts/memory_profiler.py
```

**Resolution Steps:**
1. **Increase memory limits:**
   ```bash
   kubectl patch deployment infra-mind-api -n infra-mind-prod -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","resources":{"limits":{"memory":"4Gi"}}}]}}}}'
   ```

2. **Optimize memory usage:**
   - Implement connection pooling
   - Clear unused objects
   - Optimize data structures

3. **Scale horizontally:**
   ```bash
   kubectl scale deployment infra-mind-api --replicas=5 -n infra-mind-prod
   ```

### Issue: High CPU Usage

**Symptoms:**
- CPU usage > 80%
- Slow response times
- High load averages

**Diagnostic Steps:**
```bash
# Check CPU usage
kubectl top pods -n infra-mind-prod --sort-by=cpu

# Check CPU limits
kubectl describe pods -n infra-mind-prod | grep -A 5 "Limits:"

# Profile CPU usage
python scripts/cpu_profiler.py
```

**Resolution Steps:**
1. **Increase CPU limits:**
   ```bash
   kubectl patch deployment infra-mind-api -n infra-mind-prod -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","resources":{"limits":{"cpu":"2000m"}}}]}}}}'
   ```

2. **Optimize CPU-intensive operations:**
   - Use async operations
   - Implement caching
   - Optimize algorithms

3. **Scale horizontally:**
   ```bash
   kubectl scale deployment infra-mind-api --replicas=5 -n infra-mind-prod
   ```

## Frontend Issues

### Issue: Frontend Not Loading

**Symptoms:**
- Blank page or loading spinner
- JavaScript errors in browser console
- Failed API calls

**Diagnostic Steps:**
```bash
# Check frontend pod status
kubectl get pods -n infra-mind-prod -l app=infra-mind-frontend

# Check frontend logs
kubectl logs deployment/infra-mind-frontend -n infra-mind-prod

# Check API connectivity from frontend
curl -f http://api.infra-mind.com/health

# Check browser console for errors
# Open browser developer tools
```

**Resolution Steps:**
1. **Restart frontend pods:**
   ```bash
   kubectl rollout restart deployment/infra-mind-frontend -n infra-mind-prod
   ```

2. **Check API configuration:**
   ```bash
   # Verify API URL in frontend config
   kubectl get configmap frontend-config -n infra-mind-prod -o yaml
   ```

3. **Clear browser cache:**
   ```bash
   # Instruct users to clear cache
   # Or implement cache-busting in deployment
   ```

### Issue: WebSocket Connection Failures

**Symptoms:**
- Real-time features not working
- WebSocket connection errors
- No live updates

**Diagnostic Steps:**
```bash
# Check WebSocket endpoint
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Key: test" -H "Sec-WebSocket-Version: 13" http://api.infra-mind.com/ws

# Check WebSocket logs
kubectl logs deployment/infra-mind-api -n infra-mind-prod | grep -i websocket

# Test WebSocket from browser console
# new WebSocket('ws://api.infra-mind.com/ws')
```

**Resolution Steps:**
1. **Check load balancer configuration:**
   ```bash
   # Ensure WebSocket support in NGINX
   kubectl get configmap nginx-config -n infra-mind-prod -o yaml
   ```

2. **Restart API pods:**
   ```bash
   kubectl rollout restart deployment/infra-mind-api -n infra-mind-prod
   ```

3. **Update WebSocket configuration:**
   ```python
   # Check WebSocket settings
   WEBSOCKET_CONFIG = {
       'ping_interval': 20,
       'ping_timeout': 10,
       'close_timeout': 10
   }
   ```

## Infrastructure Problems

### Issue: Kubernetes Pod Failures

**Symptoms:**
- Pods in CrashLoopBackOff state
- Pod restart loops
- Failed deployments

**Diagnostic Steps:**
```bash
# Check pod status
kubectl get pods -n infra-mind-prod

# Check pod events
kubectl describe pod <pod-name> -n infra-mind-prod

# Check pod logs
kubectl logs <pod-name> -n infra-mind-prod --previous

# Check resource constraints
kubectl top pods -n infra-mind-prod
```

**Resolution Steps:**
1. **Check resource limits:**
   ```bash
   kubectl describe pod <pod-name> -n infra-mind-prod | grep -A 10 "Limits:"
   ```

2. **Update resource limits:**
   ```bash
   kubectl patch deployment <deployment-name> -n infra-mind-prod -p '{"spec":{"template":{"spec":{"containers":[{"name":"<container-name>","resources":{"limits":{"memory":"2Gi","cpu":"1000m"}}}]}}}}'
   ```

3. **Check configuration:**
   ```bash
   kubectl get configmap -n infra-mind-prod
   kubectl get secret -n infra-mind-prod
   ```

### Issue: Load Balancer Problems

**Symptoms:**
- Unable to reach application
- Load balancer health check failures
- Uneven traffic distribution

**Diagnostic Steps:**
```bash
# Check load balancer status
kubectl get svc -n infra-mind-prod

# Check ingress status
kubectl get ingress -n infra-mind-prod

# Check endpoint status
kubectl get endpoints -n infra-mind-prod

# Test load balancer health
curl -f http://load-balancer-ip/health
```

**Resolution Steps:**
1. **Check service configuration:**
   ```bash
   kubectl describe svc infra-mind-api -n infra-mind-prod
   ```

2. **Update health check configuration:**
   ```yaml
   # Update ingress health check
   nginx.ingress.kubernetes.io/health-check-path: "/health"
   nginx.ingress.kubernetes.io/health-check-interval: "30s"
   ```

3. **Restart ingress controller:**
   ```bash
   kubectl rollout restart deployment/nginx-ingress-controller -n ingress-nginx
   ```

## Monitoring and Logging Issues

### Issue: Missing Metrics

**Symptoms:**
- Gaps in monitoring dashboards
- Missing Prometheus metrics
- Grafana showing no data

**Diagnostic Steps:**
```bash
# Check Prometheus status
kubectl get pods -n monitoring -l app=prometheus

# Check Prometheus targets
curl http://prometheus:9090/api/v1/targets

# Check metric endpoints
curl http://api.infra-mind.com/metrics

# Check Grafana data sources
# Login to Grafana and check data source configuration
```

**Resolution Steps:**
1. **Restart Prometheus:**
   ```bash
   kubectl rollout restart deployment/prometheus -n monitoring
   ```

2. **Check metric exposition:**
   ```python
   # Ensure metrics are being exposed
   from prometheus_client import Counter, generate_latest
   
   # Add metrics to application
   REQUEST_COUNT = Counter('api_requests_total', 'Total API requests')
   ```

3. **Update Prometheus configuration:**
   ```yaml
   # Add scrape targets
   scrape_configs:
     - job_name: 'infra-mind-api'
       static_configs:
         - targets: ['api.infra-mind.com:8000']
   ```

### Issue: Log Aggregation Problems

**Symptoms:**
- Missing logs in ELK stack
- Log parsing errors
- High log volume causing issues

**Diagnostic Steps:**
```bash
# Check Elasticsearch status
curl -X GET "elasticsearch:9200/_cluster/health"

# Check Logstash status
kubectl get pods -n logging -l app=logstash

# Check Kibana status
curl -f http://kibana:5601/api/status

# Check log volume
kubectl logs deployment/infra-mind-api -n infra-mind-prod | wc -l
```

**Resolution Steps:**
1. **Restart ELK stack:**
   ```bash
   kubectl rollout restart deployment/elasticsearch -n logging
   kubectl rollout restart deployment/logstash -n logging
   kubectl rollout restart deployment/kibana -n logging
   ```

2. **Optimize log configuration:**
   ```python
   # Reduce log verbosity
   LOGGING_CONFIG = {
       'level': 'INFO',
       'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       'max_bytes': 10485760,  # 10MB
       'backup_count': 5
   }
   ```

3. **Clean up old logs:**
   ```bash
   # Delete old Elasticsearch indices
   curl -X DELETE "elasticsearch:9200/logstash-*"
   ```

## Emergency Procedures

### Complete System Outage

**Immediate Actions:**
1. **Assess scope of outage:**
   ```bash
   # Check all services
   kubectl get pods --all-namespaces
   
   # Check external dependencies
   python scripts/check_all_dependencies.py
   ```

2. **Notify stakeholders:**
   ```bash
   # Send alert to status page
   # Notify customer support team
   # Update social media if needed
   ```

3. **Begin recovery:**
   ```bash
   # Start with database
   kubectl rollout restart statefulset/mongodb -n infra-mind-prod
   
   # Then cache
   kubectl rollout restart statefulset/redis -n infra-mind-prod
   
   # Finally application
   kubectl rollout restart deployment/infra-mind-api -n infra-mind-prod
   ```

### Data Corruption

**Immediate Actions:**
1. **Stop all writes:**
   ```bash
   # Scale down API to prevent further corruption
   kubectl scale deployment infra-mind-api --replicas=0 -n infra-mind-prod
   ```

2. **Assess damage:**
   ```bash
   # Check data integrity
   python scripts/check_data_integrity.py
   
   # Identify corrupted records
   python scripts/find_corrupted_data.py
   ```

3. **Restore from backup:**
   ```bash
   # Restore latest clean backup
   python scripts/backup_restore.py --restore --backup-id=<latest_clean_backup>
   ```

### Security Breach

**Immediate Actions:**
1. **Isolate affected systems:**
   ```bash
   # Block suspicious traffic
   kubectl apply -f security/emergency-network-policy.yaml
   
   # Scale down affected services
   kubectl scale deployment infra-mind-api --replicas=0 -n infra-mind-prod
   ```

2. **Preserve evidence:**
   ```bash
   # Capture logs
   kubectl logs deployment/infra-mind-api -n infra-mind-prod > security-incident-logs.txt
   
   # Capture system state
   kubectl get all -o yaml > security-incident-state.yaml
   ```

3. **Notify security team:**
   ```bash
   # Follow incident response plan
   # Contact legal team if needed
   # Prepare customer communications
   ```

## Contact Information

### Emergency Contacts

- **On-Call Engineer**: +1-555-0123 (24/7)
- **Engineering Manager**: +1-555-0124 (escalation)
- **Security Team**: security@infra-mind.com
- **Customer Support**: support@infra-mind.com

### Vendor Support

- **AWS Support**: Case creation via AWS Console
- **Azure Support**: Case creation via Azure Portal
- **GCP Support**: Case creation via Google Cloud Console
- **MongoDB Atlas**: support@mongodb.com
- **Redis Enterprise**: support@redis.com

---

*This troubleshooting guide should be updated regularly based on new issues encountered and lessons learned from incidents.*