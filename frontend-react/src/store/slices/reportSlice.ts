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
    async ({ reportId, format }: { reportId: string; format: string }) => {
        // Simulate export process with progress
        return new Promise<{ url: string; format: string }>((resolve) => {
            let progress = 0;
            const interval = setInterval(() => {
                progress += 20;
                if (progress >= 100) {
                    clearInterval(interval);
                    resolve({
                        url: `https://example.com/reports/${reportId}.${format}`,
                        format,
                    });
                }
            }, 200);
        });
    }
);

export const shareReport = createAsyncThunk(
    'report/share',
    async ({ reportId }: { reportId: string }) => {
        // Simulate API call
        const response = await new Promise<{ shareUrl: string }>((resolve) => {
            setTimeout(() => {
                resolve({
                    shareUrl: `https://example.com/shared/reports/${reportId}`,
                });
            }, 1000);
        });
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
            
            // Transform the response to ensure compatibility with frontend
            const transformedReports = response.map((report: Report) => ({
                ...report,
                // Add compatibility fields
                assessmentId: report.assessment_id || report.assessmentId,
                generated_at: report.completed_at || report.created_at,
                estimated_savings: report.estimated_savings || 0,
            }));
            
            console.log('✅ Transformed reports:', transformedReports);
            return transformedReports;
        } catch (error) {
            console.error('❌ Failed to fetch reports:', error);
            return rejectWithValue(error instanceof Error ? error.message : 'Failed to fetch reports');
        }
    }
);

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