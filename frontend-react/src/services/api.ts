/**
 * API Client Service for Infra Mind Frontend
 * 
 * This service provides a centralized way to interact with the backend API,
 * including authentication, error handling, and request/response transformation.
 */

import { Assessment, BusinessRequirements, TechnicalRequirements } from '@/store/slices/assessmentSlice';
import { cacheBuster, getNoCacheHeaders } from '@/utils/cache-buster';

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

export interface CloudService {
    id: string;
    name: string;
    provider: 'AWS' | 'Azure' | 'GCP' | 'Alibaba' | 'IBM';
    category: string;
    description: string;
    pricing: {
        model: string;
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

    public setStoredToken(token: string): void {
        if (typeof window !== 'undefined') {
            localStorage.setItem('auth_token', token);
        }
        this.token = token;
    }

    public removeStoredToken(): void {
        if (typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
        }
        this.token = null;
    }

    // HTTP request helper with enhanced error handling and loading states
    private async request<T>(
        endpoint: string,
        options: RequestInit & { useFullUrl?: boolean } = {}
    ): Promise<T> {
        const { useFullUrl, ...fetchOptions } = options;
        const url = useFullUrl ? endpoint : `${this.baseURL}${endpoint}`;

        const headers: HeadersInit = {
            'Content-Type': 'application/json',
            'X-Client-Version': '2.0.0',
            'X-Request-ID': this.generateRequestId(),
            ...fetchOptions.headers,
        };

        if (this.token) {
            headers.Authorization = `Bearer ${this.token}`;
        }

        const config: RequestInit = {
            ...fetchOptions,
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
                
                // Handle network connectivity issues
                if (error.message.includes('fetch') || error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
                    throw new Error('Connection failed - please check if the server is running at http://localhost:8000');
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
        return this.request<Assessment>('/assessments/', {
            method: 'POST',
            body: JSON.stringify(assessmentData),
        });
    }

    async createSimpleAssessment(data: { title: string; description?: string }): Promise<Assessment> {
        return this.request<Assessment>('/assessments/simple', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getAssessments(): Promise<Assessment[]> {
        // Use cache buster to ensure fresh data
        const url = cacheBuster.bustCache('/assessments/', 'assessments_list');
        const response = await this.request<{assessments: Assessment[], total: number, page: number, limit: number, pages: number}>(url, {
            headers: {
                ...getNoCacheHeaders()
            }
        });
        return response.assessments;
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
        return this.request<Assessment>(`/assessments/${id}`, {
            method: 'PUT',
            body: JSON.stringify({
                draft_data: draftData.draft_data,
                current_step: draftData.current_step,
                status: 'draft'
            }),
        });
    }

    // Recommendation methods
    async generateRecommendations(assessmentId: string): Promise<{ workflow_id: string }> {
        return this.request<{ workflow_id: string }>(`/recommendations/${assessmentId}/generate`, {
            method: 'POST',
        });
    }

    async getRecommendations(assessmentId: string): Promise<Recommendation[]> {
        // Use cache buster to ensure fresh recommendations data
        const url = cacheBuster.bustCache(`/recommendations/${assessmentId}`, `recommendations_${assessmentId}`);
        const response = await this.request<{recommendations: Recommendation[], total: number, assessment_id: string, summary: any}>(url, {
            headers: {
                ...getNoCacheHeaders()
            }
        });
        return response.recommendations;
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

    async getReports(assessmentId: string): Promise<Report[]> {
        // Add cache-busting timestamp to ensure fresh data
        const timestamp = Date.now();
        const response = await this.request<{reports: Report[]}>(
            `/reports/${assessmentId}?t=${timestamp}`, 
            {
                headers: {
                    'Cache-Control': 'no-cache'
                }
            }
        );
        return response.reports || [];
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
        }>(`${API_BASE_URL}/api/cloud-services?${params.toString()}`, { ...options, useFullUrl: true });
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
        return this.request('/cloud-services/providers');
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
        return !!this.token;
    }

    getAuthToken(): string | null {
        return this.token;
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
            const url = `${API_BASE_URL}/health`;
            
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                // Add timeout for health check
                signal: AbortSignal.timeout(10000), // 10 second timeout
            });
            
            if (!response.ok) {
                throw new Error(`Health check failed: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Health check error:', error);
            // Return a fallback response instead of throwing
            return {
                status: 'unknown',
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
                'Authorization': this.getStoredToken() ? `Bearer ${this.getStoredToken()}` : '',
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

    async deleteConversation(conversationId: string): Promise<{
        message: string;
    }> {
        return this.chatRequest(`/conversations/${conversationId}`, {
            method: 'DELETE',
        });
    }

    async endConversation(conversationId: string, satisfactionRating?: number): Promise<{
        message: string;
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

    // Simple chat without conversations (for quick questions)
    async sendSimpleMessage(message: string, sessionId?: string): Promise<{
        response: string;
        session_id: string;
        timestamp: string;
    }> {
        return this.request(`${API_BASE_URL}/api/chat/simple`, {
            method: 'POST',
            body: JSON.stringify({
                message,
                session_id: sessionId || `simple_${Date.now()}`
            }),
            useFullUrl: true
        });
    }

    // Intelligent Form Features
    async getSmartDefaults(fieldName: string, context?: Record<string, any>): Promise<{
        value: any;
        confidence: number;
        reason: string;
        source: string;
    }[]> {
        try {
            return await this.request('/forms/smart-defaults', {
                method: 'POST',
                body: JSON.stringify({ field_name: fieldName, context })
            });
        } catch (error) {
            // Fallback to basic defaults if API fails
            console.warn('Smart defaults API failed, using fallbacks:', error);
            return this.getFallbackDefaults(fieldName);
        }
    }

    async getFieldSuggestions(fieldName: string, query: string, context?: Record<string, any>): Promise<{
        value: string;
        label: string;
        description?: string;
        confidence: number;
    }[]> {
        try {
            return await this.request('/forms/suggestions', {
                method: 'POST',
                body: JSON.stringify({ field_name: fieldName, query, context })
            });
        } catch (error) {
            // Fallback to basic suggestions if API fails
            console.warn('Field suggestions API failed, using fallbacks:', error);
            return this.getFallbackSuggestions(fieldName, query);
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
            // Fallback to basic help if API fails
            console.warn('Contextual help API failed, using fallbacks:', error);
            return this.getFallbackHelp(fieldName);
        }
    }

    // Fallback methods for when intelligent form APIs are not available
    private getFallbackDefaults(fieldName: string): {
        value: any;
        confidence: number;
        reason: string;
        source: string;
    }[] {
        const defaults: Record<string, any[]> = {
            industry: [
                { value: 'technology', confidence: 0.6, reason: 'Most common industry in our user base', source: 'usage_patterns' }
            ],
            companySize: [
                { value: 'small', confidence: 0.5, reason: 'Common starting point for assessments', source: 'industry_patterns' }
            ],
            monthlyBudget: [
                { value: '5k-25k', confidence: 0.4, reason: 'Typical budget range for small to medium companies', source: 'size_patterns' }
            ]
        };
        return defaults[fieldName] || [];
    }

    private getFallbackSuggestions(fieldName: string, query: string): {
        value: string;
        label: string;
        description?: string;
        confidence: number;
    }[] {
        const suggestions: Record<string, any[]> = {
            companyName: [
                { value: 'TechCorp', label: 'TechCorp', description: 'Technology company', confidence: 0.6 },
                { value: 'InnovateLabs', label: 'InnovateLabs', description: 'Innovation laboratory', confidence: 0.5 }
            ]
        };
        
        const fieldSuggestions = suggestions[fieldName] || [];
        return fieldSuggestions.filter(s =>
            s.value.toLowerCase().includes(query.toLowerCase()) ||
            s.label.toLowerCase().includes(query.toLowerCase())
        );
    }

    private getFallbackHelp(fieldName: string): {
        title: string;
        content: string;
        examples?: string[];
        tips?: string[];
        related_fields?: string[];
        help_type: 'tooltip' | 'modal' | 'inline';
    } | null {
        const help: Record<string, any> = {
            companySize: {
                title: 'Company Size',
                content: 'Select the size category that best matches your organization.',
                examples: [
                    'Startup: 1-50 employees, early stage',
                    'Small: 51-200 employees, established',
                    'Medium: 201-1000 employees, multiple departments'
                ],
                tips: [
                    'Consider total employee count, not just technical team',
                    'This affects budget recommendations and complexity levels'
                ],
                related_fields: ['monthlyBudget', 'technicalTeamSize'],
                help_type: 'tooltip'
            },
            industry: {
                title: 'Industry',
                content: 'Select the industry that best describes your business.',
                examples: [
                    'Technology: Software, hardware, IT services',
                    'Healthcare: Medical, pharmaceutical, health services',
                    'Finance: Banking, insurance, fintech'
                ],
                tips: [
                    'This affects compliance requirements and service recommendations',
                    'Choose the primary industry if you operate in multiple sectors'
                ],
                related_fields: ['complianceRequirements'],
                help_type: 'tooltip'
            }
        };
        return help[fieldName] || null;
    }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Export default
export default apiClient;