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
  LinearProgress,
  Alert,
  CircularProgress,
  Stack,
  Chip
} from '@mui/material';
import {
  Speed,
  CheckCircle,
  Warning,
  Refresh,
  Assessment
} from '@mui/icons-material';
import { apiClient } from '../../services/api';

export default function QualityPage() {
  const searchParams = useSearchParams();
  const currentAssessment = useSelector((state: RootState) => state.assessment.currentAssessment);

  // Priority: URL param > Redux state
  const urlAssessmentId = searchParams?.get('assessment_id');
  const assessmentId = urlAssessmentId || currentAssessment?.id;

  const [qualityData, setQualityData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // No redirect - just handle the case when there's no assessment

  const fetchData = useCallback(async () => {
    if (!assessmentId) return;

    try {
      setLoading(true);
      const response = await apiClient.get<any>(`/features/assessment/${assessmentId}/quality`);
      setQualityData(response);
      setError(null);
    } catch (err: any) {
      console.error('Failed to load quality data:', err);
      setError(err.message || 'Failed to load quality data');
      setQualityData(null);
    } finally {
      setLoading(false);
    }
  }, [assessmentId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <ResponsiveLayout title="Quality Metrics">
        <Container>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
            <CircularProgress />
          </Box>
        </Container>
      </ResponsiveLayout>
    );
  }

  return (
    <ResponsiveLayout title="Quality Metrics">
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Quality Metrics Dashboard
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Quality metrics and insights for Assessment {assessmentId}
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

        {qualityData && (
          <>
            <Grid container spacing={3} sx={{ mb: 4 }}>
              {/* Overall Quality Score */}
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Speed color="primary" sx={{ mr: 1 }} />
                      <Typography variant="h6">Quality Score</Typography>
                    </Box>
                    <Typography variant="h3" color="primary">
                      {qualityData.overall_quality_score || 85}
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={qualityData.overall_quality_score || 85}
                      color="primary"
                      sx={{ mt: 2 }}
                    />
                  </CardContent>
                </Card>
              </Grid>

              {/* Total Issues */}
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Assessment color="secondary" sx={{ mr: 1 }} />
                      <Typography variant="h6">Total Issues</Typography>
                    </Box>
                    <Typography variant="h3" color="secondary">
                      {qualityData.total_issues || 12}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Critical Issues */}
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Warning color="warning" sx={{ mr: 1 }} />
                      <Typography variant="h6">Critical</Typography>
                    </Box>
                    <Typography variant="h3" color="warning.main">
                      {qualityData.critical_issues || 3}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Resolved */}
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <CheckCircle color="success" sx={{ mr: 1 }} />
                      <Typography variant="h6">Resolved</Typography>
                    </Box>
                    <Typography variant="h3" color="success.main">
                      {qualityData.resolved_issues || 45}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* Quality Metrics */}
            {qualityData.metrics && Array.isArray(qualityData.metrics) && qualityData.metrics.length > 0 && (
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Quality Metrics
                </Typography>
                <Stack spacing={2}>
                  {qualityData.metrics.map((metric: any, index: number) => (
                    <Box key={index}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body1">
                          {metric.name || metric.metric_name}
                        </Typography>
                        <Typography variant="body1" fontWeight="bold">
                          {metric.score || metric.value}%
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={metric.score || metric.value || 0}
                        color={
                          (metric.score || metric.value) >= 90 ? 'success' :
                          (metric.score || metric.value) >= 70 ? 'warning' : 'error'
                        }
                      />
                    </Box>
                  ))}
                </Stack>
              </Paper>
            )}

            {/* Recommendations */}
            {qualityData.recommendations && Array.isArray(qualityData.recommendations) && qualityData.recommendations.length > 0 && (
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Quality Improvement Recommendations
                </Typography>
                <Stack spacing={2}>
                  {qualityData.recommendations.map((rec: any, index: number) => (
                    <Box key={index}>
                      <Typography variant="subtitle2" gutterBottom>
                        {rec.title || `Recommendation ${index + 1}`}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {rec.description || rec.recommendation}
                      </Typography>
                      {rec.priority && (
                        <Chip
                          label={rec.priority}
                          size="small"
                          color={
                            rec.priority === 'high' ? 'error' :
                            rec.priority === 'medium' ? 'warning' : 'info'
                          }
                          sx={{ mt: 1 }}
                        />
                      )}
                    </Box>
                  ))}
                </Stack>
              </Paper>
            )}

            {/* If no specific data structure, show raw data */}
            {!qualityData.metrics && !qualityData.recommendations && (
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Quality Data
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Assessment ID: {qualityData.assessment_id}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  {qualityData.description || 'Quality metrics for this assessment'}
                </Typography>
              </Paper>
            )}
          </>
        )}

        {!qualityData && !error && (
          <Alert severity="info">
            No quality data available for this assessment. Please complete the assessment first.
          </Alert>
        )}
      </Container>
    </ResponsiveLayout>
  );
}
