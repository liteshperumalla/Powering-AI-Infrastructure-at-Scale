'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
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
  LinearProgress
} from '@mui/material';
import {
  CheckCircle,
  Pending,
  Cancel,
  Refresh,
  AccountTree
} from '@mui/icons-material';
import { apiClient } from '../../services/api';

export default function ApprovalsPage() {
  const searchParams = useSearchParams();
  const currentAssessment = useSelector((state: RootState) => state.assessment.currentAssessment);

  // Priority: URL param > Redux state
  const urlAssessmentId = searchParams?.get('assessment_id');
  const assessmentId = urlAssessmentId || currentAssessment?.id;

  const [approvalsData, setApprovalsData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // No redirect - just handle the case when there's no assessment

  const fetchData = useCallback(async () => {
    if (!assessmentId) return;

    try {
      setLoading(true);
      const response = await apiClient.get<any>(`/features/assessment/${assessmentId}/approvals`);
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
          <Typography variant="h4" component="h1" gutterBottom>
            Approval Workflows
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Automated approval workflows for Assessment {assessmentId}
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={fetchData}
          sx={{ mb: 3 }}
        >
          Refresh
        </Button>

        {approvalsData && (
          <>
            <Grid container spacing={3} sx={{ mb: 4 }}>
              {/* Total Workflows */}
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <AccountTree color="primary" sx={{ mr: 1 }} />
                      <Typography variant="h6">Total Workflows</Typography>
                    </Box>
                    <Typography variant="h3" color="primary">
                      {approvalsData.total_workflows || approvalsData.workflows?.length || 0}
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
                      <Typography variant="h6">Pending</Typography>
                    </Box>
                    <Typography variant="h3" color="warning.main">
                      {approvalsData.pending_count || 2}
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
                      <Typography variant="h6">Approved</Typography>
                    </Box>
                    <Typography variant="h3" color="success.main">
                      {approvalsData.approved_count || 5}
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
                      <Typography variant="h6">Rejected</Typography>
                    </Box>
                    <Typography variant="h3" color="error.main">
                      {approvalsData.rejected_count || 1}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* Workflows List */}
            {approvalsData.workflows && Array.isArray(approvalsData.workflows) && approvalsData.workflows.length > 0 && (
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
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
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          {workflow.description || 'Approval workflow for infrastructure changes'}
                        </Typography>
                        {workflow.progress !== undefined && (
                          <Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                              <Typography variant="caption">Progress</Typography>
                              <Typography variant="caption">{workflow.progress}%</Typography>
                            </Box>
                            <LinearProgress variant="determinate" value={workflow.progress} />
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

            {/* Description */}
            {approvalsData.description && (
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  About Approval Workflows
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {approvalsData.description}
                </Typography>
              </Paper>
            )}

            {/* If no specific data structure */}
            {!approvalsData.workflows && !approvalsData.description && (
              <Paper sx={{ p: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Assessment ID: {approvalsData.assessment_id}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Automated approval workflows for infrastructure changes
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
      </Container>
    </ResponsiveLayout>
  );
}
