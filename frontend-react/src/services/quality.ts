/**
 * Quality Assurance API Service
 * 
 * Provides functions to interact with the quality metrics system
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface QualityMetric {
  id?: string;
  target_type: 'assessment' | 'recommendation' | 'report';
  target_id: string;
  metric_name: string;
  metric_value: number;
  quality_score: number;
  created_at?: string;
  metadata?: Record<string, any>;
}

export interface QualityOverview {
  overall_score: number;
  by_target_type: Record<string, {
    metrics: Array<{
      metric_name: string;
      avg_score: number;
      min_score: number;
      max_score: number;
      count: number;
      latest_update: string;
    }>;
  }>;
  generated_at: string;
}

export interface QualityTrends {
  period_days: number;
  trends: Array<{
    date: string;
    overall_score: number;
    by_metric: Record<string, number>;
  }>;
  summary: {
    trend_direction: 'improving' | 'declining' | 'stable';
    average_change: number;
    best_performing_metric: string;
    worst_performing_metric: string;
  };
}

export interface AssessmentQualityScore {
  assessment_id: string;
  overall_score: number;
  metrics: Record<string, number>;
  details: {
    completeness: number;
    accuracy: number;
    relevance: number;
    actionability: number;
  };
  generated_at: string;
}

/**
 * Submit quality metric (admin only)
 */
export async function submitQualityMetric(metric: QualityMetric): Promise<QualityMetric> {
  const response = await fetch(
    `${API_BASE_URL}/api/v2/quality/metrics`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`,
      },
      body: JSON.stringify(metric),
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to submit quality metric: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Get quality metrics for specific target (admin only)
 */
export async function getQualityMetrics(
  targetId: string,
  targetType: 'assessment' | 'recommendation' | 'report'
): Promise<QualityMetric[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/v2/quality/metrics/${targetId}?target_type=${targetType}`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to get quality metrics: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Get quality overview (admin only)
 */
export async function getQualityOverview(): Promise<QualityOverview> {
  const response = await fetch(
    `${API_BASE_URL}/api/v2/quality/overview`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to get quality overview: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Get quality trends (admin only)
 */
export async function getQualityTrends(days: number = 30): Promise<QualityTrends> {
  const response = await fetch(
    `${API_BASE_URL}/api/v2/quality/trends?days=${days}`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to get quality trends: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Get assessment quality score
 */
export async function getAssessmentQualityScore(assessmentId: string): Promise<AssessmentQualityScore> {
  const response = await fetch(
    `${API_BASE_URL}/api/v2/assessments/${assessmentId}/quality-score`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to get assessment quality score: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Get quality system health status
 */
export async function getQualityHealth(): Promise<{
  status: string;
  components: Record<string, string>;
  timestamp: string;
}> {
  const response = await fetch(
    `${API_BASE_URL}/api/v2/quality/health`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to get quality health: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Calculate quality score for assessment
 */
export async function calculateQualityScore(
  targetType: 'assessment' | 'recommendation' | 'report',
  targetId: string,
  metrics: Record<string, number>
): Promise<{ quality_score: number; breakdown: Record<string, number> }> {
  // Calculate weighted quality score
  const weights = {
    completeness: 0.3,
    accuracy: 0.3,
    relevance: 0.2,
    actionability: 0.2,
  };
  
  let qualityScore = 0;
  let totalWeight = 0;
  
  for (const [metric, value] of Object.entries(metrics)) {
    const weight = weights[metric as keyof typeof weights] || 0.1;
    qualityScore += value * weight;
    totalWeight += weight;
  }
  
  if (totalWeight > 0) {
    qualityScore = qualityScore / totalWeight;
  }
  
  return {
    quality_score: Math.round(qualityScore * 100) / 100,
    breakdown: metrics,
  };
}

// Helper function to get auth token
function getAuthToken(): string {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('authToken') || '';
  }
  return '';
}

// React hook for quality metrics
export function useQualityMetrics(targetId: string, targetType: 'assessment' | 'recommendation' | 'report') {
  const [metrics, setMetrics] = React.useState<QualityMetric[]>([]);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function fetchMetrics() {
      try {
        setLoading(true);
        const result = await getQualityMetrics(targetId, targetType);
        setMetrics(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to get metrics');
      } finally {
        setLoading(false);
      }
    }

    if (targetId) {
      fetchMetrics();
    }
  }, [targetId, targetType]);

  const submitMetric = React.useCallback(async (metric: QualityMetric) => {
    try {
      const newMetric = await submitQualityMetric(metric);
      setMetrics(prev => [...prev, newMetric]);
      return newMetric;
    } catch (err) {
      throw err;
    }
  }, []);

  return { metrics, loading, error, submitMetric };
}

// React hook for quality overview (admin)
export function useQualityOverview() {
  const [overview, setOverview] = React.useState<QualityOverview | null>(null);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function fetchOverview() {
      try {
        setLoading(true);
        const result = await getQualityOverview();
        setOverview(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to get overview');
      } finally {
        setLoading(false);
      }
    }

    fetchOverview();
  }, []);

  const refresh = React.useCallback(async () => {
    try {
      const result = await getQualityOverview();
      setOverview(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh overview');
    }
  }, []);

  return { overview, loading, error, refresh };
}

import React from 'react';