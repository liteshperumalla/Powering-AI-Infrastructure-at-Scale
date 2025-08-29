'use client';

import React, { useEffect, useState } from 'react';
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

export default function RecommendationsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [assessment, setAssessment] = useState<AssessmentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const assessmentId = searchParams.get('assessment_id');

  useEffect(() => {
    const fetchData = async () => {
      if (!assessmentId) {
        setError('Assessment ID is required');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        
        console.log('🔍 Fetching recommendations for assessment:', assessmentId);
        
        // Fetch both assessment info and recommendations
        const [assessmentData, recommendationsData] = await Promise.all([
          apiClient.getAssessment(assessmentId),
          apiClient.getRecommendations(assessmentId)
        ]);
        
        console.log('📊 Assessment data:', assessmentData);
        console.log('💡 Recommendations data:', recommendationsData);
        
        setAssessment(assessmentData);
        setRecommendations(recommendationsData?.recommendations || []);
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
      <Container maxWidth="lg" sx={{ py: 4 }}>
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
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={handleBackToAssessment}
        >
          Back to Assessment
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
            Found {recommendations.length} recommendation{recommendations.length !== 1 ? 's' : ''} from AI agents
          </Alert>
        )}
      </Box>

      {/* Recommendations */}
      {recommendations.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <RecommendIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            No Recommendations Available
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Recommendations are still being generated for this assessment.
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
                        {rec.title}
                      </Typography>
                      <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                        <Chip
                          label={rec.agent_name}
                          size="small"
                          variant="outlined"
                        />
                        <Chip
                          label={rec.category}
                          size="small"
                          color="primary"
                        />
                        <Chip
                          label={rec.priority}
                          size="small"
                          color={getPriorityColor(rec.priority) as any}
                        />
                      </Stack>
                    </Box>
                    
                    <Box sx={{ textAlign: 'right' }}>
                      <Typography variant="body2" color="text.secondary">
                        Confidence Score
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Rating
                          value={rec.confidence_score}
                          max={1}
                          precision={0.1}
                          readOnly
                          size="small"
                        />
                        <Typography variant="body2" sx={{ ml: 1 }}>
                          {Math.round(rec.confidence_score * 100)}%
                        </Typography>
                      </Box>
                    </Box>
                  </Box>

                  {/* Description */}
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    {rec.description}
                  </Typography>

                  {/* Key Metrics */}
                  <Grid container spacing={2} sx={{ mb: 3 }}>
                    {rec.estimated_cost_savings > 0 && (
                      <Grid item xs={12} sm={6} md={3}>
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
                    
                    <Grid item xs={12} sm={6} md={3}>
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
                      <Grid item xs={12} sm={6} md={3}>
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
                      <Grid item xs={12} sm={6} md={3}>
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
                          <Typography key={idx} variant="body2" sx={{ display: 'flex', alignItems: 'center' }}>
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
                          <Typography key={idx} variant="body2" sx={{ display: 'flex', alignItems: 'flex-start' }}>
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
                          <Typography key={idx} variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center' }}>
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