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
  Divider
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import AssessmentIcon from '@mui/icons-material/Assessment';
import BusinessIcon from '@mui/icons-material/Business';
import SecurityIcon from '@mui/icons-material/Security';
import CloudIcon from '@mui/icons-material/Cloud';
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

export default function AssessmentDetailPage() {
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
        
        <Typography variant="h4" gutterBottom>
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
              <Typography variant="h6" gutterBottom>
                Assessment Progress
              </Typography>
              <Box sx={{ mb: 2 }}>
                <LinearProgress
                  variant="determinate"
                  value={assessment.completion_percentage || 0}
                  sx={{ height: 8, borderRadius: 4 }}
                />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  {assessment.completion_percentage || 0}% Complete
                </Typography>
              </Box>
            </CardContent>
          </Card>

          {/* Business Requirements */}
          {assessment.business_requirements && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <BusinessIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Business Requirements
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                {assessment.business_requirements.objectives && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Objectives:
                    </Typography>
                    {assessment.business_requirements.objectives.map((obj: string, idx: number) => (
                      <Typography key={idx} variant="body2" sx={{ mb: 0.5 }}>
                        • {obj}
                      </Typography>
                    ))}
                  </Box>
                )}
                
                {assessment.business_requirements.budget_constraint && (
                  <Typography variant="body2">
                    <strong>Budget:</strong> ${assessment.business_requirements.budget_constraint.toLocaleString()}
                  </Typography>
                )}
              </CardContent>
            </Card>
          )}

          {/* Technical Requirements */}
          {assessment.technical_requirements && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <CloudIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Technical Requirements
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                {assessment.technical_requirements.performance_targets && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Performance Targets:
                    </Typography>
                    {Object.entries(assessment.technical_requirements.performance_targets).map(([key, value]) => (
                      <Typography key={key} variant="body2" sx={{ mb: 0.5 }}>
                        • {key.replace(/_/g, ' ')}: {String(value)}
                      </Typography>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          )}

          {/* Current Infrastructure */}
          {assessment.current_infrastructure && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
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
              <Typography variant="h6" gutterBottom>
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
              <Typography variant="h6" gutterBottom>
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