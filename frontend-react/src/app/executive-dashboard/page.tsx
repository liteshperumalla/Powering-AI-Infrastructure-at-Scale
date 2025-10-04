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
  Divider
} from '@mui/material';
import {
  TrendingUp,
  AttachMoney,
  CheckCircle,
  Refresh,
  Assessment,
  Speed
} from '@mui/icons-material';
import { apiClient } from '../../services/api';

export default function ExecutiveDashboardPage() {
  const searchParams = useSearchParams();
  const currentAssessment = useSelector((state: RootState) => state.assessment.currentAssessment);

  // Priority: URL param > Redux state
  const urlAssessmentId = searchParams?.get('assessment_id');
  const assessmentId = urlAssessmentId || currentAssessment?.id;

  const [executiveData, setExecutiveData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // No redirect - just handle the case when there's no assessment

  const fetchData = useCallback(async () => {
    if (!assessmentId) return;

    try {
      setLoading(true);
      const response = await apiClient.get<any>(`/features/assessment/${assessmentId}/executive`);
      setExecutiveData(response);
      setError(null);
    } catch (err: any) {
      console.error('Failed to load executive dashboard:', err);
      setError(err.message || 'Failed to load executive dashboard');
      setExecutiveData(null);
    } finally {
      setLoading(false);
    }
  }, [assessmentId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <ResponsiveLayout title="Executive Dashboard">
        <Container>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
            <CircularProgress />
          </Box>
        </Container>
      </ResponsiveLayout>
    );
  }

  return (
    <ResponsiveLayout title="Executive Dashboard">
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Executive Dashboard
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            High-level insights and metrics for Assessment {assessmentId}
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

        {executiveData && (
          <>
            {/* Key Metrics */}
            {executiveData.key_metrics && (
              <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} md={3}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Assessment color="primary" sx={{ mr: 1 }} />
                        <Typography variant="h6">Total Recommendations</Typography>
                      </Box>
                      <Typography variant="h3" color="primary">
                        {executiveData.key_metrics.total_recommendations || 0}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={3}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <AttachMoney color="success" sx={{ mr: 1 }} />
                        <Typography variant="h6">Potential Savings</Typography>
                      </Box>
                      <Typography variant="h3" color="success.main">
                        ${(executiveData.key_metrics.total_cost_savings || 0).toLocaleString()}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={3}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Speed color="secondary" sx={{ mr: 1 }} />
                        <Typography variant="h6">Avg Confidence</Typography>
                      </Box>
                      <Typography variant="h3" color="secondary.main">
                        {executiveData.key_metrics.avg_confidence_score
                          ? `${Math.round(executiveData.key_metrics.avg_confidence_score * 100)}%`
                          : 'N/A'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={3}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <TrendingUp color="info" sx={{ mr: 1 }} />
                        <Typography variant="h6">Timeline</Typography>
                      </Box>
                      <Typography variant="h3" color="info.main">
                        {executiveData.key_metrics.implementation_timeline || 'N/A'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            )}

            {/* Insights */}
            {executiveData.insights && Array.isArray(executiveData.insights) && executiveData.insights.length > 0 && (
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Key Insights
                </Typography>
                <Stack spacing={2}>
                  {executiveData.insights.map((insight: any, index: number) => (
                    <Alert key={index} severity="info" icon={<TrendingUp />}>
                      {typeof insight === 'string' ? insight : insight.description || insight.insight}
                    </Alert>
                  ))}
                </Stack>
              </Paper>
            )}

            {/* Strategic Initiatives */}
            {executiveData.strategic_initiatives && Array.isArray(executiveData.strategic_initiatives) && executiveData.strategic_initiatives.length > 0 && (
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Strategic Initiatives
                </Typography>
                <Grid container spacing={2}>
                  {executiveData.strategic_initiatives.map((initiative: any, index: number) => (
                    <Grid item xs={12} md={6} key={index}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                            {initiative.name || initiative.title}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" paragraph>
                            {initiative.description}
                          </Typography>
                          {initiative.priority && (
                            <Chip
                              label={`Priority: ${initiative.priority}`}
                              size="small"
                              color={
                                initiative.priority === 'high' ? 'error' :
                                initiative.priority === 'medium' ? 'warning' : 'default'
                              }
                            />
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Paper>
            )}

            {/* Risks */}
            {executiveData.risks && Array.isArray(executiveData.risks) && executiveData.risks.length > 0 && (
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Risk Factors
                </Typography>
                <Stack spacing={2}>
                  {executiveData.risks.map((risk: any, index: number) => (
                    <Box key={index} sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="subtitle2">
                          {risk.name || risk.title || `Risk ${index + 1}`}
                        </Typography>
                        <Chip
                          label={risk.severity || risk.level || 'Medium'}
                          size="small"
                          color={
                            (risk.severity || risk.level) === 'high' ? 'error' :
                            (risk.severity || risk.level) === 'low' ? 'success' : 'warning'
                          }
                        />
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        {risk.description || risk.details}
                      </Typography>
                    </Box>
                  ))}
                </Stack>
              </Paper>
            )}

            {/* Summary */}
            {executiveData.summary && (
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Executive Summary
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {typeof executiveData.summary === 'string'
                    ? executiveData.summary
                    : executiveData.summary.description || JSON.stringify(executiveData.summary)}
                </Typography>
              </Paper>
            )}

            {/* Fallback */}
            {!executiveData.key_metrics && !executiveData.insights && !executiveData.summary && (
              <Paper sx={{ p: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Assessment ID: {executiveData.assessment_id}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Executive-level insights and strategic recommendations
                </Typography>
              </Paper>
            )}
          </>
        )}

        {!executiveData && !error && (
          <Alert severity="info">
            No executive dashboard data available for this assessment.
          </Alert>
        )}
      </Container>
    </ResponsiveLayout>
  );
}
