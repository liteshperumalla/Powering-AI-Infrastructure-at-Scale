'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  Alert,
  Skeleton,
  Stack,
  Paper,
  Divider,
  Rating,
  LinearProgress,
  IconButton,
  Tooltip
} from '@mui/material';
import ResponsiveLayout from '@/components/ResponsiveLayout';
import ProtectedRoute from '@/components/ProtectedRoute';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import RecommendIcon from '@mui/icons-material/Recommend';
import CloudIcon from '@mui/icons-material/Cloud';
import SecurityIcon from '@mui/icons-material/Security';
import MonetizationOnIcon from '@mui/icons-material/MonetizationOn';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import InfoIcon from '@mui/icons-material/Info';
import { apiClient } from '../../services/api';

interface Recommendation {
  _id: string;
  agent_name: string;
  agent_type: string;
  category: string;
  title: string;
  description: string;
  confidence_score: number;
  priority: string;
  implementation_effort: string;
  estimated_cost_savings: number;
  estimated_implementation_time: string;
  benefits: string[];
  implementation_steps: string[];
  dependencies: string[];
  risks: string[];
  cloud_provider: string;
  service_recommendations: any[];
  technical_details: any;
  business_impact: any;
  created_at: string;
  updated_at: string;
}

interface AssessmentData {
  _id: string;
  title: string;
  company_name?: string;
  status: string;
}

function RecommendationsPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [assessment, setAssessment] = useState<AssessmentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const assessmentId = searchParams.get('assessment_id');

  useEffect(() => {
    const fetchData = async () => {
      try {
        let finalAssessmentId = assessmentId;

        // If no assessment ID provided, try to get the first available assessment
        if (!assessmentId) {
          console.log('🔍 No assessment ID provided, fetching available assessments...');
          try {
            const assessmentsResponse = await apiClient.getAssessments();
            const availableAssessments = assessmentsResponse?.assessments || [];

            if (availableAssessments.length > 0) {
              // Use the first completed assessment with recommendations, or the first one
              const completedAssessment = availableAssessments.find(a =>
                a.status === 'completed' && a.recommendations_generated
              ) || availableAssessments[0];

              finalAssessmentId = completedAssessment.id;
              console.log('✅ Auto-selected assessment:', finalAssessmentId);

              // Update URL to reflect the selected assessment
              router.replace(`/recommendations?assessment_id=${finalAssessmentId}`);
            } else {
              setError('No assessments available. Please create an assessment first.');
              setLoading(false);
              return;
            }
          } catch (err) {
            console.error('❌ Failed to fetch assessments:', err);
            setError('Assessment ID is required');
            setLoading(false);
            return;
          }
        }

        if (!finalAssessmentId) {
          setError('Assessment ID is required');
          setLoading(false);
          return;
        }

        setLoading(true);
        setError(null);

        console.log('🔍 Fetching recommendations for assessment:', finalAssessmentId);

        // Fetch both assessment info and recommendations
        const [assessmentData, recommendationsData] = await Promise.all([
          apiClient.getAssessment(finalAssessmentId),
          apiClient.getRecommendations(finalAssessmentId)
        ]);

        console.log('📊 Assessment data:', assessmentData);
        console.log('💡 Recommendations data:', recommendationsData);

        setAssessment(assessmentData);
        // Handle different API response formats
        const recs = recommendationsData?.recommendations || recommendationsData || [];
        setRecommendations(Array.isArray(recs) ? recs : []);
      } catch (err: any) {
        console.error('❌ Error fetching data:', err);
        setError(err.message || 'Failed to load recommendations');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [assessmentId]);

  const getPriorityColor = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getEffortColor = (effort: string) => {
    switch (effort?.toLowerCase()) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const handleBackToAssessment = () => {
    if (assessmentId) {
      router.push(`/assessment/${assessmentId}`);
    } else {
      router.push('/dashboard');
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 3, py: 4 }}>
        <Stack spacing={3}>
          <Skeleton variant="rectangular" height={60} />
          <Grid container spacing={3}>
            {[1, 2, 3].map((i) => (
              <Grid item xs={12} key={i}>
                <Skeleton variant="rectangular" height={200} />
              </Grid>
            ))}
          </Grid>
        </Stack>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 3, py: 4 }}>
        <Card sx={{ textAlign: 'center', py: 6 }}>
          <CardContent>
            <RecommendIcon 
              sx={{ fontSize: 80, color: 'error.main', mb: 3, opacity: 0.7 }} 
            />
            <Typography variant="h4" gutterBottom color="error.main">
              Unable to Load Recommendations
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: 600, mx: 'auto' }}>
              {error === 'Assessment ID is required' 
                ? 'No assessment has been selected. Please start by creating or selecting an assessment from the dashboard.'
                : error === 'Failed to load recommendations'
                ? 'We encountered an issue while loading your recommendations. This might be due to a temporary connectivity issue or the assessment data may still be processing.'
                : `Error: ${error}`
              }
            </Typography>
            
            <Stack 
              direction={{ xs: 'column', sm: 'row' }} 
              spacing={2} 
              justifyContent="center"
              sx={{ mt: 4 }}
            >
              <Button
                variant="contained"
                startIcon={<ArrowBackIcon />}
                onClick={() => router.push('/dashboard')}
                color="primary"
              >
                Go to Dashboard
              </Button>
              {assessmentId && (
                <Button
                  variant="outlined"
                  onClick={() => {
                    setError(null);
                    setLoading(true);
                    // Retry loading
                    window.location.reload();
                  }}
                >
                  Try Again
                </Button>
              )}
            </Stack>

            {error !== 'Assessment ID is required' && (
              <Alert severity="info" sx={{ mt: 4, textAlign: 'left' }}>
                <Typography variant="subtitle2" gutterBottom>
                  Troubleshooting Tips:
                </Typography>
                <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                  <li>Check your internet connection</li>
                  <li>Ensure the assessment has completed processing</li>
                  <li>Try refreshing the page or navigating back to the dashboard</li>
                  <li>Contact support if the issue persists</li>
                </ul>
              </Alert>
            )}
          </CardContent>
        </Card>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 3, py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={handleBackToAssessment}
          sx={{ mb: 2 }}
        >
          Back to Assessment
        </Button>
        
        <Typography variant="h4" gutterBottom>
          <RecommendIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Recommendations
        </Typography>
        
        {assessment && (
          <Typography variant="h6" color="text.secondary" gutterBottom>
            For {assessment.title} - {assessment.company_name || 'Unknown Company'}
          </Typography>
        )}

        {recommendations.length > 0 && (
          <Alert severity="info" sx={{ mt: 2 }}>
            <strong>AI Analysis Complete:</strong> Found {recommendations.length} optimization recommendation{recommendations.length !== 1 ? 's' : ''} generated by our specialized AI agents based on your infrastructure assessment
          </Alert>
        )}
      </Box>

      {/* Recommendations */}
      {recommendations.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <RecommendIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            AI Analysis in Progress
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Our AI agents are analyzing your infrastructure to generate personalized recommendations. This process typically takes 2-5 minutes for a comprehensive assessment.
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            <strong>What our AI is analyzing:</strong>
            <br />
            • Cost optimization opportunities
            <br />
            • Security enhancement recommendations
            <br />
            • Performance improvement strategies
            <br />
            • Compliance and governance suggestions
          </Typography>
          <Button
            variant="contained"
            onClick={handleBackToAssessment}
          >
            Back to Assessment
          </Button>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {recommendations.map((rec) => (
            <Grid item xs={12} key={rec._id}>
              <Card>
                <CardContent>
                  {/* Header */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6" gutterBottom>
                        {rec.title || 'Infrastructure Optimization Recommendation'}
                      </Typography>
                      <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                        <Chip
                          label={`By ${rec.agent_name || 'AI Agent'}`}
                          size="small"
                          variant="outlined"
                          color="info"
                        />
                        <Chip
                          label={rec.category || 'General'}
                          size="small"
                          color="primary"
                        />
                        <Chip
                          label={`${rec.priority || 'Medium'} Priority`}
                          size="small"
                          color={getPriorityColor(rec.priority) as any}
                        />
                      </Stack>
                    </Box>
                    
                    <Box sx={{ textAlign: 'right' }}>
                      <Typography variant="body2" color="text.secondary">
                        AI Confidence
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Rating
                          value={rec.confidence_score || 0.8}
                          max={1}
                          precision={0.1}
                          readOnly
                          size="small"
                        />
                        <Typography variant="body2" sx={{ ml: 1, fontWeight: 600 }}>
                          {Math.round((rec.confidence_score || 0.8) * 100)}%
                        </Typography>
                      </Box>
                    </Box>
                  </Box>

                  {/* Description */}
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    {rec.description || 'This recommendation has been generated by our AI infrastructure analysis to help optimize your cloud infrastructure setup, reduce costs, and improve performance.'}
                  </Typography>

                  {/* Key Metrics */}
                  <Grid container spacing={2} sx={{ mb: 3 }}>
                    {rec.estimated_cost_savings > 0 && (
                      <Grid item xs={12} sm={6} md={3} key={`cost-savings-${rec._id}`}>
                        <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light', color: 'success.contrastText' }}>
                          <MonetizationOnIcon sx={{ mb: 1 }} />
                          <Typography variant="h6">
                            ${rec.estimated_cost_savings.toLocaleString()}
                          </Typography>
                          <Typography variant="caption">
                            Estimated Savings
                          </Typography>
                        </Paper>
                      </Grid>
                    )}

                    <Grid item xs={12} sm={6} md={3} key={`implementation-effort-${rec._id}`}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <TrendingUpIcon sx={{ mb: 1 }} />
                        <Typography variant="h6">
                          {rec.implementation_effort}
                        </Typography>
                        <Typography variant="caption">
                          Implementation Effort
                        </Typography>
                      </Paper>
                    </Grid>

                    {rec.estimated_implementation_time && (
                      <Grid item xs={12} sm={6} md={3} key={`timeline-${rec._id}`}>
                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h6">
                            {rec.estimated_implementation_time}
                          </Typography>
                          <Typography variant="caption">
                            Timeline
                          </Typography>
                        </Paper>
                      </Grid>
                    )}

                    {rec.cloud_provider && (
                      <Grid item xs={12} sm={6} md={3} key={`cloud-provider-${rec._id}`}>
                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                          <CloudIcon sx={{ mb: 1 }} />
                          <Typography variant="h6">
                            {rec.cloud_provider.toUpperCase()}
                          </Typography>
                          <Typography variant="caption">
                            Cloud Provider
                          </Typography>
                        </Paper>
                      </Grid>
                    )}
                  </Grid>

                  {/* Benefits */}
                  {rec.benefits && rec.benefits.length > 0 && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Key Benefits:
                      </Typography>
                      <Stack spacing={1}>
                        {rec.benefits.map((benefit, idx) => (
                          <Typography key={`benefit-${rec._id}-${idx}`} variant="body2" sx={{ display: 'flex', alignItems: 'center' }}>
                            • {benefit}
                          </Typography>
                        ))}
                      </Stack>
                    </Box>
                  )}

                  {/* Implementation Steps */}
                  {rec.implementation_steps && rec.implementation_steps.length > 0 && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Implementation Steps:
                      </Typography>
                      <Stack spacing={1}>
                        {rec.implementation_steps.map((step, idx) => (
                          <Typography key={`step-${rec._id}-${idx}`} variant="body2" sx={{ display: 'flex', alignItems: 'flex-start' }}>
                            {idx + 1}. {step}
                          </Typography>
                        ))}
                      </Stack>
                    </Box>
                  )}

                  {/* Risks */}
                  {rec.risks && rec.risks.length > 0 && (
                    <Box>
                      <Typography variant="subtitle2" gutterBottom color="error">
                        Potential Risks:
                      </Typography>
                      <Stack spacing={1}>
                        {rec.risks.map((risk, idx) => (
                          <Typography key={`risk-${rec._id}-${idx}`} variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center' }}>
                            ⚠️ {risk}
                          </Typography>
                        ))}
                      </Stack>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Container>
  );
}

export default function RecommendationsPage() {
  return (
    <ProtectedRoute>
      <ResponsiveLayout title="Recommendations">
        <Suspense fallback={<Container><Typography>Loading...</Typography></Container>}>
          <RecommendationsPageContent />
        </Suspense>
      </ResponsiveLayout>
    </ProtectedRoute>
  );
}