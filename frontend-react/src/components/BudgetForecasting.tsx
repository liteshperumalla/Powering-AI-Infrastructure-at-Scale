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
  const [budgetAllocations, setBudgetAllocations] = useState<BudgetAllocation[]>([]);
  const [optimizationOpportunities, setOptimizationOpportunities] = useState<OptimizationOpportunity[]>([]);
  const [costModels, setCostModels] = useState<CostModel[]>([]);
  const [budgetAlerts, setBudgetAlerts] = useState<BudgetAlert[]>([]);
  const [currentSpending, setCurrentSpending] = useState<any>(null);

  // Dialog states
  const [forecastDialog, setForecastDialog] = useState(false);
  const [modelDialog, setModelDialog] = useState(false);
  const [allocationDialog, setAllocationDialog] = useState(false);
  
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

      // Map the API response to component state
      // The API returns budget forecasting data in the format we need
      setCurrentSpending(budgetData.summary || {});
      setOptimizationOpportunities(budgetData.recommendations || []);
      setBudgetAllocations(budgetData.breakdown || []);
      setForecasts(budgetData.forecasts || []);
      setCostModels(budgetData.models || []);
      setBudgetAlerts(budgetData.alerts || []);

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
                  ${currentSpending.current_month_spend?.toLocaleString() || '0'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Current Month Spend
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={(currentSpending.current_month_spend && currentSpending.projected_month_end) 
                    ? (currentSpending.current_month_spend / currentSpending.projected_month_end) * 100 
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
                  {currentSpending.days_remaining_at_current_rate || '0'}
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
            {forecasts.length > 0 && forecasts[0].forecast_data.length > 0 && (
              <ResponsiveContainer width="100%" height={400}>
                <ComposedChart data={forecasts[0].forecast_data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" />
                  <YAxis />
                  <ChartTooltip />
                  <Area type="monotone" dataKey="predicted_cost" fill="#8884d8" fillOpacity={0.3} />
                  <Line type="monotone" dataKey="actual_cost" stroke="#82ca9d" strokeWidth={3} />
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
        <Button 
          variant="contained" 
          startIcon={<PlayArrow />}
          onClick={() => setForecastDialog(true)}
        >
          Create Forecast
        </Button>
      </Box>

      <Grid container spacing={3}>
        {Array.isArray(forecasts) && forecasts.length > 0 ? forecasts.map((forecast) => (
          <Grid item xs={12} md={6} lg={4} key={forecast.id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6" color="text.primary">{forecast.forecast_name}</Typography>
                  <Chip 
                    label={`${forecast.accuracy_score.toFixed(1)}% accurate`}
                    color={forecast.accuracy_score >= 80 ? 'success' : 'warning'}
                    size="small"
                  />
                </Box>
                
                <Typography variant="body2" color="text.secondary" mb={2}>
                  Period: {forecast.period} | Horizon: {forecast.forecast_horizon_months} months
                </Typography>
                
                <Box mb={2}>
                  <Typography variant="caption" color="text.secondary">
                    Confidence Interval
                  </Typography>
                  <Typography variant="body2">
                    ${forecast.confidence_interval.lower_bound.toLocaleString()} - 
                    ${forecast.confidence_interval.upper_bound.toLocaleString()}
                  </Typography>
                </Box>
                
                {forecast.forecast_data.length > 0 && (
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
                  <Typography variant="caption" color="text.secondary">
                    Updated: {new Date(forecast.last_updated).toLocaleDateString()}
                  </Typography>
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
            <Box textAlign="center" py={3}>
              <Typography color="textSecondary">
                No forecasts available
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
                      Potential Savings
                    </Typography>
                    <Typography variant="h6" color="success.main">
                      ${opportunity.potential_savings.toLocaleString()}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Annual Savings
                    </Typography>
                    <Typography variant="h6" color="success.main">
                      ${opportunity.annual_savings_potential.toLocaleString()}
                    </Typography>
                  </Grid>
                </Grid>
                
                <Box mb={2}>
                  <Typography variant="body2" mb={1}>
                    ROI Analysis
                  </Typography>
                  <Typography variant="caption">
                    Payback: {opportunity.roi_analysis.payback_period_months} months | 
                    NPV: ${opportunity.roi_analysis.net_present_value.toLocaleString()} | 
                    IRR: {opportunity.roi_analysis.internal_rate_of_return.toFixed(1)}%
                  </Typography>
                </Box>
                
                <Box display="flex" justify="space-between" alignItems="center">
                  <Box>
                    <Chip 
                      label={opportunity.implementation_effort}
                      size="small"
                      color={
                        opportunity.implementation_effort === 'low' ? 'success' :
                        opportunity.implementation_effort === 'medium' ? 'warning' : 'error'
                      }
                    />
                    <Chip 
                      label={opportunity.risk_level}
                      size="small"
                      color={
                        opportunity.risk_level === 'low' ? 'success' :
                        opportunity.risk_level === 'medium' ? 'warning' : 'error'
                      }
                      sx={{ ml: 1 }}
                    />
                  </Box>
                  <Button size="small" variant="outlined">
                    Implement
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
                    <IconButton size="small">
                      <PlayArrow />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="View Performance">
                    <IconButton size="small">
                      <Analytics />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Configure">
                    <IconButton size="small">
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
    </Box>
  );
};

export default BudgetForecasting;