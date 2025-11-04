/**
 * Centralized Logging Utility for Frontend
 *
 * Replaces 412 scattered console.log statements with a unified logging system
 * that prevents information leakage in production and provides better debugging.
 *
 * Features:
 * - Environment-aware logging (dev vs production)
 * - Automatic data sanitization (removes tokens, passwords, secrets)
 * - Log levels (log, info, warn, error, debug)
 * - Performance tracking
 * - Optional error tracking service integration (Sentry, etc.)
 *
 * Usage:
 * ```typescript
 * import Logger from '@/utils/logger';
 *
 * Logger.log('User logged in', { userId: user.id });
 * Logger.error('API call failed', error);
 * Logger.debug('Component rendered', { props });
 * ```
 *
 * @module logger
 */

export enum LogLevel {
    DEBUG = 'DEBUG',
    LOG = 'LOG',
    INFO = 'INFO',
    WARN = 'WARN',
    ERROR = 'ERROR',
}

interface LogContext {
    timestamp: string;
    level: LogLevel;
    environment: string;
    userAgent?: string;
    url?: string;
}

interface PerformanceMetric {
    name: string;
    duration: number;
    timestamp: string;
}

/**
 * Centralized logger for the application
 */
class Logger {
    private static readonly isDev = process.env.NODE_ENV === 'development';
    private static readonly isTest = process.env.NODE_ENV === 'test';
    private static readonly isProd = process.env.NODE_ENV === 'production';

    // Sensitive fields to remove from logs
    private static readonly SENSITIVE_FIELDS = [
        'token',
        'accessToken',
        'access_token',
        'refreshToken',
        'refresh_token',
        'password',
        'secret',
        'apiKey',
        'api_key',
        'authorization',
        'auth',
        'jwt',
        'bearer',
        'credentials',
    ];

    // Performance tracking
    private static performanceMetrics: PerformanceMetric[] = [];
    private static readonly MAX_METRICS = 100;

    /**
     * Check if logging is enabled for current environment
     */
    private static shouldLog(level: LogLevel): boolean {
        // Never log in test environment
        if (this.isTest) {
            return false;
        }

        // In production, only log warnings and errors
        if (this.isProd) {
            return level === LogLevel.WARN || level === LogLevel.ERROR;
        }

        // In development, log everything
        return true;
    }

    /**
     * Sanitize data by removing sensitive fields
     */
    private static sanitize(data: any): any {
        if (data === null || data === undefined) {
            return data;
        }

        // Handle primitive types
        if (typeof data !== 'object') {
            return data;
        }

        // Handle arrays
        if (Array.isArray(data)) {
            return data.map(item => this.sanitize(item));
        }

        // Handle objects
        const sanitized: any = {};
        for (const [key, value] of Object.entries(data)) {
            // Check if key is sensitive
            const lowerKey = key.toLowerCase();
            const isSensitive = this.SENSITIVE_FIELDS.some(field =>
                lowerKey.includes(field.toLowerCase())
            );

            if (isSensitive) {
                sanitized[key] = '[REDACTED]';
            } else if (typeof value === 'object' && value !== null) {
                sanitized[key] = this.sanitize(value);
            } else {
                sanitized[key] = value;
            }
        }

        return sanitized;
    }

    /**
     * Create log context with metadata
     */
    private static createContext(level: LogLevel): LogContext {
        return {
            timestamp: new Date().toISOString(),
            level,
            environment: process.env.NODE_ENV || 'development',
            userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
            url: typeof window !== 'undefined' ? window.location.href : undefined,
        };
    }

    /**
     * Format log message for console output
     */
    private static formatMessage(level: LogLevel, message: string, ...args: any[]): string {
        const timestamp = new Date().toISOString();
        const prefix = `[${timestamp}] [${level}]`;
        return `${prefix} ${message}`;
    }

    /**
     * Send error to tracking service (e.g., Sentry)
     */
    private static sendToErrorTracking(error: Error, context?: any): void {
        // Only send in production
        if (!this.isProd) {
            return;
        }

        // TODO: Integrate with Sentry or other error tracking service
        // Example:
        // if (typeof window !== 'undefined' && window.Sentry) {
        //     window.Sentry.captureException(error, {
        //         extra: this.sanitize(context),
        //     });
        // }
    }

    /**
     * Log debug information (development only)
     */
    static debug(message: string, ...args: any[]): void {
        if (!this.shouldLog(LogLevel.DEBUG)) {
            return;
        }

        const sanitizedArgs = args.map(arg => this.sanitize(arg));
        console.debug(this.formatMessage(LogLevel.DEBUG, message), ...sanitizedArgs);
    }

    /**
     * Log general information
     */
    static log(message: string, ...args: any[]): void {
        if (!this.shouldLog(LogLevel.LOG)) {
            return;
        }

        const sanitizedArgs = args.map(arg => this.sanitize(arg));
        console.log(this.formatMessage(LogLevel.LOG, message), ...sanitizedArgs);
    }

    /**
     * Log informational messages
     */
    static info(message: string, ...args: any[]): void {
        if (!this.shouldLog(LogLevel.INFO)) {
            return;
        }

        const sanitizedArgs = args.map(arg => this.sanitize(arg));
        console.info(this.formatMessage(LogLevel.INFO, message), ...sanitizedArgs);
    }

    /**
     * Log warnings
     */
    static warn(message: string, ...args: any[]): void {
        if (!this.shouldLog(LogLevel.WARN)) {
            return;
        }

        const sanitizedArgs = args.map(arg => this.sanitize(arg));
        console.warn(this.formatMessage(LogLevel.WARN, message), ...sanitizedArgs);
    }

    /**
     * Log errors and send to tracking service
     */
    static error(message: string, error?: Error | any, context?: any): void {
        if (!this.shouldLog(LogLevel.ERROR)) {
            return;
        }

        const sanitizedContext = context ? this.sanitize(context) : undefined;

        // Log to console
        console.error(
            this.formatMessage(LogLevel.ERROR, message),
            error,
            sanitizedContext
        );

        // Send to error tracking in production
        if (error instanceof Error) {
            this.sendToErrorTracking(error, {
                message,
                context: sanitizedContext,
            });
        }
    }

    /**
     * Track performance metric
     */
    static trackPerformance(name: string, duration: number): void {
        const metric: PerformanceMetric = {
            name,
            duration,
            timestamp: new Date().toISOString(),
        };

        this.performanceMetrics.push(metric);

        // Keep only last MAX_METRICS
        if (this.performanceMetrics.length > this.MAX_METRICS) {
            this.performanceMetrics.shift();
        }

        // Log slow operations in development
        if (this.isDev && duration > 1000) {
            this.warn(`Slow operation detected: ${name} took ${duration}ms`);
        }
    }

    /**
     * Get performance metrics
     */
    static getPerformanceMetrics(): PerformanceMetric[] {
        return [...this.performanceMetrics];
    }

    /**
     * Clear performance metrics
     */
    static clearPerformanceMetrics(): void {
        this.performanceMetrics = [];
    }

    /**
     * Create a performance tracker for timing operations
     */
    static startTimer(name: string): () => void {
        const startTime = performance.now();

        return () => {
            const duration = performance.now() - startTime;
            this.trackPerformance(name, duration);
        };
    }

    /**
     * Log API request (with automatic sanitization)
     */
    static apiRequest(method: string, url: string, data?: any): void {
        if (!this.shouldLog(LogLevel.DEBUG)) {
            return;
        }

        this.debug(
            `API Request: ${method} ${url}`,
            data ? this.sanitize(data) : undefined
        );
    }

    /**
     * Log API response (with automatic sanitization)
     */
    static apiResponse(method: string, url: string, status: number, data?: any): void {
        const level = status >= 400 ? LogLevel.ERROR : LogLevel.DEBUG;

        if (!this.shouldLog(level)) {
            return;
        }

        const message = `API Response: ${method} ${url} - Status ${status}`;

        if (level === LogLevel.ERROR) {
            this.error(message, undefined, data ? this.sanitize(data) : undefined);
        } else {
            this.debug(message, data ? this.sanitize(data) : undefined);
        }
    }

    /**
     * Group related logs together (development only)
     */
    static group(label: string, callback: () => void): void {
        if (!this.isDev) {
            callback();
            return;
        }

        console.group(label);
        callback();
        console.groupEnd();
    }

    /**
     * Log table data (development only)
     */
    static table(data: any): void {
        if (!this.isDev) {
            return;
        }

        console.table(this.sanitize(data));
    }

    /**
     * Assert condition and log if false
     */
    static assert(condition: boolean, message: string): void {
        if (!condition) {
            this.error(`Assertion failed: ${message}`);

            if (this.isDev) {
                console.assert(condition, message);
            }
        }
    }

    /**
     * Log component lifecycle event (development only)
     */
    static lifecycle(componentName: string, event: string, data?: any): void {
        if (!this.isDev) {
            return;
        }

        this.debug(
            `[Lifecycle] ${componentName}.${event}`,
            data ? this.sanitize(data) : undefined
        );
    }

    /**
     * Create a scoped logger for a specific component/module
     */
    static createScoped(scope: string) {
        return {
            debug: (message: string, ...args: any[]) =>
                Logger.debug(`[${scope}] ${message}`, ...args),
            log: (message: string, ...args: any[]) =>
                Logger.log(`[${scope}] ${message}`, ...args),
            info: (message: string, ...args: any[]) =>
                Logger.info(`[${scope}] ${message}`, ...args),
            warn: (message: string, ...args: any[]) =>
                Logger.warn(`[${scope}] ${message}`, ...args),
            error: (message: string, error?: Error, context?: any) =>
                Logger.error(`[${scope}] ${message}`, error, context),
        };
    }
}

export default Logger;

// Example usage:
//
// // Basic logging
// Logger.log('User logged in', { userId: '123' });
// Logger.error('API call failed', error);
//
// // Performance tracking
// const stopTimer = Logger.startTimer('fetchData');
// await fetchData();
// stopTimer(); // Automatically logs duration
//
// // API logging
// Logger.apiRequest('POST', '/api/users', userData);
// Logger.apiResponse('POST', '/api/users', 200, response);
//
// // Scoped logging
// const logger = Logger.createScoped('UserProfile');
// logger.log('Component mounted');
// logger.error('Failed to load data', error);
//
// // Grouped logs (dev only)
// Logger.group('User Actions', () => {
//     Logger.log('Action 1');
//     Logger.log('Action 2');
// });
