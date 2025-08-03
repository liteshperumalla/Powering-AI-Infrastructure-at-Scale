# Operational Runbooks

## Overview

This document contains step-by-step operational procedures for maintaining the Infra Mind production environment. Each runbook provides detailed instructions for common operational tasks.

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [Weekly Maintenance](#weekly-maintenance)
3. [Monthly Procedures](#monthly-procedures)
4. [Deployment Runbooks](#deployment-runbooks)
5. [Backup and Recovery](#backup-and-recovery)
6. [Security Operations](#security-operations)
7. [Performance Optimization](#performance-optimization)
8. [Incident Response](#incident-response)
9. [Capacity Management](#capacity-management)
10. [Vendor Management](#vendor-management)

## Daily Operations

### Daily Health Check Runbook

**Frequency:** Every day at 9:00 AM UTC  
**Duration:** 15-20 minutes  
**Owner:** DevOps Engineer

#### Prerequisites
- Access to Kubernetes cluster
- Monitoring dashboard access
- Database access credentials

#### Procedure

1. **System Health Overview**
   ```bash
   # Check overall cluster health
   kubectl get nodes
   kubectl get pods --all-namespaces | grep -v Running
   
   # Check critical services
   kubectl get pods -n infra-mind-prod -l tier=critical
   ```

2. **Application Health**
   ```bash
   # Test API endpoints
   curl -f http://api.infra-mind.com/health
   curl -f http://api.infra-mind.com/metrics
   
   # Check API response times
   curl -w "@curl-format.txt" -o /dev/null -s "http://api.infra-mind.com/health"
   ```

3. **Database Health**
   ```bash
   # Check MongoDB status
   kubectl exec -it mongodb-0 -n infra-mind-prod -- mongo --eval "
   db.runCommand({ping: 1});
   rs.status().ok;
   db.stats();
   "
   
   # Check Redis status
   kubectl exec -it redis-0 -n infra-mind-prod -- redis-cli ping
   kubectl exec -it redis-0 -n infra-mind-prod -- redis-cli info replication
   ```

4. **Resource Utilization**
   ```bash
   # Check resource usage
   kubectl top nodes
   kubectl top pods -n infra-mind-prod --sort-by=memory
   kubectl top pods -n infra-mind-prod --sort-by=cpu
   ```

5. **External Dependencies**
   ```bash
   # Test cloud provider APIs
   python scripts/check_external_apis.py
   
   # Test LLM providers
   python scripts/test_llm_connectivity.py
   ```

6. **Backup Verification**
   ```bash
   # Verify last night's backup
   python scripts/verify_daily_backup.py
   
   # Check backup storage usage
   aws s3 ls s3://infra-mind-backups/ --recursive --human-readable --summarize
   ```

#### Success Criteria
- All pods in Running state
- API response time < 2 seconds
- Database connections successful
- Resource usage < 80%
- External APIs responding
- Backup completed successfully

#### Escalation
If any check fails:
1. Follow troubleshooting guide
2. If unresolved in 30 minutes, escalate to Senior Engineer
3. If critical, page on-call engineer immediately

### Daily Log Review Runbook

**Frequency:** Every day at 10:00 AM UTC  
**Duration:** 30 minutes  
**Owner:** DevOps Engineer

#### Procedure

1. **Error Log Analysis**
   ```bash
   # Check for errors in last 24 hours
   kubectl logs --since=24h deployment/infra-mind-api -n infra-mind-prod | grep -i error | head -20
   
   # Check error patterns
   kubectl logs --since=24h deployment/infra-mind-api -n infra-mind-prod | grep -i error | sort | uniq -c | sort -nr
   ```

2. **Security Log Review**
   ```bash
   # Check authentication failures
   kubectl logs --since=24h deployment/infra-mind-api -n infra-mind-prod | grep -i "authentication failed"
   
   # Check suspicious access patterns
   kubectl logs --since=24h deployment/infra-mind-api -n infra-mind-prod | grep -i "suspicious"
   ```

3. **Performance Log Analysis**
   ```bash
   # Check slow requests
   kubectl logs --since=24h deployment/infra-mind-api -n infra-mind-prod | grep "slow_request" | head -10
   
   # Check database slow queries
   kubectl exec -it mongodb-0 -n infra-mind-prod -- mongo --eval "
   db.system.profile.find({ts: {\$gte: new Date(Date.now() - 24*60*60*1000)}}).sort({ts: -1}).limit(10)
   "
   ```

4. **Business Metrics Review**
   ```bash
   # Check assessment completion rates
   python scripts/daily_metrics_report.py
   
   # Check user activity
   python scripts/user_activity_report.py --days=1
   ```

#### Actions Required
- Document any recurring errors
- Create tickets for issues requiring investigation
- Update monitoring alerts if new patterns emerge
- Notify relevant teams of significant issues

## Weekly Maintenance

### Weekly Security Update Runbook

**Frequency:** Every Sunday at 2:00 AM UTC  
**Duration:** 2-3 hours  
**Owner:** DevOps Engineer

#### Prerequisites
- Maintenance window scheduled
- Backup completed
- Change approval obtained

#### Procedure

1. **Pre-maintenance Backup**
   ```bash
   # Create full system backup
   python scripts/backup_restore.py --full-backup --tag="pre-security-update-$(date +%Y%m%d)"
   
   # Verify backup integrity
   python scripts/verify_backup.py --backup-tag="pre-security-update-$(date +%Y%m%d)"
   ```

2. **Security Scanning**
   ```bash
   # Scan container images
   trivy image infra-mind-api:latest
   trivy image infra-mind-frontend:latest
   
   # Scan dependencies
   pip-audit --requirements requirements.txt
   npm audit --audit-level moderate
   ```

3. **Update Base Images**
   ```bash
   # Update Dockerfile base images
   docker pull python:3.11-slim
   docker pull node:18-alpine
   docker pull nginx:1.24-alpine
   
   # Rebuild images
   ./scripts/build-production.sh
   ```

4. **Update Dependencies**
   ```bash
   # Update Python dependencies
   pip-compile --upgrade requirements.in
   
   # Update Node.js dependencies
   cd frontend-react && npm update
   
   # Update Kubernetes components
   kubectl apply -f k8s/updated-manifests/
   ```

5. **Deploy Updates**
   ```bash
   # Deploy with rolling update
   kubectl set image deployment/infra-mind-api api=infra-mind-api:$(date +%Y%m%d) -n infra-mind-prod
   kubectl rollout status deployment/infra-mind-api -n infra-mind-prod
   
   # Deploy frontend updates
   kubectl set image deployment/infra-mind-frontend frontend=infra-mind-frontend:$(date +%Y%m%d) -n infra-mind-prod
   kubectl rollout status deployment/infra-mind-frontend -n infra-mind-prod
   ```

6. **Post-deployment Verification**
   ```bash
   # Run health checks
   ./scripts/health-check.sh
   
   # Run security tests
   python tests/test_security.py
   
   # Verify functionality
   python tests/test_smoke.py
   ```

#### Rollback Procedure
If issues are detected:
```bash
# Rollback deployment
kubectl rollout undo deployment/infra-mind-api -n infra-mind-prod
kubectl rollout undo deployment/infra-mind-frontend -n infra-mind-prod

# Restore from backup if needed
python scripts/backup_restore.py --restore --backup-tag="pre-security-update-$(date +%Y%m%d)"
```

### Weekly Performance Review Runbook

**Frequency:** Every Friday at 4:00 PM UTC  
**Duration:** 1 hour  
**Owner:** Senior Engineer

#### Procedure

1. **Performance Metrics Analysis**
   ```bash
   # Generate weekly performance report
   python scripts/weekly_performance_report.py
   
   # Check response time trends
   python scripts/analyze_response_times.py --days=7
   
   # Check resource utilization trends
   python scripts/analyze_resource_usage.py --days=7
   ```

2. **Database Performance Review**
   ```bash
   # Analyze slow queries
   kubectl exec -it mongodb-0 -n infra-mind-prod -- mongo --eval "
   db.system.profile.find({ts: {\$gte: new Date(Date.now() - 7*24*60*60*1000)}})
     .sort({millis: -1}).limit(20)
   "
   
   # Check index usage
   python scripts/analyze_index_usage.py
   ```

3. **Cache Performance Review**
   ```bash
   # Check Redis performance
   kubectl exec -it redis-0 -n infra-mind-prod -- redis-cli info stats
   
   # Analyze cache hit rates
   python scripts/analyze_cache_performance.py --days=7
   ```

4. **External API Performance**
   ```bash
   # Check cloud API response times
   python scripts/analyze_external_api_performance.py --days=7
   
   # Check LLM API performance
   python scripts/analyze_llm_performance.py --days=7
   ```

#### Actions Required
- Document performance trends
- Identify optimization opportunities
- Plan capacity changes if needed
- Update performance baselines

## Monthly Procedures

### Monthly Capacity Planning Runbook

**Frequency:** First Monday of each month  
**Duration:** 2-3 hours  
**Owner:** Engineering Manager

#### Procedure

1. **Usage Trend Analysis**
   ```bash
   # Generate monthly usage report
   python scripts/monthly_usage_report.py
   
   # Analyze user growth trends
   python scripts/analyze_user_growth.py --months=3
   
   # Check assessment volume trends
   python scripts/analyze_assessment_trends.py --months=3
   ```

2. **Resource Utilization Review**
   ```bash
   # Check compute resource trends
   python scripts/analyze_compute_usage.py --months=1
   
   # Check storage growth
   python scripts/analyze_storage_growth.py --months=1
   
   # Check network usage
   python scripts/analyze_network_usage.py --months=1
   ```

3. **Cost Analysis**
   ```bash
   # Generate cost report
   python scripts/monthly_cost_report.py
   
   # Analyze cloud provider costs
   python scripts/analyze_cloud_costs.py --months=1
   
   # Check LLM usage costs
   python scripts/analyze_llm_costs.py --months=1
   ```

4. **Capacity Projections**
   ```bash
   # Project resource needs
   python scripts/project_capacity_needs.py --months=6
   
   # Generate scaling recommendations
   python scripts/generate_scaling_recommendations.py
   ```

#### Deliverables
- Monthly capacity report
- Resource scaling recommendations
- Cost optimization suggestions
- Infrastructure roadmap updates

### Monthly Security Audit Runbook

**Frequency:** Second Monday of each month  
**Duration:** 4-6 hours  
**Owner:** Security Engineer

#### Procedure

1. **Access Review**
   ```bash
   # Review user access
   python scripts/audit_user_access.py
   
   # Check service account permissions
   kubectl auth can-i --list --as=system:serviceaccount:infra-mind-prod:api-service
   
   # Review API key usage
   python scripts/audit_api_key_usage.py
   ```

2. **Security Configuration Audit**
   ```bash
   # Check security policies
   kubectl get networkpolicies -n infra-mind-prod
   kubectl get podsecuritypolicies
   
   # Audit RBAC configuration
   kubectl get rolebindings -n infra-mind-prod
   kubectl get clusterrolebindings | grep infra-mind
   ```

3. **Vulnerability Assessment**
   ```bash
   # Scan for vulnerabilities
   trivy image --severity HIGH,CRITICAL infra-mind-api:latest
   
   # Check for exposed secrets
   python scripts/scan_for_secrets.py
   
   # Audit dependencies
   pip-audit --requirements requirements.txt --format=json
   ```

4. **Compliance Check**
   ```bash
   # Check data encryption
   python scripts/verify_encryption.py
   
   # Audit data retention
   python scripts/audit_data_retention.py
   
   # Check backup encryption
   python scripts/verify_backup_encryption.py
   ```

#### Deliverables
- Monthly security audit report
- Vulnerability remediation plan
- Compliance status update
- Security improvement recommendations

## Deployment Runbooks

### Production Deployment Runbook

**Frequency:** As needed  
**Duration:** 1-2 hours  
**Owner:** DevOps Engineer

#### Prerequisites
- Code review completed
- Tests passing
- Change approval obtained
- Maintenance window scheduled (if needed)

#### Procedure

1. **Pre-deployment Preparation**
   ```bash
   # Create deployment backup
   python scripts/backup_restore.py --backup --tag="pre-deploy-$(date +%Y%m%d-%H%M)"
   
   # Verify system health
   ./scripts/health-check.sh
   
   # Run integration tests
   python -m pytest tests/test_integration.py -v
   ```

2. **Database Migration (if needed)**
   ```bash
   # Check for pending migrations
   python scripts/check_migrations.py
   
   # Run migrations
   python scripts/migrate_data.py --environment=production --dry-run
   python scripts/migrate_data.py --environment=production
   
   # Verify migration
   python scripts/verify_migration.py
   ```

3. **Application Deployment**
   ```bash
   # Build production images
   ./scripts/build-production.sh
   
   # Tag images
   docker tag infra-mind-api:latest infra-mind-api:$(git rev-parse --short HEAD)
   docker tag infra-mind-frontend:latest infra-mind-frontend:$(git rev-parse --short HEAD)
   
   # Push to registry
   docker push infra-mind-api:$(git rev-parse --short HEAD)
   docker push infra-mind-frontend:$(git rev-parse --short HEAD)
   ```

4. **Rolling Deployment**
   ```bash
   # Update API deployment
   kubectl set image deployment/infra-mind-api api=infra-mind-api:$(git rev-parse --short HEAD) -n infra-mind-prod
   kubectl rollout status deployment/infra-mind-api -n infra-mind-prod --timeout=600s
   
   # Update frontend deployment
   kubectl set image deployment/infra-mind-frontend frontend=infra-mind-frontend:$(git rev-parse --short HEAD) -n infra-mind-prod
   kubectl rollout status deployment/infra-mind-frontend -n infra-mind-prod --timeout=600s
   ```

5. **Post-deployment Verification**
   ```bash
   # Health check
   ./scripts/health-check.sh
   
   # Smoke tests
   python tests/test_smoke.py
   
   # Performance check
   python scripts/check_performance.py
   
   # Monitor for 15 minutes
   watch -n 30 'kubectl get pods -n infra-mind-prod'
   ```

#### Rollback Procedure
```bash
# If issues detected within 1 hour
kubectl rollout undo deployment/infra-mind-api -n infra-mind-prod
kubectl rollout undo deployment/infra-mind-frontend -n infra-mind-prod

# If database issues
python scripts/backup_restore.py --restore --backup-tag="pre-deploy-$(date +%Y%m%d-%H%M)"

# Verify rollback
./scripts/health-check.sh
```

### Emergency Hotfix Deployment Runbook

**Frequency:** As needed for critical issues  
**Duration:** 30-60 minutes  
**Owner:** On-call Engineer

#### Prerequisites
- Critical issue identified
- Hotfix code ready
- Incident commander assigned

#### Procedure

1. **Rapid Assessment**
   ```bash
   # Assess impact
   python scripts/assess_incident_impact.py
   
   # Create emergency backup
   python scripts/backup_restore.py --emergency-backup
   ```

2. **Fast-track Deployment**
   ```bash
   # Build hotfix image
   docker build -t infra-mind-api:hotfix-$(date +%Y%m%d-%H%M) .
   docker push infra-mind-api:hotfix-$(date +%Y%m%d-%H%M)
   
   # Deploy immediately
   kubectl set image deployment/infra-mind-api api=infra-mind-api:hotfix-$(date +%Y%m%d-%H%M) -n infra-mind-prod
   ```

3. **Immediate Verification**
   ```bash
   # Quick health check
   curl -f http://api.infra-mind.com/health
   
   # Verify fix
   python scripts/verify_hotfix.py
   ```

4. **Post-incident Actions**
   - Document incident
   - Schedule proper fix deployment
   - Update monitoring if needed
   - Conduct post-mortem

## Backup and Recovery

### Daily Backup Runbook

**Frequency:** Every day at 2:00 AM UTC  
**Duration:** 1-2 hours  
**Owner:** Automated (with monitoring)

#### Procedure

1. **Database Backup**
   ```bash
   # MongoDB backup
   mongodump --uri="mongodb://mongodb:27017/infra_mind_prod" \
            --out="/backups/mongodb/$(date +%Y%m%d)" \
            --gzip
   
   # Redis backup
   kubectl exec -it redis-0 -n infra-mind-prod -- redis-cli BGSAVE
   kubectl cp redis-0:/data/dump.rdb /backups/redis/dump-$(date +%Y%m%d).rdb -n infra-mind-prod
   ```

2. **Configuration Backup**
   ```bash
   # Kubernetes configurations
   kubectl get all -o yaml -n infra-mind-prod > /backups/k8s/k8s-config-$(date +%Y%m%d).yaml
   
   # Application configurations
   tar -czf /backups/config/app-config-$(date +%Y%m%d).tar.gz /app/config/
   ```

3. **Upload to Cloud Storage**
   ```bash
   # Upload to S3
   aws s3 sync /backups/ s3://infra-mind-backups/$(date +%Y%m%d)/ --delete
   
   # Verify upload
   aws s3 ls s3://infra-mind-backups/$(date +%Y%m%d)/ --recursive
   ```

4. **Backup Verification**
   ```bash
   # Test backup integrity
   python scripts/verify_backup_integrity.py --date=$(date +%Y%m%d)
   
   # Update backup catalog
   python scripts/update_backup_catalog.py --date=$(date +%Y%m%d)
   ```

#### Monitoring
- Backup completion alerts
- Backup size monitoring
- Backup integrity verification
- Storage usage alerts

### Disaster Recovery Runbook

**Frequency:** As needed for major incidents  
**Duration:** 2-8 hours depending on scope  
**Owner:** Incident Commander

#### Prerequisites
- Disaster declared
- Recovery team assembled
- Communication plan activated

#### Procedure

1. **Assess Damage**
   ```bash
   # Check system status
   kubectl get nodes
   kubectl get pods --all-namespaces
   
   # Assess data integrity
   python scripts/assess_data_damage.py
   
   # Check backup availability
   aws s3 ls s3://infra-mind-backups/ --recursive
   ```

2. **Infrastructure Recovery**
   ```bash
   # Deploy fresh infrastructure
   ./scripts/deploy-k8s.sh production-dr
   
   # Verify infrastructure
   kubectl get nodes
   kubectl get pods -n infra-mind-prod
   ```

3. **Data Recovery**
   ```bash
   # Identify latest good backup
   python scripts/find_latest_backup.py
   
   # Restore database
   python scripts/backup_restore.py --restore --backup-id=<latest_backup_id>
   
   # Verify data integrity
   python scripts/verify_data_integrity.py
   ```

4. **Application Recovery**
   ```bash
   # Deploy applications
   kubectl apply -f k8s/production/
   
   # Verify functionality
   ./scripts/health-check.sh
   python tests/test_smoke.py
   ```

5. **DNS and Traffic Cutover**
   ```bash
   # Update DNS records
   aws route53 change-resource-record-sets --hosted-zone-id Z123456789 --change-batch file://dns-update.json
   
   # Verify traffic flow
   curl -f http://api.infra-mind.com/health
   ```

#### Communication
- Status page updates
- Customer notifications
- Stakeholder updates
- Post-recovery communication

## Security Operations

### Security Incident Response Runbook

**Frequency:** As needed for security incidents  
**Duration:** Variable  
**Owner:** Security Team Lead

#### Prerequisites
- Security incident detected
- Incident response team activated
- Communication channels established

#### Procedure

1. **Immediate Containment**
   ```bash
   # Isolate affected systems
   kubectl apply -f security/emergency-network-policy.yaml
   
   # Stop affected services
   kubectl scale deployment infra-mind-api --replicas=0 -n infra-mind-prod
   
   # Preserve evidence
   kubectl logs deployment/infra-mind-api -n infra-mind-prod > incident-logs-$(date +%Y%m%d-%H%M).txt
   ```

2. **Evidence Collection**
   ```bash
   # Capture system state
   kubectl get all -o yaml > incident-state-$(date +%Y%m%d-%H%M).yaml
   
   # Collect access logs
   python scripts/collect_access_logs.py --incident-id=<incident_id>
   
   # Capture network traffic
   tcpdump -i any -w incident-traffic-$(date +%Y%m%d-%H%M).pcap
   ```

3. **Impact Assessment**
   ```bash
   # Check for data breaches
   python scripts/check_data_breach.py
   
   # Assess system compromise
   python scripts/assess_compromise.py
   
   # Check user accounts
   python scripts/audit_user_accounts.py --suspicious
   ```

4. **Eradication and Recovery**
   ```bash
   # Remove malicious code/access
   python scripts/remove_malicious_access.py
   
   # Patch vulnerabilities
   ./scripts/emergency-security-patch.sh
   
   # Reset compromised credentials
   python scripts/reset_compromised_credentials.py
   ```

5. **System Restoration**
   ```bash
   # Restore from clean backup
   python scripts/backup_restore.py --restore --clean-backup
   
   # Verify system integrity
   python scripts/verify_system_integrity.py
   
   # Gradual service restoration
   kubectl scale deployment infra-mind-api --replicas=1 -n infra-mind-prod
   ```

#### Post-Incident
- Forensic analysis
- Lessons learned session
- Security improvements
- Customer notification (if required)

### Certificate Renewal Runbook

**Frequency:** 30 days before expiration  
**Duration:** 30 minutes  
**Owner:** DevOps Engineer

#### Procedure

1. **Check Certificate Status**
   ```bash
   # Check current certificates
   openssl x509 -in /etc/ssl/certs/infra-mind.crt -noout -dates
   
   # Check expiration dates
   python scripts/check_cert_expiration.py
   ```

2. **Renew Certificates**
   ```bash
   # Renew Let's Encrypt certificates
   certbot renew --nginx --dry-run
   certbot renew --nginx
   
   # Or renew commercial certificates
   # Follow vendor-specific process
   ```

3. **Update Kubernetes Secrets**
   ```bash
   # Update TLS secret
   kubectl create secret tls infra-mind-tls \
     --cert=/etc/letsencrypt/live/infra-mind.com/fullchain.pem \
     --key=/etc/letsencrypt/live/infra-mind.com/privkey.pem \
     --dry-run=client -o yaml | kubectl apply -f -
   ```

4. **Verify Certificate Installation**
   ```bash
   # Test HTTPS connection
   curl -I https://api.infra-mind.com/health
   
   # Check certificate details
   openssl s_client -connect api.infra-mind.com:443 -servername api.infra-mind.com
   ```

## Performance Optimization

### Database Optimization Runbook

**Frequency:** Monthly or when performance issues detected  
**Duration:** 2-4 hours  
**Owner:** Database Administrator

#### Procedure

1. **Performance Analysis**
   ```bash
   # Enable profiling
   kubectl exec -it mongodb-0 -n infra-mind-prod -- mongo --eval "
   db.setProfilingLevel(2, {slowms: 1000})
   "
   
   # Analyze slow queries
   kubectl exec -it mongodb-0 -n infra-mind-prod -- mongo --eval "
   db.system.profile.find().sort({millis: -1}).limit(20).pretty()
   "
   ```

2. **Index Optimization**
   ```bash
   # Check index usage
   kubectl exec -it mongodb-0 -n infra-mind-prod -- mongo --eval "
   db.assessments.aggregate([{\$indexStats: {}}])
   "
   
   # Create missing indexes
   kubectl exec -it mongodb-0 -n infra-mind-prod -- mongo --eval "
   db.assessments.createIndex({user_id: 1, created_at: -1});
   db.reports.createIndex({assessment_id: 1, status: 1});
   "
   ```

3. **Query Optimization**
   ```bash
   # Analyze query patterns
   python scripts/analyze_query_patterns.py
   
   # Optimize aggregation pipelines
   python scripts/optimize_aggregations.py
   ```

4. **Database Maintenance**
   ```bash
   # Compact collections
   kubectl exec -it mongodb-0 -n infra-mind-prod -- mongo --eval "
   db.runCommand({compact: 'assessments'});
   db.runCommand({compact: 'reports'});
   "
   
   # Rebuild indexes
   kubectl exec -it mongodb-0 -n infra-mind-prod -- mongo --eval "
   db.assessments.reIndex();
   db.reports.reIndex();
   "
   ```

### Cache Optimization Runbook

**Frequency:** Weekly or when cache performance degrades  
**Duration:** 1-2 hours  
**Owner:** DevOps Engineer

#### Procedure

1. **Cache Performance Analysis**
   ```bash
   # Check Redis stats
   kubectl exec -it redis-0 -n infra-mind-prod -- redis-cli info stats
   
   # Check memory usage
   kubectl exec -it redis-0 -n infra-mind-prod -- redis-cli info memory
   
   # Analyze cache hit rates
   python scripts/analyze_cache_performance.py
   ```

2. **Cache Configuration Optimization**
   ```bash
   # Optimize memory policy
   kubectl exec -it redis-0 -n infra-mind-prod -- redis-cli CONFIG SET maxmemory-policy allkeys-lru
   
   # Adjust TTL values
   python scripts/optimize_cache_ttl.py
   ```

3. **Cache Warming**
   ```bash
   # Warm frequently accessed data
   python scripts/warm_cache.py --priority=high
   
   # Pre-load common queries
   python scripts/preload_cache.py
   ```

4. **Cache Cleanup**
   ```bash
   # Remove expired keys
   kubectl exec -it redis-0 -n infra-mind-prod -- redis-cli --scan --pattern "*" | xargs -L 1000 redis-cli DEL
   
   # Optimize memory usage
   kubectl exec -it redis-0 -n infra-mind-prod -- redis-cli MEMORY PURGE
   ```

## Contact Information

### Runbook Owners

- **DevOps Engineer**: devops@infra-mind.com
- **Senior Engineer**: senior-eng@infra-mind.com
- **Engineering Manager**: eng-manager@infra-mind.com
- **Security Team Lead**: security-lead@infra-mind.com
- **Database Administrator**: dba@infra-mind.com

### Emergency Contacts

- **On-Call Engineer**: +1-555-0123 (24/7)
- **Incident Commander**: +1-555-0124
- **Security Hotline**: +1-555-0125
- **Management Escalation**: +1-555-0126

---

*These runbooks should be reviewed and updated quarterly to ensure they remain current with system changes and operational improvements.*