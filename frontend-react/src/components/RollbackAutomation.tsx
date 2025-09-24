'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Chip,
  LinearProgress,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  Stepper,
  Step,
  StepLabel,
  Divider,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  History,
  Assessment,
  Settings,
  CheckCircle,
  Error,
  Warning,
  Info,
  Visibility,
  Edit,
  Delete,
  Schedule,
  Timeline,
  TrendingUp,
  Security,
  CloudQueue,
  Speed,
  ExpandMore,
  Refresh,
  Download,
  Upload,
} from '@mui/icons-material';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as ChartTooltip, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import { getRollbackService, RollbackPlan, DeploymentInfo, RollbackExecution, HealthCheck, AutoTrigger, ValidationProcedure, DRPlan, RollbackMetrics, HealthMetric, RollbackTemplate } from '../services/rollbackAutomation';

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

const RollbackAutomation: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rollbackService] = useState(() => getRollbackService());

  // State for different sections
  const [deployments, setDeployments] = useState<DeploymentInfo[]>([]);
  const [rollbackPlans, setRollbackPlans] = useState<RollbackPlan[]>([]);
  const [executions, setExecutions] = useState<RollbackExecution[]>([]);
  const [healthChecks, setHealthChecks] = useState<HealthCheck[]>([]);
  const [autoTriggers, setAutoTriggers] = useState<AutoTrigger[]>([]);
  const [templates, setTemplates] = useState<RollbackTemplate[]>([]);
  const [metrics, setMetrics] = useState<RollbackMetrics | null>(null);

  // Dialog states
  const [createPlanDialog, setCreatePlanDialog] = useState(false);
  const [executionDialog, setExecutionDialog] = useState(false);
  const [selectedDeployment, setSelectedDeployment] = useState<string>('');
  const [selectedRollbackPlan, setSelectedRollbackPlan] = useState<RollbackPlan | null>(null);
  const [executionInProgress, setExecutionInProgress] = useState(false);

  // Form states
  const [newPlanData, setNewPlanData] = useState({
    name: '',
    deployment_id: '',
    rollback_strategy: 'blue_green',
    description: '',
    automated: false,
  });

  const rollbackStrategies = ['blue_green', 'canary', 'rolling', 'instant', 'custom'];
  const statusColors = {
    pending: '#ff9800',
    in_progress: '#2196f3',
    completed: '#4caf50',
    failed: '#f44336',
    cancelled: '#9e9e9e',
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [deploymentsData, plansData, executionsData, healthData, triggersData, templatesData, metricsData] = await Promise.all([
        rollbackService.getDeployments(),
        rollbackService.getRollbackPlans(),
        rollbackService.getRollbackExecutions(),
        rollbackService.getHealthChecks(),
        rollbackService.getAutoTriggers(),
        rollbackService.getTemplates(),
        rollbackService.getMetrics('7d'),
      ]);

      // Ensure all data is in array format
      setDeployments(Array.isArray(deploymentsData) ? deploymentsData : []);
      setRollbackPlans(Array.isArray(plansData) ? plansData : []);
      setExecutions(Array.isArray(executionsData) ? executionsData : []);
      setHealthChecks(Array.isArray(healthData) ? healthData : []);
      setAutoTriggers(Array.isArray(triggersData) ? triggersData : []);
      setTemplates(Array.isArray(templatesData) ? templatesData : []);
      setMetrics(metricsData || {});
    } catch (error) {
      setError('Failed to load rollback data');
      console.error('Error loading rollback data:', error);
      // Set empty arrays as fallback
      setDeployments([]);
      setRollbackPlans([]);
      setExecutions([]);
      setHealthChecks([]);
      setAutoTriggers([]);
      setTemplates([]);
      setMetrics({});
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRollbackPlan = async () => {
    try {
      setLoading(true);
      const plan = await rollbackService.createRollbackPlan({
        ...newPlanData,
        target_version: 'latest',
        validation_steps: [],
        health_checks: [],
        notification_settings: {
          channels: ['email'],
          recipients: [],
          on_start: true,
          on_complete: true,
          on_failure: true,
        },
      });
      
      setRollbackPlans(prev => [...prev, plan]);
      setCreatePlanDialog(false);
      setNewPlanData({
        name: '',
        deployment_id: '',
        rollback_strategy: 'blue_green',
        description: '',
        automated: false,
      });
    } catch (error) {
      setError('Failed to create rollback plan');
      console.error('Error creating rollback plan:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteRollback = async () => {
    if (!selectedRollbackPlan) return;
    
    try {
      setExecutionInProgress(true);
      const execution = await rollbackService.executeRollback(selectedRollbackPlan.id, {
        force_rollback: false,
        skip_health_checks: false,
        notification_channels: ['email'],
      });
      
      setExecutions(prev => [...prev, execution]);
      setExecutionDialog(false);
      setSelectedRollbackPlan(null);
    } catch (error) {
      setError('Failed to execute rollback');
      console.error('Error executing rollback:', error);
    } finally {
      setExecutionInProgress(false);
    }
  };

  const renderDeploymentsTab = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">Active Deployments</Typography>
          <Button startIcon={<Refresh />} onClick={loadInitialData} disabled={loading}>
            Refresh
          </Button>
        </Box>
      </Grid>
      
      {Array.isArray(deployments) ? deployments.map((deployment) => (
        <Grid item xs={12} md={6} lg={4} key={deployment.id}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" noWrap>{deployment.name}</Typography>
                <Chip 
                  label={deployment.status} 
                  color={deployment.status === 'success' ? 'success' : deployment.status === 'failed' ? 'error' : 'default'}
                  size="small"
                />
              </Box>
              
              <Typography variant="body2" color="text.secondary" mb={1}>
                Environment: {deployment.environment}
              </Typography>
              <Typography variant="body2" color="text.secondary" mb={1}>
                Version: {deployment.version}
              </Typography>
              <Typography variant="body2" color="text.secondary" mb={2}>
                Deployed: {new Date(deployment.deployed_at).toLocaleString()}
              </Typography>
              
              <Box display="flex" justifyContent="space-between">
                <Button 
                  size="small" 
                  startIcon={<PlayArrow />}
                  onClick={() => {
                    setSelectedDeployment(deployment.id);
                    setCreatePlanDialog(true);
                  }}
                >
                  Create Rollback Plan
                </Button>
                <Button size="small" startIcon={<Assessment />}>
                  Health Check
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      )) : (
        <Grid item xs={12}>
          <Alert severity="info">No deployments available</Alert>
        </Grid>
      )}
    </Grid>
  );

  const renderRollbackPlansTab = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Rollback Plans</Typography>
        <Button 
          variant="contained" 
          startIcon={<PlayArrow />}
          onClick={() => setCreatePlanDialog(true)}
        >
          Create New Plan
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Deployment</TableCell>
              <TableCell>Strategy</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Array.isArray(rollbackPlans) ? rollbackPlans.map((plan) => (
              <TableRow key={plan.id}>
                <TableCell>{plan.name}</TableCell>
                <TableCell>{plan.deployment_id}</TableCell>
                <TableCell>
                  <Chip label={plan.rollback_strategy} size="small" variant="outlined" />
                </TableCell>
                <TableCell>
                  <Chip 
                    label={plan.status} 
                    size="small"
                    color={plan.status === 'ready' ? 'success' : 'default'}
                  />
                </TableCell>
                <TableCell>{new Date(plan.created_at).toLocaleDateString()}</TableCell>
                <TableCell>
                  <Tooltip title="Execute Rollback">
                    <IconButton 
                      size="small" 
                      onClick={() => {
                        setSelectedRollbackPlan(plan);
                        setExecutionDialog(true);
                      }}
                    >
                      <PlayArrow />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="View Details">
                    <IconButton size="small">
                      <Visibility />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Delete Plan">
                    <IconButton size="small" color="error">
                      <Delete />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            )) : (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Alert severity="info">No rollback plans available</Alert>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );

  const renderExecutionHistoryTab = () => (
    <Box>
      <Typography variant="h6" mb={3}>Execution History</Typography>
      
      {Array.isArray(executions) ? executions.map((execution) => (
        <Card key={execution.id} sx={{ mb: 2 }}>
          <CardContent>
            <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
              <Typography variant="h6">{execution.rollback_plan_id}</Typography>
              <Chip 
                label={execution.status}
                color={execution.status === 'completed' ? 'success' : execution.status === 'failed' ? 'error' : 'default'}
              />
            </Box>
            
            <Typography variant="body2" color="text.secondary" mb={1}>
              Started: {new Date(execution.started_at).toLocaleString()}
            </Typography>
            {execution.completed_at && (
              <Typography variant="body2" color="text.secondary" mb={2}>
                Completed: {new Date(execution.completed_at).toLocaleString()}
              </Typography>
            )}
            
            <LinearProgress 
              variant="determinate" 
              value={execution.progress_percentage} 
              sx={{ mb: 2 }}
            />
            <Typography variant="body2" mb={2}>
              Progress: {execution.progress_percentage}%
            </Typography>
            
            {execution.error_message && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {execution.error_message}
              </Alert>
            )}
            
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>Execution Steps</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Stepper orientation="vertical" activeStep={-1}>
                  {Array.isArray(execution.execution_steps) ? execution.execution_steps.map((step, index) => (
                    <Step key={index} completed={step.status === 'completed'}>
                      <StepLabel 
                        error={step.status === 'failed'}
                        icon={
                          step.status === 'completed' ? <CheckCircle /> :
                          step.status === 'failed' ? <Error /> :
                          step.status === 'in_progress' ? <CircularProgress size={24} /> :
                          <Schedule />
                        }
                      >
                        {step.step_name}
                      </StepLabel>
                      {step.error_message && (
                        <Typography variant="body2" color="error" sx={{ ml: 4 }}>
                          {step.error_message}
                        </Typography>
                      )}
                    </Step>
                  )) : (
                    <Typography color="textSecondary">No execution steps available</Typography>
                  )}
                </Stepper>
              </AccordionDetails>
            </Accordion>
          </CardContent>
        </Card>
      )) : (
        <Alert severity="info">No execution history available</Alert>
      )}
    </Box>
  );

  const renderHealthMonitoringTab = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" mb={2}>System Health Overview</Typography>
            {healthChecks.length > 0 && (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={healthChecks.slice(0, 10)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <ChartTooltip />
                  <Line type="monotone" dataKey="health_score" stroke="#8884d8" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" mb={2}>Health Metrics</Typography>
            <List>
              {Array.isArray(healthChecks) ? healthChecks.slice(0, 5).map((check, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    {check.status === 'healthy' ? <CheckCircle color="success" /> :
                     check.status === 'unhealthy' ? <Error color="error" /> :
                     <Warning color="warning" />}
                  </ListItemIcon>
                  <ListItemText 
                    primary={check.check_name}
                    secondary={`Score: ${check.health_score}/100`}
                  />
                </ListItem>
              )) : (
                <ListItem>
                  <ListItemText primary="No health checks available" />
                </ListItem>
              )}
            </List>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" mb={2}>Auto-Trigger Rules</Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Rule Name</TableCell>
                    <TableCell>Condition</TableCell>
                    <TableCell>Action</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Array.isArray(autoTriggers) ? autoTriggers.map((trigger) => (
                    <TableRow key={trigger.id}>
                      <TableCell>{trigger.name}</TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {trigger.conditions.health_threshold && `Health < ${trigger.conditions.health_threshold}%`}
                          {trigger.conditions.error_rate_threshold && ` | Error Rate > ${trigger.conditions.error_rate_threshold}%`}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={trigger.action_type} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>
                        <FormControlLabel
                          control={<Switch checked={trigger.enabled} size="small" />}
                          label={trigger.enabled ? 'Enabled' : 'Disabled'}
                        />
                      </TableCell>
                      <TableCell>
                        <IconButton size="small">
                          <Edit />
                        </IconButton>
                        <IconButton size="small" color="error">
                          <Delete />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  )) : (
                    <TableRow>
                      <TableCell colSpan={5} align="center">
                        <Alert severity="info">No auto-trigger rules configured</Alert>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderAnalyticsTab = () => (
    <Grid container spacing={3}>
      {metrics && (
        <>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <TrendingUp color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Success Rate</Typography>
                </Box>
                <Typography variant="h4" color="success.main">
                  {metrics.success_rate ? metrics.success_rate.toFixed(1) : '0.0'}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <Speed color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Avg Duration</Typography>
                </Box>
                <Typography variant="h4">
                  {metrics.average_duration || '0 min'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <History color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Total Executions</Typography>
                </Box>
                <Typography variant="h4">
                  {metrics.total_executions || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <Error color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Failed Executions</Typography>
                </Box>
                <Typography variant="h4" color="error.main">
                  {metrics.failed_executions || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" mb={2}>Rollback Trends</Typography>
                {metrics.execution_trends && metrics.execution_trends.length > 0 && (
                  <ResponsiveContainer width="100%" height={400}>
                    <AreaChart data={metrics.execution_trends}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <ChartTooltip />
                      <Area type="monotone" dataKey="successful" stackId="1" stroke="#4caf50" fill="#4caf50" />
                      <Area type="monotone" dataKey="failed" stackId="1" stroke="#f44336" fill="#f44336" />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" mb={2}>Rollback by Strategy</Typography>
                {metrics.strategy_distribution && metrics.strategy_distribution.length > 0 && (
                  <ResponsiveContainer width="100%" height={400}>
                    <PieChart>
                      <Pie
                        data={metrics.strategy_distribution}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="count"
                      >
                        {Array.isArray(metrics?.strategy_distribution) ? metrics.strategy_distribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={`hsl(${index * 45}, 70%, 50%)`} />
                        )) : null}
                      </Pie>
                      <ChartTooltip />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
          </Grid>
        </>
      )}
    </Grid>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Rollback Automation
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" mb={3}>
        Manage automated rollback procedures and monitoring
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab label="Deployments" icon={<CloudQueue />} />
        <Tab label="Rollback Plans" icon={<Timeline />} />
        <Tab label="Execution History" icon={<History />} />
        <Tab label="Health Monitoring" icon={<Assessment />} />
        <Tab label="Analytics" icon={<TrendingUp />} />
      </Tabs>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <TabPanel value={tabValue} index={0}>
        {renderDeploymentsTab()}
      </TabPanel>
      
      <TabPanel value={tabValue} index={1}>
        {renderRollbackPlansTab()}
      </TabPanel>
      
      <TabPanel value={tabValue} index={2}>
        {renderExecutionHistoryTab()}
      </TabPanel>
      
      <TabPanel value={tabValue} index={3}>
        {renderHealthMonitoringTab()}
      </TabPanel>
      
      <TabPanel value={tabValue} index={4}>
        {renderAnalyticsTab()}
      </TabPanel>

      {/* Create Rollback Plan Dialog */}
      <Dialog open={createPlanDialog} onClose={() => setCreatePlanDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create Rollback Plan</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Plan Name"
                value={newPlanData.name}
                onChange={(e) => setNewPlanData({ ...newPlanData, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Deployment</InputLabel>
                <Select
                  value={newPlanData.deployment_id}
                  onChange={(e) => setNewPlanData({ ...newPlanData, deployment_id: e.target.value })}
                >
                  {Array.isArray(deployments) ? deployments.map((deployment) => (
                    <MenuItem key={deployment.id} value={deployment.id}>
                      {deployment.name} ({deployment.environment})
                    </MenuItem>
                  )) : (
                    <MenuItem value="">No deployments available</MenuItem>
                  )}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Rollback Strategy</InputLabel>
                <Select
                  value={newPlanData.rollback_strategy}
                  onChange={(e) => setNewPlanData({ ...newPlanData, rollback_strategy: e.target.value })}
                >
                  {Array.isArray(rollbackStrategies) ? rollbackStrategies.map((strategy) => (
                    <MenuItem key={strategy} value={strategy}>
                      {strategy.replace('_', ' ').toUpperCase()}
                    </MenuItem>
                  )) : (
                    <MenuItem value="">No strategies available</MenuItem>
                  )}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Description"
                value={newPlanData.description}
                onChange={(e) => setNewPlanData({ ...newPlanData, description: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={newPlanData.automated}
                    onChange={(e) => setNewPlanData({ ...newPlanData, automated: e.target.checked })}
                  />
                }
                label="Enable Automated Execution"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreatePlanDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateRollbackPlan} 
            variant="contained"
            disabled={!newPlanData.name || !newPlanData.deployment_id}
          >
            Create Plan
          </Button>
        </DialogActions>
      </Dialog>

      {/* Execute Rollback Dialog */}
      <Dialog open={executionDialog} onClose={() => setExecutionDialog(false)}>
        <DialogTitle>Execute Rollback</DialogTitle>
        <DialogContent>
          <Typography variant="body1" mb={2}>
            Are you sure you want to execute the rollback plan "{selectedRollbackPlan?.name}"?
          </Typography>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This action will rollback the deployment and may cause temporary service disruption.
          </Alert>
          {selectedRollbackPlan && (
            <Box>
              <Typography variant="body2" mb={1}>
                <strong>Strategy:</strong> {selectedRollbackPlan.rollback_strategy}
              </Typography>
              <Typography variant="body2" mb={1}>
                <strong>Target Version:</strong> {selectedRollbackPlan.target_version}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExecutionDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleExecuteRollback}
            variant="contained"
            color="warning"
            disabled={executionInProgress}
            startIcon={executionInProgress ? <CircularProgress size={20} /> : <PlayArrow />}
          >
            {executionInProgress ? 'Executing...' : 'Execute Rollback'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RollbackAutomation;