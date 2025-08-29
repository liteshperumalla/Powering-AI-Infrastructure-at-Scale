import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { apiClient } from '../../services/api';

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
    companyName?: string;
    industry?: string;
    assessmentStatus?: string;
}

interface ReportState {
    reports: Report[];
    currentReport: Report | null;
    loading: boolean;
    error: string | null;
    exportProgress: number;
    shareUrl: string | null;
}

const initialState: ReportState = {
    reports: [],
    currentReport: null,
    loading: false,
    error: null,
    exportProgress: 0,
    shareUrl: null,
};

// Async thunks
export const generateReport = createAsyncThunk(
    'report/generate',
    async (assessmentId: string) => {
        // Simulate API call with correct backend structure
        const response = await new Promise<Report>((resolve) => {
            setTimeout(() => {
                resolve({
                    id: Date.now().toString(),
                    assessment_id: assessmentId,
                    user_id: 'user_123',
                    title: `AI Infrastructure Strategy Report - ${new Date().toLocaleDateString()}`,
                    description: 'High-level strategic report for executive decision-making',
                    report_type: 'executive_summary',
                    format: 'pdf',
                    status: 'completed',
                    progress_percentage: 100,
                    sections: ['executive_summary', 'strategic_recommendations', 'investment_analysis'],
                    total_pages: 12,
                    word_count: 3500,
                    file_path: '/reports/mock_report.pdf',
                    file_size_bytes: 2400000,
                    generated_by: ['report_generator_agent'],
                    generation_time_seconds: 45.2,
                    completeness_score: 0.95,
                    confidence_score: 0.89,
                    priority: 'high',
                    tags: ['executive', 'strategic'],
                    retry_count: 0,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                    completed_at: new Date().toISOString(),
                    // Compatibility fields
                    assessmentId: assessmentId,
                    generated_at: new Date().toISOString(),
                    estimated_savings: 45000,
                });
            }, 2000);
        });
        return response;
    }
);

export const exportReport = createAsyncThunk(
    'report/export',
    async ({ reportId, format }: { reportId: string; format: string }, { dispatch }) => {
        try {
            // First get the report to find the assessment ID
            const report = await apiClient.getReportById(reportId);
            
            // Update progress
            dispatch(setExportProgress(20));
            
            // Download the report file
            const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const token = localStorage.getItem('auth_token');
            
            dispatch(setExportProgress(50));
            
            const response = await fetch(
                `${API_BASE_URL}/api/v1/assessments/${report.assessment_id}/reports/${reportId}/download?format=${format}`,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                    },
                }
            );
            
            dispatch(setExportProgress(80));
            
            if (!response.ok) {
                throw new Error('Failed to download report');
            }
            
            // Create blob and download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            
            // Get filename from Content-Disposition header or use default
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `report_${reportId}.${format}`;
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
                if (filenameMatch) {
                    filename = filenameMatch[1];
                }
            }
            
            // Trigger download
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Clean up
            window.URL.revokeObjectURL(url);
            
            dispatch(setExportProgress(100));
            
            return { url, format };
        } catch (error) {
            dispatch(setExportProgress(0));
            throw error;
        }
    }
);

export const shareReport = createAsyncThunk(
    'report/share',
    async ({ reportId, settings }: { 
        reportId: string; 
        settings?: {
            isPublic?: boolean;
            sharedWith?: string[];
            expiresAt?: string;
            requireAuth?: boolean;
            allowDownload?: boolean;
            allowComments?: boolean;
            customMessage?: string;
        };
    }) => {
        const response = await apiClient.shareReport(reportId, settings || {});
        return response;
    }
);

export const fetchReports = createAsyncThunk(
    'report/fetchAll',
    async (_, { rejectWithValue }) => {
        try {
            console.log('🔄 Fetching all reports...');
            const response = await apiClient.getReports();
            console.log('📊 Raw API response:', response);
            
            // Fetch assessments to get company names and detailed data
            const assessmentsResponse = await apiClient.getAssessments();
            const assessments = assessmentsResponse.assessments || [];
            
            // Transform the response and enhance with assessment data
            const transformedReports = response.map((report: Report) => {
                const assessment = assessments.find(a => a.id === (report.assessment_id || report.assessmentId));
                
                // Calculate real savings based on assessment data
                const realSavings = assessment ? calculateEstimatedSavings(assessment) : 0;
                
                return {
                    ...report,
                    // Add compatibility fields
                    assessmentId: report.assessment_id || report.assessmentId,
                    generated_at: report.completed_at || report.created_at,
                    estimated_savings: realSavings,
                    // Extract company name from title or other fields
                    title: (() => {
                        const companyName = assessment?.companyName || assessment?.business_requirements?.company_name;
                        if (companyName) {
                            return `Complete Infrastructure Assessment - ${companyName}`;
                        }
                        // Extract company name from existing title if it contains company name
                        if (assessment?.title) {
                            const titleMatch = assessment.title.match(/^(.+?)\s+Healthcare\s+AI\s+Infrastructure\s+Assessment$/i) ||
                                              assessment.title.match(/^(.+?)\s+Infrastructure\s+Assessment$/i) ||
                                              assessment.title.match(/^(.+?)\s+AI\s+Infrastructure\s+Assessment$/i);
                            if (titleMatch) {
                                return `Complete Infrastructure Assessment - ${titleMatch[1]}`;
                            }
                        }
                        return report.title || assessment?.title || 'Complete Infrastructure Assessment';
                    })(),
                    // Add assessment context  
                    companyName: (() => {
                        const companyName = assessment?.companyName || assessment?.business_requirements?.company_name;
                        if (companyName) return companyName;
                        
                        // Extract from title
                        if (assessment?.title) {
                            const titleMatch = assessment.title.match(/^(.+?)\s+Healthcare\s+AI\s+Infrastructure\s+Assessment$/i) ||
                                              assessment.title.match(/^(.+?)\s+Infrastructure\s+Assessment$/i) ||
                                              assessment.title.match(/^(.+?)\s+AI\s+Infrastructure\s+Assessment$/i);
                            if (titleMatch) {
                                return titleMatch[1];
                            }
                        }
                        return 'Unknown Company';
                    })(),
                    industry: assessment?.industry || 'Unknown Industry',
                    assessmentStatus: assessment?.status || 'unknown'
                };
            });
            
            console.log('✅ Transformed reports with assessment data:', transformedReports);
            return transformedReports;
        } catch (error) {
            console.error('❌ Failed to fetch reports:', error);
            return rejectWithValue(error instanceof Error ? error.message : 'Failed to fetch reports');
        }
    }
);

// Helper function to calculate real savings based on assessment data
function calculateEstimatedSavings(assessment: any): number {
    try {
        // Base savings calculation on various factors
        let savings = 0;
        
        // Budget-based savings (10-30% of monthly budget)
        const monthlyBudget = parseFloat(assessment.monthlyBudget || assessment.business_requirements?.monthly_budget || '0');
        if (monthlyBudget > 0) {
            savings += monthlyBudget * 12 * 0.18; // 18% annual savings
        } else {
            // Fallback: base savings on company size and industry
            savings = 75000; // Base amount for companies
        }
        
        // Company size multiplier
        const sizeMultiplier = {
            '1-10': 0.8,
            '11-50': 1.0,
            '51-100': 1.2,
            '101-500': 1.5,
            '500+': 2.0
        };
        const companySize = assessment.companySize || '1-10';
        savings *= (sizeMultiplier[companySize] || 1.0);
        
        // Industry-specific multipliers
        const industryMultiplier = {
            'Healthcare AI': 1.4,
            'FinTech': 1.3,
            'E-commerce': 1.2,
            'Gaming': 1.1,
            'Enterprise': 1.0
        };
        const industry = assessment.industry || 'Enterprise';
        savings *= (industryMultiplier[industry] || 1.0);
        
        // AI maturity impact
        const maturityMultiplier = {
            'Pilot Projects': 1.2,
            'Production': 1.5,
            'Scaled': 1.8,
            'Research': 1.0
        };
        const aiMaturity = assessment.currentAIMaturity || 'Research';
        savings *= (maturityMultiplier[aiMaturity] || 1.0);
        
        // Round to nearest thousand
        return Math.round(savings / 1000) * 1000;
    } catch (error) {
        console.error('Error calculating savings:', error);
        return 45000; // Default fallback
    }
}

const reportSlice = createSlice({
    name: 'report',
    initialState,
    reducers: {
        setCurrentReport: (state, action: PayloadAction<Report | null>) => {
            state.currentReport = action.payload;
        },
        updateReportStatus: (state, action: PayloadAction<{ reportId: string; status: Report['status'] }>) => {
            const report = state.reports.find(r => r.id === action.payload.reportId);
            if (report) {
                report.status = action.payload.status;
            }
            if (state.currentReport?.id === action.payload.reportId) {
                state.currentReport.status = action.payload.status;
            }
        },
        setExportProgress: (state, action: PayloadAction<number>) => {
            state.exportProgress = action.payload;
        },
        clearShareUrl: (state) => {
            state.shareUrl = null;
        },
        clearError: (state) => {
            state.error = null;
        },
    },
    extraReducers: (builder) => {
        builder
            // Generate report
            .addCase(generateReport.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(generateReport.fulfilled, (state, action) => {
                state.loading = false;
                state.reports.push(action.payload);
                state.currentReport = action.payload;
            })
            .addCase(generateReport.rejected, (state, action) => {
                state.loading = false;
                state.error = action.error.message || 'Failed to generate report';
            })
            // Export report
            .addCase(exportReport.pending, (state) => {
                state.exportProgress = 0;
            })
            .addCase(exportReport.fulfilled, (state) => {
                state.exportProgress = 100;
            })
            .addCase(exportReport.rejected, (state, action) => {
                state.exportProgress = 0;
                state.error = action.error.message || 'Failed to export report';
            })
            // Share report
            .addCase(shareReport.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(shareReport.fulfilled, (state, action) => {
                state.loading = false;
                state.shareUrl = action.payload.shareUrl;
            })
            .addCase(shareReport.rejected, (state, action) => {
                state.loading = false;
                state.error = action.error.message || 'Failed to share report';
            })
            // Fetch reports
            .addCase(fetchReports.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchReports.fulfilled, (state, action) => {
                state.loading = false;
                state.reports = action.payload;
            })
            .addCase(fetchReports.rejected, (state, action) => {
                state.loading = false;
                state.error = action.error.message || 'Failed to fetch reports';
            });
    },
});

export const {
    setCurrentReport,
    updateReportStatus,
    setExportProgress,
    clearShareUrl,
    clearError,
} = reportSlice.actions;

export default reportSlice.reducer;