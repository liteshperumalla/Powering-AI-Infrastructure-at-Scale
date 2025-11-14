'use client';

import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
  Paper,
  Chip,
  Stack,
  LinearProgress,
  Divider,
} from '@mui/material';
import {
  TrendingUp,
  Security,
  Science,
  CheckCircle,
  AccountBalance,
  BarChart,
  Speed,
  Lock,
  Restore,
} from '@mui/icons-material';
import { apiClient } from '@/services/api';

interface AdditionalFeaturesProps {
  assessmentId: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`feature-tabpanel-${index}`}
      aria-labelledby={`feature-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function AdditionalFeatures({ assessmentId }: AdditionalFeaturesProps) {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [features, setFeatures] = useState<any>(null);

  useEffect(() => {
    const fetchFeatures = async () => {
      try {
        setLoading(true);
        const response = await apiClient.get(`/features/assessment/${assessmentId}/all-features`);
        setFeatures(response.data);
        setError(null);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load additional features');
      } finally {
        setLoading(false);
      }
    };

    if (assessmentId) {
      fetchFeatures();
    }
  }, [assessmentId]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  if (loading) {
    return (
      <Card>
        <CardContent sx={{ textAlign: 'center', py: 6 }}>
          <CircularProgress />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Loading additional features...
          </Typography>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        {error}
      </Alert>
    );
  }

  if (!features) {
    return null;
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h5" color="text.primary" gutterBottom sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
          <BarChart sx={{ mr: 1 }} />
          Additional Features & Insights
        </Typography>

        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} variant="scrollable" scrollButtons="auto">
            <Tab icon={<AccountBalance />} label="Budget" />
            <Tab icon={<BarChart />} label="Executive" />
            <Tab icon={<Lock />} label="Vendor Lock-in" />
            <Tab icon={<Speed />} label="Performance" />
            <Tab icon={<Security />} label="Compliance" />
            <Tab icon={<CheckCircle />} label="Approvals" />
            <Tab icon={<TrendingUp />} label="Impact" />
            <Tab icon={<Restore />} label="Rollback" />
            <Tab icon={<Science />} label="Experiments" />
          </Tabs>
        </Box>

        {/* Budget Forecasting */}
        <TabPanel value={tabValue} index={0}>
          {features.budget && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" color="text.primary" gutterBottom>Budget Forecast Summary</Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {features.budget.summary?.description || 'Financial planning and budget forecasting for your infrastructure'}
                </Typography>
              </Grid>

              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light' }}>
                  <Typography variant="h4" color="primary.contrastText">
                    ${features.budget.summary?.current_monthly_spend?.toLocaleString() || 0}
                  </Typography>
                  <Typography variant="body2" color="primary.contrastText">
                    Current Monthly Spend
                  </Typography>
                </Paper>
              </Grid>

              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light' }}>
                  <Typography variant="h4" color="success.contrastText">
                    ${features.budget.summary?.projected_monthly_spend?.toLocaleString() || 0}
                  </Typography>
                  <Typography variant="body2" color="success.contrastText">
                    Projected Monthly Spend
                  </Typography>
                </Paper>
              </Grid>

              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.light' }}>
                  <Typography variant="h4" color="warning.contrastText">
                    ${features.budget.summary?.potential_savings?.toLocaleString() || 0}
                  </Typography>
                  <Typography variant="body2" color="warning.contrastText">
                    Potential Savings
                  </Typography>
                </Paper>
              </Grid>

              {features.budget.recommendations?.length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                    Cost Optimization Recommendations
                  </Typography>
                  <Stack spacing={2}>
                    {features.budget.recommendations.map((rec: any, idx: number) => (
                      <Paper key={idx} sx={{ p: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          {rec.category || rec.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {rec.description || rec.recommendation}
                        </Typography>
                        {rec.estimated_savings && (
                          <Chip
                            label={`Save $${rec.estimated_savings.toLocaleString()}`}
                            color="success"
                            size="small"
                            sx={{ mt: 1 }}
                          />
                        )}
                      </Paper>
                    ))}
                  </Stack>
                </Grid>
              )}
            </Grid>
          )}
        </TabPanel>

        {/* Executive Dashboard */}
        <TabPanel value={tabValue} index={1}>
          {features.executive && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" color="text.primary" gutterBottom>Executive Summary</Typography>
              </Grid>

              {features.executive.key_metrics && (
                <>
                  <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" color="text.primary">
                        {features.executive.key_metrics.total_recommendations || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Recommendations
                      </Typography>
                    </Paper>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" color="text.primary">
                        ${features.executive.key_metrics.total_cost_savings?.toLocaleString() || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Potential Savings
                      </Typography>
                    </Paper>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" color="text.primary">
                        {features.executive.key_metrics.avg_confidence_score
                          ? `${Math.round(features.executive.key_metrics.avg_confidence_score * 100)}%`
                          : 'N/A'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Avg Confidence
                      </Typography>
                    </Paper>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" color="text.primary">
                        {features.executive.key_metrics.implementation_timeline || 'N/A'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Timeline
                      </Typography>
                    </Paper>
                  </Grid>
                </>
              )}

              {features.executive.insights?.length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                    Key Insights
                  </Typography>
                  <Stack spacing={1}>
                    {features.executive.insights.map((insight: string, idx: number) => (
                      <Alert key={idx} severity="info" icon={<TrendingUp />}>
                        {insight}
                      </Alert>
                    ))}
                  </Stack>
                </Grid>
              )}
            </Grid>
          )}
        </TabPanel>

        {/* Vendor Lock-in Analysis */}
        <TabPanel value={tabValue} index={2}>
          {features.vendor_lockin && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" color="text.primary" gutterBottom>Vendor Lock-in Risk Assessment</Typography>
              </Grid>

              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 3 }}>
                  <Typography variant="subtitle1" gutterBottom>Overall Risk Score</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box sx={{ flex: 1, mr: 2 }}>
                      <LinearProgress
                        variant="determinate"
                        value={(features.vendor_lockin.risk_score || 0) * 100}
                        color={
                          (features.vendor_lockin.risk_score || 0) > 0.7 ? 'error' :
                          (features.vendor_lockin.risk_score || 0) > 0.4 ? 'warning' : 'success'
                        }
                        sx={{ height: 10, borderRadius: 5 }}
                      />
                    </Box>
                    <Typography variant="h6" color="text.primary">
                      {Math.round((features.vendor_lockin.risk_score || 0) * 100)}%
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {features.vendor_lockin.risk_level || 'Medium'} Risk Level
                  </Typography>
                </Paper>
              </Grid>

              {features.vendor_lockin.mitigation_strategies?.length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                    Mitigation Strategies
                  </Typography>
                  <Stack spacing={2}>
                    {features.vendor_lockin.mitigation_strategies.map((strategy: any, idx: number) => (
                      <Paper key={idx} sx={{ p: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          {strategy.title || strategy.strategy}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {strategy.description || strategy.details}
                        </Typography>
                        {strategy.effort && (
                          <Chip
                            label={`Effort: ${strategy.effort}`}
                            size="small"
                            sx={{ mt: 1 }}
                          />
                        )}
                      </Paper>
                    ))}
                  </Stack>
                </Grid>
              )}
            </Grid>
          )}
        </TabPanel>

        {/* Performance Monitoring */}
        <TabPanel value={tabValue} index={3}>
          {features.performance && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" color="text.primary" gutterBottom>Performance Metrics</Typography>
              </Grid>

              {features.performance.summary && (
                <>
                  <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="body2" color="text.secondary">Overall Health</Typography>
                      <Typography variant="h5" color="text.primary" sx={{ mt: 1, textTransform: 'capitalize' }}>
                        {features.performance.summary.overall_health || 'Good'}
                      </Typography>
                    </Paper>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="body2" color="text.secondary">Avg Response Time</Typography>
                      <Typography variant="h5" color="text.primary" sx={{ mt: 1 }}>
                        {features.performance.summary.avg_response_time_ms || 0}ms
                      </Typography>
                    </Paper>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="body2" color="text.secondary">Uptime</Typography>
                      <Typography variant="h5" color="text.primary" sx={{ mt: 1 }}>
                        {features.performance.summary.uptime_percentage || 0}%
                      </Typography>
                    </Paper>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="body2" color="text.secondary">Active Alerts</Typography>
                      <Typography variant="h5" color="text.primary" sx={{ mt: 1, color: features.performance.summary.active_alerts > 0 ? 'error.main' : 'success.main' }}>
                        {features.performance.summary.active_alerts || 0}
                      </Typography>
                    </Paper>
                  </Grid>
                </>
              )}
            </Grid>
          )}
        </TabPanel>

        {/* Compliance */}
        <TabPanel value={tabValue} index={4}>
          {features.compliance && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" color="text.primary" gutterBottom>Compliance Status</Typography>
              </Grid>

              {features.compliance.summary && (
                <Grid item xs={12}>
                  <Paper sx={{ p: 3 }}>
                    <Typography variant="subtitle1" gutterBottom>Compliance Score</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Box sx={{ flex: 1, mr: 2 }}>
                        <LinearProgress
                          variant="determinate"
                          value={(features.compliance.summary.compliance_score || 0) * 100}
                          color="success"
                          sx={{ height: 10, borderRadius: 5 }}
                        />
                      </Box>
                      <Typography variant="h6" color="text.primary">
                        {Math.round((features.compliance.summary.compliance_score || 0) * 100)}%
                      </Typography>
                    </Box>
                  </Paper>
                </Grid>
              )}

              {features.compliance.frameworks?.length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                    Compliance Frameworks
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    {features.compliance.frameworks.map((framework: any, idx: number) => (
                      <Chip
                        key={idx}
                        label={framework.name || framework}
                        color={framework.status === 'compliant' ? 'success' : 'warning'}
                        sx={{ mb: 1 }}
                      />
                    ))}
                  </Stack>
                </Grid>
              )}
            </Grid>
          )}
        </TabPanel>

        {/* Approval Workflows */}
        <TabPanel value={tabValue} index={5}>
          {features.approvals && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" color="text.primary" gutterBottom>Approval Workflows</Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {features.approvals.description || 'Automated approval workflows for infrastructure changes'}
                </Typography>
              </Grid>

              {features.approvals.workflows?.length > 0 && (
                <Grid item xs={12}>
                  <Stack spacing={2}>
                    {features.approvals.workflows.map((workflow: any, idx: number) => (
                      <Paper key={idx} sx={{ p: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          {workflow.name || `Workflow ${idx + 1}`}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Status: <Chip label={workflow.status || 'Pending'} size="small" sx={{ ml: 1 }} />
                        </Typography>
                      </Paper>
                    ))}
                  </Stack>
                </Grid>
              )}
            </Grid>
          )}
        </TabPanel>

        {/* Impact Analysis */}
        <TabPanel value={tabValue} index={6}>
          {features.impact && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" color="text.primary" gutterBottom>Change Impact Analysis</Typography>
              </Grid>

              {features.impact.summary && (
                <Grid item xs={12}>
                  <Paper sx={{ p: 3 }}>
                    <Typography variant="subtitle1" gutterBottom>Overall Impact</Typography>
                    <Chip
                      label={features.impact.summary.overall_impact || 'Medium'}
                      color={
                        features.impact.summary.overall_impact === 'High' ? 'error' :
                        features.impact.summary.overall_impact === 'Low' ? 'success' : 'warning'
                      }
                    />
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                      {features.impact.summary.description}
                    </Typography>
                  </Paper>
                </Grid>
              )}
            </Grid>
          )}
        </TabPanel>

        {/* Rollback Plans */}
        <TabPanel value={tabValue} index={7}>
          {features.rollback && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" color="text.primary" gutterBottom>Rollback & Recovery Plans</Typography>
              </Grid>

              {features.rollback.plans?.length > 0 && (
                <Grid item xs={12}>
                  <Stack spacing={2}>
                    {features.rollback.plans.map((plan: any, idx: number) => (
                      <Paper key={idx} sx={{ p: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          {plan.title || `Rollback Plan ${idx + 1}`}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {plan.description || plan.details}
                        </Typography>
                        {plan.estimated_time && (
                          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                            Estimated Time: {plan.estimated_time}
                          </Typography>
                        )}
                      </Paper>
                    ))}
                  </Stack>
                </Grid>
              )}
            </Grid>
          )}
        </TabPanel>

        {/* Experiments */}
        <TabPanel value={tabValue} index={8}>
          {features.experiments && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" color="text.primary" gutterBottom>A/B Testing & Experiments</Typography>
              </Grid>

              {features.experiments.active_experiments?.length > 0 && (
                <Grid item xs={12}>
                  <Stack spacing={2}>
                    {features.experiments.active_experiments.map((exp: any, idx: number) => (
                      <Paper key={idx} sx={{ p: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          {exp.name || `Experiment ${idx + 1}`}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {exp.description || exp.details}
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                          <Chip label={exp.status || 'Running'} size="small" color="primary" />
                        </Box>
                      </Paper>
                    ))}
                  </Stack>
                </Grid>
              )}
            </Grid>
          )}
        </TabPanel>
      </CardContent>
    </Card>
  );
}
