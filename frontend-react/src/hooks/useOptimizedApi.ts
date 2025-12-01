/**
 * Optimized API Hooks - DRY principle for API calls
 *
 * Replaces duplicated fetch logic across 20+ components
 * with centralized, optimized hooks.
 */

import { useState, useEffect, useCallback, useRef } from 'react';

// ✅ Get API base URL from environment (client-side)
const getApiBaseUrl = () => {
  if (typeof window === 'undefined') {
    // Server-side: use environment variable or default
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  // Client-side: use environment variable or default
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  console.log('🔧 API Base URL:', baseUrl);
  return baseUrl;
};

// ✅ Build full URL with base URL
const buildFullUrl = (urlOrPath: string): string => {
  // If already absolute URL (starts with http/https), return as-is
  if (urlOrPath.startsWith('http://') || urlOrPath.startsWith('https://')) {
    return urlOrPath;
  }

  // Otherwise, prepend base URL
  const baseUrl = getApiBaseUrl();
  const fullUrl = `${baseUrl}${urlOrPath}`;
  console.log('🔧 Building full URL:', { input: urlOrPath, base: baseUrl, full: fullUrl });
  return fullUrl;
};

// ✅ Get authentication headers
const getAuthHeaders = (): HeadersInit => {
  if (typeof window === 'undefined') {
    return {};
  }

  const token = localStorage.getItem('auth_token');
  if (!token) {
    return {};
  }

  return {
    'Authorization': `Bearer ${token}`,
  };
};

// ✅ Generic data fetching hook with automatic cleanup
export function useApiData<T>(
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

  // ✅ Prevent state updates after unmount
  const isMounted = useRef(true);

  // ✅ Memoized fetch function
  const fetchData = useCallback(async () => {
    if (options?.enabled === false) return;

    setLoading(true);
    setError(null);

    try {
      const fullUrl = buildFullUrl(url);
      const response = await fetch(fullUrl, {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const json = await response.json();

      // ✅ Only update state if still mounted
      if (isMounted.current) {
        setData(json);
        options?.onSuccess?.(json);
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');

      if (isMounted.current) {
        setError(error);
        options?.onError?.(error);
      }
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  }, [url, options]);

  // ✅ Initial fetch
  useEffect(() => {
    fetchData();

    // ✅ Optional auto-refetch interval
    let intervalId: NodeJS.Timeout | undefined;

    if (options?.refetchInterval) {
      intervalId = setInterval(fetchData, options.refetchInterval);
    }

    // ✅ Cleanup
    return () => {
      isMounted.current = false;
      if (intervalId) clearInterval(intervalId);
    };
  }, [fetchData, options?.refetchInterval]);

  // ✅ Manual refetch function
  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch };
}

// ✅ Optimized mutation hook (POST, PUT, DELETE)
export function useApiMutation<TData, TVariables = any>(
  url: string,
  method: 'POST' | 'PUT' | 'DELETE' | 'PATCH' = 'POST'
) {
  const [data, setData] = useState<TData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const isMounted = useRef(true);

  useEffect(() => {
    return () => {
      isMounted.current = false;
    };
  }, []);

  const mutate = useCallback(
    async (variables: TVariables) => {
      setLoading(true);
      setError(null);

      try {
        const fullUrl = buildFullUrl(url);
        const response = await fetch(fullUrl, {
          method,
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders(),
          },
          body: JSON.stringify(variables),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const json = await response.json();

        if (isMounted.current) {
          setData(json);
        }

        return json;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Unknown error');

        if (isMounted.current) {
          setError(error);
        }

        throw error;
      } finally {
        if (isMounted.current) {
          setLoading(false);
        }
      }
    },
    [url, method]
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { data, loading, error, mutate, reset };
}

// ✅ Paginated data hook
export function usePaginatedApi<T>(
  baseUrl: string,
  options?: {
    initialPage?: number;
    pageSize?: number;
  }
) {
  const [page, setPage] = useState(options?.initialPage || 1);
  const [pageSize] = useState(options?.pageSize || 10);

  const url = `${baseUrl}?page=${page}&limit=${pageSize}`;

  const { data, loading, error, refetch } = useApiData<{
    items: T[];
    total: number;
    page: number;
    pages: number;
  }>(url);

  const nextPage = useCallback(() => {
    if (data && page < data.pages) {
      setPage((p) => p + 1);
    }
  }, [data, page]);

  const prevPage = useCallback(() => {
    if (page > 1) {
      setPage((p) => p - 1);
    }
  }, [page]);

  const goToPage = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);

  return {
    data: data?.items || [],
    total: data?.total || 0,
    page,
    pages: data?.pages || 0,
    pageSize,
    loading,
    error,
    nextPage,
    prevPage,
    goToPage,
    refetch,
    hasNext: data ? page < data.pages : false,
    hasPrev: page > 1,
  };
}

// ✅ Debounced search hook
export function useDebouncedSearch<T>(
  searchFn: (query: string) => Promise<T[]>,
  delay: number = 300
) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const timeoutRef = useRef<NodeJS.Timeout>();
  const isMounted = useRef(true);

  useEffect(() => {
    return () => {
      isMounted.current = false;
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    // Clear previous timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Don't search empty query
    if (!query.trim()) {
      setResults([]);
      return;
    }

    // Debounce search
    timeoutRef.current = setTimeout(async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await searchFn(query);

        if (isMounted.current) {
          setResults(data);
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Search failed');

        if (isMounted.current) {
          setError(error);
        }
      } finally {
        if (isMounted.current) {
          setLoading(false);
        }
      }
    }, delay);
  }, [query, searchFn, delay]);

  return { query, setQuery, results, loading, error };
}

// ✅ Optimistic update hook
export function useOptimisticMutation<TData, TVariables>(
  url: string,
  options: {
    optimisticUpdate?: (variables: TVariables) => TData;
    onSuccess?: (data: TData) => void;
    onError?: (error: Error, rollback: () => void) => void;
  }
) {
  const [data, setData] = useState<TData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const previousData = useRef<TData | null>(null);

  const mutate = useCallback(
    async (variables: TVariables) => {
      // ✅ Store previous state for rollback
      previousData.current = data;

      // ✅ Optimistic update (immediate UI feedback)
      if (options.optimisticUpdate) {
        const optimisticData = options.optimisticUpdate(variables);
        setData(optimisticData);
      }

      setLoading(true);
      setError(null);

      try {
        const fullUrl = buildFullUrl(url);
        const response = await fetch(fullUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders(),
          },
          body: JSON.stringify(variables),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();

        setData(result);
        options.onSuccess?.(result);

        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Mutation failed');

        // ✅ Rollback on error
        const rollback = () => {
          setData(previousData.current);
        };

        rollback();
        setError(error);
        options.onError?.(error, rollback);

        throw error;
      } finally {
        setLoading(false);
      }
    },
    [url, data, options]
  );

  return { data, loading, error, mutate };
}
// Cache bust v2
