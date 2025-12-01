/**
 * FIXED API Hook - Forces correct URL construction
 */

import { useState, useEffect, useCallback, useRef } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function useApiDataFixed<T>(
  url: string,
  options?: {
    enabled?: boolean;
    refetchInterval?: number;
    onSuccess?: (data: T) => void;
    onError?: (error: Error) => void;
  }
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const isMounted = useRef(true);

  // Store options in refs to avoid dependency issues
  const enabledRef = useRef(options?.enabled);
  const onSuccessRef = useRef(options?.onSuccess);
  const onErrorRef = useRef(options?.onError);

  // Update refs when options change
  enabledRef.current = options?.enabled;
  onSuccessRef.current = options?.onSuccess;
  onErrorRef.current = options?.onError;

  const fetchData = useCallback(async () => {
    if (enabledRef.current === false) {
      console.log('⏸️ API Hook - Fetch disabled by options');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Build absolute URL
      const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
      console.log('✅ FIXED API Hook - Fetching from:', fullUrl);
      
      const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      
      const response = await fetch(fullUrl, {
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
      });

      console.log('📡 API Response Status:', response.status, response.statusText);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ API Error Response:', errorText);
        throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
      }

      const json = await response.json();
      console.log('✅ API Response Data:', json);

      if (isMounted.current) {
        console.log('💾 Setting data state...');
        setData(json);
        console.log('✅ Data state set successfully');
        onSuccessRef.current?.(json);
      } else {
        console.warn('⚠️ Component unmounted, skipping data update');
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      console.error('❌ API Hook Error:', error.message, err);

      if (isMounted.current) {
        setError(error);
        onErrorRef.current?.(error);
      }
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  }, [url]); // Only depend on URL, not options object

  useEffect(() => {
    isMounted.current = true;
    fetchData();

    let intervalId: NodeJS.Timeout | undefined;

    if (options?.refetchInterval) {
      intervalId = setInterval(fetchData, options.refetchInterval);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [fetchData, options?.refetchInterval]);

  // Separate effect for unmount cleanup
  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch };
}
