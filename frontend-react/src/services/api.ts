/**
 * API Client Service for Infra Mind Frontend
 * 
 * This service provides a centralized way to interact with the backend API,
 * including authentication, error handling, and request/response transformation.
 */

import { Assessment, BusinessRequirements, TechnicalRequirements } from '@/store/slices/assessmentSlice';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_VERSION = 'v1';
const API_PREFIX = `/api/${API_VERSION}`;

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
    token_type: string;
    expires_in: number;
    user_id: string;
    email: string;
    full_name: string;
}

export interface RegisterRequest {
    email: string;
    password: string;
    full_name: string;
    company?: string;
}

export interface CreateAssessmentRequest {
    title: string;
    description?: string;
    business_requirements: BusinessRequirements;
    technical_requirements: TechnicalRequirements;
}

export interface Recommendation {
    id: string;
    assessment_id: string;
    agent_name: string;
    title: string;
    description: string;
    confidence_score: number;
    business_alignment: number;
    recommended_services: Array<{
        service_name: string;
        provider: string;
        estimated_monthly_cost: number;
        specifications: Record<string, unknown>;
    }>;
    pros: string[];
    cons: string[];
    implementation_complexity: 'low' | 'medium' | 'high';
    status: 'pending' | 'approved' | 'rejected';
    created_at: string;
}

export interface Report {
    id: string;
    assessment_id: string;
    title: string;
    status: 'generating' | 'completed' | 'failed';
    sections: Array<{
        title: string;
        content: string;
        type: 'executive' | 'technical' | 'financial';
    }>;
    key_findings: string[];
    recommendations: string[];
    estimated_savings: number;
    compliance_score: number;
    generated_at: string;
}

// API Client Class
class ApiClient {
    private baseURL: string;
    private token: string | null = null;

    constructor() {
        this.baseURL = API_BASE_URL + API_PREFIX;
        this.token = this.getStoredToken();
    }

    // Token management
    private getStoredToken(): string | null {
        if (typeof window !== 'undefined') {
            return localStorage.getItem('auth_token');
        }
        return null;
    }

    private setStoredToken(token: string): void {
        if (typeof window !== 'undefined') {
            localStorage.setItem('auth_token', token);
        }
        this.token = token;
    }

    private removeStoredToken(): void {
        if (typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
        }
        this.token = null;
    }

    // HTTP request helper with enhanced error handling and loading states
    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseURL}${endpoint}`;

        const headers: HeadersInit = {
            'Content-Type': 'application/json',
            'X-Client-Version': '2.0.0',
            'X-Request-ID': this.generateRequestId(),
            ...options.headers,
        };

        if (this.token) {
            headers.Authorization = `Bearer ${this.token}`;
        }

        const config: RequestInit = {
            ...options,
            headers,
            // Add timeout for requests
            signal: AbortSignal.timeout(30000), // 30 second timeout
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
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
                        this.removeStoredToken();
                        if (typeof window !== 'undefined') {
                            window.location.href = '/auth/login';
                        }
                        break;
                    case 403:
                        throw new Error('Access denied. Please check your permissions.');
                    case 404:
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

            // Handle different content types
            const contentType = response.headers.get('content-type');
            if (contentType?.includes('application/json')) {
                return await response.json();
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
                console.error(`API request failed: ${endpoint}`, error);
                throw error;
            }
            throw new Error('An unexpected error occurred');
        }
    }

    // Generate unique request ID for tracking
    private generateRequestId(): string {
        return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    // Authentication methods
    async login(credentials: LoginRequest): Promise<LoginResponse> {
        const response = await this.request<LoginResponse>('/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials),
        });

        this.setStoredToken(response.access_token);
        return response;
    }

    async register(userData: RegisterRequest): Promise<LoginResponse> {
        const response = await this.request<LoginResponse>('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData),
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
        return this.request<Assessment>('/assessments', {
            method: 'POST',
            body: JSON.stringify(assessmentData),
        });
    }

    async getAssessments(): Promise<Assessment[]> {
        return this.request<Assessment[]>('/assessments');
    }

    async getAssessment(id: string): Promise<Assessment> {
        return this.request<Assessment>(`/assessments/${id}`);
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

    // Recommendation methods
    async generateRecommendations(assessmentId: string): Promise<{ workflow_id: string }> {
        return this.request<{ workflow_id: string }>(`/recommendations/${assessmentId}/generate`, {
            method: 'POST',
        });
    }

    async getRecommendations(assessmentId: string): Promise<Recommendation[]> {
        return this.request<Recommendation[]>(`/recommendations/${assessmentId}`);
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

    // Report methods
    async generateReport(assessmentId: string, options?: {
        template?: string;
        sections?: string[];
        format?: 'pdf' | 'docx' | 'html';
    }): Promise<{ report_id: string; workflow_id: string }> {
        return this.request<{ report_id: string; workflow_id: string }>(`/reports/${assessmentId}/generate`, {
            method: 'POST',
            body: JSON.stringify(options || {}),
        });
    }

    async getReports(assessmentId?: string): Promise<Report[]> {
        const endpoint = assessmentId ? `/reports?assessment_id=${assessmentId}` : '/reports';
        return this.request<Report[]>(endpoint);
    }

    async getReport(reportId: string): Promise<Report> {
        return this.request<Report>(`/reports/${reportId}`);
    }

    async downloadReport(reportId: string, format: 'pdf' | 'docx' | 'html' = 'pdf'): Promise<Blob> {
        const response = await fetch(`${this.baseURL}/reports/${reportId}/download?format=${format}`, {
            headers: {
                Authorization: `Bearer ${this.token}`,
            },
        });

        if (!response.ok) {
            throw new Error('Failed to download report');
        }

        return response.blob();
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
        return this.request('/health/detailed');
    }

    // User management methods
    async getCurrentUser(): Promise<{
        id: string;
        email: string;
        full_name: string;
        company: string;
        role: string;
        is_active: boolean;
        created_at: string;
    }> {
        return this.request('/auth/profile');
    }

    async updateUserProfile(updates: {
        full_name?: string;
        company?: string;
        preferences?: Record<string, unknown>;
    }): Promise<void> {
        return this.request('/auth/profile', {
            method: 'PUT',
            body: JSON.stringify(updates),
        });
    }

    // WebSocket connection methods
    createWebSocketConnection(assessmentId?: string): WebSocket {
        const wsUrl = assessmentId
            ? `${WS_BASE_URL}/ws?token=${this.token}&assessment_id=${assessmentId}`
            : `${WS_BASE_URL}/ws?token=${this.token}`;

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

    // Utility methods
    isAuthenticated(): boolean {
        return !!this.token;
    }

    getAuthToken(): string | null {
        return this.token;
    }

    // Health check method
    async checkHealth(): Promise<{
        status: string;
        version: string;
        timestamp: string;
        services: Record<string, string>;
    }> {
        // This endpoint is at the root, so we call it directly without the API prefix.
        const response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) {
            throw new Error('Health check failed');
        }
        return response.json();
    }

    // Get system metrics
    async getSystemMetrics(): Promise<{
        active_connections: number;
        active_workflows: number;
        system_load: number;
        response_time_avg: number;
    }> {
        return this.request('/admin/metrics');
    }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Export default
export default apiClient;