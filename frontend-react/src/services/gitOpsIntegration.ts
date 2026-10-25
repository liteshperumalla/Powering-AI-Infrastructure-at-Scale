'use client';

import AuthStorage from '../utils/authStorage';

export interface GitRepository {
    id: string;
    name: string;
    full_name: string;
    provider: 'github' | 'gitlab' | 'bitbucket';
    url: string;
    default_branch: string;
    private: boolean;
    permissions: {
        admin: boolean;
        push: boolean;
        pull: boolean;
    };
}

export interface GitBranch {
    name: string;
    sha: string;
    protected: boolean;
    ahead_by?: number;
    behind_by?: number;
}

export interface PullRequest {
    id: number;
    title: string;
    description: string;
    state: 'open' | 'closed' | 'merged';
    source_branch: string;
    target_branch: string;
    author: string;
    created_at: string;
    updated_at: string;
    url: string;
    checks_status: 'pending' | 'success' | 'failure';
    approvals: ApprovalStatus[];
    files_changed: FileChange[];
}

export interface FileChange {
    filename: string;
    status: 'added' | 'modified' | 'removed';
    additions: number;
    deletions: number;
    changes: number;
    patch?: string;
}

export interface ApprovalStatus {
    user: string;
    status: 'approved' | 'rejected' | 'pending';
    comment?: string;
    timestamp: string;
}

export interface IaCTemplate {
    id: string;
    name: string;
    description: string;
    provider: 'terraform' | 'cloudformation' | 'pulumi' | 'arm' | 'cdk';
    language: string;
    template: string;
    variables: Record<string, any>;
    outputs: Record<string, any>;
    tags: string[];
    version: string;
}

export interface DeploymentPlan {
    id: string;
    name: string;
    repository: GitRepository;
    branch: string;
    template: IaCTemplate;
    environment: 'dev' | 'staging' | 'prod';
    variables: Record<string, any>;
    approval_required: boolean;
    auto_deploy: boolean;
    rollback_enabled: boolean;
    notification_settings: {
        channels: string[];
        on_success: boolean;
        on_failure: boolean;
        on_approval_needed: boolean;
    };
}

class GitOpsIntegrationService {
    private baseUrl: string;

    constructor() {
        this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    }

    private async makeRequest(endpoint: string, options: RequestInit = {}): Promise<any> {
        // Map to real backend endpoints
        const mappedEndpoint = this.mapEndpoint(endpoint);
        const token = AuthStorage.getTokenFromAnySource();

        const response = await fetch(`${this.baseUrl}${mappedEndpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                // Read per request: the service is created at import time, often before login
                ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
                ...options.headers,
            },
        });

        if (!response.ok) {
            // Prefer the backend's explanation (FastAPI `detail`: a string, or a list of validation errors)
            const body = await response.json().catch(() => null);
            const detail = Array.isArray(body?.detail)
                ? body.detail.map((d: { msg?: string }) => d.msg?.replace(/^Value error, /, '')).filter(Boolean).join('; ')
                : body?.detail;
            throw new Error(detail || `GitOps API Error: ${response.status} ${response.statusText}`);
        }

        // DELETE endpoints answer 204 with no body
        return response.status === 204 ? null : response.json();
    }

    private mapEndpoint(endpoint: string): string {
        // Version the path, keeping any resource ID / sub-path (the old per-resource
        // rules returned fixed paths, dropping e.g. the ID from DELETE /repositories/{id})
        return endpoint.startsWith('/api/gitops/')
            ? endpoint.replace('/api/gitops/', '/api/v1/gitops/')
            : endpoint;
    }

    // Removed getFallbackResponse - all data now comes from backend only

    // Repository Management
    async connectRepository(provider: string, repoUrl: string, accessToken: string): Promise<GitRepository> {
        return this.makeRequest('/api/gitops/repositories', {
            method: 'POST',
            body: JSON.stringify({
                provider,
                repo_url: repoUrl,
                access_token: accessToken,
            }),
        });
    }

    async getRepositories(): Promise<GitRepository[]> {
        try {
            const repos = await this.makeRequest('/api/gitops/repositories');
            // Ensure repos is an array
            if (!Array.isArray(repos)) {
                console.warn('Repositories response is not an array:', repos);
                return [];
            }
            // Transform backend format to frontend format
            return repos.map((repo: any) => ({
                id: repo?.id || '',
                name: repo?.name || 'Unknown',
                full_name: repo?.full_name || repo?.name || 'Unknown',
                provider: (['github', 'gitlab', 'bitbucket'].includes(repo?.provider) ? repo.provider : 'github') as GitRepository['provider'],
                url: repo?.url || '',
                default_branch: repo?.branch || 'main',
                private: false, // Backend doesn't specify, default to false
                permissions: {
                    admin: true,
                    push: true,
                    pull: true
                }
            }));
        } catch (error) {
            console.error('Failed to get repositories:', error);
            return [];
        }
    }

    async getRepository(repoId: string): Promise<GitRepository> {
        return this.makeRequest(`/api/gitops/repositories/${repoId}`);
    }

    async disconnectRepository(repoId: string): Promise<void> {
        await this.makeRequest(`/api/gitops/repositories/${repoId}`, {
            method: 'DELETE',
        });
    }

    // Branch Management moved below

    // Branch Management
    async getBranches(repoId: string): Promise<GitBranch[]> {
        return this.makeRequest(`/api/gitops/repositories/${repoId}/branches`);
    }

    async createBranch(repoId: string, branchName: string, sourceBranch: string = 'main'): Promise<GitBranch> {
        return this.makeRequest(`/api/gitops/repositories/${repoId}/branches`, {
            method: 'POST',
            body: JSON.stringify({
                name: branchName,
                source_branch: sourceBranch,
            }),
        });
    }

    async deleteBranch(repoId: string, branchName: string): Promise<void> {
        await this.makeRequest(`/api/gitops/repositories/${repoId}/branches/${branchName}`, {
            method: 'DELETE',
        });
    }

    // File Management
    async getFileContent(repoId: string, filePath: string, branch?: string): Promise<string> {
        const params = new URLSearchParams();
        if (branch) params.append('branch', branch);
        
        return this.makeRequest(`/api/gitops/repositories/${repoId}/files/${encodeURIComponent(filePath)}?${params}`);
    }

    async updateFile(
        repoId: string,
        filePath: string,
        content: string,
        message: string,
        branch?: string
    ): Promise<void> {
        await this.makeRequest(`/api/gitops/repositories/${repoId}/files/${encodeURIComponent(filePath)}`, {
            method: 'PUT',
            body: JSON.stringify({
                content,
                message,
                branch,
            }),
        });
    }

    async createFile(
        repoId: string,
        filePath: string,
        content: string,
        message: string,
        branch?: string
    ): Promise<void> {
        await this.makeRequest(`/api/gitops/repositories/${repoId}/files`, {
            method: 'POST',
            body: JSON.stringify({
                path: filePath,
                content,
                message,
                branch,
            }),
        });
    }

    // Pull Request Management
    async createPullRequest(
        repoId: string,
        title: string,
        description: string,
        sourceBranch: string,
        targetBranch: string = 'main'
    ): Promise<PullRequest> {
        return this.makeRequest(`/api/gitops/repositories/${repoId}/pull-requests`, {
            method: 'POST',
            body: JSON.stringify({
                title,
                description,
                source_branch: sourceBranch,
                target_branch: targetBranch,
            }),
        });
    }

    async getPullRequests(repoId: string, state?: 'open' | 'closed' | 'all'): Promise<PullRequest[]> {
        const params = new URLSearchParams();
        if (state) params.append('state', state);
        
        const response = await this.makeRequest(`/api/v2/gitops/repositories/${repoId}/pull-requests?${params}`);
        return Array.isArray(response) ? response : [];
    }

    async getPullRequest(repoId: string, prId: number): Promise<PullRequest> {
        return this.makeRequest(`/api/gitops/repositories/${repoId}/pull-requests/${prId}`);
    }

    async approvePullRequest(repoId: string, prId: number, comment?: string): Promise<void> {
        await this.makeRequest(`/api/gitops/repositories/${repoId}/pull-requests/${prId}/approve`, {
            method: 'POST',
            body: JSON.stringify({ comment }),
        });
    }

    async rejectPullRequest(repoId: string, prId: number, comment: string): Promise<void> {
        await this.makeRequest(`/api/gitops/repositories/${repoId}/pull-requests/${prId}/reject`, {
            method: 'POST',
            body: JSON.stringify({ comment }),
        });
    }

    async mergePullRequest(repoId: string, prId: number, mergeMethod: 'merge' | 'squash' | 'rebase' = 'merge'): Promise<void> {
        await this.makeRequest(`/api/gitops/repositories/${repoId}/pull-requests/${prId}/merge`, {
            method: 'POST',
            body: JSON.stringify({ merge_method: mergeMethod }),
        });
    }

    // IaC Template Management
    async getIaCTemplates(): Promise<IaCTemplate[]> {
        return this.makeRequest('/api/gitops/templates');
    }

    async createIaCTemplate(template: Omit<IaCTemplate, 'id'>): Promise<IaCTemplate> {
        return this.makeRequest('/api/gitops/templates', {
            method: 'POST',
            body: JSON.stringify(template),
        });
    }

    async updateIaCTemplate(templateId: string, template: Partial<IaCTemplate>): Promise<IaCTemplate> {
        return this.makeRequest(`/api/gitops/templates/${templateId}`, {
            method: 'PUT',
            body: JSON.stringify(template),
        });
    }

    async deleteIaCTemplate(templateId: string): Promise<void> {
        await this.makeRequest(`/api/gitops/templates/${templateId}`, {
            method: 'DELETE',
        });
    }

    // Deployment Management
    async createDeploymentPlan(plan: Omit<DeploymentPlan, 'id'>): Promise<DeploymentPlan> {
        return this.makeRequest('/api/gitops/deployment-plans', {
            method: 'POST',
            body: JSON.stringify(plan),
        });
    }

    async getDeploymentPlans(): Promise<DeploymentPlan[]> {
        try {
            const plans = await this.makeRequest('/api/gitops/deployment-plans');
            if (!Array.isArray(plans)) {
                console.warn('Deployment plans response is not an array:', plans);
                return [];
            }
            // repository/template are null if they were removed after the plan was created
            return plans.filter((plan: any) => plan?.repository && plan?.template);
        } catch (error) {
            console.error('Failed to get deployment plans:', error);
            return [];
        }
    }

    async executeDeployment(planId: string, environment: string): Promise<{ deployment_id: string }> {
        return this.makeRequest(`/api/gitops/deployment-plans/${planId}/deploy`, {
            method: 'POST',
            body: JSON.stringify({ environment }),
        });
    }

    async getDeploymentStatus(deploymentId: string): Promise<{
        status: 'pending' | 'running' | 'success' | 'failed';
        logs: string[];
        progress: number;
        start_time: string;
        end_time?: string;
        error?: string;
    }> {
        return this.makeRequest(`/api/gitops/deployments/${deploymentId}/status`);
    }

    // Webhook Management
    async setupWebhook(repoId: string, events: string[]): Promise<{ webhook_id: string; webhook_url: string }> {
        return this.makeRequest(`/api/gitops/repositories/${repoId}/webhooks`, {
            method: 'POST',
            body: JSON.stringify({ events }),
        });
    }

    async removeWebhook(repoId: string, webhookId: string): Promise<void> {
        await this.makeRequest(`/api/gitops/repositories/${repoId}/webhooks/${webhookId}`, {
            method: 'DELETE',
        });
    }

    // Infrastructure Diff & Preview
    async previewChanges(
        repoId: string,
        branch: string,
        templateId: string,
        variables: Record<string, any>
    ): Promise<{
        plan: string;
        changes: {
            to_add: number;
            to_change: number;
            to_destroy: number;
        };
        resources: Array<{
            address: string;
            mode: string;
            type: string;
            name: string;
            change: {
                actions: string[];
                before: any;
                after: any;
            };
        }>;
    }> {
        return this.makeRequest(`/api/gitops/repositories/${repoId}/preview`, {
            method: 'POST',
            body: JSON.stringify({
                branch,
                template_id: templateId,
                variables,
            }),
        });
    }

    // Git Integration Utilities
    async validateRepository(repoUrl: string, accessToken: string): Promise<{ valid: boolean; error?: string }> {
        return this.makeRequest('/api/gitops/validate-repository', {
            method: 'POST',
            body: JSON.stringify({
                repo_url: repoUrl,
                access_token: accessToken,
            }),
        });
    }

    async generateIaCFromAssessment(assessmentId: string, provider: 'terraform' | 'cloudformation'): Promise<{
        template: string;
        variables: Record<string, any>;
        outputs: Record<string, any>;
    }> {
        return this.makeRequest(`/api/gitops/generate-iac/${assessmentId}`, {
            method: 'POST',
            body: JSON.stringify({ provider }),
        });
    }
}

// Singleton instance
let gitOpsService: GitOpsIntegrationService | null = null;

export const getGitOpsService = (): GitOpsIntegrationService => {
    if (!gitOpsService) {
        gitOpsService = new GitOpsIntegrationService();
    }
    return gitOpsService;
};

export default GitOpsIntegrationService;