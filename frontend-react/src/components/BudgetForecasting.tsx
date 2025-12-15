'use client';

import React, { useState, useEffect } from 'react';
import { useFreshData } from '../hooks/useFreshData';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Button,
  Grid,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch,
  FormControlLabel,
  Divider,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AttachMoney,
  Assessment,
  Timeline,
  Visibility,
  Edit,
  Delete,
  Download,
  Refresh,
  PlayArrow,
  Stop,
  ModelTraining,
  Analytics,
  Warning,
  CheckCircle,
  ExpandMore,
  Settings,
  PieChart,
  BarChart,
} from '@mui/icons-material';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as ChartTooltip, AreaChart, Area, PieChart as RechartsPieChart, Pie, Cell, BarChart as RechartsBarChart, Bar, ComposedChart } from 'recharts';
import { getBudgetForecastingService, CostForecast, BudgetAllocation, OptimizationOpportunity, CostModel, BudgetAlert } from '../services/budgetForecasting';

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
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

interface BudgetForecastingProps {
  assessmentId?: string;
}

const BudgetForecasting: React.FC<BudgetForecastingProps> = ({ assessmentId }) => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [forecastService] = useState(() => getBudgetForecastingService());

  // Auto-refresh budget forecasting data every 45 seconds
  const { forceRefresh: refreshBudgetData, isStale, lastRefresh } = useFreshData('budget_forecasting', {
    autoRefresh: true,
    refreshInterval: 45000, // 45 seconds
    onRefresh: () => {
      console.log('🔄 Auto-refreshing budget forecasting data...');
      loadForecastingData();
    }
  });

  // State for different sections
  const [forecasts, setForecasts] = useState<CostForecast[]>([]);
  const [forecastChartData, setForecastChartData] = useState<any[]>([]); // For Overview tab charts
  const [budgetAllocations, setBudgetAllocations] = useState<BudgetAllocation[]>([]);
  const [optimizationOpportunities, setOptimizationOpportunities] = useState<OptimizationOpportunity[]>([]);
  const [costModels, setCostModels] = useState<CostModel[]>([]);
  const [budgetAlerts, setBudgetAlerts] = useState<BudgetAlert[]>([]);
  const [currentSpending, setCurrentSpending] = useState<any>(null);

  // Dialog states
  const [forecastDialog, setForecastDialog] = useState(false);
  const [modelDialog, setModelDialog] = useState(false);
  const [allocationDialog, setAllocationDialog] = useState(false);
  const [modelPerformanceDialog, setModelPerformanceDialog] = useState(false);
  const [opportunityDetailsDialog, setOpportunityDetailsDialog] = useState(false);

  // Selected items for dialogs
  const [selectedModel, setSelectedModel] = useState<CostModel | null>(null);
  const [selectedOpportunity, setSelectedOpportunity] = useState<OptimizationOpportunity | null>(null);
  
  // Form states
  const [newForecastData, setNewForecastData] = useState({
    forecast_name: '',
    period: 'monthly',
    forecast_horizon_months: 12,
    include_scenarios: true,
    model_type: 'ensemble',
  });

  const [newModelData, setNewModelData] = useState({
    model_name: '',
    model_type: 'ensemble',
    training_period_months: 12,
    features: [] as string[],
    validation_split: 0.2,
  });

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  useEffect(() => {
    loadForecastingData();
  }, [assessmentId]);

  const loadForecastingData = async () => {
    if (!assessmentId) return;

    setLoading(true);
    try {
      // Use apiClient for authenticated requests
      const { apiClient } = await import('../services/api');
      const budgetData = await apiClient.get<any>(`/features/assessment/${assessmentId}/budget`);

      console.log('📊 Budget Data Loaded:', budgetData);

      // Map the real backend data to component state
      setCurrentSpending({
        current_month: budgetData.current_monthly_estimate || 0,
        projected_month_end: budgetData.forecast_months?.[0]?.projected_cost || 0,
        budget_remaining: (budgetData.summary?.monthly_budget_limit || 0) - (budgetData.current_monthly_estimate || 0),
        days_remaining: Math.floor(((budgetData.summary?.monthly_budget_limit || 0) / (budgetData.current_monthly_estimate || 1)) * 30),
        total_estimated: budgetData.summary?.total_estimated || 0,
        annual_projection: budgetData.annual_projection || 0,
      });

      // Transform forecast_months into chart data format for Overview tab
      const chartData = (budgetData.forecast_months || []).map((month: any) => ({
        period: month.month,
        predicted_cost: month.projected_cost,
        actual_cost: month.projected_cost, // Use projected as actual for now
        budget_allocated: month.budget_allocated,
        variance: month.variance
      }));

      // Store chart data separately
      setForecastChartData(chartData);

      // Keep forecasts empty for now (will be populated when user creates forecasts)
      setForecasts([]);

      // Budget allocation data (create from forecast)
      setBudgetAllocations(budgetData.forecast_months?.map((f: any) => ({
        category: f.month,
        allocated: f.budget_allocated,
        spent: f.projected_cost,
        remaining: f.variance
      })) || []);

      // Get optimization opportunities from backend
      setOptimizationOpportunities(budgetData.optimization_opportunities || []);

      // Get budget alerts from backend
      setBudgetAlerts(budgetData.alerts || []);

      // Get AI cost models from backend (if available)
      setCostModels(budgetData.cost_models || []);

    } catch (error) {
      setError('Failed to load budget forecasting data');
      console.error('Error loading forecasting data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateForecast = async () => {
    try {
      setLoading(true);
      const forecast = await forecastService.createCostForecast(newForecastData);
      setForecasts(prev => [...prev, forecast]);
      setForecastDialog(false);
      setNewForecastData({
        forecast_name: '',
        period: 'monthly',
        forecast_horizon_months: 12,
        include_scenarios: true,
        model_type: 'ensemble',
      });
    } catch (error) {
      setError('Failed to create forecast');
      console.error('Error creating forecast:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateModel = async () => {
    try {
      setLoading(true);
      const model = await forecastService.createCostModel(newModelData);
      setCostModels(prev => [...prev, model]);
      setModelDialog(false);
      setNewModelData({
        model_name: '',
        model_type: 'ensemble',
        training_period_months: 12,
        features: [],
        validation_split: 0.2,
      });
    } catch (error) {
      setError('Failed to create model');
      console.error('Error creating model:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderOverviewTab = () => (
    <Grid container spacing={3}>
      {/* Current Spending Overview */}
      {currentSpending && (
        <>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="primary.main">
                  ${currentSpending.current_month?.toLocaleString() || '0'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Current Month Spend
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={(currentSpending.current_month && currentSpending.projected_month_end)
                    ? (currentSpending.current_month / currentSpending.projected_month_end) * 100
                    : 0}
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="warning.main">
                  ${currentSpending.projected_month_end?.toLocaleString() || '0'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Projected Month End
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="success.main">
                  ${currentSpending.budget_remaining?.toLocaleString() || '0'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Budget Remaining
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="error.main">
                  {currentSpending.days_remaining || '0'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Days Remaining at Current Rate
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </>
      )}

      {/* Forecast Accuracy Chart */}
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.primary" mb={2}>Forecast vs Actual Spending</Typography>
            {forecastChartData.length > 0 && (
              <ResponsiveContainer width="100%" height={400}>
                <ComposedChart data={forecastChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" />
                  <YAxis />
                  <ChartTooltip />
                  <Area type="monotone" dataKey="predicted_cost" fill="#8884d8" fillOpacity={0.3} />
                  <Line type="monotone" dataKey="budget_allocated" stroke="#82ca9d" strokeWidth={3} />
                </ComposedChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Budget Alerts */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.primary" mb={2}>Budget Alerts</Typography>
            {Array.isArray(budgetAlerts) ? budgetAlerts.slice(0, 5).map((alert) => (
              <Alert 
                key={alert.id}
                severity={alert.severity as any}
                sx={{ mb: 1 }}
              >
                <Typography variant="body2">{alert.message}</Typography>
              </Alert>
            )) : null}
            {(!Array.isArray(budgetAlerts) || budgetAlerts.length === 0) && (
              <Box display="flex" alignItems="center">
                <CheckCircle color="success" sx={{ mr: 1 }} />
                <Typography variant="body2">No active alerts</Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Monthly Spending Trend */}
      {forecastChartData.length > 0 && (
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.primary" mb={2}>6-Month Budget Projection</Typography>
              <ResponsiveContainer width="100%" height={350}>
                <LineChart data={forecastChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" />
                  <YAxis />
                  <ChartTooltip
                    formatter={(value: any) => `$${value.toLocaleString()}`}
                    labelStyle={{ color: '#000' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="predicted_cost"
                    stroke="#8884d8"
                    strokeWidth={3}
                    name="Projected Cost"
                    dot={{ fill: '#8884d8', r: 5 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="budget_allocated"
                    stroke="#82ca9d"
                    strokeWidth={3}
                    name="Budget Allocated"
                    strokeDasharray="5 5"
                    dot={{ fill: '#82ca9d', r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      )}

      {/* Budget Variance Chart */}
      {forecastChartData.length > 0 && (
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.primary" mb={2}>Monthly Variance</Typography>
              <ResponsiveContainer width="100%" height={350}>
                <RechartsBarChart data={forecastChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" tick={{ fontSize: 10 }} />
                  <YAxis />
                  <ChartTooltip formatter={(value: any) => `$${value.toLocaleString()}`} />
                  <Bar dataKey="variance" fill="#00C49F" name="Budget Remaining" />
                </RechartsBarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      )}

      {/* Top Spending Services */}
      {currentSpending?.top_spending_services && (
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.primary" mb={2}>Top Spending Services</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <RechartsBarChart data={currentSpending.top_spending_services}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="service_name" />
                  <YAxis />
                  <ChartTooltip />
                  <Bar dataKey="monthly_cost" fill="#8884d8" />
                </RechartsBarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      )}
    </Grid>
  );

  const renderForecastsTab = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6" color="text.primary">Cost Forecasts</Typography>
        <Tooltip title="Custom forecast creation coming soon! Use the Overview tab for current projections.">
          <span>
            <Button
              variant="contained"
              startIcon={<PlayArrow />}
              onClick={() => setForecastDialog(true)}
              disabled
            >
              Create Forecast
            </Button>
          </span>
        </Tooltip>
      </Box>

      <Grid container spacing={3}>
        {Array.isArray(forecasts) && forecasts.length > 0 ? forecasts.map((forecast) => (
          <Grid item xs={12} md={6} lg={4} key={forecast.id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6" color="text.primary">{forecast.forecast_name || 'Unnamed Forecast'}</Typography>
                  {forecast.accuracy_score && (
                    <Chip
                      label={`${forecast.accuracy_score.toFixed(1)}% accurate`}
                      color={forecast.accuracy_score >= 80 ? 'success' : 'warning'}
                      size="small"
                    />
                  )}
                </Box>

                <Typography variant="body2" color="text.secondary" mb={2}>
                  Period: {forecast.period || 'monthly'} | Horizon: {forecast.forecast_horizon_months || 12} months
                </Typography>

                {forecast.confidence_interval && (
                  <Box mb={2}>
                    <Typography variant="caption" color="text.secondary">
                      Confidence Interval
                    </Typography>
                    <Typography variant="body2">
                      ${(forecast.confidence_interval.lower_bound || 0).toLocaleString()} -
                      ${(forecast.confidence_interval.upper_bound || 0).toLocaleString()}
                    </Typography>
                  </Box>
                )}

                {forecast.forecast_data && forecast.forecast_data.length > 0 && (
                  <Box height={150}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={forecast.forecast_data.slice(0, 6)}>
                        <Line type="monotone" dataKey="predicted_cost" stroke="#8884d8" strokeWidth={2} />
                        <XAxis dataKey="period" hide />
                        <YAxis hide />
                        <ChartTooltip />
                      </LineChart>
                    </ResponsiveContainer>
                  </Box>
                )}
                
                <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
                  {forecast.last_updated && (
                    <Typography variant="caption" color="text.secondary">
                      Updated: {new Date(forecast.last_updated).toLocaleDateString()}
                    </Typography>
                  )}
                  <Box>
                    <Tooltip title="View Details">
                      <IconButton size="small">
                        <Visibility />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Recalculate">
                      <IconButton size="small">
                        <Refresh />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )) : (
          <Grid item xs={12}>
            <Box textAlign="center" py={6}>
              <Typography variant="h6" color="textSecondary" mb={2}>
                No Custom Forecasts Created
              </Typography>
              <Typography variant="body2" color="textSecondary" mb={3}>
                The Overview tab shows the default 6-month budget projection.
                <br />
                Custom forecasts with advanced scenarios are coming soon!
              </Typography>
            </Box>
          </Grid>
        )}
      </Grid>
    </Box>
  );

  const renderOptimizationTab = () => (
    <Box>
      <Typography variant="h6" color="text.primary" mb={3}>Cost Optimization Opportunities</Typography>
      
      <Grid container spacing={3}>
        {Array.isArray(optimizationOpportunities) && optimizationOpportunities.length > 0 ? optimizationOpportunities.map((opportunity) => (
          <Grid item xs={12} md={6} key={opportunity.id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                  <Typography variant="h6" color="text.primary">{opportunity.title}</Typography>
                  <Chip 
                    label={opportunity.category}
                    size="small"
                    variant="outlined"
                  />
                </Box>
                
                <Typography variant="body2" color="text.secondary" mb={2}>
                  {opportunity.description}
                </Typography>
                
                <Grid container spacing={2} mb={2}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Monthly Savings
                    </Typography>
                    <Typography variant="h6" color="success.main">
                      ${(opportunity.potential_savings || 0).toLocaleString()}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Annual Savings
                    </Typography>
                    <Typography variant="h6" color="success.main">
                      ${((opportunity.potential_savings || 0) * 12).toLocaleString()}
                    </Typography>
                  </Grid>
                </Grid>

                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Box>
                    <Chip
                      label={`Impact: ${opportunity.impact || 'medium'}`}
                      size="small"
                      color={
                        opportunity.impact === 'low' ? 'info' :
                        opportunity.impact === 'medium' ? 'warning' : 'error'
                      }
                      sx={{ mr: 1 }}
                    />
                    <Chip
                      label={`Effort: ${opportunity.effort || 'medium'}`}
                      size="small"
                      color={
                        opportunity.effort === 'low' ? 'success' :
                        opportunity.effort === 'medium' ? 'warning' : 'error'
                      }
                    />
                  </Box>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => {
                      setSelectedOpportunity(opportunity);
                      setOpportunityDetailsDialog(true);
                    }}
                  >
                    View Details
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )) : (
          <Grid item xs={12}>
            <Box textAlign="center" py={3}>
              <Typography color="textSecondary">
                No optimization opportunities available
              </Typography>
            </Box>
          </Grid>
        )}
      </Grid>
    </Box>
  );

  const renderModelsTab = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6" color="text.primary">AI Cost Models</Typography>
        <Button 
          variant="contained" 
          startIcon={<ModelTraining />}
          onClick={() => setModelDialog(true)}
        >
          Create Model
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Model Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Accuracy Score</TableCell>
              <TableCell>Last Trained</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Array.isArray(costModels) && costModels.length > 0 ? costModels.map((model) => (
              <TableRow key={model.id}>
                <TableCell>{model.model_name}</TableCell>
                <TableCell>
                  <Chip label={model.model_type} size="small" variant="outlined" />
                </TableCell>
                <TableCell>
                  <Box display="flex" alignItems="center">
                    <Typography variant="body2" sx={{ mr: 1 }}>
                      {(model.accuracy_metrics.accuracy_score * 100).toFixed(1)}%
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={model.accuracy_metrics.accuracy_score * 100}
                      sx={{ width: 60 }}
                    />
                  </Box>
                </TableCell>
                <TableCell>
                  {new Date(model.last_retrained).toLocaleDateString()}
                </TableCell>
                <TableCell>
                  <Chip 
                    label="Active"
                    color="success"
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Tooltip title="Train Model">
                    <IconButton
                      size="small"
                      onClick={() => {
                        alert(`Training ${model.model_name}...\nThis would trigger model retraining in production.`);
                      }}
                    >
                      <PlayArrow />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="View Performance">
                    <IconButton
                      size="small"
                      onClick={() => {
                        setSelectedModel(model);
                        setModelPerformanceDialog(true);
                      }}
                    >
                      <Analytics />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Configure">
                    <IconButton
                      size="small"
                      onClick={() => {
                        alert(`Configure ${model.model_name}\nHyperparameters and training settings would be adjustable here.`);
                      }}
                    >
                      <Settings />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            )) : (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography color="textSecondary">
                    No cost models available
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );

  if (!assessmentId) {
    const AssessmentSelector = require('./AssessmentSelector').default;
    return (
      <AssessmentSelector
        redirectPath="/budget-forecasting"
        title="Select Assessment for Budget Forecasting"
        description="Choose an assessment to view budget forecasting data"
      />
    );
  }

  return (
    <Box sx={{ mt: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
        <Box>
          <Typography variant="h4" color="text.primary" gutterBottom>
            Budget Forecasting
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            AI-powered infrastructure cost predictions and optimization •
            <Chip
              label={isStale ? "Data may be outdated" : "Live data"}
              size="small"
              color={isStale ? "warning" : "success"}
              variant="outlined"
              sx={{ ml: 1 }}
            />
          </Typography>
        </Box>
        <Tooltip title={`Last updated: ${new Date(lastRefresh).toLocaleTimeString()}`}>
          <IconButton
            onClick={refreshBudgetData}
            color="primary"
            size="large"
          >
            <Refresh />
          </IconButton>
        </Tooltip>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab label="Overview" icon={<Analytics />} />
        <Tab label="Forecasts" icon={<Timeline />} />
        <Tab label="Optimization" icon={<TrendingUp />} />
        <Tab label="AI Models" icon={<ModelTraining />} />
      </Tabs>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <TabPanel value={tabValue} index={0}>
        {renderOverviewTab()}
      </TabPanel>
      
      <TabPanel value={tabValue} index={1}>
        {renderForecastsTab()}
      </TabPanel>
      
      <TabPanel value={tabValue} index={2}>
        {renderOptimizationTab()}
      </TabPanel>
      
      <TabPanel value={tabValue} index={3}>
        {renderModelsTab()}
      </TabPanel>

      {/* Create Forecast Dialog */}
      <Dialog open={forecastDialog} onClose={() => setForecastDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Cost Forecast</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Forecast Name"
                value={newForecastData.forecast_name}
                onChange={(e) => setNewForecastData({ ...newForecastData, forecast_name: e.target.value })}
              />
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Period</InputLabel>
                <Select
                  value={newForecastData.period}
                  onChange={(e) => setNewForecastData({ ...newForecastData, period: e.target.value as any })}
                >
                  <MenuItem value="monthly">Monthly</MenuItem>
                  <MenuItem value="quarterly">Quarterly</MenuItem>
                  <MenuItem value="annual">Annual</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                type="number"
                label="Forecast Horizon (Months)"
                value={newForecastData.forecast_horizon_months}
                onChange={(e) => setNewForecastData({ ...newForecastData, forecast_horizon_months: parseInt(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Model Type</InputLabel>
                <Select
                  value={newForecastData.model_type}
                  onChange={(e) => setNewForecastData({ ...newForecastData, model_type: e.target.value })}
                >
                  <MenuItem value="linear_regression">Linear Regression</MenuItem>
                  <MenuItem value="arima">ARIMA</MenuItem>
                  <MenuItem value="prophet">Prophet</MenuItem>
                  <MenuItem value="neural_network">Neural Network</MenuItem>
                  <MenuItem value="ensemble">Ensemble</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={newForecastData.include_scenarios}
                    onChange={(e) => setNewForecastData({ ...newForecastData, include_scenarios: e.target.checked })}
                  />
                }
                label="Include Scenario Analysis"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setForecastDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateForecast} 
            variant="contained"
            disabled={!newForecastData.forecast_name}
          >
            Create Forecast
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Model Dialog */}
      <Dialog open={modelDialog} onClose={() => setModelDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New AI Model</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Model Name"
                value={newModelData.model_name}
                onChange={(e) => setNewModelData({ ...newModelData, model_name: e.target.value })}
              />
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Model Type</InputLabel>
                <Select
                  value={newModelData.model_type}
                  onChange={(e) => setNewModelData({ ...newModelData, model_type: e.target.value })}
                >
                  <MenuItem value="linear_regression">Linear Regression</MenuItem>
                  <MenuItem value="polynomial">Polynomial</MenuItem>
                  <MenuItem value="arima">ARIMA</MenuItem>
                  <MenuItem value="prophet">Prophet</MenuItem>
                  <MenuItem value="neural_network">Neural Network</MenuItem>
                  <MenuItem value="ensemble">Ensemble</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                type="number"
                label="Training Period (Months)"
                value={newModelData.training_period_months}
                onChange={(e) => setNewModelData({ ...newModelData, training_period_months: parseInt(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                type="number"
                step="0.1"
                label="Validation Split"
                value={newModelData.validation_split}
                onChange={(e) => setNewModelData({ ...newModelData, validation_split: parseFloat(e.target.value) })}
                inputProps={{ min: 0.1, max: 0.5 }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setModelDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateModel} 
            variant="contained"
            disabled={!newModelData.model_name}
          >
            Create Model
          </Button>
        </DialogActions>
      </Dialog>

      {/* Model Performance Dialog */}
      <Dialog
        open={modelPerformanceDialog}
        onClose={() => setModelPerformanceDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedModel?.model_name} - Performance Metrics
        </DialogTitle>
        <DialogContent>
          {selectedModel && (
            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>Accuracy Metrics</Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6} md={3}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" variant="body2">Accuracy Score</Typography>
                        <Typography variant="h5">{(selectedModel.accuracy_metrics.accuracy_score * 100).toFixed(1)}%</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" variant="body2">MAE</Typography>
                        <Typography variant="h5">${selectedModel.accuracy_metrics.mae.toLocaleString()}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" variant="body2">RMSE</Typography>
                        <Typography variant="h5">${selectedModel.accuracy_metrics.rmse.toLocaleString()}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" variant="body2">R²</Typography>
                        <Typography variant="h5">{selectedModel.accuracy_metrics.r_squared.toFixed(3)}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>Feature Importance</Typography>
                {selectedModel.feature_importance.map((feature, idx) => (
                  <Box key={idx} mb={2}>
                    <Box display="flex" justifyContent="space-between" mb={0.5}>
                      <Typography variant="body2">{feature.feature}</Typography>
                      <Typography variant="body2">{(feature.importance * 100).toFixed(0)}%</Typography>
                    </Box>
                    <LinearProgress variant="determinate" value={feature.importance * 100} />
                  </Box>
                ))}
              </Grid>

              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>Hyperparameters</Typography>
                <TableContainer component={Paper}>
                  <Table size="small">
                    <TableBody>
                      {Object.entries(selectedModel.hyperparameters).map(([key, value]) => (
                        <TableRow key={key}>
                          <TableCell><strong>{key}</strong></TableCell>
                          <TableCell>{String(value)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setModelPerformanceDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Optimization Opportunity Details Dialog */}
      <Dialog
        open={opportunityDetailsDialog}
        onClose={() => setOpportunityDetailsDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {selectedOpportunity?.title}
        </DialogTitle>
        <DialogContent>
          {selectedOpportunity && (
            <Box sx={{ mt: 2 }}>
              <Chip label={selectedOpportunity.category} color="primary" size="small" sx={{ mb: 2 }} />

              <Typography variant="body1" paragraph>
                {selectedOpportunity.description}
              </Typography>

              <Grid container spacing={2} sx={{ my: 2 }}>
                <Grid item xs={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography color="textSecondary" variant="caption">Monthly Savings</Typography>
                      <Typography variant="h6" color="success.main">
                        ${(selectedOpportunity.potential_savings || 0).toLocaleString()}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography color="textSecondary" variant="caption">Annual Savings</Typography>
                      <Typography variant="h6" color="success.main">
                        ${((selectedOpportunity.potential_savings || 0) * 12).toLocaleString()}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              <Box sx={{ my: 2 }}>
                <Typography variant="body2" gutterBottom><strong>Impact:</strong> {selectedOpportunity.impact}</Typography>
                <Typography variant="body2" gutterBottom><strong>Effort:</strong> {selectedOpportunity.effort}</Typography>
                <Typography variant="body2" gutterBottom><strong>Category:</strong> {selectedOpportunity.category}</Typography>
              </Box>

              <Alert severity="info" sx={{ mt: 2 }}>
                <strong>Next Steps:</strong> Review the affected resources and create an implementation plan. Contact your infrastructure team to begin optimization.
              </Alert>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpportunityDetailsDialog(false)}>Close</Button>
          <Button variant="contained" color="primary">
            Create Implementation Plan
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BudgetForecasting;