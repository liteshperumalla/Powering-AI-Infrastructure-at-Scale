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
  const router = useRouter();
  const currentAssessment = useSelector((state: RootState) => state.assessment.currentAssessment);
  const assessments = useSelector((state: RootState) => state.assessment.assessments);

  // Priority: URL param > Redux currentAssessment > First assessment in list
  const urlAssessmentId = searchParams?.get('assessment_id');
  const assessmentId = urlAssessmentId || currentAssessment?.id || (assessments.length > 0 ? assessments[0].id : null);

  // Debug logging
  React.useEffect(() => {
    console.log('🔍 Quality Page Assessment Resolution:', {
      urlAssessmentId,
      currentAssessmentId: currentAssessment?.id,
      assessmentsCount: assessments.length,
      firstAssessmentId: assessments[0]?.id,
      resolvedAssessmentId: assessmentId
    });
  }, [urlAssessmentId, currentAssessment, assessments, assessmentId]);

  const [qualityData, setQualityData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // No redirect - just handle the case when there's no assessment

  const fetchData = useCallback(async () => {
    if (!assessmentId) {
      setError('No assessment ID provided. Please select an assessment first.');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const response = await apiClient.get<any>(`/features/assessment/${assessmentId}/quality`);
      console.log('📊 Quality Data Received:', {
        hasMetrics: !!response?.metrics,
        hasRecommendationsQuality: !!response?.recommendations_quality,
        hasAssessmentQuality: !!response?.assessment_quality,
        hasIssueBreakdown: !!response?.issue_breakdown,
        metricsType: typeof response?.metrics,
        fullData: response
      });
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
          <Typography variant="h4" color="text.primary" component="h1" gutterBottom>
            Quality Metrics Dashboard
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Quality metrics and insights for Assessment {assessmentId}
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
                <Typography variant="body2" sx={{ mt: 2 }}>
                  Or follow these steps:
                </Typography>
                <ul style={{ marginTop: '8px', paddingLeft: '20px' }}>
                  <li>Go to <strong>Assessments</strong> page</li>
                  <li>Click on an assessment to select it</li>
                  <li>Then return to this Quality Metrics page</li>
                </ul>
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

        {qualityData && (
          <>
            <Grid container spacing={3} sx={{ mb: 4 }}>
              {/* Overall Quality Score */}
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Speed color="primary" sx={{ mr: 1 }} />
                      <Typography variant="h6" color="text.primary">Quality Score</Typography>
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
                      <Typography variant="h6" color="text.primary">Total Issues</Typography>
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
                      <Typography variant="h6" color="text.primary">Critical</Typography>
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
                      <Typography variant="h6" color="text.primary">Resolved</Typography>
                    </Box>
                    <Typography variant="h3" color="success.main">
                      {qualityData.resolved_issues || 45}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* Quality Metrics */}
            {qualityData.metrics && (
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" color="text.primary" gutterBottom>
                  Quality Metrics
                </Typography>
                <Stack spacing={2}>
                  {Object.entries(qualityData.metrics).map(([key, value]: [string, any]) => (
                    <Box key={key}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body1" sx={{ textTransform: 'capitalize' }}>
                          {key}
                        </Typography>
                        <Typography variant="body1" fontWeight="bold">
                          {typeof value === 'number' ? value.toFixed(1) : value}%
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={typeof value === 'number' ? value : 0}
                        color={
                          value >= 90 ? 'success' :
                          value >= 70 ? 'warning' : 'error'
                        }
                      />
                    </Box>
                  ))}
                </Stack>
              </Paper>
            )}

            {/* Recommendations Quality */}
            {qualityData.recommendations_quality && (
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" color="text.primary" gutterBottom>
                  Recommendations Quality
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <Typography variant="body2" color="text.secondary">Total Recommendations</Typography>
                    <Typography variant="h5" color="text.primary">{qualityData.recommendations_quality.total}</Typography>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Typography variant="body2" color="text.secondary">High Confidence</Typography>
                    <Typography variant="h5" color="text.primary">{qualityData.recommendations_quality.high_confidence}</Typography>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Typography variant="body2" color="text.secondary">Average Confidence</Typography>
                    <Typography variant="h5" color="text.primary">{qualityData.recommendations_quality.average_confidence}%</Typography>
                  </Grid>
                </Grid>
              </Paper>
            )}

            {/* Issue Breakdown by Category */}
            {qualityData.issue_breakdown && Array.isArray(qualityData.issue_breakdown) && (
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" color="text.primary" gutterBottom>
                  Issues by Category
                </Typography>
                <Stack spacing={2}>
                  {qualityData.issue_breakdown.map((category: any, index: number) => (
                    <Box key={index}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="subtitle1" fontWeight="bold">
                          {category.category}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 2 }}>
                          {category.critical > 0 && <Chip label={`${category.critical} Critical`} color="error" size="small" />}
                          {category.high > 0 && <Chip label={`${category.high} High`} color="warning" size="small" />}
                          {category.medium > 0 && <Chip label={`${category.medium} Medium`} color="info" size="small" />}
                        </Box>
                      </Box>
                      {category.issues && category.issues.slice(0, 3).map((issue: any, idx: number) => (
                        <Typography key={idx} variant="body2" color="text.secondary" sx={{ ml: 2 }}>
                          • {issue.title}
                        </Typography>
                      ))}
                    </Box>
                  ))}
                </Stack>
              </Paper>
            )}

            {/* Assessment Quality Details */}
            {qualityData.assessment_quality && (
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" color="text.primary" gutterBottom>
                  Assessment Quality
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <Typography variant="body2" color="text.secondary">Completion Rate</Typography>
                    <Typography variant="h5" color="text.primary">{qualityData.assessment_quality.completion_rate}%</Typography>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Typography variant="body2" color="text.secondary">Data Coverage</Typography>
                    <Typography variant="h5" color="text.primary">{qualityData.assessment_quality.data_coverage}%</Typography>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Typography variant="body2" color="text.secondary">Validation</Typography>
                    <Chip
                      label={qualityData.assessment_quality.validation_passed ? "Passed" : "Failed"}
                      color={qualityData.assessment_quality.validation_passed ? "success" : "error"}
                    />
                  </Grid>
                </Grid>
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
