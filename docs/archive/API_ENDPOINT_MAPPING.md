# API Endpoint Mapping - Frontend to Backend to Database

**Generated**: 2025-10-07
**Purpose**: Complete mapping of all API endpoints from frontend services to backend routes to database models

---

## 1. Authentication & User Management

### Frontend → Backend → Database

| Frontend Call | Backend Route | HTTP Method | Database Model | Status |
|--------------|---------------|-------------|----------------|---------|
| `apiClient.login()` | `/api/v1/auth/login` | POST | `User` | ✅ Working |
| `apiClient.register()` | `/api/v1/auth/register` | POST | `User` | ✅ Working |
| `apiClient.googleLogin()` | `/api/v1/auth/google` | POST | `User` | ✅ Working |
| `apiClient.logout()` | `/api/v1/auth/logout` | POST | `User` (token invalidation) | ✅ Working |
| `apiClient.refreshToken()` | `/api/v1/auth/refresh` | POST | `User` | ✅ Working |
| `apiClient.getCurrentUser()` | `/api/v1/auth/me` | GET | `User` | ✅ Working |
| `apiClient.updateUserProfile()` | `/api/v1/auth/me` | PUT | `User` | ✅ Working |

---

## 2. Assessments

### Frontend → Backend → Database

| Frontend Call | Backend Route | HTTP Method | Database Model | Status |
|--------------|---------------|-------------|----------------|---------|
| `apiClient.createAssessment()` | `/api/v1/assessments` | POST | `Assessment` | ✅ Working |
| `apiClient.getAssessments()` | `/api/v1/assessments` | GET | `Assessment` | ✅ Working |
| `apiClient.getAssessment(id)` | `/api/v1/assessments/{id}` | GET | `Assessment` | ✅ Working |
| `apiClient.updateAssessment(id)` | `/api/v1/assessments/{id}` | PUT | `Assessment` | ✅ Working |
| `apiClient.deleteAssessment(id)` | `/api/v1/assessments/{id}` | DELETE | `Assessment` | ✅ Working |
| `apiClient.bulkDeleteAssessments()` | `/api/v1/assessments/bulk-delete` | POST | `Assessment` | ✅ Working |
| `apiClient.bulkUpdateAssessments()` | `/api/v1/assessments/bulk-update` | POST | `Assessment` | ✅ Working |

---

## 3. Assessment Features (Special Features APIs)

### Frontend → Backend → Database

| Frontend Call | Backend Route | HTTP Method | Database Model | Status |
|--------------|---------------|-------------|----------------|---------|
| N/A (Direct API call) | `/api/v1/features/assessment/{id}/performance` | GET | `Assessment.technical_requirements.performance_requirements` | ✅ Fixed - No mock data |
| N/A (Direct API call) | `/api/v1/features/assessment/{id}/compliance` | GET | `Assessment.technical_requirements.compliance_requirements` | ✅ Fixed - No mock data |
| N/A (Direct API call) | `/api/v1/features/assessment/{id}/experiments` | GET | `Assessment.experiments` | ✅ Fixed - No mock data |
| N/A (Direct API call) | `/api/v1/features/assessment/{id}/quality` | GET | `Assessment` + `Recommendations` | ✅ Working |
| N/A (Direct API call) | `/api/v1/features/assessment/{id}/approvals` | GET | `Assessment` + workflows | ✅ Working |
| N/A (Direct API call) | `/api/v1/features/assessment/{id}/budget` | GET | `Assessment` + cost data | ✅ Working |
| N/A (Direct API call) | `/api/v1/features/assessment/{id}/executive` | GET | `Assessment` aggregated | ✅ Working |
| N/A (Direct API call) | `/api/v1/features/assessment/{id}/impact` | GET | `Assessment` + analytics | ✅ Working |
| N/A (Direct API call) | `/api/v1/features/assessment/{id}/rollback` | GET | `Assessment` rollback plans | ✅ Working |
| N/A (Direct API call) | `/api/v1/features/assessment/{id}/vendor-lockin` | GET | `Assessment` + vendor analysis | ✅ Working |
| N/A (Direct API call) | `/api/v1/features/assessment/{id}/all-features` | GET | All feature data combined | ✅ Working |

---

## 4. Recommendations

### Frontend → Backend → Database

| Frontend Call | Backend Route | HTTP Method | Database Model | Status |
|--------------|---------------|-------------|----------------|---------|
| `apiClient.generateRecommendations()` | `/api/v1/assessments/{id}/generate` | POST | `Recommendation` (creates) | ✅ Working |
| `apiClient.getRecommendations(assessmentId)` | `/api/v1/recommendations?assessment_id={id}` | GET | `Recommendation` | ✅ Working |
| `apiClient.updateRecommendationStatus()` | `/api/v1/recommendations/{id}/status` | PUT | `Recommendation.status` | ✅ Working |

---

## 5. Reports

### Frontend → Backend → Database

| Frontend Call | Backend Route | HTTP Method | Database Model | Status |
|--------------|---------------|-------------|----------------|---------|
| `apiClient.generateReport()` | `/api/v1/reports/generate` | POST | `Report` | ⚠️ Needs verification |
| `apiClient.getReports()` | `/api/v1/reports` | GET | `Report` | ⚠️ Needs verification |
| `apiClient.getReport(id)` | `/api/v1/reports/{id}` | GET | `Report` | ⚠️ Needs verification |
| `apiClient.downloadReport()` | `/api/v1/reports/{id}/download` | GET | `Report` (PDF generation) | ⚠️ Needs verification |
| `apiClient.shareReport()` | `/api/v1/reports/{id}/share` | POST | `Report.shares` | ⚠️ Needs verification |

---

## 6. Cloud Services

### Frontend → Backend → Database

| Frontend Call | Backend Route | HTTP Method | Database Model | Status |
|--------------|---------------|-------------|----------------|---------|
| `apiClient.getCloudServices()` | `/api/v1/cloud-services` | GET | Cloud services catalog | ✅ Working |
| `apiClient.getCloudServiceDetails()` | `/api/v1/cloud-services/{id}` | GET | Service details | ✅ Working |
| `apiClient.compareCloudServices()` | `/api/v1/cloud-services/compare` | POST | Comparison logic | ✅ Working |
| `apiClient.getCloudServiceProviders()` | `/api/v1/cloud-services/providers` | GET | Providers list | ✅ Working |
| `apiClient.getCloudServiceCategories()` | `/api/v1/cloud-services/categories` | GET | Categories | ✅ Working |

---

## 7. Chat/AI Assistant

### Frontend → Backend → Database

| Frontend Call | Backend Route | HTTP Method | Database Model | Status |
|--------------|---------------|-------------|----------------|---------|
| `apiClient.startConversation()` | `/api/v1/chat/conversations` | POST | `Conversation` | ✅ Working |
| `apiClient.getConversations()` | `/api/v1/chat/conversations` | GET | `Conversation` | ✅ Working |
| `apiClient.getConversation(id)` | `/api/v1/chat/conversations/{id}` | GET | `Conversation` + `Message` | ✅ Working |
| `apiClient.sendMessage()` | `/api/v1/chat/conversations/{id}/messages` | POST | `Message` | ✅ Working |
| `apiClient.deleteConversation()` | `/api/v1/chat/conversations/{id}` | DELETE | `Conversation` | ✅ Working |

---

## 8. Advanced Analytics

### Frontend → Backend → Database

| Frontend Call | Backend Route | HTTP Method | Database Model | Status |
|--------------|---------------|-------------|----------------|---------|
| `apiClient.getAdvancedAnalyticsDashboard()` | `/api/v2/advanced-analytics/dashboard` | GET | Multiple models aggregated | ✅ Working |
| `apiClient.getCostPredictions()` | `/api/v2/advanced-analytics/cost-predictions` | GET | Cost analysis | ✅ Working |
| `apiClient.getSecurityAudit()` | `/api/v2/advanced-analytics/security-audit` | GET | Security data | ✅ Working |
| `apiClient.getCostOptimization()` | `/api/v2/advanced-analytics/cost-optimization` | GET | Optimization data | ✅ Working |

---

## 9. Compliance Automation

### Frontend → Backend → Database

| Frontend Service | Backend Route | HTTP Method | Database Model | Status |
|-----------------|---------------|-------------|----------------|---------|
| `complianceService.getComplianceDashboard()` | `/api/v1/features/assessment/{id}/compliance` | GET | `Assessment.technical_requirements.compliance_requirements` | ✅ Fixed |
| `complianceService.getComplianceFrameworks()` | `/api/v1/features/assessment/{id}/compliance` | GET | Same as above | ✅ Fixed |
| ~~`/api/v2/compliance/dashboard`~~ | N/A | N/A | N/A | ❌ Removed - Does not exist |
| ~~`/api/v2/compliance/frameworks`~~ | N/A | N/A | N/A | ❌ Removed - Does not exist |

**Note**: Compliance service was updated to use the correct `/api/v1/features/assessment/{id}/compliance` endpoint instead of non-existent v2 routes.

---

## 10. Performance Monitoring

### Frontend → Backend → Database

| Frontend Component | Backend Route | HTTP Method | Database Model | Status |
|-------------------|---------------|-------------|----------------|---------|
| PerformanceMonitoringDashboard | `/api/v1/features/assessment/{id}/performance` | GET | `Assessment.technical_requirements.performance_requirements` + `Assessment.current_metrics` | ✅ Fixed - No mock data |

---

## 11. Experiments (A/B Testing)

### Frontend → Backend → Database

| Frontend Service | Backend Route | HTTP Method | Database Model | Status |
|-----------------|---------------|-------------|----------------|---------|
| `experimentsService.*` | `/api/v1/features/assessment/{id}/experiments` | GET | `Assessment.experiments` | ✅ Fixed - No mock data |
| Various experiment calls | `/api/v2/experiments/*` | Multiple | Experiment tracking | ⚠️ Needs implementation |

---

## 12. Monitoring & Performance

### Frontend → Backend → Database

| Frontend Call | Backend Route | HTTP Method | Database Model | Status |
|--------------|---------------|-------------|----------------|---------|
| `apiClient.getWorkflowStatus()` | `/api/v1/monitoring/workflow/{id}/status` | GET | Workflow state | ✅ Working |
| `apiClient.getSystemHealth()` | `/api/v1/monitoring/health` | GET | System metrics | ✅ Working |
| `apiClient.getSystemMetrics()` | `/api/v1/monitoring/metrics` | GET | System metrics | ✅ Working |

---

## Key Findings & Issues Fixed

### ✅ Fixed Issues:

1. **Performance Monitoring**: Removed all mock data, now uses real `Assessment` data
2. **Compliance Dashboard**: Removed mock frameworks, now uses real `compliance_requirements` from Assessment
3. **Experiments**: Removed fake experiment, now uses real `Assessment.experiments` array
4. **Compliance Service**: Fixed to use correct `/api/v1/features/assessment/{id}/compliance` endpoint

### ⚠️ Potential Issues to Investigate:

1. **Reports API**: Need to verify if Report generation and retrieval is working correctly
2. **Experiments Full Implementation**: The `/api/v2/experiments/*` endpoints may need implementation for full A/B testing functionality
3. **Empty Data States**: Many pages will show empty states if Assessment doesn't have required data configured (this is correct behavior)

### 🔑 Database Model Dependencies:

**Assessment Model** is the primary model and contains:
- `business_requirements` - Business context and goals
- `technical_requirements` - Contains:
  - `performance_requirements` (response time, throughput, error rate targets)
  - `compliance_requirements` (list of frameworks like GDPR, SOC2, HIPAA)
  - `workload_types`
- `current_metrics` - Current performance metrics
- `experiments` - A/B test experiments
- `analytics_data` - Scores and analytics

**Other Models**:
- `User` - User authentication and profile
- `Recommendation` - AI-generated recommendations linked to Assessment
- `Report` - Generated reports from assessments
- `Conversation` + `Message` - Chat history
- Various feature-specific collections for workflows, approvals, etc.

---

## API Version Strategy

- **v1**: Stable, core functionality (auth, assessments, recommendations, reports)
- **v2**: Enhanced features (compliance, experiments, feedback, quality, advanced analytics)
- **Default**: Routes to v2 when no version specified

All frontend services should use **`/api/v1`** prefix for core operations and **`/api/v2`** for advanced features.

---

## Recommendations

1. ✅ **No Mock Data**: All mock/hardcoded data has been removed
2. ✅ **Correct Endpoints**: Frontend services now use correct backend routes
3. ⚠️ **Data Configuration**: Users must configure assessment requirements for features to show data
4. 🔄 **Report API**: Should verify report generation workflow end-to-end
5. 📊 **Experiments**: Consider full implementation of A/B testing endpoints if needed

