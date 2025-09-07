'use client';

export interface User {
    id: string;
    name: string;
    email: string;
    role: string;
    department: string;
    avatar?: string;
}

export interface ApprovalRule {
    id: string;
    name: string;
    description: string;
    trigger_conditions: {
        resource_type?: string[];
        environment?: string[];
        cost_threshold?: number;
        risk_level?: 'low' | 'medium' | 'high' | 'critical';
        change_type?: 'create' | 'update' | 'delete';
    };
    approval_levels: ApprovalLevel[];
    timeout_hours: number;
    escalation_policy: {
        enabled: boolean;
        escalation_hours: number;
        escalation_to: string[];
    };
    notification_settings: {
        channels: ('email' | 'slack' | 'teams' | 'webhook')[];
        remind_hours: number[];
    };
    bypass_conditions?: {
        emergency_override: boolean;
        authorized_users: string[];
        require_justification: boolean;
    };
    active: boolean;
    created_at: string;
    updated_at: string;
}

export interface ApprovalLevel {
    level: number;
    name: string;
    required_approvals: number;
    approvers: ApproverGroup[];
    parallel: boolean;
    conditions?: {
        all_required?: boolean;
        any_from_group?: boolean;
        minimum_seniority?: string;
    };
}

export interface ApproverGroup {
    type: 'user' | 'role' | 'department';
    values: string[];
    name: string;
}

export interface ApprovalRequest {
    id: string;
    title: string;
    description: string;
    request_type: 'deployment' | 'infrastructure_change' | 'configuration_update' | 'rollback';
    resource_details: {
        type: string;
        name: string;
        environment: string;
        provider: string;
        estimated_cost?: number;
        risk_assessment: {
            level: 'low' | 'medium' | 'high' | 'critical';
            factors: string[];
            impact_score: number;
        };
    };
    change_details: {
        summary: string;
        diff?: string;
        files_changed: string[];
        resources_affected: ResourceChange[];
        impact_analysis?: ChangeImpactAnalysis;
    };
    workflow: {
        rule_id: string;
        rule_name: string;
        current_level: number;
        total_levels: number;
        status: 'pending' | 'in_progress' | 'approved' | 'rejected' | 'expired' | 'cancelled';
        approval_progress: ApprovalProgress[];
    };
    requester: User;
    created_at: string;
    updated_at: string;
    expires_at: string;
    comments: ApprovalComment[];
    attachments: ApprovalAttachment[];
}

export interface ApprovalProgress {
    level: number;
    level_name: string;
    status: 'pending' | 'in_progress' | 'approved' | 'rejected';
    required_approvals: number;
    current_approvals: number;
    approvals: ApprovalAction[];
    started_at?: string;
    completed_at?: string;
}

export interface ApprovalAction {
    id: string;
    approver: User;
    action: 'approve' | 'reject' | 'delegate' | 'request_changes';
    comment?: string;
    timestamp: string;
    delegated_to?: User;
    conditions_met: boolean;
}

export interface ApprovalComment {
    id: string;
    user: User;
    content: string;
    timestamp: string;
    reply_to?: string;
}

export interface ApprovalAttachment {
    id: string;
    filename: string;
    size: number;
    type: string;
    url: string;
    uploaded_by: User;
    uploaded_at: string;
}

export interface ResourceChange {
    resource_address: string;
    resource_type: string;
    change_type: 'create' | 'update' | 'delete' | 'replace';
    before: any;
    after: any;
    risk_factors: string[];
    dependencies: string[];
}

export interface ChangeImpactAnalysis {
    id: string;
    summary: string;
    risk_score: number;
    impact_areas: {
        area: string;
        severity: 'low' | 'medium' | 'high' | 'critical';
        description: string;
        affected_resources: string[];
    }[];
    dependencies: {
        upstream: string[];
        downstream: string[];
        circular: string[];
    };
    recommendations: {
        type: 'warning' | 'suggestion' | 'requirement';
        message: string;
        action?: string;
    }[];
    blast_radius: {
        affected_services: string[];
        potential_downtime: string;
        recovery_time: string;
    };
    compliance_impact: {
        policies_affected: string[];
        violations: string[];
        required_approvals: string[];
    };
    generated_at: string;
}

class ApprovalWorkflowService {
    private baseUrl: string;
    private token: string | null = null;

    constructor() {
        this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        this.token = typeof window !== 'undefined' ? typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null : null;
    }

    private async makeRequest(endpoint: string, options: RequestInit = {}): Promise<any> {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`,
                ...options.headers,
            },
        });

        if (!response.ok) {
            throw new Error(`Approval Workflow API Error: ${response.statusText}`);
        }

        return response.json();
    }

    // Approval Rules Management
    async getApprovalRules(): Promise<ApprovalRule[]> {
        return this.makeRequest('/api/approval-workflows/rules');
    }

    async getApprovalRule(ruleId: string): Promise<ApprovalRule> {
        return this.makeRequest(`/api/approval-workflows/rules/${ruleId}`);
    }

    async createApprovalRule(rule: Omit<ApprovalRule, 'id' | 'created_at' | 'updated_at'>): Promise<ApprovalRule> {
        return this.makeRequest('/api/approval-workflows/rules', {
            method: 'POST',
            body: JSON.stringify(rule),
        });
    }

    async updateApprovalRule(ruleId: string, rule: Partial<ApprovalRule>): Promise<ApprovalRule> {
        return this.makeRequest(`/api/approval-workflows/rules/${ruleId}`, {
            method: 'PUT',
            body: JSON.stringify(rule),
        });
    }

    async deleteApprovalRule(ruleId: string): Promise<void> {
        await this.makeRequest(`/api/approval-workflows/rules/${ruleId}`, {
            method: 'DELETE',
        });
    }

    async testApprovalRule(ruleId: string, testData: any): Promise<{
        matches: boolean;
        triggered_rule: ApprovalRule;
        approval_path: ApprovalLevel[];
        estimated_time: string;
    }> {
        return this.makeRequest(`/api/approval-workflows/rules/${ruleId}/test`, {
            method: 'POST',
            body: JSON.stringify(testData),
        });
    }

    // Approval Requests Management
    async createApprovalRequest(request: Omit<ApprovalRequest, 'id' | 'workflow' | 'created_at' | 'updated_at' | 'expires_at' | 'comments' | 'attachments'>): Promise<ApprovalRequest> {
        return this.makeRequest('/api/approval-workflows/requests', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async getApprovalRequests(filters?: {
        status?: string;
        requester_id?: string;
        environment?: string;
        request_type?: string;
        assigned_to_me?: boolean;
    }): Promise<ApprovalRequest[]> {
        const params = new URLSearchParams();
        if (filters) {
            Object.entries(filters).forEach(([key, value]) => {
                if (value !== undefined) {
                    params.append(key, value.toString());
                }
            });
        }
        return this.makeRequest(`/api/approval-workflows/requests?${params}`);
    }

    async getApprovalRequest(requestId: string): Promise<ApprovalRequest> {
        return this.makeRequest(`/api/approval-workflows/requests/${requestId}`);
    }

    async approveRequest(requestId: string, levelId: number, comment?: string): Promise<ApprovalAction> {
        return this.makeRequest(`/api/approval-workflows/requests/${requestId}/approve`, {
            method: 'POST',
            body: JSON.stringify({ level: levelId, comment }),
        });
    }

    async rejectRequest(requestId: string, levelId: number, comment: string): Promise<ApprovalAction> {
        return this.makeRequest(`/api/approval-workflows/requests/${requestId}/reject`, {
            method: 'POST',
            body: JSON.stringify({ level: levelId, comment }),
        });
    }

    async delegateApproval(requestId: string, levelId: number, delegateToUserId: string, comment?: string): Promise<ApprovalAction> {
        return this.makeRequest(`/api/approval-workflows/requests/${requestId}/delegate`, {
            method: 'POST',
            body: JSON.stringify({ level: levelId, delegate_to: delegateToUserId, comment }),
        });
    }

    async requestChanges(requestId: string, levelId: number, comment: string, requiredChanges: string[]): Promise<ApprovalAction> {
        return this.makeRequest(`/api/approval-workflows/requests/${requestId}/request-changes`, {
            method: 'POST',
            body: JSON.stringify({ level: levelId, comment, required_changes: requiredChanges }),
        });
    }

    async cancelRequest(requestId: string, reason: string): Promise<void> {
        await this.makeRequest(`/api/approval-workflows/requests/${requestId}/cancel`, {
            method: 'POST',
            body: JSON.stringify({ reason }),
        });
    }

    async escalateRequest(requestId: string, levelId: number, reason: string): Promise<void> {
        await this.makeRequest(`/api/approval-workflows/requests/${requestId}/escalate`, {
            method: 'POST',
            body: JSON.stringify({ level: levelId, reason }),
        });
    }

    // Emergency Override
    async emergencyOverride(requestId: string, justification: string, overrideCode?: string): Promise<{
        success: boolean;
        audit_id: string;
        warning: string;
    }> {
        return this.makeRequest(`/api/approval-workflows/requests/${requestId}/emergency-override`, {
            method: 'POST',
            body: JSON.stringify({ justification, override_code: overrideCode }),
        });
    }

    // Comments and Communication
    async addComment(requestId: string, content: string, replyTo?: string): Promise<ApprovalComment> {
        return this.makeRequest(`/api/approval-workflows/requests/${requestId}/comments`, {
            method: 'POST',
            body: JSON.stringify({ content, reply_to: replyTo }),
        });
    }

    async getComments(requestId: string): Promise<ApprovalComment[]> {
        return this.makeRequest(`/api/approval-workflows/requests/${requestId}/comments`);
    }

    // File Attachments
    async uploadAttachment(requestId: string, file: File): Promise<ApprovalAttachment> {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${this.baseUrl}/api/approval-workflows/requests/${requestId}/attachments`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
            },
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }

        return response.json();
    }

    async deleteAttachment(requestId: string, attachmentId: string): Promise<void> {
        await this.makeRequest(`/api/approval-workflows/requests/${requestId}/attachments/${attachmentId}`, {
            method: 'DELETE',
        });
    }

    // Analytics and Reporting
    async getApprovalMetrics(timeRange: string): Promise<{
        total_requests: number;
        approved_requests: number;
        rejected_requests: number;
        pending_requests: number;
        average_approval_time: string;
        approval_rate: number;
        bottleneck_levels: Array<{
            level: number;
            average_time: string;
            timeout_rate: number;
        }>;
        top_approvers: Array<{
            user: User;
            approvals_count: number;
            average_time: string;
        }>;
    }> {
        return this.makeRequest(`/api/approval-workflows/metrics?time_range=${timeRange}`);
    }

    async getApprovalHistory(requestId: string): Promise<{
        timeline: Array<{
            timestamp: string;
            event: string;
            user: User;
            details: any;
        }>;
        duration_by_level: Array<{
            level: number;
            duration: string;
            status: string;
        }>;
    }> {
        return this.makeRequest(`/api/approval-workflows/requests/${requestId}/history`);
    }

    // User Management
    async getUsers(): Promise<User[]> {
        return this.makeRequest('/api/approval-workflows/users');
    }

    async getUsersByRole(role: string): Promise<User[]> {
        return this.makeRequest(`/api/approval-workflows/users?role=${role}`);
    }

    async getUsersByDepartment(department: string): Promise<User[]> {
        return this.makeRequest(`/api/approval-workflows/users?department=${department}`);
    }

    // Notification Management
    async sendNotification(requestId: string, userIds: string[], message: string, channels: string[]): Promise<void> {
        await this.makeRequest(`/api/approval-workflows/requests/${requestId}/notify`, {
            method: 'POST',
            body: JSON.stringify({ user_ids: userIds, message, channels }),
        });
    }

    async getNotificationSettings(userId: string): Promise<{
        email_enabled: boolean;
        slack_enabled: boolean;
        teams_enabled: boolean;
        remind_hours: number[];
        escalation_notifications: boolean;
    }> {
        return this.makeRequest(`/api/approval-workflows/users/${userId}/notification-settings`);
    }

    async updateNotificationSettings(userId: string, settings: any): Promise<void> {
        await this.makeRequest(`/api/approval-workflows/users/${userId}/notification-settings`, {
            method: 'PUT',
            body: JSON.stringify(settings),
        });
    }

    // Bulk Operations
    async bulkApprove(requestIds: string[], comment?: string): Promise<{
        successful: string[];
        failed: Array<{ request_id: string; error: string }>;
    }> {
        return this.makeRequest('/api/approval-workflows/requests/bulk-approve', {
            method: 'POST',
            body: JSON.stringify({ request_ids: requestIds, comment }),
        });
    }

    async bulkReject(requestIds: string[], comment: string): Promise<{
        successful: string[];
        failed: Array<{ request_id: string; error: string }>;
    }> {
        return this.makeRequest('/api/approval-workflows/requests/bulk-reject', {
            method: 'POST',
            body: JSON.stringify({ request_ids: requestIds, comment }),
        });
    }

    // Integration Hooks
    async setupWebhook(url: string, events: string[], secret?: string): Promise<{ webhook_id: string }> {
        return this.makeRequest('/api/approval-workflows/webhooks', {
            method: 'POST',
            body: JSON.stringify({ url, events, secret }),
        });
    }

    async testWebhook(webhookId: string): Promise<{ success: boolean; response: any }> {
        return this.makeRequest(`/api/approval-workflows/webhooks/${webhookId}/test`, {
            method: 'POST',
        });
    }
}

// Singleton instance
let approvalWorkflowService: ApprovalWorkflowService | null = null;

export const getApprovalWorkflowService = (): ApprovalWorkflowService => {
    if (!approvalWorkflowService) {
        approvalWorkflowService = new ApprovalWorkflowService();
    }
    return approvalWorkflowService;
};

export default ApprovalWorkflowService;