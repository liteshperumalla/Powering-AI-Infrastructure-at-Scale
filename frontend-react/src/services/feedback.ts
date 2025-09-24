/**
 * User Feedback API Service
 * 
 * Provides functions to interact with the feedback collection system
 */

import React from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type FeedbackType = 'assessment_quality' | 'ui_experience' | 'performance' | 'feature_request' | 'bug_report' | 'general';

export interface UserFeedback {
  id?: string;
  feedback_type: FeedbackType;
  rating?: number;
  comments?: string;
  assessment_id?: string;
  channel?: 'web' | 'mobile' | 'api';
  sentiment?: 'positive' | 'neutral' | 'negative';
  processed?: boolean;
  created_at?: string;
  user_id?: string;
}

export interface FeedbackAnalytics {
  total_feedback: number;
  average_rating: number;
  sentiment_breakdown: {
    positive: number;
    neutral: number;
    negative: number;
  };
  by_type: Record<FeedbackType, {
    count: number;
    average_rating: number;
  }>;
  by_channel: Record<string, number>;
}

export interface FeedbackSummary {
  period_days: number;
  total_feedback: number;
  average_rating: number;
  top_categories: Array<{
    category: string;
    count: number;
    percentage: number;
  }>;
  sentiment_trend: Array<{
    date: string;
    positive: number;
    neutral: number;
    negative: number;
  }>;
}

/**
 * Submit user feedback
 */
export async function submitFeedback(feedback: UserFeedback): Promise<UserFeedback> {
  const response = await fetch(
    `${API_BASE_URL}/api/v2/feedback/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`,
      },
      body: JSON.stringify({
        ...feedback,
        channel: 'web',
      }),
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to submit feedback: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Get feedback analytics dashboard (admin only)
 */
export async function getFeedbackAnalytics(): Promise<FeedbackAnalytics> {
  const response = await fetch(
    `${API_BASE_URL}/api/v2/feedback/analytics/dashboard`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to get feedback analytics: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Get feedback summary for period (admin only)
 */
export async function getFeedbackSummary(days: number = 30): Promise<FeedbackSummary> {
  const response = await fetch(
    `${API_BASE_URL}/api/v2/feedback/summary/period?days=${days}`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to get feedback summary: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Get list of feedback entries (admin only)
 */
export async function getFeedbackList(params: {
  limit?: number;
  feedback_type?: FeedbackType;
  channel?: string;
  sentiment?: string;
  processed?: boolean;
} = {}): Promise<UserFeedback[]> {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) {
      searchParams.append(key, value.toString());
    }
  });
  
  const response = await fetch(
    `${API_BASE_URL}/api/v2/feedback/?${searchParams.toString()}`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to get feedback list: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Get feedback health status
 */
export async function getFeedbackHealth(): Promise<{
  status: string;
  components: Record<string, string>;
  timestamp: string;
}> {
  const response = await fetch(
    `${API_BASE_URL}/api/v2/feedback/health`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to get feedback health: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Submit assessment-specific feedback
 */
export async function submitAssessmentFeedback(
  assessmentId: string, 
  feedback: Omit<UserFeedback, 'assessment_id'>
): Promise<UserFeedback> {
  return submitFeedback({
    ...feedback,
    assessment_id: assessmentId,
  });
}

// Helper function to get auth token
function getAuthToken(): string {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('auth_token') || '';
  }
  return '';
}

// React hook for feedback submission
export function useFeedbackSubmission() {
  const [loading, setLoading] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string | null>(null);
  const [success, setSuccess] = React.useState<boolean>(false);

  const submit = React.useCallback(async (feedback: UserFeedback) => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(false);
      
      await submitFeedback(feedback);
      setSuccess(true);
      
      // Reset success after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit feedback');
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = React.useCallback(() => {
    setError(null);
    setSuccess(false);
  }, []);

  return { submit, loading, error, success, reset };
}