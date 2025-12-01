/**
 * API Client Service for Infra Mind Frontend
 *
 * This service provides a centralized way to interact with the backend API,
 * including authentication, error handling, and request/response transformation.
 */

import { Assessment, BusinessRequirements, TechnicalRequirements } from '../store/slices/assessmentSlice';
import AuthStorage from '../utils/authStorage';

// API Configuration
// Always use the public URL that browsers can reach, even for SSR
const getApiBaseUrl = () => {
    // Always prefer the public API URL for consistency between SSR and client-side
    const envUrl = process.env.NEXT_PUBLIC_API_URL;
    if (envUrl) {
        return envUrl;
    }

    // Fallback to localhost for development
    return 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();
const API_VERSION = 'v2';
const API_PREFIX = `/api/v2`; // Use v2 prefix to match backend

// If env vars are missing, log a warning
if (!process.env.NEXT_PUBLIC_API_URL) {
    console.warn('⚠️ NEXT_PUBLIC_API_URL is not set! This may cause connection issues.');
}

// Cache busting utilities
const cacheBuster = {
    bustCache: (path: string, key?: string) => {
        const timestamp = Date.now();
        const separator = path.includes('?') ? '&' : '?';
        return `${path}${separator}t=${timestamp}${key ? `&key=${key}` : ''}`;
    }
};

const getNoCacheHeaders = () => ({
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
});

// WebSocket Configuration
const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

// Types
export interface ApiResponse<T> {
    data: T;
    message?: string;
    status: 'success' | 'error';
    timestamp: string;
}

export interface ApiError {
    error: string;
    message: string;
    status_code: number;
    request_id?: string;
}

export interface LoginRequest {
    email: string;
    password: string;
}

export interface LoginResponse {
    access_token: string;
    refresh_token?: string;
    token_type: string;
    expires_in: number;
    user_id: string;
    email: string;
    full_name: string;
    user?: any;
}

export interface MFARequiredResponse {
    mfa_required: boolean;
    temp_token: string;
    message: string;
}

export interface RegisterRequest {
    email: string;
    password: string;
    full_name: string;
    company?: string;
    job_title?: string;
}

export interface CreateAssessmentRequest {
    title: string;
    description?: string;
    business_goal?: string;
    priority?: 'low' | 'medium' | 'high' | 'critical';
    business_requirements: BusinessRequirements;
    technical_requirements: TechnicalRequirements;
    source?: string;
    tags?: string[];
}

export interface Recommendation {
    id: string;
    assessment_id: string;
    agent_name: string;
    title: string;
    summary: string;
    confidence_level: string;
    confidence_score: number;
    business_alignment?: number;
    recommended_services: Array<{
        service_name: string;
        provider: string;
        service_category: string;
        estimated_monthly_cost: string;
        cost_model: string;
        configuration: Record<string, unknown>;
        reasons: string[];
        alternatives: string[];
        setup_complexity: 'low' | 'medium' | 'high';
        implementation_time_hours: number;
    }>;
    cost_estimates: {
        total_monthly?: number;
        annual_savings?: number;
        [key: string]: number | undefined;
    };
    total_estimated_monthly_cost: string;
    implementation_steps: string[];
    prerequisites: string[];
    risks_and_considerations: string[];
    business_impact: 'low' | 'medium' | 'high';
    alignment_score: number;
    tags: string[];
    priority: 'low' | 'medium' | 'high';
    category: string;
    pros?: string[];
    cons?: string[];
    implementation_complexity?: 'low' | 'medium' | 'high';
    status?: 'pending' | 'approved' | 'rejected';
    created_at: string;
    updated_at: string;
}

// Backend report structure matching actual API response
export interface Report {
    id: string;
    assessment_id: string;
    user_id: string;
    title: string;
    description: string;
    report_type: string;
    format: string;
    status: 'completed' | 'generating' | 'failed' | 'pending';
    progress_percentage: number;
    sections: string[];
    total_pages: number;
    word_count: number;
    file_path: string;
    file_size_bytes: number;
    generated_by: string[];
    generation_time_seconds: number;
    completeness_score: number;
    confidence_score: number;
    priority: string;
    tags: string[];
    error_message?: string;
    retry_count: number;
    created_at: string;
    updated_at: string;
    completed_at: string;
    // Additional frontend fields for compatibility
    assessmentId?: string;
    generated_at?: string;
    estimated_savings?: number;
}

export interface CloudService {
    id: string;
    name: string;
    provider: string; // Changed to allow any provider string (lowercase)
    category: string;
    description: string;
    pricing: {
        model?: string;
        starting_price: number;
        unit: string;
    };
    features: string[];
    rating: number;
    compliance: string[];
    region_availability: string[];
    use_cases?: string[];
    integration?: string[];
    managed?: boolean;
}

// API Client Class
class ApiClient {
    private baseURL: string;

    constructor() {
        // Set baseURL dynamically based on environment
        this.baseURL = getApiBaseUrl() + API_PREFIX;

        // Clear old tokens that might be missing required claims
        this.clearOldTokens();
    }

    // Token management - now using centralized AuthStorage
    private getStoredToken(): string | null {
        // Use migration helper during transition period
        return AuthStorage.getTokenFromAnySource();
    }

    public setStoredToken(token: string): void {
        AuthStorage.setToken(token);
    }

    public removeStoredToken(): void {
        AuthStorage.clearAuth();
    }

    // Clear old tokens that might be missing required claims
    public clearOldTokens(): void {
        const token = AuthStorage.getToken();
        if (token) {
            try {
                // Decode token without verification to check claims
                const parts = token.split('.');
                if (parts.length === 3) {
                    const payload = JSON.parse(atob(parts[1]));
                    // If token is missing required claims, remove it
                    const requiredClaims = ['iss', 'aud', 'token_type', 'jti'];
                    const missingClaims = requiredClaims.filter(claim => !payload[claim]);
                    if (missingClaims.length > 0) {
                        console.log('🔄 Removing old token missing claims:', missingClaims);
                        AuthStorage.clearAuth();
                    }
                }
            } catch (error) {
                // If we can't decode the token, it's probably invalid
                console.log('🔄 Removing invalid token');
                AuthStorage.clearAuth();
            }
        }
    }

    // HTTP request helper with enhanced error handling and loading states
    private async request<T>(
        endpoint: string,
        options: RequestInit & { useFullUrl?: boolean } = {}
    ): Promise<T> {
        const { useFullUrl, ...fetchOptions } = options;
        const url = useFullUrl ? endpoint : `${this.baseURL}${endpoint}`;

        const token = this.getStoredToken();

        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            // Aggressive cache busting headers
            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '0',
            'If-None-Match': '*',
            'If-Modified-Since': 'Thu, 01 Jan 1970 00:00:00 GMT',
            // Temporarily remove custom headers to debug CORS issues
            // 'X-Client-Version': '2.0.0',
            // 'X-Request-ID': this.generateRequestId(),
            ...(fetchOptions.headers as Record<string, string> || {}),
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const config: RequestInit = {
            ...fetchOptions,
            headers,
            // Add timeout for requests - shorter for form suggestions
            signal: AbortSignal.timeout(60000), // 60 second timeout to handle slower responses
        };

        try {
            console.log('🌐 API Request:', { method: config.method || 'GET', url, hasAuth: !!headers.Authorization });
            const response = await fetch(url, config);

            if (!response.ok) {
                console.error('❌ API Request failed:', {
                    status: response.status,
                    statusText: response.statusText,
                    url
                });
                let errorData: ApiError;

                try {
                    errorData = await response.json();
                } catch {
                    errorData = {
                        error: 'Network Error',
                        message: `HTTP ${response.status}: ${response.statusText}`,
                        status_code: response.status,
                    };
                }

                // Handle different error types
                switch (response.status) {
                    case 401:
                        // Only logout for certain 401 errors, not all of them
                        const shouldLogout = this.shouldLogoutOn401(errorData, endpoint);
                        if (shouldLogout) {
                            console.log('🔒 Authentication failed - logging out user');
                            this.removeStoredToken();
                            if (typeof window !== 'undefined') {
                                window.location.href = '/auth/login';
                            }
                        } else {
                            console.warn('🔒 401 error but not logging out:', errorData.message);
                        }
                        break;
                    case 403:
                        throw new Error('Access denied. Please check your permissions.');
                    case 404:
                        // For delete operations, 404 might be expected (already deleted)
                        if (config.method === 'DELETE') {
                            console.log('✅ Resource already deleted (404)');
                            return null; // Return null for successful deletion of non-existent resource
                        }
                        throw new Error('Resource not found.');
                    case 429:
                        throw new Error('Too many requests. Please try again later.');
                    case 500:
                        throw new Error('Server error. Please try again later.');
                    case 503:
                        throw new Error('Service temporarily unavailable.');
                    default:
                        break;
                }

                throw new Error(errorData.message || errorData.error);
            }

            // Handle different content types and empty responses
            const contentType = response.headers.get('content-type');

            // Check if response has content
            const contentLength = response.headers.get('content-length');
            const hasContent = contentLength !== '0' && contentLength !== null;

            // Handle empty responses (common for DELETE operations)
            if (!hasContent) {
                return undefined as unknown as T;
            }

            if (contentType?.includes('application/json')) {
                try {
                    return await response.json();
                } catch (error) {
                    console.warn('Failed to parse JSON response, might be empty:', error);
                    return undefined as unknown as T;
                }
            } else if (contentType?.includes('text/')) {
                return await response.text() as unknown as T;
            } else {
                return await response.blob() as unknown as T;
            }
        } catch (error) {
            if (error instanceof Error) {
                if (error.name === 'AbortError') {
                    throw new Error('Request timeout. Please try again.');
                }

                // Handle actual network connectivity issues (not HTTP error responses)
                if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError') || error.name === 'TypeError') {
                    console.error(`Network request failed: ${config.method || 'GET'} ${endpoint}`, error);
                    console.error('Full error details:', {
                        message: error.message,
                        name: error.name,
                        stack: error.stack,
                        url: url
                    });
                    throw new Error(`API request failed: ${error.message}. Check browser console for details.`);
                }

                console.error(`API request failed: ${config.method || 'GET'} ${endpoint}`, error);
                throw error;
            }
            throw new Error('An unexpected error occurred');
        }
    }

    // Generate unique request ID for tracking
    private generateRequestId(): string {
        return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    // Determine if a 401 error should trigger logout
    private shouldLogoutOn401(errorData: ApiError, endpoint: string): boolean {
        // Always logout for explicit authentication endpoints
        if (endpoint.includes('/auth/')) {
            return true;
        }

        // Don't logout for missing resources or malformed requests
        if (errorData.message?.includes('not found') ||
            errorData.message?.includes('invalid format') ||
            errorData.message?.includes('malformed')) {
            return false;
        }

        // Check if this is a token-related error that should cause logout
        const tokenErrors = [
            'invalid token',
            'token expired',
            'token has been revoked',
            'authentication required',
            'token validation failed',
            'invalid token signature',
            'invalid token issuer',
            'invalid token audience',
            'unauthorized',
            'could not validate credentials'
        ];

        const errorMessage = errorData.message?.toLowerCase() || errorData.error?.toLowerCase() || '';
        const shouldLogout = tokenErrors.some(err => errorMessage.includes(err));

        // More aggressive: if we get multiple 401s in a row, logout
        // This prevents users from getting stuck with expired tokens
        if (!shouldLogout && errorData.status_code === 401) {
            // Check if we have a stored token - if yes and getting 401, likely expired
            const hasToken = typeof window !== 'undefined' && typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
            if (hasToken) {
                console.log('🔒 401 error with stored token - likely expired, logging out');
                return true;
            }
        }

        console.log('🔍 Checking 401 error:', {
            endpoint,
            errorMessage,
            shouldLogout,
            errorData
        });

        return shouldLogout;
    }

    // Debug connection method
    async debugConnection(): Promise<any> {
        console.log('🔍 Starting connection debug...');

        const testUrls = [
            'http://localhost:8000',
            'http://127.0.0.1:8000',
            'http://api:8000'
        ];

        const debugInfo = {
            currentConfig: {
                baseURL: this.baseURL,
                environment: typeof window !== 'undefined' ? 'client' : 'server',
                envVars: {
                    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
                    API_URL: process.env.API_URL,
                    NODE_ENV: process.env.NODE_ENV
                }
            },
            testResults: {} as any
        };

        // Test each URL
        for (const testUrl of testUrls) {
            try {
                console.log(`🧪 Testing ${testUrl}/health...`);
                const response = await fetch(`${testUrl}/health`, {
                    method: 'GET',
                    headers: { 'Accept': 'application/json' },
                    signal: AbortSignal.timeout(5000)
                });

                debugInfo.testResults[testUrl] = {
                    success: true,
                    status: response.status,
                    statusText: response.statusText,
                    headers: Object.fromEntries(response.headers.entries())
                };

                if (response.ok) {
                    console.log(`✅ ${testUrl} - SUCCESS (${response.status})`);
                } else {
                    console.log(`⚠️ ${testUrl} - HTTP Error (${response.status})`);
                }
            } catch (error) {
                console.log(`❌ ${testUrl} - FAILED: ${error instanceof Error ? error.message : 'Unknown error'}`);
                debugInfo.testResults[testUrl] = {
                    success: false,
                    error: error instanceof Error ? error.message : 'Unknown error'
                };
            }
        }

        console.log('🔍 Connection debug complete:', debugInfo);
        return debugInfo;
    }

    // Generic HTTP methods
    async get<T>(endpoint: string): Promise<T> {
        return this.request<T>(endpoint, {
            method: 'GET'
        });
    }

    async post<T>(endpoint: string, data?: any): Promise<T> {
        return this.request<T>(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put<T>(endpoint: string, data?: any): Promise<T> {
        return this.request<T>(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async delete<T>(endpoint: string): Promise<T> {
        return this.request<T>(endpoint, {
            method: 'DELETE'
        });
    }

    // Authentication methods
    async login(credentials: LoginRequest): Promise<LoginResponse | MFARequiredResponse> {
        const response = await this.request<LoginResponse | MFARequiredResponse>('/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials),
        });

        // Check if MFA is required
        if ('mfa_required' in response && response.mfa_required) {
            return response as MFARequiredResponse;
        }

        // Normal login response
        const loginResponse = response as LoginResponse;
        this.setStoredToken(loginResponse.access_token);
        return loginResponse;
    }

    async register(userData: RegisterRequest): Promise<LoginResponse> {
        const response = await this.request<LoginResponse>('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData),
        });

        this.setStoredToken(response.access_token);
        return response;
    }

    async googleLogin(credential: string): Promise<LoginResponse> {
        const response = await this.request<LoginResponse>('/auth/google', {
            method: 'POST',
            body: JSON.stringify({ credential }),
        });

        this.setStoredToken(response.access_token);
        return response;
    }


    async logout(): Promise<void> {
        try {
            await this.request('/auth/logout', {
                method: 'POST',
            });
        } finally {
            this.removeStoredToken();
        }
    }

    async refreshToken(): Promise<LoginResponse> {
        const response = await this.request<LoginResponse>('/auth/refresh', {
            method: 'POST',
        });

        this.setStoredToken(response.access_token);
        return response;
    }

    // Assessment methods
    async createAssessment(assessmentData: CreateAssessmentRequest): Promise<Assessment> {
        console.log('🔄 Creating assessment with data:', assessmentData);
        console.log('📊 Business requirements:', assessmentData.business_requirements);
        console.log('⚙️ Technical requirements:', assessmentData.technical_requirements);

        try {
            const result = await this.request<Assessment>('/assessments/', {
                method: 'POST',
                body: JSON.stringify(assessmentData),
            });
            console.log('✅ Assessment created successfully:', result);
            return result;
        } catch (error) {
            console.error('❌ Assessment creation failed:', error);
            console.error('📝 Failed assessment data:', assessmentData);
            throw error;
        }
    }

    async createSimpleAssessment(data: { title: string; description?: string }): Promise<Assessment> {
        return this.request<Assessment>('/assessments/simple', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getAssessments(): Promise<{ assessments: Assessment[], total: number, page: number, limit: number, pages: number }> {
        // Aggressive cache busting for assessments
        const timestamp = Date.now();
        const random = Math.random().toString(36).substr(2, 9);
        const url = `/assessments/?_t=${timestamp}&_cb=${random}&_fresh=true`;
        const response = await this.request<{ assessments: Assessment[], total: number, page: number, limit: number, pages: number }>(url, {
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        });
        return response;
    }

    async getAssessment(id: string): Promise<Assessment> {
        // Use cache buster for individual assessment
        const url = cacheBuster.bustCache(`/assessments/${id}`, `assessment_${id}`);
        return this.request<Assessment>(url, {
            headers: {
                ...getNoCacheHeaders()
            }
        });
    }

    async updateAssessment(id: string, updates: Partial<Assessment>): Promise<Assessment> {
        return this.request<Assessment>(`/assessments/${id}`, {
            method: 'PUT',
            body: JSON.stringify(updates),
        });
    }

    async deleteAssessment(id: string): Promise<void> {
        return this.request<void>(`/assessments/${id}`, {
            method: 'DELETE',
        });
    }

    // Phase 2: Bulk Operations
    async bulkDeleteAssessments(ids: string[]): Promise<void> {
        return this.request<void>('/assessments/bulk/delete', {
            method: 'POST',
            body: JSON.stringify({ assessment_ids: ids }),
        });
    }

    async bulkUpdateAssessments(ids: string[], updates: Partial<Assessment>): Promise<void> {
        return this.request<void>('/assessments/bulk/update', {
            method: 'POST',
            body: JSON.stringify({
                assessment_ids: ids,
                updates
            }),
        });
    }

    async getAssessmentVisualizationData(id: string): Promise<{
        assessment_id: string;
        data: {
            assessment_results: Array<{
                category: string;
                currentScore: number;
                targetScore: number;
                improvement: number;
                color: string;
            }>;
            overall_score: number;
            recommendations_count: number;
            completion_status: string;
            generated_at: string;
            fallback_data?: boolean;
        };
        generated_at: string;
        status: string;
    }> {
        // Use cache buster to ensure fresh visualization data
        const url = cacheBuster.bustCache(`/assessments/${id}/visualization-data`, `visualization_${id}`);
        return this.request<{
            assessment_id: string;
            data: {
                assessment_results: Array<{
                    category: string;
                    currentScore: number;
                    targetScore: number;
                    improvement: number;
                    color: string;
                }>;
                overall_score: number;
                recommendations_count: number;
                completion_status: string;
                generated_at: string;
                fallback_data?: boolean;
            };
            generated_at: string;
            status: string;
        }>(url, {
            // Disable caching for fresh data
            headers: {
                ...getNoCacheHeaders()
            }
        });
    }

    // Draft assessment methods
    async createDraftAssessment(draftData: {
        title: string;
        draft_data: Record<string, unknown>;
        current_step: number;
        status: 'draft';
    }): Promise<Assessment> {
        return this.request<Assessment>('/assessments/', {
            method: 'POST',
            body: JSON.stringify({
                title: draftData.title,
                status: 'draft',
                draft_data: draftData.draft_data,
                current_step: draftData.current_step,
                // Add minimal required fields for validation
                business_requirements: {
                    business_goals: [],
                    growth_projection: 'stable',
                    budget_constraints: 50000,
                    team_structure: 'small',
                    compliance_requirements: ['none'],
                    project_timeline_months: 6
                },
                technical_requirements: {
                    current_infrastructure: 'on_premise',
                    workload_types: ['web_application'],
                    performance_requirements: {},
                    scalability_requirements: {},
                    security_requirements: {},
                    integration_requirements: {}
                }
            }),
        });
    }

    async updateDraftAssessment(id: string, draftData: {
        draft_data: Record<string, unknown>;
        current_step: number;
    }): Promise<Assessment> {
        const payload = {
            draft_data: draftData.draft_data,
            current_step: draftData.current_step,
            status: 'draft'
        };
        console.log('💾 updateDraftAssessment payload:', payload);
        console.log('💾 draft_data keys:', Object.keys(draftData.draft_data));

        return this.request<Assessment>(`/assessments/${id}`, {
            method: 'PUT',
            body: JSON.stringify(payload),
        });
    }

    async deleteAssessment(id: string): Promise<void> {
        await this.request<void>(`/assessments/${id}`, {
            method: 'DELETE',
        });
    }

    // Recommendation methods
    async generateRecommendations(assessmentId: string): Promise<{ workflow_id: string }> {
        return this.request<{ workflow_id: string }>(`/recommendations/${assessmentId}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                agent_names: null,
                priority_override: null,
                custom_config: null
            }),
        });
    }

    async getRecommendations(assessmentId: string): Promise<Recommendation[]> {
        // Super aggressive cache busting for recommendations
        const timestamp = Date.now();
        const random = Math.random().toString(36).substr(2, 9);
        const microtime = performance.now();
        const url = `/recommendations/${assessmentId}?_t=${timestamp}&_cb=${random}&_mt=${microtime}&_nocache=true&_fresh=true`;

        try {
            const response = await this.request<{ recommendations: Recommendation[], total: number, assessment_id: string, summary: any }>(url, {
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0, s-maxage=0',
                    'Pragma': 'no-cache',
                    'Expires': '0',
                    'If-None-Match': '*',
                    'If-Modified-Since': 'Thu, 01 Jan 1970 00:00:00 GMT'
                }
            });
            // Safely return recommendations array, defaulting to empty array if not present
            return Array.isArray(response?.recommendations) ? response.recommendations : [];
        } catch (error) {
            console.warn(`Failed to load recommendations for assessment ${assessmentId}:`, error);
            // Return empty array on error to prevent frontend crashes
            return [];
        }
    }

    async updateRecommendationStatus(
        recommendationId: string,
        status: 'approved' | 'rejected'
    ): Promise<Recommendation> {
        return this.request<Recommendation>(`/recommendations/${recommendationId}/status`, {
            method: 'PUT',
            body: JSON.stringify({ status }),
        });
    }

    // ML Interaction Tracking Methods
    async trackRecommendationInteraction(
        recommendationId: string,
        interactionType: 'view' | 'click' | 'implement' | 'save' | 'share' | 'rate' | 'dismiss',
        interactionValue?: number,
        context?: Record<string, any>
    ): Promise<{ status: string; message: string }> {
        try {
            return await this.request<{ status: string; message: string }>(
                `/recommendations/interact/${recommendationId}`,
                {
                    method: 'POST',
                    body: JSON.stringify({
                        interaction_type: interactionType,
                        interaction_value: interactionValue,
                        context: context || {}
                    }),
                }
            );
        } catch (error) {
            console.error(`Failed to track ${interactionType} interaction:`, error);
            // Fail silently - don't disrupt user experience if tracking fails
            return { status: 'error', message: 'Failed to track interaction' };
        }
    }

    async getRecommendationStats(recommendationId: string): Promise<any> {
        return this.request<any>(`/recommendations/stats/${recommendationId}`, {
            method: 'GET',
        });
    }

    async getUserInteractionHistory(limit: number = 100): Promise<any> {
        return this.request<any>(`/recommendations/user/history?limit=${limit}`, {
            method: 'GET',
        });
    }

    // Report methods
    async generateReport(assessmentId: string, options?: {
        template?: string;
        sections?: string[];
        format?: 'pdf' | 'docx' | 'html';
    }): Promise<{ report_id: string; workflow_id: string }> {
        return this.request<{ report_id: string; workflow_id: string }>(`/reports/assessment/${assessmentId}/generate`, {
            method: 'POST',
            body: JSON.stringify(options || {}),
        });
    }

    async getReports(assessmentId?: string): Promise<Report[]> {
        if (assessmentId) {
            // Get reports for specific assessment
            const timestamp = Date.now();
            const response = await this.request<{ reports: Report[] }>(
                `/reports/assessment/${assessmentId}?t=${timestamp}`,
                {
                    headers: {
                        'Cache-Control': 'no-cache'
                    }
                }
            );
            return response.reports || [];
        } else {
            // Use the new endpoint to get all user reports
            try {
                console.log('🔄 Getting all user reports...');
                const reports = await this.request<Report[]>('/reports/all', {
                    headers: {
                        'Cache-Control': 'no-cache'
                    }
                });
                console.log(`🔄 Found ${reports.length} reports for user`);
                return reports || [];
            } catch (error) {
                console.error('Failed to fetch all user reports:', error);
                // Fallback to old behavior if new endpoint fails
                try {
                    console.log('🔄 Trying fallback method...');
                    const assessmentsResponse = await this.getAssessments();
                    if (assessmentsResponse.assessments && assessmentsResponse.assessments.length > 0) {
                        const latestAssessment = assessmentsResponse.assessments[0];
                        console.log(`🔄 Fallback: Getting reports for latest assessment: ${latestAssessment.id}`);
                        return await this.getReports(latestAssessment.id);
                    } else {
                        console.log('🔄 No assessments found, returning empty array');
                        return [];
                    }
                } catch (fallbackError) {
                    console.error('Fallback also failed:', fallbackError);
                    return [];
                }
            }
        }
    }

    async getReport(reportId: string, assessmentId?: string): Promise<Report> {
        if (assessmentId) {
            return this.request<Report>(`/reports/assessment/${assessmentId}/reports/${reportId}`);
        }
        // Fallback - use the generic endpoint
        return this.request<Report>(`/reports/${reportId}`);
    }

    async getReportById(reportId: string): Promise<Report> {
        return this.request<Report>(`/reports/${reportId}`);
    }

    async downloadReport(reportId: string, format: 'pdf' | 'docx' | 'html' = 'pdf', assessmentId?: string): Promise<Blob> {
        let downloadUrl;
        if (assessmentId) {
            downloadUrl = `${this.baseURL}/reports/assessment/${assessmentId}/reports/${reportId}/download?format=${format}`;
        } else {
            // Try to get assessment ID from the report data first
            try {
                const report = await this.getReport(reportId);
                if (report && (report as any).assessment_id) {
                    downloadUrl = `${this.baseURL}/reports/assessment/${(report as any).assessment_id}/reports/${reportId}/download?format=${format}`;
                } else {
                    downloadUrl = `${this.baseURL}/reports/${reportId}/download?format=${format}`;
                }
            } catch {
                downloadUrl = `${this.baseURL}/reports/${reportId}/download?format=${format}`;
            }
        }

        const response = await fetch(downloadUrl, {
            headers: {
                'Authorization': `Bearer ${this.getStoredToken()}`,
            },
        });

        if (!response.ok) {
            throw new Error('Failed to download report');
        }

        return response.blob();
    }

    async shareReport(reportId: string, shareOptions: {
        user_email: string;
        permission?: 'view' | 'edit' | 'admin';
    }): Promise<{ message: string }> {
        return this.request<{ message: string }>(`/v1/reports/${reportId}/share`, {
            method: 'POST',
            body: JSON.stringify(shareOptions),
        });
    }

    async createPublicLink(reportId: string): Promise<{ public_token: string }> {
        return this.request<{ public_token: string }>(`/v1/reports/${reportId}/public-link`, {
            method: 'POST',
        });
    }

    // Monitoring methods
    async getWorkflowStatus(workflowId: string): Promise<{
        id: string;
        status: 'pending' | 'running' | 'completed' | 'failed';
        progress: number;
        current_step: string;
        steps: Array<{
            name: string;
            status: 'pending' | 'running' | 'completed' | 'failed';
            started_at?: string;
            completed_at?: string;
        }>;
        created_at: string;
        updated_at: string;
    }> {
        return this.request(`/monitoring/workflows/${workflowId}`);
    }

    async getSystemHealth(): Promise<{
        status: 'healthy' | 'degraded' | 'unhealthy';
        components: Record<string, {
            status: 'healthy' | 'degraded' | 'unhealthy';
            response_time_ms?: number;
            error_rate_percent?: number;
        }>;
        timestamp: string;
    }> {
        const response = await this.request<{
            success: boolean;
            data: {
                overall_status: 'healthy' | 'degraded' | 'unhealthy';
                components: Record<string, {
                    status: 'healthy' | 'degraded' | 'unhealthy';
                    response_time_ms?: number;
                    last_check?: string;
                    error_message?: string;
                }>;
                timestamp: string;
            };
        }>('/monitoring/health');

        return {
            status: response.data.overall_status,
            components: response.data.components,
            timestamp: response.data.timestamp
        };
    }

    // User management methods
    async getCurrentUser(): Promise<{
        id: string;
        email: string;
        full_name: string;
        company_name?: string;
        job_title?: string;
        role: string;
        is_active: boolean;
        created_at: string;
    }> {
        return this.request('/auth/profile');
    }

    async updateUserProfile(updates: {
        full_name?: string;
        company?: string;
        job_title?: string;
        preferences?: Record<string, unknown>;
    }): Promise<void> {
        return this.request('/auth/profile', {
            method: 'PUT',
            body: JSON.stringify(updates),
        });
    }

    // WebSocket connection methods
    createWebSocketConnection(assessmentId?: string): WebSocket {
        const token = this.getStoredToken();
        const wsUrl = assessmentId
            ? `${WS_BASE_URL}/ws?token=${token}&assessment_id=${assessmentId}`
            : `${WS_BASE_URL}/ws?token=${token}`;

        return new WebSocket(wsUrl);
    }

    // Real-time progress tracking
    async subscribeToWorkflowProgress(workflowId: string, callback: (progress: unknown) => void): Promise<WebSocket> {
        const ws = this.createWebSocketConnection();

        ws.onopen = () => {
            ws.send(JSON.stringify({
                type: 'subscribe',
                data: { workflow_id: workflowId }
            }));
        };

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'workflow_progress' && message.data.workflow_id === workflowId) {
                callback(message.data);
            }
        };

        return ws;
    }

    // Cloud Services methods
    async getCloudServices(options?: {
        provider?: string;
        category?: string;
        search?: string;
        limit?: number;
        offset?: number;
    }): Promise<{
        services: CloudService[];
        pagination: {
            total: number;
            limit: number;
            offset: number;
            has_more: boolean;
        };
        filters: {
            provider?: string;
            category?: string;
            search?: string;
        };
    }> {
        const params = new URLSearchParams();

        if (options?.provider) {
            params.append('provider', options.provider);
        }
        if (options?.category) {
            params.append('category', options.category);
        }
        if (options?.search) {
            params.append('search', options.search);
        }
        if (options?.limit) {
            params.append('limit', options.limit.toString());
        }
        if (options?.offset) {
            params.append('offset', options.offset.toString());
        }

        return this.request<{
            services: CloudService[];
            pagination: {
                total: number;
                limit: number;
                offset: number;
                has_more: boolean;
            };
            filters: {
                provider?: string;
                category?: string;
                search?: string;
            };
        }>(`${API_BASE_URL}/api/cloud-services?${params.toString()}`, { useFullUrl: true });
    }

    async getCloudServiceDetails(serviceId: string): Promise<CloudService> {
        return this.request<CloudService>(`${API_BASE_URL}/api/cloud-services/${serviceId}`, { useFullUrl: true });
    }

    async compareCloudServices(serviceIds: string[]): Promise<{
        services: CloudService[];
        comparison: {
            price_comparison: any;
            feature_overlap: any;
            compliance_comparison: any;
            recommendations: any[];
        };
        compared_count: number;
    }> {
        const serviceIdsParam = serviceIds.join(',');
        return this.request(`/cloud-services/compare/${serviceIdsParam}`);
    }

    async getCloudServiceProviders(): Promise<{
        providers: Array<{
            name: string;
            service_count: number;
            categories: string[];
        }>;
        total_providers: number;
    }> {
        return this.request(`${API_BASE_URL}/api/cloud-services/providers`, { useFullUrl: true });
    }

    async getCloudServiceCategories(): Promise<{
        categories: Array<{
            name: string;
            service_count: number;
            providers: string[];
        }>;
        total_categories: number;
    }> {
        return this.request(`${API_BASE_URL}/api/cloud-services/categories`, { useFullUrl: true });
    }

    async getCloudServicesStats(): Promise<{
        total_services: number;
        providers: Record<string, any>;
        categories: Record<string, any>;
        pricing: {
            min_price: number;
            max_price: number;
            avg_price: number;
        };
        compliance_standards: Record<string, number>;
        most_common_compliance: string;
    }> {
        return this.request('/cloud-services/stats');
    }

    // Utility methods
    isAuthenticated(): boolean {
        return !!this.getStoredToken();
    }

    getAuthToken(): string | null {
        return this.getStoredToken();
    }

    // Health check method
    async checkHealth(): Promise<{
        status: string;
        version?: string;
        timestamp: string;
        services?: Record<string, string>;
        system?: any;
        performance?: any;
    }> {
        try {
            // Use the base URL directly for health endpoint (no API prefix needed)
            const healthUrl = `${getApiBaseUrl()}/health`;
            console.log('Health check attempting to connect to:', healthUrl);

            const response = await fetch(healthUrl, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                // Add timeout for health check
                signal: AbortSignal.timeout(10000), // 10 second timeout
            });

            if (!response.ok) {
                console.error(`Health check HTTP error: ${response.status} ${response.statusText}`);
                throw new Error(`Health check failed: ${response.status}`);
            }

            const healthData = await response.json();
            console.log('Health check successful:', healthData);
            return healthData;
        } catch (error) {
            console.error('Health check error details:', {
                error: error,
                message: error instanceof Error ? error.message : 'Unknown error',
                healthUrl: `${getApiBaseUrl()}/health`,
                baseURL: getApiBaseUrl(),
                environment: typeof window !== 'undefined' ? 'client' : 'server',
                envVars: {
                    NEXT_PUBLIC_API_URL: typeof window !== 'undefined' ? process.env.NEXT_PUBLIC_API_URL : 'N/A',
                    API_URL: typeof window === 'undefined' ? process.env.API_URL : 'N/A'
                }
            });
            // Return a fallback response instead of throwing
            return {
                status: 'connection_failed',
                error: error instanceof Error ? error.message : 'Unknown error',
                timestamp: new Date().toISOString(),
                system: {
                    cpu_usage_percent: 0,
                    memory_usage_percent: 0,
                    active_connections: 0
                },
                performance: {
                    avg_response_time_ms: 0,
                    error_rate_percent: 0
                }
            };
        }
    }

    // Get system metrics
    async getSystemMetrics(): Promise<{
        active_connections: number;
        active_workflows: number;
        system_load: number;
        response_time_avg: number;
    }> {
        try {
            return this.request('/admin/metrics');
        } catch (error) {
            console.warn('System metrics endpoint not available, using fallback data:', error);
            // Return fallback metrics data
            return {
                active_connections: 5,
                active_workflows: 2,
                system_load: 25.5,
                response_time_avg: 145.2
            };
        }
    }

    // Helper method for chat API requests (uses v1 API path)
    private async chatRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
        const url = `/api/v1/chat${endpoint}`;
        const response = await fetch(`${API_BASE_URL}${url}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...(this.getStoredToken() && { 'Authorization': `Bearer ${this.getStoredToken()}` }),
                ...getNoCacheHeaders(),
                ...options?.headers,
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // Handle empty responses
        const contentType = response.headers.get('content-type');
        const contentLength = response.headers.get('content-length');
        const hasContent = contentLength !== '0' && contentLength !== null;

        if (!hasContent) {
            return undefined as unknown as T;
        }

        if (contentType?.includes('application/json')) {
            return await response.json();
        }

        return await response.text() as unknown as T;
    }

    // Chat API methods
    async startConversation(request: {
        title?: string;
        context?: string;
        assessment_id?: string;
        report_id?: string;
        initial_message?: string;
    }): Promise<{
        id: string;
        title: string;
        status: string;
        context: string;
        messages: Array<{
            id: string;
            role: 'user' | 'assistant' | 'system';
            content: string;
            timestamp: string;
            metadata?: any;
        }>;
        message_count: number;
        started_at: string;
        last_activity: string;
        assessment_id?: string;
        report_id?: string;
        escalated: boolean;
        total_tokens_used: number;
        topics_discussed: string[];
    }> {
        return this.chatRequest('/conversations', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async getConversations(params?: {
        page?: number;
        limit?: number;
        status_filter?: string;
        context_filter?: string;
    }): Promise<{
        conversations: Array<{
            id: string;
            title: string;
            status: string;
            context: string;
            message_count: number;
            started_at: string;
            last_activity: string;
            assessment_id?: string;
            report_id?: string;
            escalated: boolean;
        }>;
        total: number;
        page: number;
        limit: number;
        has_more: boolean;
    }> {
        const searchParams = new URLSearchParams();
        if (params?.page) searchParams.append('page', params.page.toString());
        if (params?.limit) searchParams.append('limit', params.limit.toString());
        if (params?.status_filter) searchParams.append('status_filter', params.status_filter);
        if (params?.context_filter) searchParams.append('context_filter', params.context_filter);

        const query = searchParams.toString();
        return this.chatRequest(`/conversations${query ? `?${query}` : ''}`);
    }

    async getConversation(conversationId: string): Promise<{
        id: string;
        title: string;
        status: string;
        context: string;
        messages: Array<{
            id: string;
            role: 'user' | 'assistant' | 'system';
            content: string;
            timestamp: string;
            metadata?: any;
        }>;
        message_count: number;
        started_at: string;
        last_activity: string;
        assessment_id?: string;
        report_id?: string;
        escalated: boolean;
        total_tokens_used: number;
        topics_discussed: string[];
    }> {
        return this.chatRequest(`/conversations/${conversationId}`);
    }

    async sendMessage(conversationId: string, request: {
        content: string;
        context?: string;
        assessment_id?: string;
        report_id?: string;
    }): Promise<{
        id: string;
        role: 'user' | 'assistant' | 'system';
        content: string;
        timestamp: string;
        metadata?: any;
    }> {
        return this.chatRequest(`/conversations/${conversationId}/messages`, {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async updateConversationTitle(conversationId: string, title: string): Promise<{
        message: string;
    }> {
        return this.chatRequest(`/conversations/${conversationId}/title`, {
            method: 'PUT',
            body: JSON.stringify({ title }),
        });
    }

    async generateConversationTitle(conversationId: string): Promise<{
        message: string;
        title: string;
    }> {
        return this.chatRequest(`/conversations/${conversationId}/generate-title`, {
            method: 'POST',
        });
    }

    async deleteConversation(conversationId: string): Promise<{
        message: string;
    }> {
        return this.chatRequest(`/conversations/${conversationId}`, {
            method: 'DELETE',
        });
    }

    async endConversation(conversationId: string, satisfactionRating?: number): Promise<{
        message: string;
        title?: string;
    }> {
        const params = new URLSearchParams();
        if (satisfactionRating) {
            params.append('satisfaction_rating', satisfactionRating.toString());
        }

        const query = params.toString();
        return this.chatRequest(`/conversations/${conversationId}/end${query ? `?${query}` : ''}`, {
            method: 'POST',
        });
    }

    async getChatAnalytics(days: number = 30): Promise<{
        total_conversations: number;
        total_messages: number;
        avg_conversation_length: number;
        escalation_rate: number;
        satisfaction_score?: number;
        top_contexts: Array<{
            context: string;
            count: number;
        }>;
        recent_activity: Array<{
            date: string;
            title: string;
            context: string;
            message_count: number;
            escalated: boolean;
        }>;
    }> {
        return this.chatRequest(`/analytics?days=${days}`);
    }

    // Network debugging utility
    async debugConnection(): Promise<{
        success: boolean;
        details: any;
        recommendations: string[];
    }> {
        const results = {
            success: false,
            details: {
                environment: typeof window !== 'undefined' ? 'client' : 'server',
                baseURL: getApiBaseUrl(),
                apiPrefix: this.baseURL,
                envVars: {
                    NEXT_PUBLIC_API_URL: typeof window !== 'undefined' ? process.env.NEXT_PUBLIC_API_URL : 'N/A',
                    API_URL: typeof window === 'undefined' ? process.env.API_URL : 'N/A'
                },
                tests: {} as any
            },
            recommendations: [] as string[]
        };

        // Test 1: Basic health check
        try {
            const healthResult = await this.checkHealth();
            results.details.tests.healthCheck = {
                success: healthResult.status !== 'connection_failed',
                status: healthResult.status,
                error: healthResult.error || null
            };
        } catch (error) {
            results.details.tests.healthCheck = {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error'
            };
        }

        // Test 2: Try alternative URLs
        const alternativeUrls = [
            'http://localhost:8000',
            'http://host.docker.internal:8000',
            'http://127.0.0.1:8000',
            'http://api:8000'
        ];

        for (const url of alternativeUrls) {
            try {
                const response = await fetch(`${url}/health`, {
                    method: 'GET',
                    signal: AbortSignal.timeout(5000)
                });
                results.details.tests[`alternative_${url.replace(/[^a-z0-9]/gi, '_')}`] = {
                    success: response.ok,
                    status: response.status
                };
                if (response.ok) {
                    results.success = true;
                    results.recommendations.push(`Working URL found: ${url}`);
                }
            } catch (error) {
                results.details.tests[`alternative_${url.replace(/[^a-z0-9]/gi, '_')}`] = {
                    success: false,
                    error: error instanceof Error ? error.message : 'Unknown error'
                };
            }
        }

        // Generate recommendations
        if (!results.success) {
            results.recommendations.push('1. Ensure the backend API server is running');
            results.recommendations.push('2. Check if Docker containers are properly started');
            results.recommendations.push('3. Verify network connectivity between containers');
            results.recommendations.push('4. Check CORS configuration in backend');
            results.recommendations.push('5. Validate environment variables are set correctly');
        }

        return results;
    }

    // Simple chat without conversations (for quick questions)
    async sendSimpleMessage(message: string, sessionId?: string): Promise<{
        response: string;
        session_id: string;
        timestamp: string;
    }> {
        const url = `${getApiBaseUrl()}${API_PREFIX}/chat/simple`;
        const payload = {
            message,
            session_id: sessionId || `simple_${Date.now()}`
        };


        try {
            // Use direct fetch to avoid authentication and complex headers
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });


            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ HTTP error response:', errorText);
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('✅ SendSimpleMessage success:', result);
            return result;
        } catch (error) {
            console.error('❌ SendSimpleMessage failed:', error);
            throw error;
        }
    }

    // Advanced Analytics methods (v2 API only)
    async getAdvancedAnalyticsDashboard(timeframe?: string): Promise<{
        timestamp: string;
        timeframe: string;
        analytics: {
            cost_modeling: any;
            scaling_simulations: any;
            performance_benchmarks: any;
            multi_cloud_analysis: any;
            security_analytics: any;
            recommendation_trends: any;
        };
        visualizations: {
            d3js_charts: any;
            interactive_dashboards: any;
        };
        predictive_insights: any;
        optimization_opportunities: any[];
    }> {
        const params = new URLSearchParams();
        if (timeframe) {
            params.append('timeframe', timeframe);
        }

        // Ultra aggressive cache busting for analytics data
        const timestamp = Date.now();
        const random = Math.random().toString(36).substr(2, 9);
        const microtime = performance.now();
        const sessionId = Math.random().toString(36).substr(2, 15);

        params.append('_t', timestamp.toString());
        params.append('_cb', random);
        params.append('_mt', microtime.toString());
        params.append('_sid', sessionId);
        params.append('_nocache', 'true');
        params.append('_fresh', 'true');
        params.append('_bust', Date.now().toString());

        // Use v2 API explicitly for advanced analytics with ultra cache busting
        const url = `${getApiBaseUrl()}/api/v2/advanced-analytics/dashboard?${params.toString()}`;
        return this.request(url, {
            useFullUrl: true,
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0, s-maxage=0',
                'Pragma': 'no-cache',
                'Expires': '0',
                'If-None-Match': '*',
                'If-Modified-Since': 'Thu, 01 Jan 1970 00:00:00 GMT',
                'X-No-Cache': 'true',
                'X-Fresh-Data': 'true'
            }
        });
    }

    async getCostPredictions(assessmentId?: string, projectionMonths?: number): Promise<{
        predictions: any;
        projection_months: number;
        generated_at: string;
    }> {
        const params = new URLSearchParams();
        if (assessmentId) {
            params.append('assessment_id', assessmentId);
        }
        if (projectionMonths) {
            params.append('projection_months', projectionMonths.toString());
        }

        // Use v2 API explicitly for advanced analytics
        const url = `${getApiBaseUrl()}/api/v2/advanced-analytics/cost-predictions${params.toString() ? `?${params.toString()}` : ''}`;
        return this.request(url, { useFullUrl: true });
    }

    async getSecurityAudit(assessmentId?: string, includeRemediation?: boolean): Promise<{
        security_audit: any;
        audit_timestamp: string;
        next_audit_recommended: string;
    }> {
        const params = new URLSearchParams();
        if (assessmentId) {
            params.append('assessment_id', assessmentId);
        }
        if (includeRemediation !== undefined) {
            params.append('include_remediation', includeRemediation.toString());
        }

        // Use v2 API explicitly for advanced analytics
        const url = `${getApiBaseUrl()}/api/v2/advanced-analytics/security-audit${params.toString() ? `?${params.toString()}` : ''}`;
        return this.request(url, { useFullUrl: true });
    }

    async getCostOptimization(assessmentId?: string, optimizationLevel?: string): Promise<{
        cost_optimization: any;
        optimization_level: string;
        potential_monthly_savings: number;
        confidence_score: number;
        generated_at: string;
    }> {
        const params = new URLSearchParams();
        if (assessmentId) {
            params.append('assessment_id', assessmentId);
        }
        if (optimizationLevel) {
            params.append('optimization_level', optimizationLevel);
        }

        // Use v2 API explicitly for advanced analytics
        const url = `${getApiBaseUrl()}/api/v2/advanced-analytics/infrastructure-cost-optimization${params.toString() ? `?${params.toString()}` : ''}`;
        return this.request(url, { useFullUrl: true });
    }

    // Intelligent Form Features
    async getSmartDefaults(fieldName: string, context?: Record<string, any>): Promise<{
        value: any;
        confidence: number;
        reason: string;
        source: string;
    }[]> {
        try {
            const response = await this.request('/forms/smart-defaults', {
                method: 'POST',
                body: JSON.stringify({ field_name: fieldName, context })
            });
            // Extract the defaults array from the API response
            return response.defaults || [];
        } catch (error) {
            console.error('Smart defaults API failed:', error);
            return [];
        }
    }

    async getFieldSuggestions(fieldName: string, query: string, context?: Record<string, any>): Promise<{
        value: string;
        label: string;
        description?: string;
        confidence: number;
    }[]> {
        try {
            const response = await this.request('/forms/suggestions', {
                method: 'POST',
                body: JSON.stringify({ field_name: fieldName, query, context })
            });
            // Extract the suggestions array from the API response
            return response.suggestions || [];
        } catch (error) {
            console.error('Field suggestions API failed:', error);
            return [];
        }
    }

    async getContextualHelp(fieldName: string, context?: Record<string, any>): Promise<{
        title: string;
        content: string;
        examples?: string[];
        tips?: string[];
        related_fields?: string[];
        help_type: 'tooltip' | 'modal' | 'inline';
    } | null> {
        try {
            return await this.request('/forms/contextual-help', {
                method: 'POST',
                body: JSON.stringify({ field_name: fieldName, context })
            });
        } catch (error) {
            console.error('Contextual help API failed:', error);
            return null;
        }
    }


    // Workflow control methods
    async getAssessmentWorkflowStatus(assessmentId: string): Promise<{
        assessment_id: string;
        current_step: string;
        progress: number;
        status: string;
        steps: Array<{
            name: string;
            status: 'pending' | 'in_progress' | 'completed' | 'failed';
        }>;
        can_advance: boolean;
        is_running: boolean;
        workflow_id: string;
        last_updated: string;
    }> {
        return this.request(`/assessments/${assessmentId}/workflow/status`);
    }

    async advanceAssessmentWorkflow(assessmentId: string): Promise<{
        assessment_id: string;
        previous_step: string;
        current_step: string;
        progress: number;
        status: string;
        message: string;
        completed: boolean;
    }> {
        return this.request(`/assessments/${assessmentId}/workflow/advance`, {
            method: 'POST',
        });
    }

    async pauseAssessmentWorkflow(assessmentId: string): Promise<{
        assessment_id: string;
        status: string;
        message: string;
        paused_at: string;
    }> {
        return this.request(`/assessments/${assessmentId}/workflow/pause`, {
            method: 'POST',
        });
    }

    async resumeAssessmentWorkflow(assessmentId: string): Promise<{
        assessment_id: string;
        status: string;
        current_step: string;
        message: string;
        resumed_at: string;
    }> {
        return this.request(`/assessments/${assessmentId}/workflow/resume`, {
            method: 'POST',
        });
    }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Export default
export default apiClient;