'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Tabs,
  Tab,
  Button,
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Avatar,
  AvatarGroup,
  Badge,
  Divider,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AttachMoney,
  Speed,
  Security,
  Assessment,
  Warning,
  CheckCircle,
  Error,
  Info,
  Timeline,
  PieChart,
  BarChart,
  Download,
  Refresh as RefreshIcon,
  Visibility,
  Business,
  Analytics,
  AccountBalance,
  Gavel,
  CloudQueue,
} from '@mui/icons-material';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as ChartTooltip, AreaChart, Area, PieChart as RechartsPieChart, Pie, Cell, BarChart as RechartsBarChart, Bar } from 'recharts';
import { getExecutiveDashboardService, ExecutiveMetric, KPICard, ExecutiveSummary, StrategicInitiative, RiskFactor, BusinessUnit } from '../services/executiveDashboard';

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

interface ExecutiveDashboardProps {
  assessmentId?: string;
}

const ExecutiveDashboard: React.FC<ExecutiveDashboardProps> = ({ assessmentId }) => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [executiveService] = useState(() => getExecutiveDashboardService());

  // State for different sections
  const [executiveMetrics, setExecutiveMetrics] = useState<ExecutiveMetric[]>([]);
  const [kpiCards, setKpiCards] = useState<KPICard[]>([]);
  const [executiveSummary, setExecutiveSummary] = useState<ExecutiveSummary | null>(null);
  const [strategicInitiatives, setStrategicInitiatives] = useState<StrategicInitiative[]>([]);
  const [riskFactors, setRiskFactors] = useState<RiskFactor[]>([]);
  const [businessUnits, setBusinessUnits] = useState<BusinessUnit[]>([]);

  // Dialog states
  const [initiativeDialog, setInitiativeDialog] = useState(false);
  const [riskDialog, setRiskDialog] = useState(false);
  const [selectedInitiative, setSelectedInitiative] = useState<StrategicInitiative | null>(null);
  const [selectedRisk, setSelectedRisk] = useState<RiskFactor | null>(null);

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  useEffect(() => {
    loadExecutiveData();
  }, []);

  const loadExecutiveData = async () => {
    setLoading(true);
    try {
      // Load data with individual error handling instead of Promise.all
      let metricsData: ExecutiveMetric[] = [];
      let kpiData: KPICard[] = [];
      let summaryData: any = null;
      let initiativesData: StrategicInitiative[] = [];
      let riskData: RiskFactor[] = [];
      let businessUnitsData: BusinessUnit[] = [];

      // Load each data source individually with try-catch
      try {
        metricsData = await executiveService.getExecutiveMetrics('30d');
      } catch (error) {
        console.warn('Failed to load executive metrics, using fallback data:', error);
        metricsData = [];
      }

      try {
        kpiData = await executiveService.getKPIDashboard();
      } catch (error) {
        console.warn('Failed to load KPI dashboard, using fallback data:', error);
        kpiData = [];
      }

      try {
        summaryData = await executiveService.getExecutiveSummary('monthly');
      } catch (error) {
        console.warn('Failed to load executive summary, using fallback data:', error);
        summaryData = null;
      }

      try {
        initiativesData = await executiveService.getStrategicInitiatives();
      } catch (error) {
        console.warn('Failed to load strategic initiatives, using fallback data:', error);
        initiativesData = [];
      }

      try {
        const riskDashboard = await executiveService.getRiskDashboard();
        riskData = riskDashboard.top_risks || [];
      } catch (error) {
        console.warn('Failed to load risk dashboard, using fallback data:', error);
        riskData = [];
      }

      try {
        businessUnitsData = await executiveService.getBusinessUnits();
      } catch (error) {
        console.warn('Failed to load business units, using fallback data:', error);
        businessUnitsData = [];
      }

      setExecutiveMetrics(metricsData);
      setKpiCards(kpiData);
      setExecutiveSummary(summaryData);
      setStrategicInitiatives(initiativesData);
      setRiskFactors(riskData);
      setBusinessUnits(businessUnitsData);
    } catch (error) {
      setError('Failed to load executive dashboard data');
      console.error('Error loading executive data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <TrendingUp color="success" />;
      case 'down':
        return <TrendingDown color="error" />;
      default:
        return <Timeline color="info" />;
    }
  };

  const getAlertColor = (level: 'none' | 'info' | 'warning' | 'critical') => {
    switch (level) {
      case 'critical':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      default:
        return 'default';
    }
  };

  const renderOverviewTab = () => (
    <Grid container spacing={3}>
      {/* Key Metrics Cards */}
      <Grid item xs={12}>
        <Typography variant="h6" color="text.primary" mb={2}>Key Performance Indicators</Typography>
        <Grid container spacing={2}>
          {kpiCards.slice(0, 4).map((kpi) => (
            <Grid item xs={12} sm={6} md={3} key={kpi.id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                    <Box>
                      <Typography variant="h4" color="primary.main">
                        {kpi.primary_metric.value}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {kpi.title}
                      </Typography>
                    </Box>
                    <Box display="flex" flexDirection="column" alignItems="flex-end">
                      {getTrendIcon(kpi.primary_metric.trend)}
                      <Typography variant="caption" color={
                        kpi.primary_metric.trend === 'up' ? 'success.main' : 
                        kpi.primary_metric.trend === 'down' ? 'error.main' : 'info.main'
                      }>
                        {kpi.primary_metric.trend_percentage > 0 ? '+' : ''}{kpi.primary_metric.trend_percentage}%
                      </Typography>
                    </Box>
                  </Box>
                  
                  {kpi.alert_level !== 'none' && (
                    <Alert severity={getAlertColor(kpi.alert_level) as any} sx={{ mt: 1, py: 0 }}>
                      <Typography variant="caption">{kpi.alert_message}</Typography>
                    </Alert>
                  )}
                  
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      Progress to Target
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={Math.min(100, (Number(kpi.primary_metric.value) / kpi.targets.current_target) * 100)}
                      sx={{ mt: 1 }}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Grid>

      {/* Executive Summary */}
      {executiveSummary && (
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.primary" mb={2}>Executive Summary - {executiveSummary.period}</Typography>
              
              <Grid container spacing={2} mb={3}>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="primary">
                      ${executiveSummary.total_infrastructure_cost.toLocaleString()}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Total Infrastructure Cost
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="success.main">
                      {executiveSummary.cost_efficiency_score}/100
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Cost Efficiency Score
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="info.main">
                      {executiveSummary.operational_excellence_score}/100
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Operational Excellence
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="warning.main">
                      {executiveSummary.security_posture_score}/100
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Security Posture
                    </Typography>
                  </Box>
                </Grid>
              </Grid>

              <Divider sx={{ my: 2 }} />

              <Box mb={2}>
                <Typography variant="subtitle2" mb={1}>Key Achievements</Typography>
                <List dense>
                  {executiveSummary.key_achievements.slice(0, 3).map((achievement, index) => (
                    <ListItem key={index}>
                      <ListItemIcon><CheckCircle color="success" fontSize="small" /></ListItemIcon>
                      <ListItemText primary={achievement} />
                    </ListItem>
                  ))}
                </List>
              </Box>

              <Box>
                <Typography variant="subtitle2" mb={1}>Critical Issues</Typography>
                <List dense>
                  {executiveSummary.critical_issues.slice(0, 3).map((issue, index) => (
                    <ListItem key={index}>
                      <ListItemIcon><Warning color="error" fontSize="small" /></ListItemIcon>
                      <ListItemText primary={issue} />
                    </ListItem>
                  ))}
                </List>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      )}

      {/* Risk Overview */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.primary" mb={2}>Risk Overview</Typography>
            
            {riskFactors.length > 0 && (
              <ResponsiveContainer width="100%" height={200}>
                <RechartsPieChart>
                  <Pie
                    data={[
                      { name: 'Critical', value: riskFactors.filter(r => r.severity === 'critical').length, color: '#f44336' },
                      { name: 'High', value: riskFactors.filter(r => r.severity === 'high').length, color: '#ff9800' },
                      { name: 'Medium', value: riskFactors.filter(r => r.severity === 'medium').length, color: '#2196f3' },
                      { name: 'Low', value: riskFactors.filter(r => r.severity === 'low').length, color: '#4caf50' },
                    ]}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {[{ color: '#f44336' }, { color: '#ff9800' }, { color: '#2196f3' }, { color: '#4caf50' }].map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <ChartTooltip />
                </RechartsPieChart>
              </ResponsiveContainer>
            )}

            <List dense>
              {riskFactors.slice(0, 3).map((risk) => (
                <ListItem key={risk.id} button onClick={() => {
                  setSelectedRisk(risk);
                  setRiskDialog(true);
                }}>
                  <ListItemIcon>
                    <Badge 
                      color={
                        risk.severity === 'critical' ? 'error' : 
                        risk.severity === 'high' ? 'warning' : 
                        risk.severity === 'medium' ? 'info' : 'success'
                      }
                      variant="dot"
                    >
                      <Security />
                    </Badge>
                  </ListItemIcon>
                  <ListItemText 
                    primary={risk.title}
                    secondary={`${risk.category} - ${risk.status}`}
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderStrategicInitiativesTab = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6" color="text.primary">Strategic Initiatives</Typography>
        <Button variant="contained" onClick={() => setInitiativeDialog(true)}>
          View Details
        </Button>
      </Box>

      <Grid container spacing={3}>
        {strategicInitiatives.map((initiative) => (
          <Grid item xs={12} md={6} lg={4} key={initiative.id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                  <Typography variant="h6" color="text.primary" noWrap>{initiative.title}</Typography>
                  <Chip 
                    label={initiative.status} 
                    color={
                      initiative.status === 'completed' ? 'success' : 
                      initiative.status === 'in_progress' ? 'primary' :
                      initiative.status === 'on_hold' ? 'warning' : 'default'
                    }
                    size="small"
                  />
                </Box>
                
                <Typography variant="body2" color="text.secondary" mb={2}>
                  {initiative.description.substring(0, 100)}...
                </Typography>
                
                <Box mb={2}>
                  <Typography variant="body2" mb={1}>
                    Progress: {initiative.progress_percentage}%
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={initiative.progress_percentage}
                    sx={{ mb: 1 }}
                  />
                </Box>
                
                <Grid container spacing={2} mb={2}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Budget Allocated
                    </Typography>
                    <Typography variant="body2">
                      ${initiative.budget_allocated.toLocaleString()}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Expected ROI
                    </Typography>
                    <Typography variant="body2" color="success.main">
                      {initiative.roi_projection}%
                    </Typography>
                  </Grid>
                </Grid>
                
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Chip 
                    label={initiative.priority} 
                    size="small"
                    color={
                      initiative.priority === 'critical' ? 'error' :
                      initiative.priority === 'high' ? 'warning' :
                      initiative.priority === 'medium' ? 'info' : 'default'
                    }
                    variant="outlined"
                  />
                  <Button 
                    size="small" 
                    onClick={() => {
                      setSelectedInitiative(initiative);
                      setInitiativeDialog(true);
                    }}
                  >
                    View Details
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );

  const renderBusinessUnitsTab = () => (
    <Box>
      <Typography variant="h6" color="text.primary" mb={3}>Business Unit Performance</Typography>
      
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Business Unit</TableCell>
              <TableCell>Department</TableCell>
              <TableCell align="right">Monthly Budget</TableCell>
              <TableCell align="right">Current Spend</TableCell>
              <TableCell align="right">Efficiency Score</TableCell>
              <TableCell>Key Initiatives</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {businessUnits.map((unit) => (
              <TableRow key={unit.id}>
                <TableCell>{unit.name}</TableCell>
                <TableCell>{unit.department}</TableCell>
                <TableCell align="right">
                  ${unit.monthly_budget.toLocaleString()}
                </TableCell>
                <TableCell align="right">
                  <Box>
                    ${unit.current_spend.toLocaleString()}
                    <Typography variant="caption" display="block" color={
                      unit.current_spend > unit.monthly_budget ? 'error.main' : 'success.main'
                    }>
                      {((unit.current_spend / unit.monthly_budget) * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell align="right">
                  <Box display="flex" alignItems="center">
                    <CircularProgress 
                      variant="determinate" 
                      value={unit.efficiency_score} 
                      size={30}
                      color={
                        unit.efficiency_score >= 80 ? 'success' :
                        unit.efficiency_score >= 60 ? 'warning' : 'error'
                      }
                    />
                    <Typography variant="body2" sx={{ ml: 1 }}>
                      {unit.efficiency_score}%
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Box>
                    {unit.key_initiatives.slice(0, 2).map((initiative, index) => (
                      <Chip 
                        key={index}
                        label={initiative} 
                        size="small" 
                        sx={{ mr: 0.5, mb: 0.5 }}
                      />
                    ))}
                    {unit.key_initiatives.length > 2 && (
                      <Typography variant="caption" color="text.secondary">
                        +{unit.key_initiatives.length - 2} more
                      </Typography>
                    )}
                  </Box>
                </TableCell>
                <TableCell>
                  <Tooltip title="View Details">
                    <IconButton size="small">
                      <Visibility />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Generate Report">
                    <IconButton size="small">
                      <Download />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );

  const renderAnalyticsTab = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.primary" mb={2}>Cost Trends</Typography>
            {kpiCards.length > 0 && kpiCards[0].chart_data.length > 0 && (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={kpiCards[0].chart_data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <ChartTooltip />
                  <Area type="monotone" dataKey="value" stroke="#8884d8" fill="#8884d8" fillOpacity={0.3} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.primary" mb={2}>Performance Metrics</Typography>
            {kpiCards.length > 1 && kpiCards[1].chart_data.length > 0 && (
              <ResponsiveContainer width="100%" height={300}>
                <RechartsBarChart data={kpiCards[1].chart_data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <ChartTooltip />
                  <Bar dataKey="value" fill="#82ca9d" />
                </RechartsBarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.primary" mb={2}>Key Metrics Summary</Typography>
            <Grid container spacing={2}>
              {executiveMetrics.slice(0, 8).map((metric) => (
                <Grid item xs={12} sm={6} md={3} key={metric.id}>
                  <Box textAlign="center" p={2} border={1} borderColor="divider" borderRadius={1}>
                    <Typography variant="h5" color="primary.main">
                      {metric.value}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {metric.name}
                    </Typography>
                    <Box display="flex" justifyContent="center" alignItems="center" mt={1}>
                      {getTrendIcon(metric.trend)}
                      <Typography variant="caption" sx={{ ml: 0.5 }}>
                        {metric.trend_percentage > 0 ? '+' : ''}{metric.trend_percentage}%
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  if (!assessmentId) {
    const AssessmentSelector = require('./AssessmentSelector').default;
    return (
      <AssessmentSelector
        redirectPath="/executive-dashboard"
        title="Select Assessment for Executive Dashboard"
        description="Choose an assessment to view executive dashboard data"
      />
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" color="text.primary" gutterBottom>
            Executive Dashboard
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            C-suite focused metrics and strategic insights
          </Typography>
        </Box>
        <Box>
          <Button startIcon={<RefreshIcon />} onClick={loadExecutiveData} disabled={loading} sx={{ mr: 1 }}>
            Refresh
          </Button>
          <Button startIcon={<Download />} variant="outlined">
            Export Report
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab label="Overview" icon={<Analytics />} />
        <Tab label="Strategic Initiatives" icon={<Business />} />
        <Tab label="Business Units" icon={<AccountBalance />} />
        <Tab label="Analytics" icon={<BarChart />} />
      </Tabs>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <TabPanel value={tabValue} index={0}>
        {renderOverviewTab()}
      </TabPanel>
      
      <TabPanel value={tabValue} index={1}>
        {renderStrategicInitiativesTab()}
      </TabPanel>
      
      <TabPanel value={tabValue} index={2}>
        {renderBusinessUnitsTab()}
      </TabPanel>
      
      <TabPanel value={tabValue} index={3}>
        {renderAnalyticsTab()}
      </TabPanel>

      {/* Strategic Initiative Dialog */}
      <Dialog 
        open={initiativeDialog} 
        onClose={() => setInitiativeDialog(false)} 
        maxWidth="md" 
        fullWidth
      >
        <DialogTitle>
          {selectedInitiative ? selectedInitiative.title : 'Strategic Initiatives'}
        </DialogTitle>
        <DialogContent>
          {selectedInitiative ? (
            <Box>
              <Typography variant="body1" mb={2}>
                {selectedInitiative.description}
              </Typography>
              
              <Grid container spacing={2} mb={2}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Budget Allocated</Typography>
                  <Typography variant="body2">${selectedInitiative.budget_allocated.toLocaleString()}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Expected Savings</Typography>
                  <Typography variant="body2">${selectedInitiative.expected_savings.toLocaleString()}</Typography>
                </Grid>
              </Grid>
              
              <Box mb={2}>
                <Typography variant="subtitle2" mb={1}>Progress</Typography>
                <LinearProgress variant="determinate" value={selectedInitiative.progress_percentage} />
                <Typography variant="caption">{selectedInitiative.progress_percentage}% Complete</Typography>
              </Box>
              
              <Box>
                <Typography variant="subtitle2" mb={1}>Stakeholders</Typography>
                <AvatarGroup max={4}>
                  {selectedInitiative.stakeholders.slice(0, 4).map((stakeholder, index) => (
                    <Avatar key={index}>{stakeholder[0]}</Avatar>
                  ))}
                </AvatarGroup>
              </Box>
            </Box>
          ) : (
            <Typography>Loading initiative details...</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInitiativeDialog(false)}>Close</Button>
          <Button variant="contained">Update Status</Button>
        </DialogActions>
      </Dialog>

      {/* Risk Dialog */}
      <Dialog 
        open={riskDialog} 
        onClose={() => setRiskDialog(false)} 
        maxWidth="md" 
        fullWidth
      >
        <DialogTitle>
          {selectedRisk ? selectedRisk.title : 'Risk Details'}
        </DialogTitle>
        <DialogContent>
          {selectedRisk ? (
            <Box>
              <Alert severity={selectedRisk.severity === 'critical' ? 'error' : 'warning'} sx={{ mb: 2 }}>
                <Typography variant="body2">{selectedRisk.description}</Typography>
              </Alert>
              
              <Typography variant="subtitle2" mb={1}>Impact Assessment</Typography>
              <Typography variant="body2" mb={2}>
                Probability: {selectedRisk.impact_assessment.probability}% | 
                Financial Impact: ${selectedRisk.impact_assessment.financial_impact.toLocaleString()}
              </Typography>
              
              <Typography variant="subtitle2" mb={1}>Mitigation Strategies</Typography>
              <List>
                {selectedRisk.mitigation_strategies.map((strategy, index) => (
                  <ListItem key={index}>
                    <ListItemIcon><CheckCircle fontSize="small" /></ListItemIcon>
                    <ListItemText primary={strategy} />
                  </ListItem>
                ))}
              </List>
            </Box>
          ) : (
            <Typography>Loading risk details...</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRiskDialog(false)}>Close</Button>
          <Button variant="contained" color="warning">Update Mitigation</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ExecutiveDashboard;