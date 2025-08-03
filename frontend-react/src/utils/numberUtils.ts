/**
 * Utility functions for safe number formatting
 */

export const safeToFixed = (value: number | undefined | null, decimals: number = 1): string => {
    if (value === undefined || value === null || isNaN(value)) return '0';
    return value.toFixed(decimals);
};

export const safeNumber = (value: number | undefined | null, fallback: number = 0): number => {
    if (value === undefined || value === null || isNaN(value)) return fallback;
    return value;
};

export const safePercentage = (value: number | undefined | null, decimals: number = 1): string => {
    return `${safeToFixed(value, decimals)}%`;
};

export const formatDuration = (ms: number | undefined | null): string => {
    if (!ms || isNaN(ms)) return '0ms';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
};

export const formatBytes = (bytes: number | undefined | null): string => {
    if (!bytes || isNaN(bytes)) return '0 B';
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
};

export const safeSlice = <T>(array: T[] | undefined | null, start?: number, end?: number): T[] => {
    if (!array || !Array.isArray(array)) return [];
    return array.slice(start, end);
};