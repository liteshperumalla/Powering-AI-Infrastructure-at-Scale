/**
 * A/B Testing and Experiments API Service
 * 
 * Provides functions to interact with the experiments API endpoints
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ExperimentVariant {
  feature_flag: string;
  user_id: string;
  variant: string;
  assigned_at: string;
  experiment_id: string | null;
}

export interface ExperimentEvent {
  user_id: string;
  event_type: string;
  value?: number;
  custom_metrics?: Record<string, any>;
  user_attributes?: Record<string, any>;
  session_id?: string;
}

export interface Experiment {
  id: string;
  name: string;
  description: string;
  feature_flag: string;
  status: 'draft' | 'running' | 'completed' | 'paused';
  variants: string[];
  target_metric: string;
  created_at: string;
  created_by: string;
}

/**
 * Get user variant for A/B test
 */
export async function getUserVariant(
  featureFlag: string, 
  userId: string
): Promise<ExperimentVariant> {
  const response = await fetch(
    `${API_BASE_URL}/api/v2/experiments/feature/${featureFlag}/variant?user_id=${userId}`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to get user variant: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Track experiment event
 */
export async function trackExperimentEvent(
  featureFlag: string,
  eventData: ExperimentEvent
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/v2/experiments/feature/${featureFlag}/track`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`,
      },
      body: JSON.stringify(eventData),
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to track event: ${response.statusText}`);
  }
}

/**
 * Get list of experiments (admin only)
 */
export async function getExperiments(): Promise<Experiment[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/v2/experiments/`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to get experiments: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Create new experiment (admin only)
 */
export async function createExperiment(experimentData: Partial<Experiment>): Promise<Experiment> {
  const response = await fetch(
    `${API_BASE_URL}/api/v2/experiments/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`,
      },
      body: JSON.stringify(experimentData),
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to create experiment: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Get experiment dashboard data (admin only)
 */
export async function getExperimentDashboard(): Promise<any> {
  const response = await fetch(
    `${API_BASE_URL}/api/v2/experiments/dashboard/data`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to get dashboard data: ${response.statusText}`);
  }
  
  return response.json();
}

// Helper function to get auth token
function getAuthToken(): string {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('authToken') || '';
  }
  return '';
}

// Hook for using experiments in React components
export function useExperiment(featureFlag: string, userId: string) {
  const [variant, setVariant] = React.useState<string>('control');
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function fetchVariant() {
      try {
        setLoading(true);
        const result = await getUserVariant(featureFlag, userId);
        setVariant(result.variant);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to get variant');
        setVariant('control'); // Fallback to control
      } finally {
        setLoading(false);
      }
    }

    fetchVariant();
  }, [featureFlag, userId]);

  const trackEvent = React.useCallback(async (eventData: Omit<ExperimentEvent, 'user_id'>) => {
    try {
      await trackExperimentEvent(featureFlag, { ...eventData, user_id: userId });
    } catch (err) {
      console.error('Failed to track experiment event:', err);
    }
  }, [featureFlag, userId]);

  return { variant, loading, error, trackEvent };
}

import React from 'react';