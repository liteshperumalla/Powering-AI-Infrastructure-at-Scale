'use client';

import React, { useState, useEffect } from 'react';
import {
    Container,
    Typography,
    Box,
    Card,
    CardContent,
    Button,
    Grid,
    Chip,
    LinearProgress,
    Alert,
    CircularProgress,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    IconButton,
    Tooltip,
    Checkbox
} from '@mui/material';
import {
    Add as AddIcon,
    Visibility as ViewIcon,
    Edit as EditIcon,
    Delete as DeleteIcon,
    PlayArrow as StartIcon,
    Assessment as AssessmentIcon,
    SelectAll as SelectAllIcon,
    GetApp as ExportIcon,
    DeleteSweep as BulkDeleteIcon,
    CheckBox,
    CheckBoxOutlineBlank,
    Timeline as WorkflowIcon,
    Close as CloseIcon
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import { apiClient } from '../../services/api';
import { Assessment } from '../../store/slices/assessmentSlice';
import WorkflowProgress from '../../components/WorkflowProgress';
import { useAppSelector } from '../../store/hooks';
import ResponsiveLayout from '@/components/ResponsiveLayout';
import ProtectedRoute from '@/components/ProtectedRoute';

interface AssessmentsPageState {
    assessments: Assessment[];
    loading: boolean;
    error: string | null;
    selectedAssessments: string[];
    bulkOperationLoading: boolean;
    workflowViewAssessmentId: string | null;
}

const AssessmentsPage: React.FC = () => {
    const router = useRouter();
    const { isAuthenticated, loading: authLoading } = useAppSelector(state => state.auth);
    const [state, setState] = useState<AssessmentsPageState>({
        assessments: [],
        loading: true,
        error: null,
        selectedAssessments: [],
        bulkOperationLoading: false,
        workflowViewAssessmentId: null
    });

    useEffect(() => {
        if (isAuthenticated && !authLoading) {
            loadAssessments();
        } else if (!authLoading && !isAuthenticated) {
            // User is not authenticated, redirect to login
            router.push('/auth/login');
        }
    }, [isAuthenticated, authLoading, router]);

    const loadAssessments = async () => {
        if (!isAuthenticated) {
            setState(prev => ({ ...prev, loading: false }));
            return;
        }
        
        try {
            setState(prev => ({ ...prev, loading: true, error: null }));
            const response = await apiClient.getAssessments();
            setState(prev => ({
                ...prev,
                assessments: response.assessments || [],
                loading: false
            }));
        } catch (error) {
            console.error('Failed to load assessments:', error);
            setState(prev => ({
                ...prev,
                error: error instanceof Error ? error.message : 'Failed to load assessments',
                loading: false
            }));
        }
    };

    const handleCreateAssessment = () => {
        router.push('/assessment');
    };

    const handleViewAssessment = (assessmentId: string) => {
        router.push(`/dashboard?assessment=${assessmentId}`);
    };

    const handleEditAssessment = (assessmentId: string) => {
        router.push(`/assessment?edit=${assessmentId}`);
    };

    const handleDeleteAssessment = async (assessmentId: string) => {
        if (!confirm('Are you sure you want to delete this assessment?')) {
            return;
        }

        try {
            await apiClient.deleteAssessment(assessmentId);
            await loadAssessments(); // Reload the list
        } catch (error) {
            console.error('Failed to delete assessment:', error);
            alert('Failed to delete assessment. Please try again.');
        }
    };

    // Phase 2: Multi-selection and bulk operations
    const handleSelectAssessment = (assessmentId: string, checked: boolean) => {
        setState(prev => ({
            ...prev,
            selectedAssessments: checked 
                ? [...prev.selectedAssessments, assessmentId]
                : prev.selectedAssessments.filter(id => id !== assessmentId)
        }));
    };

    const handleSelectAll = (checked: boolean) => {
        setState(prev => ({
            ...prev,
            selectedAssessments: checked ? state.assessments.map(a => a.id) : []
        }));
    };

    const handleBulkDelete = async () => {
        if (state.selectedAssessments.length === 0) return;
        
        if (!confirm(`Are you sure you want to delete ${state.selectedAssessments.length} assessment(s)?`)) {
            return;
        }

        setState(prev => ({ ...prev, bulkOperationLoading: true }));
        
        try {
            // Try bulk delete API first, fallback to sequential delete
            try {
                await apiClient.bulkDeleteAssessments(state.selectedAssessments);
            } catch (bulkError) {
                console.log('Bulk delete not available, using sequential delete');
                // Delete assessments sequentially to avoid overwhelming the API
                for (const assessmentId of state.selectedAssessments) {
                    await apiClient.deleteAssessment(assessmentId);
                }
            }
            await loadAssessments();
            setState(prev => ({ ...prev, selectedAssessments: [], bulkOperationLoading: false }));
        } catch (error) {
            console.error('Failed to bulk delete assessments:', error);
            alert('Failed to delete some assessments. Please try again.');
            setState(prev => ({ ...prev, bulkOperationLoading: false }));
        }
    };

    const handleBulkExport = async () => {
        if (state.selectedAssessments.length === 0) return;
        
        setState(prev => ({ ...prev, bulkOperationLoading: true }));
        
        try {
            // Create CSV data for selected assessments
            const selectedData = state.assessments.filter(a => 
                state.selectedAssessments.includes(a.id)
            );
            
            const csvHeaders = ['Title', 'Status', 'Progress', 'Created', 'Updated'];
            const csvData = selectedData.map(assessment => [
                assessment.title,
                assessment.status || 'Unknown',
                `${assessment.completion_percentage || 0}%`,
                formatDate(assessment.created_at),
                formatDate(assessment.updated_at)
            ]);
            
            const csvContent = [
                csvHeaders.join(','),
                ...csvData.map(row => row.map(cell => `"${cell}"`).join(','))
            ].join('\n');
            
            // Download CSV
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `assessments_export_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
            setState(prev => ({ ...prev, bulkOperationLoading: false }));
        } catch (error) {
            console.error('Failed to export assessments:', error);
            alert('Failed to export assessments. Please try again.');
            setState(prev => ({ ...prev, bulkOperationLoading: false }));
        }
    };

    const handleShowWorkflowProgress = (assessmentId: string) => {
        setState(prev => ({ ...prev, workflowViewAssessmentId: assessmentId }));
    };

    const handleHideWorkflowProgress = () => {
        setState(prev => ({ ...prev, workflowViewAssessmentId: null }));
    };

    const getStatusColor = (status: string) => {
        switch (status?.toLowerCase()) {
            case 'completed': return 'success';
            case 'in_progress': return 'warning';
            case 'draft': return 'default';
            case 'failed': return 'error';
            default: return 'default';
        }
    };

    const formatDate = (dateString: string) => {
        try {
            return new Date(dateString).toLocaleDateString();
        } catch {
            return 'N/A';
        }
    };

    if (state.loading) {
        return (
            <Container maxWidth="lg" sx={{ mt: 3, py: 4 }}>
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
                    <CircularProgress />
                </Box>
            </Container>
        );
    }

    return (
        <Container maxWidth="lg" sx={{ py: 4 }}>
            {/* Header */}
            <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                    <Typography
                        variant="h4"
                        component="h1"
                        gutterBottom
                        sx={{
                            color: 'text.primary',
                            fontWeight: 'bold'
                        }}
                    >
                        Infrastructure Assessments
                    </Typography>
                    <Typography
                        variant="body1"
                        sx={{
                            color: 'text.secondary'
                        }}
                    >
                        Manage and view your cloud infrastructure assessments
                    </Typography>
                </Box>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={handleCreateAssessment}
                    size="large"
                >
                    New Assessment
                </Button>
            </Box>

            {/* Error Alert */}
            {state.error && (
                <Alert severity="error" sx={{ mb: 3 }} onClose={() => setState(prev => ({ ...prev, error: null }))}>
                    {state.error}
                </Alert>
            )}

            {/* Workflow Progress Modal */}
            {state.workflowViewAssessmentId && (
                <Card sx={{ mb: 3 }}>
                    <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                            <Typography variant="h6">
                                Workflow Progress
                            </Typography>
                            <IconButton onClick={handleHideWorkflowProgress}>
                                <CloseIcon />
                            </IconButton>
                        </Box>
                        <WorkflowProgress
                            assessmentId={state.workflowViewAssessmentId}
                            onProgressUpdate={() => loadAssessments()}
                            autoRefresh={true}
                            refreshInterval={5000}
                        />
                    </CardContent>
                </Card>
            )}

            {/* Phase 2: Bulk Actions Toolbar */}
            {state.selectedAssessments.length > 0 && (
                <Card sx={{ mb: 3, bgcolor: 'action.selected' }}>
                    <CardContent sx={{ py: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <SelectAllIcon color="primary" />
                                {state.selectedAssessments.length} assessment(s) selected
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 1 }}>
                                <Button
                                    variant="outlined"
                                    startIcon={<ExportIcon />}
                                    onClick={handleBulkExport}
                                    disabled={state.bulkOperationLoading}
                                    size="small"
                                >
                                    Export CSV
                                </Button>
                                <Button
                                    variant="outlined"
                                    color="error"
                                    startIcon={<BulkDeleteIcon />}
                                    onClick={handleBulkDelete}
                                    disabled={state.bulkOperationLoading}
                                    size="small"
                                >
                                    Delete Selected
                                </Button>
                                <Button
                                    variant="text"
                                    onClick={() => setState(prev => ({ ...prev, selectedAssessments: [] }))}
                                    size="small"
                                >
                                    Clear Selection
                                </Button>
                            </Box>
                        </Box>
                        {state.bulkOperationLoading && (
                            <LinearProgress sx={{ mt: 1 }} />
                        )}
                    </CardContent>
                </Card>
            )}

            {/* Summary Cards */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="text.secondary" gutterBottom>
                                Total Assessments
                            </Typography>
                            <Typography variant="h4">
                                {state.assessments.length}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="text.secondary" gutterBottom>
                                Completed
                            </Typography>
                            <Typography variant="h4" color="success.main">
                                {state.assessments.filter(a => a.status === 'completed').length}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="text.secondary" gutterBottom>
                                In Progress
                            </Typography>
                            <Typography variant="h4" color="warning.main">
                                {state.assessments.filter(a => a.status === 'in_progress').length}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="text.secondary" gutterBottom>
                                Drafts
                            </Typography>
                            <Typography variant="h4" color="text.secondary">
                                {state.assessments.filter(a => a.status === 'draft').length}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Assessments Table or Empty State */}
            {state.assessments.length === 0 ? (
                <Card>
                    <CardContent>
                        <Box sx={{ 
                            display: 'flex', 
                            flexDirection: 'column', 
                            alignItems: 'center', 
                            justifyContent: 'center',
                            py: 6,
                            textAlign: 'center'
                        }}>
                            <AssessmentIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                            <Typography variant="h6" color="text.secondary" gutterBottom>
                                No Assessments Yet
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                                Create your first infrastructure assessment to get personalized recommendations.
                            </Typography>
                            <Button 
                                variant="contained" 
                                startIcon={<AddIcon />}
                                onClick={handleCreateAssessment}
                            >
                                Create Assessment
                            </Button>
                        </Box>
                    </CardContent>
                </Card>
            ) : (
                <Card>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>
                            Your Assessments
                        </Typography>
                        <TableContainer component={Paper} elevation={0}>
                            <Table>
                                <TableHead>
                                    <TableRow>
                                        <TableCell padding="checkbox">
                                            <Checkbox
                                                indeterminate={
                                                    state.selectedAssessments.length > 0 && 
                                                    state.selectedAssessments.length < state.assessments.length
                                                }
                                                checked={
                                                    state.assessments.length > 0 && 
                                                    state.selectedAssessments.length === state.assessments.length
                                                }
                                                onChange={(event) => handleSelectAll(event.target.checked)}
                                                inputProps={{ 'aria-label': 'select all assessments' }}
                                            />
                                        </TableCell>
                                        <TableCell>Title</TableCell>
                                        <TableCell>Status</TableCell>
                                        <TableCell>Progress</TableCell>
                                        <TableCell>Created</TableCell>
                                        <TableCell>Updated</TableCell>
                                        <TableCell align="right">Actions</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {state.assessments.map((assessment) => (
                                        <TableRow key={assessment.id} hover>
                                            <TableCell padding="checkbox">
                                                <Checkbox
                                                    checked={state.selectedAssessments.includes(assessment.id)}
                                                    onChange={(event) => handleSelectAssessment(assessment.id, event.target.checked)}
                                                    inputProps={{ 'aria-label': `select assessment ${assessment.title}` }}
                                                />
                                            </TableCell>
                                            <TableCell>
                                                <Box>
                                                    <Typography variant="body1" fontWeight="medium">
                                                        {assessment.title}
                                                    </Typography>
                                                    {assessment.description && (
                                                        <Typography variant="body2" color="text.secondary">
                                                            {assessment.description}
                                                        </Typography>
                                                    )}
                                                </Box>
                                            </TableCell>
                                            <TableCell>
                                                <Chip
                                                    label={assessment.status?.replace('_', ' ').toUpperCase() || 'UNKNOWN'}
                                                    color={getStatusColor(assessment.status || '') as any}
                                                    size="small"
                                                />
                                            </TableCell>
                                            <TableCell>
                                                <Box sx={{ width: 100 }}>
                                                    <LinearProgress
                                                        variant="determinate"
                                                        value={assessment.completion_percentage || 0}
                                                        sx={{ mb: 0.5 }}
                                                    />
                                                    <Typography variant="caption">
                                                        {assessment.completion_percentage || 0}%
                                                    </Typography>
                                                </Box>
                                            </TableCell>
                                            <TableCell>
                                                {formatDate(assessment.created_at)}
                                            </TableCell>
                                            <TableCell>
                                                {formatDate(assessment.updated_at)}
                                            </TableCell>
                                            <TableCell align="right">
                                                <Box sx={{ display: 'flex', gap: 1 }}>
                                                    <Tooltip title="View Details">
                                                        <IconButton
                                                            size="small"
                                                            onClick={() => handleViewAssessment(assessment.id)}
                                                        >
                                                            <ViewIcon />
                                                        </IconButton>
                                                    </Tooltip>
                                                    {assessment.status === 'in_progress' && (
                                                        <Tooltip title="View Workflow Progress">
                                                            <IconButton
                                                                size="small"
                                                                onClick={() => handleShowWorkflowProgress(assessment.id)}
                                                                color="primary"
                                                            >
                                                                <WorkflowIcon />
                                                            </IconButton>
                                                        </Tooltip>
                                                    )}
                                                    <Tooltip title="Edit">
                                                        <IconButton
                                                            size="small"
                                                            onClick={() => handleEditAssessment(assessment.id)}
                                                        >
                                                            <EditIcon />
                                                        </IconButton>
                                                    </Tooltip>
                                                    <Tooltip title="Delete">
                                                        <IconButton
                                                            size="small"
                                                            onClick={() => handleDeleteAssessment(assessment.id)}
                                                            color="error"
                                                        >
                                                            <DeleteIcon />
                                                        </IconButton>
                                                    </Tooltip>
                                                </Box>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    </CardContent>
                </Card>
            )}
        </Container>
    );
};

function AssessmentsPageWithLayout() {
    return (
        <ProtectedRoute>
            <ResponsiveLayout title="Assessments">
                <AssessmentsPage />
            </ResponsiveLayout>
        </ProtectedRoute>
    );
}

export default AssessmentsPageWithLayout;