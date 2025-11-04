/**
 * Centralized Authentication Token Storage
 *
 * This utility provides a single source of truth for authentication token management,
 * preventing inconsistent token storage across the application.
 */

export class AuthStorage {
    // Use a single, consistent key for all token storage
    private static readonly TOKEN_KEY = 'auth_token';
    private static readonly REFRESH_TOKEN_KEY = 'refresh_token';
    private static readonly USER_KEY = 'user_data';

    /**
     * Store authentication token
     */
    static setToken(token: string): void {
        if (typeof window !== 'undefined') {
            localStorage.setItem(this.TOKEN_KEY, token);
            // Clean up old token keys
            this.cleanupLegacyTokens();
        }
    }

    /**
     * Get authentication token
     */
    static getToken(): string | null {
        if (typeof window !== 'undefined') {
            return localStorage.getItem(this.TOKEN_KEY);
        }
        return null;
    }

    /**
     * Store refresh token
     */
    static setRefreshToken(token: string): void {
        if (typeof window !== 'undefined') {
            localStorage.setItem(this.REFRESH_TOKEN_KEY, token);
        }
    }

    /**
     * Get refresh token
     */
    static getRefreshToken(): string | null {
        if (typeof window !== 'undefined') {
            return localStorage.getItem(this.REFRESH_TOKEN_KEY);
        }
        return null;
    }

    /**
     * Store user data
     */
    static setUser(user: any): void {
        if (typeof window !== 'undefined') {
            localStorage.setItem(this.USER_KEY, JSON.stringify(user));
        }
    }

    /**
     * Get user data
     */
    static getUser(): any | null {
        if (typeof window !== 'undefined') {
            const userData = localStorage.getItem(this.USER_KEY);
            if (userData) {
                try {
                    return JSON.parse(userData);
                } catch (e) {
                    console.error('Failed to parse user data:', e);
                    return null;
                }
            }
        }
        return null;
    }

    /**
     * Clear all authentication data
     */
    static clearAuth(): void {
        if (typeof window !== 'undefined') {
            localStorage.removeItem(this.TOKEN_KEY);
            localStorage.removeItem(this.REFRESH_TOKEN_KEY);
            localStorage.removeItem(this.USER_KEY);
            // Also clear legacy keys
            this.cleanupLegacyTokens();
        }
    }

    /**
     * Check if user is authenticated
     */
    static isAuthenticated(): boolean {
        return this.getToken() !== null;
    }

    /**
     * Remove legacy token keys to prevent confusion
     */
    private static cleanupLegacyTokens(): void {
        if (typeof window !== 'undefined') {
            const legacyKeys = ['token', 'access_token', 'accessToken', 'refreshToken'];
            legacyKeys.forEach(key => {
                if (localStorage.getItem(key) !== null) {
                    localStorage.removeItem(key);
                }
            });
        }
    }

    /**
     * Migration helper: get token from any legacy location
     * Use this during transition period only
     */
    static getTokenFromAnySource(): string | null {
        if (typeof window !== 'undefined') {
            // Try official key first
            const token = this.getToken();
            if (token) return token;

            // Check legacy locations
            const legacyKeys = ['access_token', 'token', 'accessToken'];
            for (const key of legacyKeys) {
                const legacyToken = localStorage.getItem(key);
                if (legacyToken) {
                    // Migrate to official location
                    this.setToken(legacyToken);
                    return legacyToken;
                }
            }
        }
        return null;
    }
}

export default AuthStorage;
