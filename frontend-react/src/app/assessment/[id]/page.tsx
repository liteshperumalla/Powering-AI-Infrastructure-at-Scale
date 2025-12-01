'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  LinearProgress,
  Alert,
  Skeleton,
  Stack,
  Paper,
  Divider,
  List,
  ListItem,
  ListItemText
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import AssessmentIcon from '@mui/icons-material/Assessment';
import BusinessIcon from '@mui/icons-material/Business';
import SecurityIcon from '@mui/icons-material/Security';
import CloudIcon from '@mui/icons-material/Cloud';
import ResponsiveLayout from '@/components/ResponsiveLayout';
import ProtectedRoute from '@/components/ProtectedRoute';
import { apiClient } from '../../../services/api';

interface AssessmentData {
  _id: string;
  title: string;
  description?: string;
  status: string;
  completion_percentage: number;
  progress_percentage: number;
  company_name?: string;
  industry?: string;
  budget_range?: string;
  workload_types?: string[];
  geographic_regions?: string[];
  compliance_requirements?: string[];
  business_requirements?: any;
  technical_requirements?: any;
  current_infrastructure?: any;
  scalability_requirements?: any;
  recommendations_generated: boolean;
  reports_generated: boolean;
  created_at: string;
  updated_at: string;
}

function AssessmentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [assessment, setAssessment] = useState<AssessmentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const assessmentId = params.id as string;

  useEffect(() => {
    const fetchAssessment = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log('🔍 Fetching assessment:', assessmentId);
        const data = await apiClient.getAssessment(assessmentId);
        console.log('📊 Assessment data:', data);
        
        setAssessment(data);
      } catch (err: any) {
        console.error('❌ Error fetching assessment:', err);
        setError(err.message || 'Failed to load assessment');
      } finally {
        setLoading(false);
      }
    };

    if (assessmentId) {
      fetchAssessment();
    }
  }, [assessmentId]);

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed': return 'success';
      case 'in_progress': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const handleViewReports = () => {
    router.push(`/reports?assessment_id=${assessmentId}`);
  };

  const handleViewRecommendations = () => {
    router.push(`/recommendations?assessment_id=${assessmentId}`);
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Stack spacing={3}>
          <Skeleton variant="rectangular" height={60} />
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Skeleton variant="rectangular" height={400} />
            </Grid>
            <Grid item xs={12} md={4}>
              <Skeleton variant="rectangular" height={300} />
            </Grid>
          </Grid>
        </Stack>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => router.push('/dashboard')}
        >
          Back to Dashboard
        </Button>
      </Container>
    );
  }

  if (!assessment) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="warning" sx={{ mb: 3 }}>
          Assessment not found
        </Alert>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => router.push('/dashboard')}
        >
          Back to Dashboard
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => router.push('/dashboard')}
          sx={{ mb: 2 }}
        >
          Back to Dashboard
        </Button>
        
        <Typography variant="h4" color="text.primary" gutterBottom>
          {assessment.title}
        </Typography>
        
        <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
          <Chip
            label={assessment.status}
            color={getStatusColor(assessment.status) as any}
            size="small"
          />
          <Chip
            icon={<BusinessIcon />}
            label={assessment.company_name || 'Unknown Company'}
            variant="outlined"
            size="small"
          />
          {assessment.industry && (
            <Chip
              label={assessment.industry}
              variant="outlined"
              size="small"
            />
          )}
        </Stack>

        {assessment.description && (
          <Typography variant="body1" color="text.secondary" gutterBottom>
            {assessment.description}
          </Typography>
        )}
      </Box>

      <Grid container spacing={3}>
        {/* Main Content */}
        <Grid item xs={12} md={8}>
          {/* Progress Section */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" color="text.primary" gutterBottom>
                Assessment Progress
              </Typography>
              <Box sx={{ mb: 2 }}>
                <LinearProgress
                  variant="determinate"
                  value={assessment.progress_percentage || assessment.completion_percentage || 0}
                  sx={{ height: 8, borderRadius: 4 }}
                />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  {assessment.progress_percentage || assessment.completion_percentage || 0}% Complete
                </Typography>
              </Box>
            </CardContent>
          </Card>

          {/* Business Requirements */}
          {assessment.business_requirements && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" color="text.primary" gutterBottom>
                  <BusinessIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Business Requirements
                </Typography>
                <Divider sx={{ mb: 2 }} />

                <Grid container spacing={2}>
                  {/* Company Info */}
                  {assessment.business_requirements.company_name && (
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Company:
                      </Typography>
                      <Typography variant="body1">
                        {assessment.business_requirements.company_name}
                      </Typography>
                    </Grid>
                  )}

                  {assessment.business_requirements.industry && (
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Industry:
                      </Typography>
                      <Typography variant="body1">
                        {assessment.business_requirements.industry}
                      </Typography>
                    </Grid>
                  )}

                  {assessment.business_requirements.company_size && (
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Company Size:
                      </Typography>
                      <Typography variant="body1">
                        {assessment.business_requirements.company_size}
                      </Typography>
                    </Grid>
                  )}

                  {/* Budget */}
                  {assessment.business_requirements.budget_constraints && (
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Budget Range:
                      </Typography>
                      <Typography variant="body1">
                        {assessment.business_requirements.budget_constraints.total_budget_range || 'Not specified'}
                      </Typography>
                      {assessment.business_requirements.budget_constraints.monthly_budget_limit && (
                        <Typography variant="body2" color="text.secondary">
                          Monthly Limit: ${Number(assessment.business_requirements.budget_constraints.monthly_budget_limit).toLocaleString()}
                        </Typography>
                      )}
                    </Grid>
                  )}
                </Grid>

                {/* Business Goals */}
                {assessment.business_requirements.business_goals && assessment.business_requirements.business_goals.length > 0 && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Business Goals:
                    </Typography>
                    <List dense>
                      {assessment.business_requirements.business_goals.map((goal: any, idx: number) => (
                        <ListItem key={idx}>
                          <ListItemText
                            primary={goal.goal || goal}
                            secondary={
                              goal.priority && goal.timeline_months
                                ? `Priority: ${goal.priority} | Timeline: ${goal.timeline_months} months`
                                : null
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}

                {/* Pain Points */}
                {assessment.business_requirements.current_pain_points && assessment.business_requirements.current_pain_points.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Current Pain Points:
                    </Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                      {assessment.business_requirements.current_pain_points.map((pain: string, idx: number) => (
                        <Chip key={idx} label={pain} size="small" variant="outlined" color="warning" />
                      ))}
                    </Stack>
                  </Box>
                )}

                {/* Success Criteria */}
                {assessment.business_requirements.success_criteria && assessment.business_requirements.success_criteria.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Success Criteria:
                    </Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                      {assessment.business_requirements.success_criteria.map((criteria: string, idx: number) => (
                        <Chip key={idx} label={criteria} size="small" variant="outlined" color="success" />
                      ))}
                    </Stack>
                  </Box>
                )}
              </CardContent>
            </Card>
          )}

          {/* Technical Requirements */}
          {assessment.technical_requirements && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" color="text.primary" gutterBottom>
                  <CloudIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Technical Requirements
                </Typography>
                <Divider sx={{ mb: 2 }} />

                {!Object.keys(assessment.technical_requirements).some(key => {
                  const value = assessment.technical_requirements[key];
                  return value !== null && value !== undefined &&
                         (Array.isArray(value) ? value.length > 0 : value !== '');
                }) ? (
                  <Alert severity="info">
                    No technical requirements have been specified for this assessment yet.
                    Technical requirements can include architecture details, cloud providers,
                    programming languages, databases, and infrastructure specifications.
                  </Alert>
                ) : (
                  <Box>
                    <Grid container spacing={3}>
                      {/* Current Infrastructure */}
                      {assessment.technical_requirements.current_infrastructure && (
                        <Grid item xs={12}>
                          <Typography variant="subtitle2" color="primary" gutterBottom>
                            Current Infrastructure
                          </Typography>
                          {typeof assessment.technical_requirements.current_infrastructure === 'object' ? (
                            <Grid container spacing={2}>
                              {Object.entries(assessment.technical_requirements.current_infrastructure).map(([key, value]: [string, any]) => (
                                <Grid item xs={12} sm={6} key={key}>
                                  <Typography variant="caption" color="text.secondary">
                                    {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                                  </Typography>
                                  <Typography variant="body2">
                                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                  </Typography>
                                </Grid>
                              ))}
                            </Grid>
                          ) : (
                            <Typography variant="body2">{String(assessment.technical_requirements.current_infrastructure)}</Typography>
                          )}
                        </Grid>
                      )}

                      {/* Performance Requirements */}
                      {assessment.technical_requirements.performance_requirements && (
                        <Grid item xs={12}>
                          <Typography variant="subtitle2" color="primary" gutterBottom>
                            Performance Requirements
                          </Typography>
                          <Grid container spacing={2}>
                            {Object.entries(assessment.technical_requirements.performance_requirements).map(([key, value]: [string, any]) => (
                              <Grid item xs={12} sm={4} key={key}>
                                <Typography variant="caption" color="text.secondary">
                                  {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                                </Typography>
                                <Typography variant="body2" fontWeight="medium">
                                  {String(value)}
                                </Typography>
                              </Grid>
                            ))}
                          </Grid>
                        </Grid>
                      )}

                      {/* ML Requirements */}
                      {assessment.technical_requirements.ml_requirements && (
                        <Grid item xs={12}>
                          <Typography variant="subtitle2" color="primary" gutterBottom>
                            ML/AI Requirements
                          </Typography>
                          <Grid container spacing={2}>
                            {Object.entries(assessment.technical_requirements.ml_requirements).map(([key, value]: [string, any]) => (
                              <Grid item xs={12} sm={6} key={key}>
                                <Typography variant="caption" color="text.secondary">
                                  {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                                </Typography>
                                <Typography variant="body2">
                                  {Array.isArray(value) ? value.join(', ') : String(value)}
                                </Typography>
                              </Grid>
                            ))}
                          </Grid>
                        </Grid>
                      )}

                      {/* Data Requirements */}
                      {assessment.technical_requirements.data_requirements && (
                        <Grid item xs={12}>
                          <Typography variant="subtitle2" color="primary" gutterBottom>
                            Data Requirements
                          </Typography>
                          <Grid container spacing={2}>
                            {Object.entries(assessment.technical_requirements.data_requirements).map(([key, value]: [string, any]) => (
                              <Grid item xs={12} sm={4} key={key}>
                                <Typography variant="caption" color="text.secondary">
                                  {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                                </Typography>
                                <Typography variant="body2">
                                  {String(value)}
                                </Typography>
                              </Grid>
                            ))}
                          </Grid>
                        </Grid>
                      )}

                      {/* Security Requirements */}
                      {assessment.technical_requirements.security_requirements && (
                        <Grid item xs={12}>
                          <Typography variant="subtitle2" color="primary" gutterBottom>
                            Security Requirements
                          </Typography>
                          <Grid container spacing={1}>
                            {Object.entries(assessment.technical_requirements.security_requirements).map(([key, value]: [string, any]) => (
                              value === true && (
                                <Grid item xs={12} sm={6} md={4} key={key}>
                                  <Chip
                                    label={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                    size="small"
                                    color="success"
                                    variant="outlined"
                                  />
                                </Grid>
                              )
                            ))}
                          </Grid>
                        </Grid>
                      )}

                      {/* Workload Types */}
                      {assessment.technical_requirements.workload_types && assessment.technical_requirements.workload_types.length > 0 && (
                        <Grid item xs={12}>
                          <Typography variant="subtitle2" color="primary" gutterBottom>
                            Workload Types
                          </Typography>
                          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                            {assessment.technical_requirements.workload_types.map((type: string, idx: number) => (
                              <Chip key={idx} label={type.replace(/_/g, ' ')} size="small" color="primary" />
                            ))}
                          </Stack>
                        </Grid>
                      )}

                      {/* Programming Languages */}
                      {assessment.technical_requirements.preferred_programming_languages && assessment.technical_requirements.preferred_programming_languages.length > 0 && (
                        <Grid item xs={12}>
                          <Typography variant="subtitle2" color="primary" gutterBottom>
                            Programming Languages
                          </Typography>
                          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                            {assessment.technical_requirements.preferred_programming_languages.map((lang: string, idx: number) => (
                              <Chip key={idx} label={lang} size="small" variant="outlined" />
                            ))}
                          </Stack>
                        </Grid>
                      )}
                    </Grid>
                  </Box>
                )}
              </CardContent>
            </Card>
          )}

          {/* Current Infrastructure */}
          {assessment.current_infrastructure && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" color="text.primary" gutterBottom>
                  <SecurityIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Current Infrastructure
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                {assessment.current_infrastructure.cloud_providers && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Cloud Providers:
                    </Typography>
                    <Stack direction="row" spacing={1}>
                      {assessment.current_infrastructure.cloud_providers.map((provider: string) => (
                        <Chip key={provider} label={provider.toUpperCase()} size="small" />
                      ))}
                    </Stack>
                  </Box>
                )}
                
                {assessment.current_infrastructure.current_monthly_spend && (
                  <Typography variant="body2">
                    <strong>Current Monthly Spend:</strong> ${assessment.current_infrastructure.current_monthly_spend.toLocaleString()}
                  </Typography>
                )}
              </CardContent>
            </Card>
          )}
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          {/* Quick Actions */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" color="text.primary" gutterBottom>
                Quick Actions
              </Typography>
              <Stack spacing={2}>
                <Button
                  variant="contained"
                  startIcon={<AssessmentIcon />}
                  onClick={handleViewReports}
                  disabled={!assessment.reports_generated}
                  fullWidth
                >
                  View Reports
                </Button>
                <Button
                  variant="outlined"
                  onClick={handleViewRecommendations}
                  disabled={!assessment.recommendations_generated}
                  fullWidth
                >
                  View Recommendations
                </Button>
              </Stack>
            </CardContent>
          </Card>

          {/* Assessment Details */}
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.primary" gutterBottom>
                Assessment Details
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Created: {new Date(assessment.created_at).toLocaleDateString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Updated: {new Date(assessment.updated_at).toLocaleDateString()}
                </Typography>
              </Box>

              {assessment.budget_range && (
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Budget Range:</strong> {assessment.budget_range}
                </Typography>
              )}

              {assessment.workload_types && assessment.workload_types.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Workload Types:</strong>
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    {assessment.workload_types.map((type: string) => (
                      <Chip key={type} label={type.replace(/_/g, ' ')} size="small" />
                    ))}
                  </Stack>
                </Box>
              )}

              {assessment.compliance_requirements && assessment.compliance_requirements.length > 0 && (
                <Box>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Compliance:</strong>
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    {assessment.compliance_requirements.map((req: string) => (
                      <Chip key={req} label={req.toUpperCase()} size="small" color="secondary" />
                    ))}
                  </Stack>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
}

// Wrap with layout and protection
export default function AssessmentDetailPageWrapper() {
  return (
    <ProtectedRoute>
      <ResponsiveLayout title="Assessment Details">
        <AssessmentDetailPage />
      </ResponsiveLayout>
    </ProtectedRoute>
  );
}