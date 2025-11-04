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
import RefreshIcon from '@mui/icons-material/Refresh';
import { apiClient } from '../../services/api';
import { useRecommendationsData } from '../../hooks/useFreshData';
import RecommendationInsightsPanel from '../../components/RecommendationInsightsPanel';

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
  const [viewStartTimes, setViewStartTimes] = useState<Record<string, number>>({});

  const assessmentId = searchParams.get('assessment_id');

  // ML Interaction Tracking Functions
  const trackInteraction = async (
    recommendationId: string,
    interactionType: 'view' | 'click' | 'implement' | 'save' | 'share' | 'rate' | 'dismiss',
    interactionValue?: number
  ) => {
    try {
      await apiClient.trackRecommendationInteraction(
        recommendationId,
        interactionType,
        interactionValue,
        { assessment_id: assessmentId }
      );
      console.log(`✅ Tracked ${interactionType} for recommendation ${recommendationId}`);
    } catch (error) {
      console.error(`Failed to track ${interactionType}:`, error);
    }
  };

  // Track view when recommendation becomes visible
  useEffect(() => {
    if (recommendations.length > 0) {
      recommendations.forEach((rec) => {
        // Record view start time
        setViewStartTimes(prev => ({ ...prev, [rec._id]: Date.now() }));
      });
    }
  }, [recommendations]);

  // Track view duration when component unmounts or recommendations change
  useEffect(() => {
    return () => {
      // Calculate and track view durations
      Object.entries(viewStartTimes).forEach(([recId, startTime]) => {
        const viewDuration = (Date.now() - startTime) / 1000; // Convert to seconds
        if (viewDuration > 1) { // Only track if viewed for more than 1 second
          trackInteraction(recId, 'view', viewDuration);
        }
      });
    };
  }, [viewStartTimes]);

  const handleRecommendationClick = (recommendationId: string) => {
    trackInteraction(recommendationId, 'click');
  };

  const handleImplementClick = (recommendationId: string) => {
    trackInteraction(recommendationId, 'implement');
  };

  const handleSaveClick = (recommendationId: string) => {
    trackInteraction(recommendationId, 'save');
  };

  // Handle insight action clicks
  const handleInsightAction = (action: string, insight: any) => {
    console.log('🎯 Insight action clicked:', action, insight);

    // Track the interaction for related recommendations (with validation)
    if (insight.related_recommendations && insight.related_recommendations.length > 0) {
      insight.related_recommendations.forEach((recId: string) => {
        // Only track if recId is valid (not undefined, null, or 'undefined' string)
        if (recId && recId !== 'undefined' && recId !== 'null') {
          trackInteraction(recId, 'click');
        } else {
          console.warn('⚠️ Skipping invalid recommendation ID:', recId);
        }
      });
    }

    // Action handlers based on action type
    switch (action) {
      // Quick Wins actions
      case 'View Quick Wins':
        scrollToRecommendations(insight.related_recommendations);
        highlightRecommendations(insight.related_recommendations);
        break;

      case 'Create Action Plan':
        generateActionPlan(insight);
        break;

      case 'Assign to Team':
        openAssignmentDialog(insight);
        break;

      // Cost Optimization actions
      case 'View Cost Breakdown':
        showCostBreakdown(insight);
        break;

      case 'Compare Alternatives':
        compareAlternatives(insight);
        break;

      case 'Generate ROI Report':
        generateROIReport(insight);
        break;

      // Security actions
      case 'Review Security Recommendations':
      case 'Prioritize Security Fixes':
      case 'Schedule Security Audit':
        handleSecurityAction(action, insight);
        break;

      // High Impact actions
      case 'Explore Opportunities':
      case 'Build Business Case':
      case 'Present to Stakeholders':
        handleHighImpactAction(action, insight);
        break;

      // Performance actions
      case 'Analyze Performance Impact':
      case 'Review Implementation':
      case 'Schedule Optimization':
        handlePerformanceAction(action, insight);
        break;

      default:
        console.log(`Action "${action}" not yet implemented`);
        alert(`Action: ${action}\n\nThis will ${action.toLowerCase()} for ${insight.related_recommendations.length} related recommendations.`);
    }
  };

  // Scroll to specific recommendations
  const scrollToRecommendations = (recIds: string[]) => {
    if (recIds && recIds.length > 0) {
      const firstRecElement = document.getElementById(`rec-${recIds[0]}`);
      if (firstRecElement) {
        firstRecElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  };

  // Highlight recommendations temporarily
  const highlightRecommendations = (recIds: string[]) => {
    recIds.forEach(recId => {
      const element = document.getElementById(`rec-${recId}`);
      if (element) {
        element.style.transition = 'all 0.3s ease';
        element.style.backgroundColor = '#e3f2fd';
        element.style.transform = 'scale(1.02)';

        setTimeout(() => {
          element.style.backgroundColor = '';
          element.style.transform = '';
        }, 2000);
      }
    });
  };

  // Generate action plan
  const generateActionPlan = (insight: any) => {
    const relatedRecs = recommendations.filter(r =>
      insight.related_recommendations.includes(r._id)
    );

    const planText = `
🎯 Action Plan: ${insight.title}

📋 Summary:
${insight.description}

✅ Recommendations to Implement (${relatedRecs.length}):
${relatedRecs.map((rec, i) => `
${i + 1}. ${rec.title}
   - Priority: ${rec.priority}
   - Effort: ${rec.implementation_effort || 'Medium'}
   - Timeline: ${rec.estimated_implementation_time || '2-3 weeks'}
`).join('\n')}

📊 Expected Outcomes:
- Potential Savings: $${insight.metrics.potential_savings?.toLocaleString() || 'TBD'}
- Implementation Time: ${insight.metrics.implementation_time}
- Confidence Level: ${(insight.metrics.confidence * 100).toFixed(0)}%

📅 Next Steps:
1. Review each recommendation in detail
2. Assign owners for each task
3. Schedule implementation timeline
4. Set up progress tracking

Generated: ${new Date().toLocaleDateString()}
    `.trim();

    // Copy to clipboard and show alert
    navigator.clipboard.writeText(planText).then(() => {
      alert('✅ Action Plan Generated!\n\nThe action plan has been copied to your clipboard. You can paste it into your project management tool or share with your team.');
    }).catch(() => {
      alert(planText);
    });
  };

  // Open assignment dialog (placeholder)
  const openAssignmentDialog = (insight: any) => {
    alert(`🎯 Assign to Team\n\n${insight.related_recommendations.length} recommendations ready to assign.\n\nFeature coming soon: Assign recommendations to team members with notifications and tracking.`);
  };

  // Show cost breakdown
  const showCostBreakdown = (insight: any) => {
    const relatedRecs = recommendations.filter(r =>
      insight.related_recommendations.includes(r._id)
    );

    const breakdown = relatedRecs.map(rec => ({
      title: rec.title,
      cost: rec.estimated_cost_savings || 0,
      effort: rec.implementation_effort
    }));

    const message = `
💰 Cost Breakdown

Total Potential Savings: $${insight.metrics.potential_savings?.toLocaleString()}

Individual Recommendations:
${breakdown.map((item, i) =>
  `${i + 1}. ${item.title}\n   Savings: $${item.cost.toLocaleString()}/month\n   Effort: ${item.effort || 'Medium'}`
).join('\n\n')}
    `.trim();

    alert(message);
  };

  // Compare alternatives (placeholder)
  const compareAlternatives = (insight: any) => {
    alert(`🔄 Compare Alternatives\n\nAnalyzing ${insight.related_recommendations.length} recommendations to find the best cost/benefit ratio.\n\nFeature coming soon: Side-by-side comparison of cloud providers and service options.`);
  };

  // Generate ROI report
  const generateROIReport = (insight: any) => {
    const roi = insight.metrics.roi || 0;
    const savings = insight.metrics.potential_savings || 0;
    const implementationCost = savings / (roi || 1);

    const report = `
📊 ROI REPORT

Investment Analysis:
- Implementation Cost: $${implementationCost.toLocaleString()}
- Monthly Savings: $${savings.toLocaleString()}
- ROI: ${roi.toFixed(1)}x
- Payback Period: ${(implementationCost / savings).toFixed(1)} months

Recommendations Included: ${insight.related_recommendations.length}
Confidence Level: ${(insight.metrics.confidence * 100).toFixed(0)}%
Implementation Timeline: ${insight.metrics.implementation_time}

Generated: ${new Date().toLocaleString()}
    `.trim();

    navigator.clipboard.writeText(report).then(() => {
      alert('✅ ROI Report Generated!\n\nThe report has been copied to your clipboard.');
    }).catch(() => {
      alert(report);
    });
  };

  // Handle security actions
  const handleSecurityAction = (action: string, insight: any) => {
    scrollToRecommendations(insight.related_recommendations);
    highlightRecommendations(insight.related_recommendations);
    alert(`🔒 ${action}\n\nViewing ${insight.related_recommendations.length} security-related recommendations.`);
  };

  // Handle high impact actions
  const handleHighImpactAction = (action: string, insight: any) => {
    scrollToRecommendations(insight.related_recommendations);
    highlightRecommendations(insight.related_recommendations);

    if (action === 'Build Business Case') {
      generateActionPlan(insight);
    } else if (action === 'Present to Stakeholders') {
      generateROIReport(insight);
    } else {
      alert(`💡 ${action}\n\nExploring ${insight.related_recommendations.length} transformational opportunities.`);
    }
  };

  // Handle performance actions
  const handlePerformanceAction = (action: string, insight: any) => {
    scrollToRecommendations(insight.related_recommendations);
    highlightRecommendations(insight.related_recommendations);
    alert(`⚡ ${action}\n\nReviewing ${insight.related_recommendations.length} performance optimization recommendations.`);
  };

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

  // Auto-refresh recommendations data every 15 seconds
  const { forceRefresh: refreshRecommendations, isStale, lastRefresh } = useRecommendationsData(assessmentId || '', {
    autoRefresh: true,
    refreshInterval: 15000, // 15 seconds
    onRefresh: () => {
      console.log('🔄 Auto-refreshing recommendations data...');
      if (assessmentId) {
        fetchData();
      }
    }
  });

  useEffect(() => {
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
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h4" gutterBottom>
            <RecommendIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Recommendations
          </Typography>
          <Tooltip title={`Last updated: ${new Date(lastRefresh).toLocaleTimeString()}`}>
            <IconButton
              onClick={refreshRecommendations}
              color="primary"
              size="large"
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
        
        {assessment && (
          <Typography variant="h6" color="text.secondary" gutterBottom>
            For {assessment.title} - {assessment.company_name || 'Unknown Company'} •
            <Chip
              label={isStale ? "Data may be outdated" : "Live data"}
              size="small"
              color={isStale ? "warning" : "success"}
              variant="outlined"
              sx={{ ml: 1 }}
            />
          </Typography>
        )}

        {recommendations.length > 0 && (
          <Alert severity="info" sx={{ mt: 2 }}>
            <strong>AI Analysis Complete:</strong> Found {recommendations.length} optimization recommendation{recommendations.length !== 1 ? 's' : ''} generated by our specialized AI agents based on your infrastructure assessment
          </Alert>
        )}
      </Box>

      {/* Actionable Insights Panel */}
      {recommendations.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <RecommendationInsightsPanel
            recommendations={recommendations}
            assessment={assessment}
            onActionClick={handleInsightAction}
          />
        </Box>
      )}

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
            <Grid item xs={12} key={rec._id} id={`rec-${rec._id}`}>
              <Card
                sx={{ cursor: 'pointer', '&:hover': { boxShadow: 4 } }}
                onClick={() => handleRecommendationClick(rec._id)}
              >
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
                    {[
                      rec.estimated_cost_savings > 0 && {
                        key: `cost-savings-${rec._id}`,
                        content: (
                          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light', color: 'success.contrastText' }}>
                            <MonetizationOnIcon sx={{ mb: 1 }} />
                            <Typography variant="h6">
                              ${rec.estimated_cost_savings.toLocaleString()}
                            </Typography>
                            <Typography variant="caption">
                              Estimated Savings
                            </Typography>
                          </Paper>
                        )
                      },
                      {
                        key: `implementation-effort-${rec._id}`,
                        content: (
                          <Paper sx={{ p: 2, textAlign: 'center' }}>
                            <TrendingUpIcon sx={{ mb: 1 }} />
                            <Typography variant="h6">
                              {rec.implementation_effort || 'Medium'}
                            </Typography>
                            <Typography variant="caption">
                              Implementation Effort
                            </Typography>
                          </Paper>
                        )
                      },
                      rec.estimated_implementation_time && {
                        key: `timeline-${rec._id}`,
                        content: (
                          <Paper sx={{ p: 2, textAlign: 'center' }}>
                            <Typography variant="h6">
                              {rec.estimated_implementation_time}
                            </Typography>
                            <Typography variant="caption">
                              Timeline
                            </Typography>
                          </Paper>
                        )
                      },
                      rec.cloud_provider && {
                        key: `cloud-provider-${rec._id}`,
                        content: (
                          <Paper sx={{ p: 2, textAlign: 'center' }}>
                            <CloudIcon sx={{ mb: 1 }} />
                            <Typography variant="h6">
                              {rec.cloud_provider.toUpperCase()}
                            </Typography>
                            <Typography variant="caption">
                              Cloud Provider
                            </Typography>
                          </Paper>
                        )
                      }
                    ].filter(Boolean).map((metric: any) => (
                      <Grid item xs={12} sm={6} md={3} key={metric.key}>
                        {metric.content}
                      </Grid>
                    ))}
                  </Grid>

                  {/* Benefits */}
                  {Array.isArray(rec.benefits) && rec.benefits.length > 0 && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Key Benefits:
                      </Typography>
                      <Stack spacing={1}>
                        {(rec.benefits || []).map((benefit, idx) => {
                          const benefitText = typeof benefit === 'string' ? benefit : String(benefit);
                          return (
                            <Typography key={`benefit-${rec._id}-${idx}`} variant="body2" sx={{ display: 'flex', alignItems: 'center' }}>
                              • {benefitText}
                            </Typography>
                          );
                        })}
                      </Stack>
                    </Box>
                  )}

                  {/* Implementation Steps */}
                  {Array.isArray(rec.implementation_steps) && rec.implementation_steps.length > 0 && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Implementation Steps:
                      </Typography>
                      <Stack spacing={1}>
                        {(rec.implementation_steps || []).map((step, idx) => {
                          const stepText = typeof step === 'string' ? step : String(step);
                          return (
                            <Typography key={`step-${rec._id}-${idx}`} variant="body2" sx={{ display: 'flex', alignItems: 'flex-start' }}>
                              {idx + 1}. {stepText}
                            </Typography>
                          );
                        })}
                      </Stack>
                    </Box>
                  )}

                  {/* Risks */}
                  {Array.isArray(rec.risks) && rec.risks.length > 0 && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle2" gutterBottom color="error">
                        Potential Risks:
                      </Typography>
                      <Stack spacing={1}>
                        {(rec.risks || []).map((risk, idx) => {
                          const riskText = typeof risk === 'string' ? risk : String(risk);
                          return (
                            <Typography key={`risk-${rec._id}-${idx}`} variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center' }}>
                              ⚠️ {riskText}
                            </Typography>
                          );
                        })}
                      </Stack>
                    </Box>
                  )}

                  {/* Action Buttons */}
                  <Divider sx={{ my: 2 }} />
                  <Stack direction="row" spacing={2} justifyContent="flex-end">
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSaveClick(rec._id);
                      }}
                    >
                      Save for Later
                    </Button>
                    <Button
                      variant="contained"
                      size="small"
                      color="primary"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleImplementClick(rec._id);
                      }}
                    >
                      Mark as Implemented
                    </Button>
                  </Stack>
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