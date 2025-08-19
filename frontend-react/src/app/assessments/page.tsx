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
    Tooltip
} from '@mui/material';
import {
    Add as AddIcon,
    Visibility as ViewIcon,
    Edit as EditIcon,
    Delete as DeleteIcon,
    PlayArrow as StartIcon,
    Assessment as AssessmentIcon
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import { apiClient } from '../../services/api';
import { Assessment } from '../../store/slices/assessmentSlice';

interface AssessmentsPageState {
    assessments: Assessment[];
    loading: boolean;
    error: string | null;
}

const AssessmentsPage: React.FC = () => {
    const router = useRouter();
    const [state, setState] = useState<AssessmentsPageState>({
        assessments: [],
        loading: true,
        error: null
    });

    useEffect(() => {
        loadAssessments();
    }, []);

    const loadAssessments = async () => {
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
            <Container maxWidth="lg" sx={{ py: 4 }}>
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
                    <Typography variant="h4" component="h1" gutterBottom>
                        Infrastructure Assessments
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
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

export default AssessmentsPage;