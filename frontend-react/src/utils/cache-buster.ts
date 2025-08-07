/**
 * Cache Busting Utilities
 * 
 * Ensures fresh data is always fetched from the backend
 * and prevents stale data from being displayed.
 */

export class CacheBuster {
    private static instance: CacheBuster;
    private timestamps: Map<string, number> = new Map();

    private constructor() {}

    static getInstance(): CacheBuster {
        if (!CacheBuster.instance) {
            CacheBuster.instance = new CacheBuster();
        }
        return CacheBuster.instance;
    }

    /**
     * Generate a cache-busting timestamp for a specific key
     */
    getTimestamp(key: string): number {
        const now = Date.now();
        this.timestamps.set(key, now);
        return now;
    }

    /**
     * Get URL with cache-busting parameter
     */
    bustCache(url: string, key?: string): string {
        const separator = url.includes('?') ? '&' : '?';
        const timestamp = this.getTimestamp(key || url);
        return `${url}${separator}_t=${timestamp}&_cb=${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Clear cache for specific key
     */
    clearCache(key: string): void {
        this.timestamps.delete(key);
        
        // Clear browser cache for this key if possible
        if (typeof window !== 'undefined') {
            try {
                // Clear localStorage entries related to this key
                const keysToRemove: string[] = [];
                for (let i = 0; i < localStorage.length; i++) {
                    const storageKey = localStorage.key(i);
                    if (storageKey && storageKey.includes(key)) {
                        keysToRemove.push(storageKey);
                    }
                }
                keysToRemove.forEach(k => localStorage.removeItem(k));

                // Clear sessionStorage entries
                const sessionKeysToRemove: string[] = [];
                for (let i = 0; i < sessionStorage.length; i++) {
                    const storageKey = sessionStorage.key(i);
                    if (storageKey && storageKey.includes(key)) {
                        sessionKeysToRemove.push(storageKey);
                    }
                }
                sessionKeysToRemove.forEach(k => sessionStorage.removeItem(k));

            } catch (error) {
                console.warn('Failed to clear browser cache:', error);
            }
        }
    }

    /**
     * Clear all cached data
     */
    clearAllCache(): void {
        this.timestamps.clear();
        
        if (typeof window !== 'undefined') {
            try {
                // Clear all assessment-related cache
                const keysToRemove: string[] = [];
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    if (key && (key.includes('assessment') || key.includes('recommendation') || key.includes('visualization'))) {
                        keysToRemove.push(key);
                    }
                }
                keysToRemove.forEach(key => localStorage.removeItem(key));

                // Clear session storage
                sessionStorage.clear();
            } catch (error) {
                console.warn('Failed to clear all browser cache:', error);
            }
        }
    }

    /**
     * Force browser to reload resources by manipulating cache headers
     */
    getNoCacheHeaders(): HeadersInit {
        return {
            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '0',
            'If-None-Match': '*',
            'If-Modified-Since': 'Thu, 01 Jan 1970 00:00:00 GMT'
        };
    }

    /**
     * Check if data is stale based on timestamp
     */
    isStale(key: string, maxAge: number = 30000): boolean {
        const timestamp = this.timestamps.get(key);
        if (!timestamp) return true;
        
        return (Date.now() - timestamp) > maxAge;
    }

    /**
     * Invalidate cache on assessment status change
     */
    invalidateAssessmentCache(assessmentId: string): void {
        const relatedKeys = [
            `assessment_${assessmentId}`,
            `recommendations_${assessmentId}`,
            `visualization_${assessmentId}`,
            `reports_${assessmentId}`,
            'assessments_list',
            'dashboard_data'
        ];

        relatedKeys.forEach(key => this.clearCache(key));
    }

    /**
     * Force refresh of React components by clearing their data cache
     */
    forceComponentRefresh(): void {
        if (typeof window !== 'undefined') {
            // Dispatch a custom event to force component refresh
            window.dispatchEvent(new CustomEvent('forceDataRefresh', {
                detail: { timestamp: Date.now() }
            }));
        }
    }
}

// Create singleton instance
export const cacheBuster = CacheBuster.getInstance();

// Utility functions
export const bustCache = (url: string, key?: string): string => {
    return cacheBuster.bustCache(url, key);
};

export const clearAssessmentCache = (assessmentId: string): void => {
    cacheBuster.invalidateAssessmentCache(assessmentId);
};

export const forceRefresh = (): void => {
    cacheBuster.forceComponentRefresh();
};

export const getNoCacheHeaders = (): HeadersInit => {
    return cacheBuster.getNoCacheHeaders();
};