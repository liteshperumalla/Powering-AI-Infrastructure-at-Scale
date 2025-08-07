/**
 * React Hook for ensuring fresh data display
 * 
 * This hook handles cache invalidation and forces component re-renders
 * when fresh data is needed, preventing stale visualizations.
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { cacheBuster } from '@/utils/cache-buster';

interface FreshDataOptions {
    refreshInterval?: number;
    autoRefresh?: boolean;
    dependencies?: string[];
    onRefresh?: () => void;
}

export const useFreshData = (key: string, options: FreshDataOptions = {}) => {
    const {
        refreshInterval = 30000, // 30 seconds default
        autoRefresh = false,
        dependencies = [],
        onRefresh
    } = options;

    const [refreshTrigger, setRefreshTrigger] = useState(0);
    const [isStale, setIsStale] = useState(false);
    const intervalRef = useRef<NodeJS.Timeout>();
    const lastRefreshRef = useRef<number>(Date.now());

    // Force refresh function
    const forceRefresh = useCallback(() => {
        cacheBuster.clearCache(key);
        setRefreshTrigger(prev => prev + 1);
        lastRefreshRef.current = Date.now();
        setIsStale(false);
        onRefresh?.();
    }, [key, onRefresh]);

    // Check if data is stale
    const checkStale = useCallback(() => {
        const stale = cacheBuster.isStale(key, refreshInterval);
        setIsStale(stale);
        return stale;
    }, [key, refreshInterval]);

    // Set up auto refresh
    useEffect(() => {
        if (autoRefresh) {
            intervalRef.current = setInterval(() => {
                if (checkStale()) {
                    forceRefresh();
                }
            }, refreshInterval);

            return () => {
                if (intervalRef.current) {
                    clearInterval(intervalRef.current);
                }
            };
        }
    }, [autoRefresh, refreshInterval, checkStale, forceRefresh]);

    // Listen for global refresh events
    useEffect(() => {
        const handleForceRefresh = (event: CustomEvent) => {
            forceRefresh();
        };

        window.addEventListener('forceDataRefresh', handleForceRefresh as EventListener);
        return () => {
            window.removeEventListener('forceDataRefresh', handleForceRefresh as EventListener);
        };
    }, [forceRefresh]);

    // Refresh when dependencies change
    useEffect(() => {
        if (dependencies.length > 0) {
            forceRefresh();
        }
    }, dependencies);

    // Clean up on unmount
    useEffect(() => {
        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, []);

    return {
        refreshTrigger,
        isStale,
        forceRefresh,
        checkStale,
        lastRefresh: lastRefreshRef.current
    };
};

// Assessment-specific hook
export const useAssessmentData = (assessmentId?: string, options: FreshDataOptions = {}) => {
    const key = assessmentId ? `assessment_${assessmentId}` : 'assessments_list';
    
    const freshData = useFreshData(key, {
        ...options,
        autoRefresh: true,
        refreshInterval: 10000, // 10 seconds for assessment data
    });

    // Clear related cache when assessment changes
    useEffect(() => {
        if (assessmentId) {
            // Clear all related cache for this assessment
            cacheBuster.invalidateAssessmentCache(assessmentId);
        }
    }, [assessmentId]);

    return {
        ...freshData,
        refreshAssessmentData: () => {
            if (assessmentId) {
                cacheBuster.invalidateAssessmentCache(assessmentId);
            }
            freshData.forceRefresh();
        }
    };
};

// Visualization-specific hook
export const useVisualizationData = (assessmentId: string, options: FreshDataOptions = {}) => {
    const key = `visualization_${assessmentId}`;
    
    return useFreshData(key, {
        ...options,
        autoRefresh: true,
        refreshInterval: 5000, // 5 seconds for visualization data
        onRefresh: () => {
            // Also clear assessment cache when visualization refreshes
            cacheBuster.clearCache(`assessment_${assessmentId}`);
            options.onRefresh?.();
        }
    });
};

// Recommendations-specific hook
export const useRecommendationsData = (assessmentId: string, options: FreshDataOptions = {}) => {
    const key = `recommendations_${assessmentId}`;
    
    return useFreshData(key, {
        ...options,
        autoRefresh: true,
        refreshInterval: 15000, // 15 seconds for recommendations
    });
};