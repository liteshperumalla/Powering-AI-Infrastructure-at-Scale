'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import ResponsiveLayout from '../../components/ResponsiveLayout';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  Alert,
  CircularProgress,
  Stack,
  Chip,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Tabs,
  Tab,
  IconButton
} from '@mui/material';
import {
  CheckCircle,
  Pending,
  Cancel,
  Refresh,
  AccountTree,
  Warning
} from '@mui/icons-material';
import { apiClient } from '../../services/api';

export default function ApprovalsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const currentAssessment = useSelector((state: RootState) => state.assessment.currentAssessment);
  const assessments = useSelector((state: RootState) => state.assessment.assessments);
  const currentUser = useSelector((state: RootState) => state.auth.user);

  // Priority: URL param > Redux currentAssessment > First assessment in list
  const urlAssessmentId = searchParams?.get('assessment_id');
  const assessmentId = urlAssessmentId || currentAssessment?.id || (assessments.length > 0 ? assessments[0].id : null);

  const [approvalsData, setApprovalsData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Approval dialog state
  const [approvalDialog, setApprovalDialog] = useState<{
    open: boolean;
    type: 'approve' | 'reject' | null;
    recommendationId: string | null;
    recommendationTitle: string | null;
  }>({
    open: false,
    type: null,
    recommendationId: null,
    recommendationTitle: null
  });
  const [approvalComment, setApprovalComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const [recommendationStatuses, setRecommendationStatuses] = useState<Record<string, 'approved' | 'rejected' | 'pending'>>({});
  const [filterStatus, setFilterStatus] = useState<'all' | 'pending' | 'approved' | 'rejected'>('all');

  // No redirect - just handle the case when there's no assessment

  const fetchData = useCallback(async () => {
    if (!assessmentId) {
      setError('No assessment ID provided. Please select an assessment first.');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const response = await apiClient.get<any>(`/features/assessment/${assessmentId}/approvals`);
      console.log('📊 Approvals Data Received:', {
        hasWorkflows: !!response?.workflows,
        hasSummary: !!response?.summary,
        workflowsCount: response?.workflows?.length,
        fullData: response
      });
      setApprovalsData(response);
      setError(null);
    } catch (err: any) {
      console.error('Failed to load approvals data:', err);
      setError(err.message || 'Failed to load approval workflows');
      setApprovalsData(null);
    } finally {
      setLoading(false);
    }
  }, [assessmentId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const fetchRecommendations = useCallback(async () => {
    if (!assessmentId) return;

    try {
      setLoadingRecommendations(true);
      const response = await apiClient.get<any>(`/recommendations?assessment_id=${assessmentId}&limit=100`);
      console.log('📋 Recommendations loaded:', response.recommendations?.length || 0);
      setRecommendations(response.recommendations || []);
    } catch (err: any) {
      console.error('Failed to load recommendations:', err);
    } finally {
      setLoadingRecommendations(false);
    }
  }, [assessmentId]);

  useEffect(() => {
    if (approvalsData) {
      fetchRecommendations();
    }
  }, [approvalsData, fetchRecommendations]);

  const handleOpenApprovalDialog = (type: 'approve' | 'reject', recommendationId: string, recommendationTitle: string) => {
    setApprovalDialog({
      open: true,
      type,
      recommendationId,
      recommendationTitle
    });
    setApprovalComment('');
  };

  const handleCloseApprovalDialog = () => {
    setApprovalDialog({
      open: false,
      type: null,
      recommendationId: null,
      recommendationTitle: null
    });
    setApprovalComment('');
  };

  const handleSubmitApproval = async () => {
    if (!approvalDialog.recommendationId || !approvalDialog.type) return;

    try {
      setSubmitting(true);

      // Update local state immediately for better UX
      setRecommendationStatuses(prev => ({
        ...prev,
        [approvalDialog.recommendationId!]: approvalDialog.type as 'approved' | 'rejected'
      }));

      // Here you would call the backend API to persist the approval
      // For now, we're storing it in local state
      console.log(`✅ Recommendation ${approvalDialog.type}:`, {
        id: approvalDialog.recommendationId,
        title: approvalDialog.recommendationTitle,
        approver: currentUser?.email,
        comment: approvalComment,
        timestamp: new Date().toISOString()
      });

      handleCloseApprovalDialog();

      // Show success message
      setError(null);

    } catch (err: any) {
      console.error('Failed to submit approval:', err);
      setError(err.message || `Failed to ${approvalDialog.type} recommendation`);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <ResponsiveLayout title="Approval Workflows">
        <Container>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
            <CircularProgress />
          </Box>
        </Container>
      </ResponsiveLayout>
    );
  }

  return (
    <ResponsiveLayout title="Approval Workflows">
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" color="text.primary" component="h1" gutterBottom>
            Approval Workflows
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Automated approval workflows for Assessment {assessmentId}
          </Typography>
        </Box>

        {error && (
          <Alert severity={!assessmentId ? "warning" : "error"} sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
            {!assessmentId && (
              <Box sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={() => router.push('/assessments')}
                  sx={{ mt: 1 }}
                >
                  Go to Assessments
                </Button>
              </Box>
            )}
          </Alert>
        )}

        {assessmentId && (
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={fetchData}
            sx={{ mb: 3 }}
          >
            Refresh
          </Button>
        )}

        {approvalsData && (
          <>
            <Grid container spacing={3} sx={{ mb: 4 }}>
              {/* Total Workflows */}
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <AccountTree color="primary" sx={{ mr: 1 }} />
                      <Typography variant="h6" color="text.primary">Total Workflows</Typography>
                    </Box>
                    <Typography variant="h3" color="primary">
                      {approvalsData.summary?.total_workflows || approvalsData.workflows?.length || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Pending */}
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Pending color="warning" sx={{ mr: 1 }} />
                      <Typography variant="h6" color="text.primary">Pending</Typography>
                    </Box>
                    <Typography variant="h3" color="warning.main">
                      {approvalsData.summary?.pending || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Approved */}
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <CheckCircle color="success" sx={{ mr: 1 }} />
                      <Typography variant="h6" color="text.primary">Approved</Typography>
                    </Box>
                    <Typography variant="h3" color="success.main">
                      {approvalsData.summary?.approved || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Rejected */}
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Cancel color="error" sx={{ mr: 1 }} />
                      <Typography variant="h6" color="text.primary">Rejected</Typography>
                    </Box>
                    <Typography variant="h3" color="error.main">
                      {approvalsData.summary?.rejected || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* Workflows List */}
            {approvalsData.workflows && Array.isArray(approvalsData.workflows) && approvalsData.workflows.length > 0 && (
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" color="text.primary" gutterBottom>
                  Active Workflows
                </Typography>
                <List>
                  {approvalsData.workflows.map((workflow: any, index: number) => (
                    <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start', mb: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                      <Box sx={{ width: '100%', mb: 1 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Typography variant="subtitle1" fontWeight="bold">
                            {workflow.name || workflow.workflow_name || `Workflow ${index + 1}`}
                          </Typography>
                          <Chip
                            label={workflow.status || 'pending'}
                            color={
                              workflow.status === 'approved' ? 'success' :
                              workflow.status === 'rejected' ? 'error' : 'warning'
                            }
                            size="small"
                          />
                        </Box>
                        <Grid container spacing={2} sx={{ mb: 2 }}>
                          <Grid item xs={6} sm={3}>
                            <Typography variant="caption" color="text.secondary">Stage</Typography>
                            <Typography variant="body2">{workflow.stage || 'N/A'}</Typography>
                          </Grid>
                          <Grid item xs={6} sm={3}>
                            <Typography variant="caption" color="text.secondary">Recommendations</Typography>
                            <Typography variant="body2">{workflow.recommendations_count || 0}</Typography>
                          </Grid>
                          <Grid item xs={6} sm={3}>
                            <Typography variant="caption" color="text.secondary">Pending</Typography>
                            <Typography variant="body2" color="warning.main">{workflow.pending_approvals || 0}</Typography>
                          </Grid>
                          <Grid item xs={6} sm={3}>
                            <Typography variant="caption" color="text.secondary">Approved/Rejected</Typography>
                            <Typography variant="body2">
                              <span style={{ color: 'green' }}>{workflow.approved || 0}</span> / <span style={{ color: 'red' }}>{workflow.rejected || 0}</span>
                            </Typography>
                          </Grid>
                        </Grid>
                        {workflow.created_at && (
                          <Typography variant="caption" color="text.secondary">
                            Created: {new Date(workflow.created_at).toLocaleString()}
                          </Typography>
                        )}

                        {/* Info: Individual approvals below */}
                        {workflow.status === 'pending' && (
                          <Box sx={{ mt: 2, p: 1.5, bgcolor: 'info.light', borderRadius: 1 }}>
                            <Typography variant="caption" color="info.dark">
                              ℹ️ Review and approve/reject individual recommendations below
                            </Typography>
                          </Box>
                        )}
                      </Box>
                      {workflow.approvers && Array.isArray(workflow.approvers) && workflow.approvers.length > 0 && (
                        <Box sx={{ width: '100%', mt: 1 }}>
                          <Typography variant="caption" color="text.secondary">
                            Approvers: {workflow.approvers.join(', ')}
                          </Typography>
                        </Box>
                      )}
                    </ListItem>
                  ))}
                </List>
              </Paper>
            )}

            {/* Recommendations for Review */}
            {recommendations.length > 0 && (
              <Paper sx={{ p: 3, mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" color="text.primary">
                    Recommendations for Review
                  </Typography>
                  <Chip label={`${recommendations.length} Total`} color="primary" />
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Review the infrastructure recommendations below before approving this workflow
                </Typography>

                {/* High Priority Recommendations First */}
                {recommendations.filter(r => r.recommendation_data?.priority === 'high' || r.recommendation_data?.priority === 'critical').length > 0 && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" color="error" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Warning /> High Priority Items ({recommendations.filter(r => r.recommendation_data?.priority === 'high' || r.recommendation_data?.priority === 'critical').length})
                    </Typography>
                    <Stack spacing={2} sx={{ mt: 1 }}>
                      {recommendations
                        .filter(r => r.recommendation_data?.priority === 'high' || r.recommendation_data?.priority === 'critical')
                        .slice(0, 5)
                        .map((rec, idx) => (
                          <Card key={idx} variant="outlined" sx={{ borderLeft: 3, borderLeftColor: 'error.main' }}>
                            <CardContent>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                                <Typography variant="subtitle1" fontWeight="bold">
                                  {rec.title}
                                </Typography>
                                <Chip
                                  label={rec.recommendation_data?.priority || 'medium'}
                                  color="error"
                                  size="small"
                                />
                              </Box>
                              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                {rec.summary || 'No description available'}
                              </Typography>
                              <Grid container spacing={2} sx={{ mt: 1 }}>
                                <Grid item xs={6} sm={3}>
                                  <Typography variant="caption" color="text.secondary">Agent</Typography>
                                  <Typography variant="body2">{rec.agent_name}</Typography>
                                </Grid>
                                <Grid item xs={6} sm={3}>
                                  <Typography variant="caption" color="text.secondary">Confidence</Typography>
                                  <Typography variant="body2">{(rec.confidence_score * 100).toFixed(0)}%</Typography>
                                </Grid>
                                <Grid item xs={6} sm={3}>
                                  <Typography variant="caption" color="text.secondary">Est. Cost</Typography>
                                  <Typography variant="body2">${(rec.recommendation_data?.estimated_cost || 0).toLocaleString()}</Typography>
                                </Grid>
                                <Grid item xs={6} sm={3}>
                                  <Typography variant="caption" color="text.secondary">Impact</Typography>
                                  <Typography variant="body2">{rec.recommendation_data?.impact || 'Medium'}</Typography>
                                </Grid>
                              </Grid>

                              {/* Individual Approval Actions */}
                              <Box sx={{ display: 'flex', gap: 1, mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                                {recommendationStatuses[rec.id] === 'approved' ? (
                                  <Chip label="✓ Approved" color="success" size="small" />
                                ) : recommendationStatuses[rec.id] === 'rejected' ? (
                                  <Chip label="✗ Rejected" color="error" size="small" />
                                ) : (
                                  <>
                                    <Button
                                      variant="contained"
                                      color="success"
                                      size="small"
                                      startIcon={<CheckCircle />}
                                      onClick={() => handleOpenApprovalDialog('approve', rec.id, rec.title)}
                                    >
                                      Approve
                                    </Button>
                                    <Button
                                      variant="outlined"
                                      color="error"
                                      size="small"
                                      startIcon={<Cancel />}
                                      onClick={() => handleOpenApprovalDialog('reject', rec.id, rec.title)}
                                    >
                                      Reject
                                    </Button>
                                  </>
                                )}
                              </Box>
                            </CardContent>
                          </Card>
                        ))}
                    </Stack>
                  </Box>
                )}

                {/* All Recommendations Table */}
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="subtitle2">
                      All Recommendations ({recommendations.filter(r => {
                        if (filterStatus === 'all') return true;
                        const status = recommendationStatuses[r.id] || 'pending';
                        return status === filterStatus;
                      }).length})
                    </Typography>
                    <Tabs value={filterStatus} onChange={(e, v) => setFilterStatus(v)} size="small">
                      <Tab label="All" value="all" />
                      <Tab label="Pending" value="pending" />
                      <Tab label="Approved" value="approved" />
                      <Tab label="Rejected" value="rejected" />
                    </Tabs>
                  </Box>
                  <Box sx={{ maxHeight: 400, overflow: 'auto', border: 1, borderColor: 'divider', borderRadius: 1 }}>
                    <List dense>
                      {recommendations
                        .filter(r => {
                          if (filterStatus === 'all') return true;
                          const status = recommendationStatuses[r.id] || 'pending';
                          return status === filterStatus;
                        })
                        .map((rec, idx) => (
                        <ListItem
                          key={idx}
                          sx={{
                            borderBottom: idx < recommendations.length - 1 ? 1 : 0,
                            borderColor: 'divider',
                            '&:hover': { bgcolor: 'action.hover' }
                          }}
                        >
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Typography variant="body2" fontWeight="medium">
                                  {rec.title}
                                </Typography>
                                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                                  {recommendationStatuses[rec.id] === 'approved' ? (
                                    <Chip label="✓ Approved" color="success" size="small" />
                                  ) : recommendationStatuses[rec.id] === 'rejected' ? (
                                    <Chip label="✗ Rejected" color="error" size="small" />
                                  ) : (
                                    <>
                                      <IconButton
                                        size="small"
                                        color="success"
                                        onClick={() => handleOpenApprovalDialog('approve', rec.id, rec.title)}
                                        title="Approve"
                                      >
                                        <CheckCircle fontSize="small" />
                                      </IconButton>
                                      <IconButton
                                        size="small"
                                        color="error"
                                        onClick={() => handleOpenApprovalDialog('reject', rec.id, rec.title)}
                                        title="Reject"
                                      >
                                        <Cancel fontSize="small" />
                                      </IconButton>
                                    </>
                                  )}
                                  <Chip
                                    label={rec.recommendation_data?.priority || 'medium'}
                                    size="small"
                                    color={
                                      rec.recommendation_data?.priority === 'critical' ? 'error' :
                                      rec.recommendation_data?.priority === 'high' ? 'warning' : 'default'
                                    }
                                  />
                                  <Typography variant="caption" color="text.secondary">
                                    {rec.agent_name}
                                  </Typography>
                                </Box>
                              </Box>
                            }
                            secondary={
                              <Typography variant="caption" color="text.secondary">
                                Cost: ${(rec.recommendation_data?.estimated_cost || 0).toLocaleString()} •
                                Confidence: {(rec.confidence_score * 100).toFixed(0)}%
                              </Typography>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                </Box>

                {/* Progress Summary */}
                <Box sx={{ mt: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                  <Typography variant="subtitle2" gutterBottom>Approval Progress</Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={4}>
                      <Typography variant="h6" color="success.main">
                        {Object.values(recommendationStatuses).filter(s => s === 'approved').length}
                      </Typography>
                      <Typography variant="caption">Approved</Typography>
                    </Grid>
                    <Grid item xs={4}>
                      <Typography variant="h6" color="error.main">
                        {Object.values(recommendationStatuses).filter(s => s === 'rejected').length}
                      </Typography>
                      <Typography variant="caption">Rejected</Typography>
                    </Grid>
                    <Grid item xs={4}>
                      <Typography variant="h6" color="warning.main">
                        {recommendations.length - Object.keys(recommendationStatuses).length}
                      </Typography>
                      <Typography variant="caption">Pending</Typography>
                    </Grid>
                  </Grid>
                </Box>
              </Paper>
            )}

            {loadingRecommendations && (
              <Paper sx={{ p: 3, mb: 3, textAlign: 'center' }}>
                <CircularProgress size={24} />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Loading recommendations...
                </Typography>
              </Paper>
            )}

            {/* Overall Progress */}
            {approvalsData.summary && (
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" color="text.primary" gutterBottom>
                  Overall Progress
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">Approval Progress</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {approvalsData.summary.approved} of {approvalsData.summary.total_workflows} workflows approved
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={approvalsData.summary.total_workflows > 0 ? (approvalsData.summary.approved / approvalsData.summary.total_workflows * 100) : 0}
                    color="success"
                    sx={{ height: 10, borderRadius: 1 }}
                  />
                </Box>
                <Grid container spacing={2} sx={{ mt: 2 }}>
                  <Grid item xs={4}>
                    <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'warning.main', borderRadius: 1 }}>
                      <Typography variant="h4" sx={{ color: '#fff', fontWeight: 'bold' }}>{approvalsData.summary.pending}</Typography>
                      <Typography variant="caption" sx={{ color: '#fff' }}>Pending Review</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={4}>
                    <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'success.main', borderRadius: 1 }}>
                      <Typography variant="h4" sx={{ color: '#fff', fontWeight: 'bold' }}>{approvalsData.summary.approved}</Typography>
                      <Typography variant="caption" sx={{ color: '#fff' }}>Approved</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={4}>
                    <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'error.main', borderRadius: 1 }}>
                      <Typography variant="h4" sx={{ color: '#fff', fontWeight: 'bold' }}>{approvalsData.summary.rejected}</Typography>
                      <Typography variant="caption" sx={{ color: '#fff' }}>Rejected</Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Paper>
            )}

            {/* Approval Process Steps */}
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" color="text.primary" gutterBottom>
                Approval Process Steps
              </Typography>
              <Stack spacing={2} sx={{ mt: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <Box sx={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    bgcolor: 'success.main',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontWeight: 'bold'
                  }}>
                    1
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="subtitle2" fontWeight="bold">Technical Review</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Infrastructure and security teams review technical feasibility and compliance requirements
                    </Typography>
                    <Chip label="Current Stage" size="small" color="warning" sx={{ mt: 1 }} />
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <Box sx={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    bgcolor: 'action.disabled',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontWeight: 'bold'
                  }}>
                    2
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="subtitle2" fontWeight="bold" color="text.secondary">
                      Budget Approval
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Finance team reviews cost estimates and budget allocation
                    </Typography>
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <Box sx={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    bgcolor: 'action.disabled',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontWeight: 'bold'
                  }}>
                    3
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="subtitle2" fontWeight="bold" color="text.secondary">
                      Executive Sign-off
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Final approval from senior leadership for implementation
                    </Typography>
                  </Box>
                </Box>
              </Stack>
            </Paper>

            {/* Recommendations Breakdown */}
            {approvalsData.workflows && approvalsData.workflows[0] && (
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" color="text.primary" gutterBottom>
                  Recommendations Breakdown
                </Typography>
                <Grid container spacing={2} sx={{ mt: 1 }}>
                  <Grid item xs={12} md={6}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                          Total Recommendations
                        </Typography>
                        <Typography variant="h4" color="primary">
                          {approvalsData.workflows[0].recommendations_count}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                          Infrastructure changes proposed by the assessment
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                          Pending Approvals
                        </Typography>
                        <Typography variant="h4" color="warning.main">
                          {approvalsData.workflows[0].pending_approvals}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                          High-priority items requiring immediate review
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </Paper>
            )}

            {/* Action Items */}
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" color="text.primary" gutterBottom>
                Next Steps
              </Typography>
              <Stack spacing={1.5} sx={{ mt: 2 }}>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                  <CheckCircle color="action" />
                  <Box>
                    <Typography variant="body2" fontWeight="bold">Review Technical Specifications</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Ensure all infrastructure changes meet security and compliance requirements
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                  <CheckCircle color="action" />
                  <Box>
                    <Typography variant="body2" fontWeight="bold">Validate Cost Estimates</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Confirm budget allocation matches projected infrastructure costs
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                  <CheckCircle color="action" />
                  <Box>
                    <Typography variant="body2" fontWeight="bold">Schedule Stakeholder Review</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Coordinate with team leads for approval timeline discussion
                    </Typography>
                  </Box>
                </Box>
              </Stack>
            </Paper>

            {/* Description */}
            {approvalsData.description && (
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" color="text.primary" gutterBottom>
                  About Approval Workflows
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {approvalsData.description}
                </Typography>
              </Paper>
            )}
          </>
        )}

        {!approvalsData && !error && (
          <Alert severity="info">
            No approval workflow data available for this assessment.
          </Alert>
        )}

        {/* Approval Dialog */}
        <Dialog open={approvalDialog.open} onClose={handleCloseApprovalDialog} maxWidth="sm" fullWidth>
          <DialogTitle>
            {approvalDialog.type === 'approve' ? 'Approve Recommendation' : 'Reject Recommendation'}
          </DialogTitle>
          <DialogContent>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {approvalDialog.type === 'approve'
                ? `You are approving: "${approvalDialog.recommendationTitle}"`
                : `You are rejecting: "${approvalDialog.recommendationTitle}"`
              }
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={4}
              label={approvalDialog.type === 'approve' ? 'Comment (optional)' : 'Rejection Reason'}
              value={approvalComment}
              onChange={(e) => setApprovalComment(e.target.value)}
              placeholder={
                approvalDialog.type === 'approve'
                  ? 'Add any comments about your approval...'
                  : 'Please provide a reason for rejection...'
              }
              sx={{ mt: 2 }}
            />
            <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
              <Typography variant="caption" color="info.dark">
                <strong>Approver:</strong> {currentUser?.email || 'Unknown'}
              </Typography>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseApprovalDialog} disabled={submitting}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmitApproval}
              variant="contained"
              color={approvalDialog.type === 'approve' ? 'success' : 'error'}
              disabled={submitting || (approvalDialog.type === 'reject' && !approvalComment.trim())}
              startIcon={submitting ? <CircularProgress size={20} /> : null}
            >
              {submitting ? 'Processing...' : (approvalDialog.type === 'approve' ? 'Approve' : 'Reject')}
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </ResponsiveLayout>
  );
}
