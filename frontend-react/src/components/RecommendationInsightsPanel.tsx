'use client';

import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Card,
  Typography,
  Button,
  Chip,
  Alert,
  Stack,
  Divider,
  LinearProgress,
  Tooltip,
  IconButton,
  Collapse
} from '@mui/material';
import {
  TrendingUp,
  Warning,
  CheckCircle,
  Info,
  Lightbulb,
  CompareArrows,
  ExpandMore,
  ExpandLess,
  AttachMoney,
  Speed,
  Security
} from '@mui/icons-material';

interface Recommendation {
  _id: string;
  id?: string;
  title: string;
  category: string;
  priority: string;
  implementation_effort?: string;
  estimated_cost?: number;
  estimated_cost_savings?: number;
  confidence_score: number;
  business_impact?: string;
  risks?: string[];
  benefits?: string[];
}

interface RecommendationInsight {
  type: 'opportunity' | 'risk' | 'quick-win' | 'high-impact';
  title: string;
  description: string;
  metrics: {
    roi?: number;
    potential_savings?: number;
    implementation_time: string;
    confidence: number;
  };
  actions: string[];
  related_recommendations: string[];
  icon: React.ReactNode;
  color: string;
}

interface RecommendationInsightsPanelProps {
  recommendations: Recommendation[];
  assessment?: any;
  onActionClick?: (action: string, insight: RecommendationInsight) => void;
}

export default function RecommendationInsightsPanel({
  recommendations,
  assessment,
  onActionClick
}: RecommendationInsightsPanelProps) {
  const [expandedInsights, setExpandedInsights] = useState<Set<number>>(new Set([0])); // First insight expanded by default

  // Generate insights from recommendations
  const insights = useMemo(() => {
    if (!recommendations || recommendations.length === 0) {
      return [];
    }

    const generatedInsights: RecommendationInsight[] = [];

    // Insight 1: Quick Wins
    const quickWins = recommendations.filter(r =>
      (r.implementation_effort === 'low' || r.implementation_effort === 'Low') &&
      (r.estimated_cost === undefined || r.estimated_cost < 5000) &&
      r.confidence_score > 0.7
    );

    if (quickWins.length > 0) {
      const avgConfidence = quickWins.reduce((sum, r) => sum + r.confidence_score, 0) / quickWins.length;
      const totalSavings = quickWins.reduce((sum, r) => sum + (r.estimated_cost_savings || 0), 0);

      generatedInsights.push({
        type: 'quick-win',
        title: `${quickWins.length} Quick Win${quickWins.length > 1 ? 's' : ''} Available`,
        description: 'Low-effort, high-confidence recommendations you can implement this week to see immediate results',
        metrics: {
          potential_savings: totalSavings,
          implementation_time: '< 1 week',
          confidence: avgConfidence
        },
        actions: [
          'View Quick Wins',
          'Create Action Plan',
          'Assign to Team'
        ],
        related_recommendations: quickWins.map(r => r._id || r.id || ''),
        icon: <CheckCircle sx={{ fontSize: 32 }} />,
        color: 'success.main'
      });
    }

    // Insight 2: Cost Optimization Opportunities
    const costOptimizations = recommendations.filter(r =>
      (r.category === 'cost' || r.category === 'cost_optimization' || r.category === 'optimization') &&
      (r.estimated_cost_savings || 0) > 1000
    );

    if (costOptimizations.length > 0) {
      const totalSavings = costOptimizations.reduce(
        (sum, r) => sum + (r.estimated_cost_savings || 0),
        0
      );
      const totalCost = costOptimizations.reduce(
        (sum, r) => sum + (r.estimated_cost || 0),
        0
      );
      const roi = totalCost > 0 ? totalSavings / totalCost : 0;

      generatedInsights.push({
        type: 'opportunity',
        title: `Save $${totalSavings.toLocaleString()}/month`,
        description: `Identified ${costOptimizations.length} cost optimization opportunities that could reduce your infrastructure spending`,
        metrics: {
          roi: roi,
          potential_savings: totalSavings,
          implementation_time: '2-4 weeks',
          confidence: 0.85
        },
        actions: [
          'View Cost Breakdown',
          'Compare Alternatives',
          'Generate ROI Report'
        ],
        related_recommendations: costOptimizations.map(r => r._id || r.id || ''),
        icon: <AttachMoney sx={{ fontSize: 32 }} />,
        color: 'primary.main'
      });
    }

    // Insight 3: Security & Compliance Risks
    const securityRecs = recommendations.filter(r =>
      (r.category === 'security' || r.category === 'compliance') &&
      r.priority === 'high'
    );

    if (securityRecs.length > 0) {
      const avgConfidence = securityRecs.reduce((sum, r) => sum + r.confidence_score, 0) / securityRecs.length;

      generatedInsights.push({
        type: 'risk',
        title: `${securityRecs.length} Critical Security Item${securityRecs.length > 1 ? 's' : ''}`,
        description: 'Address these security recommendations to reduce risk exposure and improve compliance posture',
        metrics: {
          implementation_time: '1-2 weeks',
          confidence: avgConfidence
        },
        actions: [
          'Review Security Gaps',
          'Prioritize Remediation',
          'Create Security Plan'
        ],
        related_recommendations: securityRecs.map(r => r._id || r.id || ''),
        icon: <Security sx={{ fontSize: 32 }} />,
        color: 'warning.main'
      });
    }

    // Insight 4: High-Impact Projects
    const highImpact = recommendations.filter(r =>
      r.business_impact === 'transformational' ||
      r.business_impact === 'high' ||
      ((r.estimated_cost_savings || 0) > 10000 && r.confidence_score > 0.6)
    );

    if (highImpact.length > 0) {
      const totalSavings = highImpact.reduce((sum, r) => sum + (r.estimated_cost_savings || 0), 0);
      const totalCost = highImpact.reduce((sum, r) => sum + (r.estimated_cost || 0), 0);
      const roi = totalCost > 0 ? totalSavings / totalCost : 0;

      generatedInsights.push({
        type: 'high-impact',
        title: 'Transformational Opportunities',
        description: `${highImpact.length} high-impact recommendations that can significantly transform your infrastructure`,
        metrics: {
          roi: roi,
          potential_savings: totalSavings,
          implementation_time: '3-6 months',
          confidence: 0.75
        },
        actions: [
          'Explore Opportunities',
          'Build Business Case',
          'Present to Stakeholders'
        ],
        related_recommendations: highImpact.map(r => r._id || r.id || ''),
        icon: <Lightbulb sx={{ fontSize: 32 }} />,
        color: 'secondary.main'
      });
    }

    // Insight 5: Performance Optimization
    const performanceRecs = recommendations.filter(r =>
      r.category === 'performance' && r.confidence_score > 0.65
    );

    if (performanceRecs.length > 0) {
      generatedInsights.push({
        type: 'opportunity',
        title: 'Performance Boost Opportunities',
        description: `${performanceRecs.length} recommendations to improve system performance and user experience`,
        metrics: {
          implementation_time: '2-3 weeks',
          confidence: 0.80
        },
        actions: [
          'Analyze Performance Impact',
          'Review Implementation',
          'Schedule Optimization'
        ],
        related_recommendations: performanceRecs.map(r => r._id || r.id || ''),
        icon: <Speed sx={{ fontSize: 32 }} />,
        color: 'info.main'
      });
    }

    return generatedInsights;
  }, [recommendations]);

  const toggleInsight = (index: number) => {
    setExpandedInsights(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  const handleActionClick = (action: string, insight: RecommendationInsight) => {
    if (onActionClick) {
      onActionClick(action, insight);
    } else {
      console.log('Action clicked:', action, insight);
      // Default behavior: scroll to related recommendations
      // Or open a modal, navigate to a page, etc.
    }
  };

  if (!recommendations || recommendations.length === 0) {
    return (
      <Alert severity="info" icon={<Info />}>
        No recommendations available yet. Complete your assessment to get personalized insights and actionable recommendations.
      </Alert>
    );
  }

  if (insights.length === 0) {
    return (
      <Alert severity="info" icon={<Info />}>
        Analyzing your recommendations to generate actionable insights...
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Lightbulb color="primary" sx={{ fontSize: 32 }} />
          Actionable Insights
        </Typography>
        <Chip
          label={`${insights.length} Insight${insights.length > 1 ? 's' : ''}`}
          color="primary"
          variant="outlined"
        />
      </Box>

      <Stack spacing={2}>
        {insights.map((insight, index) => (
          <Card
            key={index}
            elevation={expandedInsights.has(index) ? 4 : 1}
            sx={{
              borderLeft: 4,
              borderColor: insight.color,
              transition: 'all 0.3s ease',
              '&:hover': {
                elevation: 4,
                transform: 'translateY(-2px)'
              }
            }}
          >
            <Box
              sx={{
                p: 2,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 2
              }}
              onClick={() => toggleInsight(index)}
            >
              <Box sx={{ color: insight.color }}>
                {insight.icon}
              </Box>

              <Box sx={{ flex: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    {insight.title}
                  </Typography>
                  <Chip
                    label={insight.type.replace('-', ' ').toUpperCase()}
                    size="small"
                    sx={{
                      bgcolor: insight.color,
                      color: 'white',
                      fontWeight: 600,
                      fontSize: '0.7rem'
                    }}
                  />
                </Box>

                <Typography variant="body2" color="text.secondary">
                  {insight.description}
                </Typography>
              </Box>

              <IconButton size="small">
                {expandedInsights.has(index) ? <ExpandLess /> : <ExpandMore />}
              </IconButton>
            </Box>

            <Collapse in={expandedInsights.has(index)}>
              <Divider />
              <Box sx={{ p: 3, pt: 2 }}>
                {/* Metrics */}
                <Stack direction="row" spacing={3} sx={{ mb: 3 }} flexWrap="wrap">
                  {insight.metrics.roi !== undefined && (
                    <Box>
                      <Typography variant="caption" color="text.secondary" display="block">
                        ROI
                      </Typography>
                      <Typography variant="h6" fontWeight="bold" color={insight.color}>
                        {insight.metrics.roi.toFixed(1)}x
                      </Typography>
                    </Box>
                  )}

                  {insight.metrics.potential_savings !== undefined && (
                    <Box>
                      <Typography variant="caption" color="text.secondary" display="block">
                        Potential Savings
                      </Typography>
                      <Typography variant="h6" fontWeight="bold" color="success.main">
                        ${insight.metrics.potential_savings.toLocaleString()}
                      </Typography>
                    </Box>
                  )}

                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Time to Implement
                    </Typography>
                    <Typography variant="h6" fontWeight="bold">
                      {insight.metrics.implementation_time}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Confidence
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress
                        variant="determinate"
                        value={insight.metrics.confidence * 100}
                        sx={{
                          width: 80,
                          height: 8,
                          borderRadius: 4,
                          backgroundColor: 'grey.200',
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: insight.color
                          }
                        }}
                      />
                      <Typography variant="body2" fontWeight="bold">
                        {(insight.metrics.confidence * 100).toFixed(0)}%
                      </Typography>
                    </Box>
                  </Box>
                </Stack>

                {/* Actions */}
                <Box>
                  <Typography variant="subtitle2" gutterBottom fontWeight={600}>
                    Recommended Actions:
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                    {insight.actions.map((action, i) => (
                      <Button
                        key={i}
                        variant="outlined"
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleActionClick(action, insight);
                        }}
                        sx={{
                          borderColor: insight.color,
                          color: insight.color,
                          '&:hover': {
                            borderColor: insight.color,
                            backgroundColor: `${insight.color}15`
                          }
                        }}
                      >
                        {action}
                      </Button>
                    ))}
                  </Stack>
                </Box>

                {/* Related recommendations count */}
                <Box sx={{ mt: 2, p: 1.5, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Based on {insight.related_recommendations.length} recommendation{insight.related_recommendations.length > 1 ? 's' : ''}
                  </Typography>
                </Box>
              </Box>
            </Collapse>
          </Card>
        ))}
      </Stack>
    </Box>
  );
}
