import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

export interface ReportSection {
    title: string;
    content: string;
    type: 'executive' | 'technical' | 'financial' | 'compliance';
}

export interface Report {
    id: string;
    title: string;
    assessmentId: string;
    generatedDate: string;
    status: 'draft' | 'generating' | 'final' | 'error';
    sections: ReportSection[];
    keyFindings: string[];
    recommendations: string[];
    estimatedSavings: number;
    complianceScore: number;
    exportFormats: ('pdf' | 'json' | 'csv' | 'markdown')[];
    shareSettings: {
        isPublic: boolean;
        sharedWith: string[];
        expiresAt?: string;
    };
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
        // Simulate API call
        const response = await new Promise<Report>((resolve) => {
            setTimeout(() => {
                resolve({
                    id: Date.now().toString(),
                    title: `AI Infrastructure Strategy Report - ${new Date().toLocaleDateString()}`,
                    assessmentId,
                    generatedDate: new Date().toISOString(),
                    status: 'final',
                    sections: [
                        {
                            title: 'Executive Summary',
                            content: 'This report provides comprehensive recommendations for scaling AI infrastructure...',
                            type: 'executive',
                        },
                        {
                            title: 'Technical Architecture',
                            content: 'Detailed technical specifications and implementation roadmap...',
                            type: 'technical',
                        },
                        {
                            title: 'Cost Analysis',
                            content: 'Financial projections and ROI calculations for the proposed infrastructure...',
                            type: 'financial',
                        },
                        {
                            title: 'Compliance Assessment',
                            content: 'Regulatory compliance analysis and recommendations...',
                            type: 'compliance',
                        },
                    ],
                    keyFindings: [
                        'Multi-cloud strategy can reduce costs by 23%',
                        'Current infrastructure is over-provisioned by 35%',
                        'Compliance gaps identified in data storage',
                    ],
                    recommendations: [
                        'Implement hybrid AWS-Azure architecture',
                        'Migrate to containerized workloads',
                        'Establish automated compliance monitoring',
                    ],
                    estimatedSavings: 45000,
                    complianceScore: 98,
                    exportFormats: ['pdf', 'json', 'markdown'],
                    shareSettings: {
                        isPublic: false,
                        sharedWith: [],
                    },
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
    async ({ reportId, settings }: { reportId: string; settings: Report['shareSettings'] }) => {
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
    async () => {
        // Simulate API call
        const response = await new Promise<Report[]>((resolve) => {
            setTimeout(() => {
                resolve([
                    {
                        id: 'report-1',
                        title: 'AI Infrastructure Strategy Report - Sample Corp',
                        assessmentId: '1',
                        generatedDate: '2024-01-15T10:30:00Z',
                        status: 'final',
                        sections: [
                            {
                                title: 'Executive Summary',
                                content: 'This report provides comprehensive recommendations for scaling AI infrastructure...',
                                type: 'executive',
                            },
                            {
                                title: 'Technical Architecture',
                                content: 'Detailed technical specifications and implementation roadmap...',
                                type: 'technical',
                            },
                            {
                                title: 'Cost Analysis',
                                content: 'Financial projections and ROI calculations for the proposed infrastructure...',
                                type: 'financial',
                            },
                        ],
                        keyFindings: [
                            'Multi-cloud strategy can reduce costs by 23%',
                            'Current infrastructure is over-provisioned by 35%',
                            'Compliance gaps identified in data storage',
                        ],
                        recommendations: [
                            'Implement hybrid AWS-Azure architecture',
                            'Migrate to containerized workloads',
                            'Establish automated compliance monitoring',
                        ],
                        estimatedSavings: 45000,
                        complianceScore: 98,
                        exportFormats: ['pdf', 'json', 'markdown'],
                        shareSettings: {
                            isPublic: false,
                            sharedWith: [],
                        },
                    },
                ]);
            }, 1000);
        });
        return response;
    }
);

const reportSlice = createSlice({
    name: 'report',
    initialState,
    reducers: {
        setCurrentReport: (state, action: PayloadAction<Report | null>) => {
            state.currentReport = action.payload;
        },
        updateReportShareSettings: (state, action: PayloadAction<{ reportId: string; settings: Report['shareSettings'] }>) => {
            const report = state.reports.find(r => r.id === action.payload.reportId);
            if (report) {
                report.shareSettings = action.payload.settings;
            }
            if (state.currentReport?.id === action.payload.reportId) {
                state.currentReport.shareSettings = action.payload.settings;
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
    updateReportShareSettings,
    setExportProgress,
    clearShareUrl,
    clearError,
} = reportSlice.actions;

export default reportSlice.reducer;