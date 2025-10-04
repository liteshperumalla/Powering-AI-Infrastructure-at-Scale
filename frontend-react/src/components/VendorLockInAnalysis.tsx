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
  CircularProgress,
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
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Divider,
} from '@mui/material';
import {
  Assessment,
  CloudQueue,
  Timeline,
  Security,
  Warning,
  CheckCircle,
  Error,
  TrendingUp,
  Visibility,
  Edit,
  Delete,
  PlayArrow,
  Download,
  Refresh,
  CompareArrows,
  AccountTree,
  Business,
  Analytics,
  ExpandMore,
  ArrowForward,
  GitHub,
  Microsoft,
  Google,
  Storage,
  DeviceHub,
} from '@mui/icons-material';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as ChartTooltip, BarChart, Bar, PieChart, Pie, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ScatterChart, Scatter } from 'recharts';
import { getVendorLockInAnalysisService, VendorLockInAssessment, ServiceLockInAnalysis, MigrationScenario, MultiCloudStrategy, ContractAnalysis } from '../services/vendorLockInAnalysis';

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

interface VendorLockInAnalysisProps {
  assessmentId?: string;
}

const VendorLockInAnalysis: React.FC<VendorLockInAnalysisProps> = ({ assessmentId }) => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lockInService] = useState(() => getVendorLockInAnalysisService());

  // Auto-refresh vendor lock-in analysis data every 60 seconds
  const { forceRefresh: refreshVendorData, isStale, lastRefresh } = useFreshData('vendor_lockin', {
    autoRefresh: true,
    refreshInterval: 60000, // 60 seconds
    onRefresh: () => {
      console.log('🔄 Auto-refreshing vendor lock-in analysis data...');
      loadVendorLockInData();
    }
  });

  // State for different sections
  const [assessments, setAssessments] = useState<VendorLockInAssessment[]>([]);
  const [serviceAnalyses, setServiceAnalyses] = useState<ServiceLockInAnalysis[]>([]);
  const [migrationScenarios, setMigrationScenarios] = useState<MigrationScenario[]>([]);
  const [multiCloudStrategies, setMultiCloudStrategies] = useState<MultiCloudStrategy[]>([]);
  const [contractAnalyses, setContractAnalyses] = useState<ContractAnalysis[]>([]);

  // Dialog states
  const [assessmentDialog, setAssessmentDialog] = useState(false);
  const [scenarioDialog, setScenarioDialog] = useState(false);
  const [strategyDialog, setStrategyDialog] = useState(false);
  const [selectedAssessment, setSelectedAssessment] = useState<VendorLockInAssessment | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<MigrationScenario | null>(null);

  // Form states
  const [newAssessmentData, setNewAssessmentData] = useState({
    assessment_name: '',
    current_provider: 'aws',
    scope: [] as string[],
    include_migration_scenarios: true,
    include_cost_analysis: true,
  });

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];
  const providers = ['aws', 'azure', 'gcp', 'hybrid', 'multi_cloud'];
  const riskLevels = ['low', 'medium', 'high', 'critical'];

  useEffect(() => {
    loadLockInData();
  }, [assessmentId]);

  const loadLockInData = async () => {
    if (!assessmentId) return;

    setLoading(true);
    try {
      // Use apiClient for authenticated requests
      const { apiClient } = await import('../services/api');
      const vendorData = await apiClient.get<any>(`/features/assessment/${assessmentId}/vendor-lockin`);

      // Map the API response to component state
      setAssessments(vendorData.assessments || []);
      setServiceAnalyses(vendorData.services_analyzed || []);
      setMigrationScenarios(vendorData.migration_scenarios || vendorData.mitigation_strategies || []);
      setMultiCloudStrategies(vendorData.strategies || []);
      setContractAnalyses(vendorData.contracts || []);

    } catch (error) {
      setError('Failed to load vendor lock-in analysis data');
      console.error('Error loading lock-in data:', error);
      // Set fallback empty arrays
      setAssessments([]);
      setMultiCloudStrategies([]);
      setContractAnalyses([]);
      setServiceAnalyses([]);
      setMigrationScenarios([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAssessment = async () => {
    try {
      setLoading(true);
      const assessment = await lockInService.createLockInAssessment(newAssessmentData);
      setAssessments(prev => [...prev, assessment]);
      setAssessmentDialog(false);
      setNewAssessmentData({
        assessment_name: '',
        current_provider: 'aws',
        scope: [],
        include_migration_scenarios: true,
        include_cost_analysis: true,
      });
    } catch (error) {
      setError('Failed to create assessment');
      console.error('Error creating assessment:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };

  const getProviderIcon = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'aws':
        return <CloudQueue color="warning" />;
      case 'azure':
        return <Microsoft color="info" />;
      case 'gcp':
        return <Google color="error" />;
      default:
        return <DeviceHub />;
    }
  };

  const renderOverviewTab = () => (
    <Grid container spacing={3}>
      {/* Risk Score Overview */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" mb={2}>Overall Risk Assessment</Typography>
            {assessments.length > 0 && (
              <Box textAlign="center">
                <CircularProgress
                  variant="determinate"
                  value={100 - assessments[0].overall_risk_score}
                  size={120}
                  thickness={8}
                  color={getRiskColor(assessments[0].risk_level) as any}
                />
                <Typography variant="h4" sx={{ mt: 2 }}>
                  {assessments[0].overall_risk_score}/100
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Lock-in Risk Score
                </Typography>
                <Chip
                  label={assessments[0].risk_level.toUpperCase()}
                  color={getRiskColor(assessments[0].risk_level) as any}
                  sx={{ mt: 1 }}
                />
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Provider Distribution */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" mb={2}>Provider Distribution</Typography>
            {assessments.length > 0 && (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={[
                      { name: 'AWS', value: 45, provider: 'aws' },
                      { name: 'Azure', value: 30, provider: 'azure' },
                      { name: 'GCP', value: 15, provider: 'gcp' },
                      { name: 'Other', value: 10, provider: 'other' },
                    ]}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {COLORS.map((color, index) => (
                      <Cell key={`cell-${index}`} fill={color} />
                    ))}
                  </Pie>
                  <ChartTooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Migration Complexity */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" mb={2}>Migration Complexity</Typography>
            {serviceAnalyses.length > 0 && (
              <Box>
                {['low', 'medium', 'high', 'critical'].map((complexity) => {
                  const count = serviceAnalyses.filter(s => s.migration_complexity === complexity).length;
                  const percentage = (count / serviceAnalyses.length) * 100;
                  return (
                    <Box key={complexity} mb={1}>
                      <Box display="flex" justifyContent="space-between" mb={0.5}>
                        <Typography variant="body2" textTransform="capitalize">
                          {complexity}
                        </Typography>
                        <Typography variant="body2">{count} services</Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={percentage}
                        color={getRiskColor(complexity) as any}
                      />
                    </Box>
                  );
                })}
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Recent Assessments */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Recent Assessments</Typography>
              <Button
                variant="contained"
                startIcon={<Assessment />}
                onClick={() => setAssessmentDialog(true)}
              >
                New Assessment
              </Button>
            </Box>
            
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Assessment Name</TableCell>
                    <TableCell>Provider</TableCell>
                    <TableCell>Risk Level</TableCell>
                    <TableCell>Services Analyzed</TableCell>
                    <TableCell>Assessment Date</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Array.isArray(assessments) ? assessments.slice(0, 5).map((assessment) => (
                    <TableRow key={assessment.id}>
                      <TableCell>{assessment.assessment_name}</TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center">
                          {getProviderIcon(assessment.current_provider)}
                          <Typography variant="body2" sx={{ ml: 1, textTransform: 'uppercase' }}>
                            {assessment.current_provider}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={assessment.risk_level}
                          color={getRiskColor(assessment.risk_level) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{assessment.services_analyzed.length}</TableCell>
                      <TableCell>{new Date(assessment.assessment_date).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => {
                              setSelectedAssessment(assessment);
                              setAssessmentDialog(true);
                            }}
                          >
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
                  )) : (
                    <TableRow>
                      <TableCell colSpan={6} align="center">
                        <Typography color="textSecondary">No assessments available</Typography>
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

  const renderServiceAnalysisTab = () => (
    <Box>
      <Typography variant="h6" mb={3}>Service Lock-in Analysis</Typography>
      
      <Grid container spacing={3}>
        {Array.isArray(serviceAnalyses) && serviceAnalyses.length > 0 ? serviceAnalyses.map((service) => (
          <Grid item xs={12} md={6} lg={4} key={service.service_name}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">{service.service_name}</Typography>
                  <Chip
                    label={service.service_category}
                    size="small"
                    variant="outlined"
                  />
                </Box>
                
                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary" mb={1}>
                    Lock-in Score
                  </Typography>
                  <Box display="flex" alignItems="center">
                    <LinearProgress
                      variant="determinate"
                      value={service.lock_in_score}
                      sx={{ flexGrow: 1, mr: 1 }}
                      color={getRiskColor(
                        service.lock_in_score >= 80 ? 'critical' :
                        service.lock_in_score >= 60 ? 'high' :
                        service.lock_in_score >= 40 ? 'medium' : 'low'
                      ) as any}
                    />
                    <Typography variant="body2">{service.lock_in_score}/100</Typography>
                  </Box>
                </Box>
                
                <Grid container spacing={1} mb={2}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Migration Cost
                    </Typography>
                    <Typography variant="body2">
                      ${service.estimated_migration_cost.toLocaleString()}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Timeline
                    </Typography>
                    <Typography variant="body2">
                      {service.estimated_migration_time}
                    </Typography>
                  </Grid>
                </Grid>
                
                <Box mb={2}>
                  <Typography variant="body2" mb={1}>
                    Migration Complexity: 
                    <Chip
                      label={service.migration_complexity}
                      size="small"
                      color={getRiskColor(service.migration_complexity) as any}
                      sx={{ ml: 1 }}
                    />
                  </Typography>
                </Box>
                
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography variant="body2">Lock-in Factors ({service.lock_in_factors.length})</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      {service.lock_in_factors.map((factor, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <Warning color={getRiskColor(factor.severity) as any} fontSize="small" />
                          </ListItemIcon>
                          <ListItemText
                            primary={factor.factor_type.replace('_', ' ')}
                            secondary={factor.description}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
              </CardContent>
            </Card>
          </Grid>
        )) : (
          <Grid item xs={12}>
            <Box textAlign="center" py={3}>
              <Typography color="textSecondary">
                No service analyses available
              </Typography>
            </Box>
          </Grid>
        )}
      </Grid>
    </Box>
  );

  const renderMigrationScenariosTab = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Migration Scenarios</Typography>
        <Button
          variant="contained"
          startIcon={<Timeline />}
          onClick={() => setScenarioDialog(true)}
        >
          Generate Scenarios
        </Button>
      </Box>
      
      <Grid container spacing={3}>
        {Array.isArray(migrationScenarios) && migrationScenarios.length > 0 ? migrationScenarios.map((scenario) => (
          <Grid item xs={12} lg={6} key={scenario.id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">{scenario.scenario_name}</Typography>
                  <Chip
                    label={scenario.scenario_type}
                    variant="outlined"
                  />
                </Box>
                
                <Typography variant="body2" color="text.secondary" mb={2}>
                  Target Providers: {scenario.target_providers.join(', ')}
                </Typography>
                
                {/* Timeline */}
                <Box mb={2}>
                  <Typography variant="subtitle2" mb={1}>Timeline</Typography>
                  <Stepper orientation="horizontal" activeStep={-1}>
                    <Step>
                      <StepLabel>Planning ({scenario.timeline.planning_phase})</StepLabel>
                    </Step>
                    <Step>
                      <StepLabel>Execution ({scenario.timeline.execution_phase})</StepLabel>
                    </Step>
                    <Step>
                      <StepLabel>Validation ({scenario.timeline.validation_phase})</StepLabel>
                    </Step>
                  </Stepper>
                  <Typography variant="body2" color="primary" sx={{ mt: 1 }}>
                    Total Duration: {scenario.timeline.total_duration}
                  </Typography>
                </Box>
                
                {/* Cost Analysis */}
                <Grid container spacing={2} mb={2}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Migration Cost
                    </Typography>
                    <Typography variant="h6" color="warning.main">
                      ${scenario.cost_analysis.migration_costs.toLocaleString()}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Break Even
                    </Typography>
                    <Typography variant="h6" color="success.main">
                      {scenario.cost_analysis.break_even_point}
                    </Typography>
                  </Grid>
                </Grid>
                
                {/* Risk Assessment */}
                <Box mb={2}>
                  <Typography variant="subtitle2" mb={1}>Risk Score: {scenario.risk_assessment.overall_risk_score}/100</Typography>
                  <LinearProgress
                    variant="determinate"
                    value={scenario.risk_assessment.overall_risk_score}
                    color={getRiskColor(
                      scenario.risk_assessment.overall_risk_score >= 80 ? 'critical' :
                      scenario.risk_assessment.overall_risk_score >= 60 ? 'high' :
                      scenario.risk_assessment.overall_risk_score >= 40 ? 'medium' : 'low'
                    ) as any}
                  />
                </Box>
                
                {/* Benefits */}
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography variant="body2">Benefits ({scenario.benefits.length})</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      {scenario.benefits.map((benefit, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <CheckCircle color="success" fontSize="small" />
                          </ListItemIcon>
                          <ListItemText
                            primary={benefit.benefit_type.replace('_', ' ')}
                            secondary={benefit.description}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
                
                <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
                  <Button
                    size="small"
                    startIcon={<PlayArrow />}
                    onClick={() => {
                      setSelectedScenario(scenario);
                      setScenarioDialog(true);
                    }}
                  >
                    Simulate
                  </Button>
                  <Button size="small" startIcon={<CompareArrows />}>
                    Compare
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )) : (
          <Grid item xs={12}>
            <Typography variant="body2" color="text.secondary" textAlign="center">
              No migration scenarios available
            </Typography>
          </Grid>
        )}
      </Grid>
    </Box>
  );

  const renderMultiCloudTab = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Multi-Cloud Strategies</Typography>
        <Button
          variant="contained"
          startIcon={<AccountTree />}
          onClick={() => setStrategyDialog(true)}
        >
          Create Strategy
        </Button>
      </Box>
      
      <Grid container spacing={3}>
        {Array.isArray(multiCloudStrategies) && multiCloudStrategies.length > 0 ? multiCloudStrategies.map((strategy) => (
          <Grid item xs={12} lg={6} key={strategy.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" mb={2}>{strategy.strategy_name}</Typography>
                <Typography variant="body2" color="text.secondary" mb={2}>
                  {strategy.description}
                </Typography>
                
                {/* Target Architecture */}
                <Box mb={2}>
                  <Typography variant="subtitle2" mb={1}>Target Architecture</Typography>
                  <Grid container spacing={1}>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">Primary Provider</Typography>
                      <Box display="flex" alignItems="center">
                        {getProviderIcon(strategy.target_architecture.primary_provider)}
                        <Typography variant="body2" sx={{ ml: 1, textTransform: 'uppercase' }}>
                          {strategy.target_architecture.primary_provider}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">Secondary Providers</Typography>
                      <Typography variant="body2">
                        {strategy.target_architecture.secondary_providers.join(', ').toUpperCase()}
                      </Typography>
                    </Grid>
                  </Grid>
                </Box>
                
                {/* Cost Analysis */}
                <Box mb={2}>
                  <Typography variant="subtitle2" mb={1}>Cost Analysis</Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={4}>
                      <Typography variant="caption" color="text.secondary">Setup</Typography>
                      <Typography variant="body2">
                        ${strategy.cost_implications.setup_costs.toLocaleString()}
                      </Typography>
                    </Grid>
                    <Grid item xs={4}>
                      <Typography variant="caption" color="text.secondary">Ongoing</Typography>
                      <Typography variant="body2">
                        ${strategy.cost_implications.ongoing_operational_costs.toLocaleString()}
                      </Typography>
                    </Grid>
                    <Grid item xs={4}>
                      <Typography variant="caption" color="text.secondary">Savings</Typography>
                      <Typography variant="body2" color="success.main">
                        ${strategy.cost_implications.potential_savings.toLocaleString()}
                      </Typography>
                    </Grid>
                  </Grid>
                </Box>
                
                {/* Implementation Roadmap */}
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography variant="body2">
                      Implementation Roadmap ({strategy.implementation_roadmap.length} phases)
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Stepper orientation="vertical">
                      {strategy.implementation_roadmap.map((phase, index) => (
                        <Step key={index} active={true}>
                          <StepLabel>
                            {phase.phase_name} ({phase.duration})
                          </StepLabel>
                          <StepContent>
                            <Typography variant="body2" color="text.secondary">
                              Budget: ${phase.budget_allocation.toLocaleString()}
                            </Typography>
                            <Box mt={1}>
                              {phase.objectives.slice(0, 2).map((objective, idx) => (
                                <Chip key={idx} label={objective} size="small" sx={{ mr: 1, mb: 1 }} />
                              ))}
                            </Box>
                          </StepContent>
                        </Step>
                      ))}
                    </Stepper>
                  </AccordionDetails>
                </Accordion>
                
                <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
                  <Button size="small" startIcon={<Visibility />}>
                    View Details
                  </Button>
                  <Button size="small" startIcon={<Assessment />}>
                    Validate
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )) : (
          <Grid item xs={12}>
            <Typography variant="body2" color="text.secondary" textAlign="center">
              No multi-cloud strategies available
            </Typography>
          </Grid>
        )}
      </Grid>
    </Box>
  );

  const renderContractAnalysisTab = () => (
    <Box>
      <Typography variant="h6" mb={3}>Contract Analysis</Typography>
      
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Vendor</TableCell>
              <TableCell>Contract Type</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell>Early Termination Fee</TableCell>
              <TableCell>Minimum Spend</TableCell>
              <TableCell>Lock-in Risk</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Array.isArray(contractAnalyses) && contractAnalyses.length > 0 ? contractAnalyses.map((contract) => (
              <TableRow key={contract.id}>
                <TableCell>
                  <Box display="flex" alignItems="center">
                    {getProviderIcon(contract.vendor_name)}
                    <Typography variant="body2" sx={{ ml: 1 }}>
                      {contract.vendor_name}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip label={contract.contract_type} size="small" variant="outlined" />
                </TableCell>
                <TableCell>{contract.contract_duration}</TableCell>
                <TableCell>
                  <Typography variant="body2" color="error.main">
                    ${contract.early_termination_clauses.termination_fees.toLocaleString()}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    ${contract.volume_commitments.minimum_spend.toLocaleString()}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box display="flex" alignItems="center">
                    <Warning 
                      color={
                        contract.lock_in_implications.switching_barriers.length >= 3 ? 'error' :
                        contract.lock_in_implications.switching_barriers.length >= 2 ? 'warning' : 'success'
                      } 
                      fontSize="small" 
                      sx={{ mr: 1 }} 
                    />
                    <Typography variant="body2">
                      {contract.lock_in_implications.switching_barriers.length} barriers
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Tooltip title="View Contract Details">
                    <IconButton size="small">
                      <Visibility />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Renewal Recommendations">
                    <IconButton size="small">
                      <Analytics />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            )) : (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography variant="body2" color="text.secondary">
                    No contract analyses available
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
        redirectPath="/vendor-lockin"
        title="Select Assessment for Vendor Lock-in Analysis"
        description="Choose an assessment to view vendor lock-in analysis"
      />
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Vendor Lock-in Risk Analysis
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Multi-cloud migration complexity assessment and risk mitigation •
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
            onClick={refreshVendorData}
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
        <Tab label="Service Analysis" icon={<Assessment />} />
        <Tab label="Migration Scenarios" icon={<Timeline />} />
        <Tab label="Multi-Cloud Strategy" icon={<AccountTree />} />
        <Tab label="Contract Analysis" icon={<Business />} />
      </Tabs>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <TabPanel value={tabValue} index={0}>
        {renderOverviewTab()}
      </TabPanel>
      
      <TabPanel value={tabValue} index={1}>
        {renderServiceAnalysisTab()}
      </TabPanel>
      
      <TabPanel value={tabValue} index={2}>
        {renderMigrationScenariosTab()}
      </TabPanel>
      
      <TabPanel value={tabValue} index={3}>
        {renderMultiCloudTab()}
      </TabPanel>
      
      <TabPanel value={tabValue} index={4}>
        {renderContractAnalysisTab()}
      </TabPanel>

      {/* Create Assessment Dialog */}
      <Dialog open={assessmentDialog} onClose={() => setAssessmentDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New Lock-in Assessment</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Assessment Name"
                value={newAssessmentData.assessment_name}
                onChange={(e) => setNewAssessmentData({ ...newAssessmentData, assessment_name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Current Provider</InputLabel>
                <Select
                  value={newAssessmentData.current_provider}
                  onChange={(e) => setNewAssessmentData({ ...newAssessmentData, current_provider: e.target.value })}
                >
                  {providers.map((provider) => (
                    <MenuItem key={provider} value={provider}>
                      {provider.toUpperCase()}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Scope (comma-separated services)"
                value={newAssessmentData.scope.join(', ')}
                onChange={(e) => setNewAssessmentData({ 
                  ...newAssessmentData, 
                  scope: e.target.value.split(',').map(s => s.trim()).filter(s => s) 
                })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAssessmentDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateAssessment} 
            variant="contained"
            disabled={!newAssessmentData.assessment_name}
          >
            Create Assessment
          </Button>
        </DialogActions>
      </Dialog>

      {/* Scenario Dialog */}
      <Dialog 
        open={scenarioDialog} 
        onClose={() => setScenarioDialog(false)} 
        maxWidth="lg" 
        fullWidth
      >
        <DialogTitle>
          {selectedScenario ? `Simulate: ${selectedScenario.scenario_name}` : 'Generate Migration Scenarios'}
        </DialogTitle>
        <DialogContent>
          {selectedScenario ? (
            <Box>
              <Typography variant="h6" mb={2}>Scenario Simulation Results</Typography>
              <Alert severity="info" sx={{ mb: 2 }}>
                This simulation shows the projected outcomes of executing this migration scenario.
              </Alert>
              
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" mb={1}>Success Probability</Typography>
                  <Box display="flex" alignItems="center">
                    <LinearProgress 
                      variant="determinate" 
                      value={75} 
                      color="success"
                      sx={{ flexGrow: 1, mr: 2 }}
                    />
                    <Typography variant="body2">75%</Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" mb={1}>Risk Level</Typography>
                  <Chip label="Medium" color="warning" />
                </Grid>
              </Grid>
            </Box>
          ) : (
            <Typography>Select migration scenario preferences and generate optimized migration paths.</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setScenarioDialog(false)}>Close</Button>
          {selectedScenario && (
            <Button variant="contained">Execute Scenario</Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default VendorLockInAnalysis;