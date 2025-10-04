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
  Badge,
  Switch,
  FormControlLabel,
  Divider,
} from '@mui/material';
import {
  Gavel,
  Security,
  Assessment,
  CheckCircle,
  Error,
  Warning,
  Schedule,
  PlayArrow,
  Stop,
  Visibility,
  Edit,
  Delete,
  Download,
  Refresh,
  CloudUpload,
  Timeline,
  Analytics,
  Settings,
  ExpandMore,
  Assignment,
  AccountBalance,
  Policy,
  VerifiedUser,
  Task,
  AutoMode,
} from '@mui/icons-material';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as ChartTooltip, BarChart, Bar, PieChart, Pie, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { getComplianceAutomationService, ComplianceFramework, ComplianceRequirement, AutomatedCheck, ComplianceDashboard, ComplianceAudit } from '../services/complianceAutomation';

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

interface ComplianceAutomationProps {
  assessmentId?: string;
}

const ComplianceAutomation: React.FC<ComplianceAutomationProps> = ({ assessmentId }) => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [complianceService] = useState(() => getComplianceAutomationService());

  // State for different sections
  const [dashboard, setDashboard] = useState<ComplianceDashboard | null>(null);
  const [frameworks, setFrameworks] = useState<ComplianceFramework[]>([]);
  const [automatedChecks, setAutomatedChecks] = useState<AutomatedCheck[]>([]);
  const [audits, setAudits] = useState<ComplianceAudit[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);

  // Dialog states
  const [frameworkDialog, setFrameworkDialog] = useState(false);
  const [checkDialog, setCheckDialog] = useState(false);
  const [auditDialog, setAuditDialog] = useState(false);
  const [evidenceDialog, setEvidenceDialog] = useState(false);
  const [selectedFramework, setSelectedFramework] = useState<ComplianceFramework | null>(null);
  const [selectedCheck, setSelectedCheck] = useState<AutomatedCheck | null>(null);

  // Form states
  const [newFrameworkData, setNewFrameworkData] = useState({
    name: '',
    type: 'soc2',
    version: '1.0',
    requirements_config: {},
    assessment_schedule: {},
  });

  const [newCheckData, setNewCheckData] = useState({
    framework_id: '',
    requirement_id: '',
    check_name: '',
    check_type: 'configuration',
    check_logic: {},
    frequency: 'daily',
    data_sources: [] as string[],
  });

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];
  const frameworkTypes = ['soc2', 'gdpr', 'hipaa', 'iso27001', 'pci_dss', 'nist', 'custom'];
  const checkTypes = ['configuration', 'policy', 'log_analysis', 'vulnerability_scan', 'access_review', 'data_classification'];

  useEffect(() => {
    loadComplianceData();
  }, []);

  const loadComplianceData = async () => {
    setLoading(true);
    try {
      const [
        dashboardData,
        frameworksData,
        checksData,
        auditsData,
        alertsData,
      ] = await Promise.all([
        complianceService.getComplianceDashboard(),
        complianceService.getComplianceFrameworks(),
        complianceService.getAutomatedChecks(),
        complianceService.getAudits(),
        complianceService.getActiveAlerts(),
      ]);

      setDashboard(dashboardData);
      setFrameworks(Array.isArray(frameworksData) ? frameworksData : []);
      setAutomatedChecks(Array.isArray(checksData) ? checksData : []);
      setAudits(Array.isArray(auditsData) ? auditsData : []);
      setAlerts(Array.isArray(alertsData) ? alertsData : []);
    } catch (error) {
      setError('Failed to load compliance data');
      console.error('Error loading compliance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFramework = async () => {
    try {
      setLoading(true);
      const framework = await complianceService.addFramework(newFrameworkData);
      setFrameworks(prev => [...prev, framework]);
      setFrameworkDialog(false);
      setNewFrameworkData({
        name: '',
        type: 'soc2',
        version: '1.0',
        requirements_config: {},
        assessment_schedule: {},
      });
    } catch (error) {
      setError('Failed to create framework');
      console.error('Error creating framework:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCheck = async () => {
    try {
      setLoading(true);
      const check = await complianceService.createAutomatedCheck(newCheckData);
      setAutomatedChecks(prev => [...prev, check]);
      setCheckDialog(false);
      setNewCheckData({
        framework_id: '',
        requirement_id: '',
        check_name: '',
        check_type: 'configuration',
        check_logic: {},
        frequency: 'daily',
        data_sources: [],
      });
    } catch (error) {
      setError('Failed to create automated check');
      console.error('Error creating check:', error);
    } finally {
      setLoading(false);
    }
  };

  const getComplianceColor = (score: number) => {
    if (score >= 90) return 'success';
    if (score >= 75) return 'info';
    if (score >= 60) return 'warning';
    return 'error';
  };

  const getFrameworkIcon = (type: string) => {
    switch (type) {
      case 'soc2':
        return <Security color="primary" />;
      case 'gdpr':
        return <Policy color="info" />;
      case 'hipaa':
        return <VerifiedUser color="success" />;
      case 'iso27001':
        return <AccountBalance color="warning" />;
      default:
        return <Gavel />;
    }
  };

  const renderOverviewTab = () => (
    <Grid container spacing={3}>
      {/* Compliance Score Overview */}
      {dashboard && (
        <>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box textAlign="center">
                  <CircularProgress
                    variant="determinate"
                    value={dashboard.overall_compliance_score}
                    size={120}
                    thickness={8}
                    color={getComplianceColor(dashboard.overall_compliance_score) as any}
                  />
                  <Typography variant="h4" sx={{ mt: 2 }}>
                    {dashboard.overall_compliance_score}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Overall Compliance
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="text.secondary">Active Findings</Typography>
                <Grid container spacing={1} mt={1}>
                  <Grid item xs={6}>
                    <Box textAlign="center">
                      <Typography variant="h5" color="error.main">
                        {dashboard.active_findings?.critical || 0}
                      </Typography>
                      <Typography variant="caption">Critical</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box textAlign="center">
                      <Typography variant="h5" color="warning.main">
                        {dashboard.active_findings?.high || 0}
                      </Typography>
                      <Typography variant="caption">High</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box textAlign="center">
                      <Typography variant="h5" color="info.main">
                        {dashboard.active_findings?.medium || 0}
                      </Typography>
                      <Typography variant="caption">Medium</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box textAlign="center">
                      <Typography variant="h5" color="success.main">
                        {dashboard.active_findings?.low || 0}
                      </Typography>
                      <Typography variant="caption">Low</Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="text.secondary">Remediation Progress</Typography>
                <Box mt={2}>
                  <Typography variant="h5">
                    {dashboard.remediation_progress?.completed_actions || 0}/{dashboard.remediation_progress?.total_actions || 0}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={dashboard.remediation_progress?.progress_percentage || 0}
                    sx={{ mt: 1 }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    {dashboard.remediation_progress?.progress_percentage || 0}% Complete
                  </Typography>
                  {dashboard.remediation_progress?.overdue_actions > 0 && (
                    <Typography variant="caption" color="error.main" display="block">
                      {dashboard.remediation_progress.overdue_actions} Overdue
                    </Typography>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="text.secondary">Automated Monitoring</Typography>
                <Box mt={2}>
                  <Grid container spacing={1}>
                    <Grid item xs={6}>
                      <Typography variant="h6" color="success.main">
                        {dashboard.automated_monitoring?.passing_checks || 0}
                      </Typography>
                      <Typography variant="caption">Passing</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="h6" color="error.main">
                        {dashboard.automated_monitoring?.failing_checks || 0}
                      </Typography>
                      <Typography variant="caption">Failing</Typography>
                    </Grid>
                  </Grid>
                  <Typography variant="caption" color="text.secondary" display="block" mt={1}>
                    Last Run: {dashboard.automated_monitoring?.last_execution ? new Date(dashboard.automated_monitoring.last_execution).toLocaleString() : 'Never'}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </>
      )}

      {/* Framework Scores */}
      <Grid item xs={12} md={8}>
        <Card>
          <CardContent>
            <Typography variant="h6" mb={2}>Framework Compliance Scores</Typography>
            {dashboard && dashboard.framework_scores && (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={dashboard.framework_scores}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="framework" />
                  <YAxis domain={[0, 100]} />
                  <ChartTooltip />
                  <Bar dataKey="score" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Upcoming Deadlines */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" mb={2}>Upcoming Deadlines</Typography>
            <List>
              {dashboard?.upcoming_deadlines?.slice(0, 5).map((deadline, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <Schedule color={
                      new Date(deadline.due_date) <= new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) 
                        ? 'error' 
                        : 'warning'
                    } />
                  </ListItemIcon>
                  <ListItemText
                    primary={deadline.item}
                    secondary={`${deadline.type} - ${new Date(deadline.due_date).toLocaleDateString()}`}
                  />
                  <Chip
                    label={deadline.priority}
                    size="small"
                    color={
                      deadline.priority === 'critical' ? 'error' :
                      deadline.priority === 'high' ? 'warning' : 'info'
                    }
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      </Grid>

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" mb={2}>Active Alerts</Typography>
              {alerts.map((alert) => (
                <Alert 
                  key={alert.id}
                  severity={alert.severity}
                  sx={{ mb: 1 }}
                  action={
                    <Button size="small" onClick={() => complianceService.acknowledgeAlert(alert.id)}>
                      Acknowledge
                    </Button>
                  }
                >
                  <Typography variant="body2">{alert.message}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Affected: {alert.affected_items.join(', ')}
                  </Typography>
                </Alert>
              ))}
            </CardContent>
          </Card>
        </Grid>
      )}
    </Grid>
  );

  const renderFrameworksTab = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Compliance Frameworks</Typography>
        <Button
          variant="contained"
          startIcon={<Gavel />}
          onClick={() => setFrameworkDialog(true)}
        >
          Add Framework
        </Button>
      </Box>
      
      <Grid container spacing={3}>
        {frameworks.map((framework) => (
          <Grid item xs={12} md={6} lg={4} key={framework.id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Box display="flex" alignItems="center">
                    {getFrameworkIcon(framework.type)}
                    <Typography variant="h6" sx={{ ml: 1 }}>
                      {framework.name}
                    </Typography>
                  </Box>
                  <Chip
                    label={framework.status}
                    color={
                      framework.status === 'compliant' ? 'success' :
                      framework.status === 'partially_compliant' ? 'warning' : 'error'
                    }
                    size="small"
                  />
                </Box>
                
                <Typography variant="body2" color="text.secondary" mb={2}>
                  Version: {framework.version} | Type: {framework.type.toUpperCase()}
                </Typography>
                
                <Box mb={2}>
                  <Typography variant="body2" mb={1}>
                    Compliance Score: {framework.overall_compliance_score}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={framework.overall_compliance_score}
                    color={getComplianceColor(framework.overall_compliance_score) as any}
                  />
                </Box>
                
                <Grid container spacing={2} mb={2}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Requirements
                    </Typography>
                    <Typography variant="body2">
                      {framework.requirements.length}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Next Assessment
                    </Typography>
                    <Typography variant="body2">
                      {new Date(framework.next_assessment_date).toLocaleDateString()}
                    </Typography>
                  </Grid>
                </Grid>
                
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Button
                    size="small"
                    startIcon={<Assessment />}
                    onClick={() => complianceService.assessFrameworkCompliance(framework.id)}
                  >
                    Assess
                  </Button>
                  <Box>
                    <Tooltip title="View Details">
                      <IconButton
                        size="small"
                        onClick={() => {
                          setSelectedFramework(framework);
                          setFrameworkDialog(true);
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
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );

  const renderAutomatedChecksTab = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Automated Compliance Checks</Typography>
        <Button
          variant="contained"
          startIcon={<AutoMode />}
          onClick={() => setCheckDialog(true)}
        >
          Create Check
        </Button>
      </Box>
      
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Check Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Frequency</TableCell>
              <TableCell>Last Result</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {automatedChecks.map((check) => (
              <TableRow key={check.id}>
                <TableCell>{check.check_name}</TableCell>
                <TableCell>
                  <Chip label={check.check_type} size="small" variant="outlined" />
                </TableCell>
                <TableCell>{check.check_frequency}</TableCell>
                <TableCell>
                  <Box display="flex" alignItems="center">
                    {check.last_result.status === 'pass' ? (
                      <CheckCircle color="success" fontSize="small" />
                    ) : check.last_result.status === 'fail' ? (
                      <Error color="error" fontSize="small" />
                    ) : (
                      <Warning color="warning" fontSize="small" />
                    )}
                    <Typography variant="body2" sx={{ ml: 1 }}>
                      {check.last_result.status} ({check.last_result.score}/100)
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Switch
                    checked={check.enabled}
                    onChange={() => {
                      // Toggle check enabled status
                    }}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Tooltip title="Run Check">
                    <IconButton
                      size="small"
                      onClick={() => complianceService.executeAutomatedCheck(check.id)}
                    >
                      <PlayArrow />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="View History">
                    <IconButton size="small">
                      <Timeline />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Configure">
                    <IconButton size="small">
                      <Settings />
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

  const renderAuditsTab = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Compliance Audits</Typography>
        <Button
          variant="contained"
          startIcon={<Assignment />}
          onClick={() => setAuditDialog(true)}
        >
          Create Audit
        </Button>
      </Box>
      
      <Grid container spacing={3}>
        {audits.map((audit) => (
          <Grid item xs={12} lg={6} key={audit.id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">{audit.audit_name}</Typography>
                  <Chip
                    label={audit.audit_type}
                    variant="outlined"
                  />
                </Box>
                
                <Typography variant="body2" color="text.secondary" mb={2}>
                  Frameworks: {audit.frameworks_in_scope.join(', ')}
                </Typography>
                
                <Box mb={2}>
                  <Typography variant="subtitle2" mb={1}>Audit Timeline</Typography>
                  <Grid container spacing={1}>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">Planning</Typography>
                      <Typography variant="body2">
                        {new Date(audit.audit_timeline.planning_start).toLocaleDateString()}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">Fieldwork</Typography>
                      <Typography variant="body2">
                        {new Date(audit.audit_timeline.fieldwork_start).toLocaleDateString()} - 
                        {new Date(audit.audit_timeline.fieldwork_end).toLocaleDateString()}
                      </Typography>
                    </Grid>
                  </Grid>
                </Box>
                
                <Box mb={2}>
                  <Typography variant="subtitle2" mb={1}>Auditor Information</Typography>
                  <Typography variant="body2">
                    {audit.auditor_information.name} ({audit.auditor_information.organization})
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Certifications: {audit.auditor_information.certification.join(', ')}
                  </Typography>
                </Box>
                
                {audit.findings.length > 0 && (
                  <Box mb={2}>
                    <Typography variant="subtitle2" mb={1}>
                      Findings ({audit.findings.length})
                    </Typography>
                    {audit.findings.slice(0, 3).map((finding, index) => (
                      <Alert 
                        key={index}
                        severity={
                          finding.severity === 'critical' ? 'error' :
                          finding.severity === 'high' ? 'warning' : 'info'
                        }
                        sx={{ mb: 1 }}
                      >
                        <Typography variant="body2">{finding.description}</Typography>
                      </Alert>
                    ))}
                  </Box>
                )}
                
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Button size="small" startIcon={<Visibility />}>
                    View Details
                  </Button>
                  {audit.certification_status && (
                    <Chip
                      label={audit.certification_status}
                      color={
                        audit.certification_status === 'certified' ? 'success' :
                        audit.certification_status === 'conditional' ? 'warning' : 'error'
                      }
                    />
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );

  const renderReportsTab = () => (
    <Box>
      <Typography variant="h6" mb={3}>Compliance Reporting</Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" mb={2}>Generate Report</Typography>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Report Type</InputLabel>
                <Select defaultValue="executive_summary">
                  <MenuItem value="executive_summary">Executive Summary</MenuItem>
                  <MenuItem value="detailed_assessment">Detailed Assessment</MenuItem>
                  <MenuItem value="audit_report">Audit Report</MenuItem>
                  <MenuItem value="gap_analysis">Gap Analysis</MenuItem>
                  <MenuItem value="remediation_plan">Remediation Plan</MenuItem>
                </Select>
              </FormControl>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Frameworks</InputLabel>
                <Select multiple defaultValue={[]}>
                  {frameworks.map((framework) => (
                    <MenuItem key={framework.id} value={framework.id}>
                      {framework.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Format</InputLabel>
                <Select defaultValue="pdf">
                  <MenuItem value="pdf">PDF</MenuItem>
                  <MenuItem value="excel">Excel</MenuItem>
                  <MenuItem value="csv">CSV</MenuItem>
                </Select>
              </FormControl>
              
              <Button
                variant="contained"
                fullWidth
                startIcon={<Download />}
                onClick={() => {
                  // Generate report
                }}
              >
                Generate Report
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" mb={2}>Scheduled Reports</Typography>
              <List>
                <ListItem>
                  <ListItemIcon><Schedule /></ListItemIcon>
                  <ListItemText
                    primary="Monthly Executive Summary"
                    secondary="SOC2, GDPR - Next: Dec 1, 2024"
                  />
                  <IconButton size="small">
                    <Edit />
                  </IconButton>
                </ListItem>
                <ListItem>
                  <ListItemIcon><Schedule /></ListItemIcon>
                  <ListItemText
                    primary="Quarterly Audit Report"
                    secondary="All Frameworks - Next: Jan 1, 2025"
                  />
                  <IconButton size="small">
                    <Edit />
                  </IconButton>
                </ListItem>
              </List>
              
              <Button
                variant="outlined"
                fullWidth
                startIcon={<Schedule />}
                sx={{ mt: 2 }}
              >
                Schedule New Report
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );

  if (!assessmentId) {
    const AssessmentSelector = require('./AssessmentSelector').default;
    return (
      <AssessmentSelector
        redirectPath="/compliance"
        title="Select Assessment for Compliance"
        description="Choose an assessment to view compliance automation data"
      />
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Compliance Automation
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" mb={3}>
        Automated compliance reporting for SOC2, GDPR, HIPAA and other frameworks
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab label="Overview" icon={<Analytics />} />
        <Tab label="Frameworks" icon={<Gavel />} />
        <Tab label="Automated Checks" icon={<AutoMode />} />
        <Tab label="Audits" icon={<Assignment />} />
        <Tab label="Reports" icon={<Analytics />} />
      </Tabs>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <TabPanel value={tabValue} index={0}>
        {renderOverviewTab()}
      </TabPanel>
      
      <TabPanel value={tabValue} index={1}>
        {renderFrameworksTab()}
      </TabPanel>
      
      <TabPanel value={tabValue} index={2}>
        {renderAutomatedChecksTab()}
      </TabPanel>
      
      <TabPanel value={tabValue} index={3}>
        {renderAuditsTab()}
      </TabPanel>
      
      <TabPanel value={tabValue} index={4}>
        {renderReportsTab()}
      </TabPanel>

      {/* Create Framework Dialog */}
      <Dialog open={frameworkDialog} onClose={() => setFrameworkDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Compliance Framework</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Framework Name"
                value={newFrameworkData.name}
                onChange={(e) => setNewFrameworkData({ ...newFrameworkData, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Framework Type</InputLabel>
                <Select
                  value={newFrameworkData.type}
                  onChange={(e) => setNewFrameworkData({ ...newFrameworkData, type: e.target.value as any })}
                >
                  {frameworkTypes.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type.toUpperCase()}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Version"
                value={newFrameworkData.version}
                onChange={(e) => setNewFrameworkData({ ...newFrameworkData, version: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFrameworkDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateFramework} 
            variant="contained"
            disabled={!newFrameworkData.name}
          >
            Add Framework
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Check Dialog */}
      <Dialog open={checkDialog} onClose={() => setCheckDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Automated Check</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Check Name"
                value={newCheckData.check_name}
                onChange={(e) => setNewCheckData({ ...newCheckData, check_name: e.target.value })}
              />
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Framework</InputLabel>
                <Select
                  value={newCheckData.framework_id}
                  onChange={(e) => setNewCheckData({ ...newCheckData, framework_id: e.target.value })}
                >
                  {frameworks.map((framework) => (
                    <MenuItem key={framework.id} value={framework.id}>
                      {framework.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Check Type</InputLabel>
                <Select
                  value={newCheckData.check_type}
                  onChange={(e) => setNewCheckData({ ...newCheckData, check_type: e.target.value as any })}
                >
                  {checkTypes.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type.replace('_', ' ')}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Requirement ID"
                value={newCheckData.requirement_id}
                onChange={(e) => setNewCheckData({ ...newCheckData, requirement_id: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Frequency</InputLabel>
                <Select
                  value={newCheckData.frequency}
                  onChange={(e) => setNewCheckData({ ...newCheckData, frequency: e.target.value })}
                >
                  <MenuItem value="real_time">Real-time</MenuItem>
                  <MenuItem value="hourly">Hourly</MenuItem>
                  <MenuItem value="daily">Daily</MenuItem>
                  <MenuItem value="weekly">Weekly</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCheckDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateCheck} 
            variant="contained"
            disabled={!newCheckData.check_name || !newCheckData.framework_id}
          >
            Create Check
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ComplianceAutomation;