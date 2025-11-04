# Quick Fix Guide for Additional Features Pages

## Problem
The individual feature pages (quality, approvals, executive, etc.) are using old API endpoints that don't exist or have permission errors.

## Solution
All these pages need to be updated to use the new features API:

```
GET /api/v1/features/assessment/{assessment_id}/[feature_name]
```

## Assessment ID to Use
The completed assessment ID is: `68dbf9e9047dde3cf58186dd`

## Quick Fix Steps

### 1. Update each page to get assessment ID from URL or context
```typescript
const searchParams = useSearchParams();
const assessmentId = searchParams.get('assessment_id') || '68dbf9e9047dde3cf58186dd';
```

### 2. Update API call
```typescript
// OLD (doesn't work):
const response = await apiClient.get('/quality/overview');

// NEW (works):
const response = await apiClient.get(`/features/assessment/${assessmentId}/quality`);
```

### 3. Handle the response structure
The new API returns data in this format:
```json
{
  "assessment_id": "...",
  "quality": { ... },
  "performance": { ... },
  etc.
}
```

## Pages That Need Fixing

1. **Quality** (`/quality`) - Use `/features/assessment/{id}/quality`
2. **Approvals** (`/approval-workflows`) - Use `/features/assessment/{id}/approvals`
3. **Executive** (`/executive-dashboard`) - Use `/features/assessment/{id}/executive`
4. **Budget** (`/budget-forecasting`) - Use `/features/assessment/{id}/budget`
5. **Vendor Lock-in** (`/vendor-lockin`) - Use `/features/assessment/{id}/vendor-lockin`
6. **Rollback** (`/rollback`) - Use `/features/assessment/{id}/rollback`
7. **Performance** (`/performance`) - Use `/features/assessment/{id}/performance`
8. **Compliance** (`/compliance`) - Use `/features/assessment/{id}/compliance`
9. **Experiments** (`/experiments`) - Use `/features/assessment/{id}/experiments`

## Testing the API
You can test any endpoint in browser console:
```javascript
fetch('http://localhost:8000/api/v1/features/assessment/68dbf9e9047dde3cf58186dd/quality', {
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('token')
  }
}).then(r => r.json()).then(console.log)
```

## Recommendation
Instead of fixing each page individually (which is time-consuming), consider:

1. **Option A**: Make all features accessible from the assessment detail page
   - Add a "View Additional Features" button on the assessment page
   - Show all features in tabs (like the AdditionalFeatures component we created)

2. **Option B**: Auto-redirect feature pages to include assessment_id
   - When user visits `/quality`, redirect to `/quality?assessment_id=68dbf9e9047dde3cf58186dd`
   - Or auto-select the most recent completed assessment

3. **Option C**: Create a context provider that tracks current assessment
   - Store current assessment in React Context
   - All feature pages read from context instead of props/URL

## Current Status
✅ Backend API working perfectly - all features endpoints return data
✅ Fixed React key warning in recommendations
✅ Created comprehensive AdditionalFeatures component (can be reused)
⚠️ Individual feature pages need API endpoint updates
