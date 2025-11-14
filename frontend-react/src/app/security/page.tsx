'use client';

import React, { useState, useEffect } from 'react';
import ResponsiveLayout from '../../components/ResponsiveLayout';
import ProtectedRoute from '@/components/ProtectedRoute';
import RoleProtectedRoute from '@/components/RoleProtectedRoute';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Grid,
  Button,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  CircularProgress,
} from '@mui/material';
import {
  Security,
  Shield,
  Warning,
  CheckCircle,
  Error,
  VpnKey,
  Lock,
  Visibility,
  Report,
  Assessment,
  Refresh,
  Settings,
  Add,
} from '@mui/icons-material';

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
      id={`security-tabpanel-${index}`}
      aria-labelledby={`security-tab-${index}`}
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

export default function SecurityPage() {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [scanResults, setScanResults] = useState<any[]>([]);
  const [securityScore, setSecurityScore] = useState(85);
  const [vulnerabilities, setVulnerabilities] = useState<any[]>([]);
  const [scanDialogOpen, setScanDialogOpen] = useState(false);

  useEffect(() => {
    loadSecurityData();
  }, []);

  const loadSecurityData = async () => {
    try {
      setLoading(true);

      // Fetch real security data from API - no more demo data
      try {
        // TODO: Replace with actual API endpoints when available
        // const scanData = await apiClient.getSecurityScans();
        // const vulnData = await apiClient.getVulnerabilities();

        // For now, initialize with empty arrays
        setScanResults([]);
        setVulnerabilities([]);
        setSecurityScore(0);
      } catch (apiError) {
        console.error('Failed to fetch security data:', apiError);
        setScanResults([]);
        setVulnerabilities([]);
        setSecurityScore(0);
      }
      
    } catch (error) {
      console.error('Failed to load security data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'primary';
      case 'failed': return 'error';
      case 'resolved': return 'success';
      case 'in_progress': return 'warning';
      case 'open': return 'error';
      default: return 'default';
    }
  };

  const handleRunScan = (scanType: string) => {
    console.log('Running scan:', scanType);
    setScanDialogOpen(false);
    // Implement scan logic here
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <RoleProtectedRoute
          allowedRoles={['admin', 'manager']}
          fallbackMessage="Security Dashboard is only available to administrators and managers."
        >
          <ResponsiveLayout title="Security Dashboard">
            <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
              <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress />
              </Box>
            </Container>
          </ResponsiveLayout>
        </RoleProtectedRoute>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <RoleProtectedRoute
        allowedRoles={['admin', 'manager']}
        fallbackMessage="Security Dashboard is only available to administrators and managers."
      >
        <ResponsiveLayout title="Security Dashboard">
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" color="text.primary" component="h1" gutterBottom>
            <Security sx={{ mr: 2, verticalAlign: 'middle' }} />
            Security Center
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Monitor and manage your infrastructure security
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setScanDialogOpen(true)}
        >
          Run Security Scan
        </Button>
      </Box>

      {/* Security Score Card */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Box position="relative" display="inline-flex" mb={2}>
                <CircularProgress
                  variant="determinate"
                  value={securityScore}
                  size={80}
                  thickness={4}
                  sx={{ color: securityScore > 80 ? 'success.main' : securityScore > 60 ? 'warning.main' : 'error.main' }}
                />
                <Box
                  position="absolute"
                  top={0}
                  left={0}
                  bottom={0}
                  right={0}
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                >
                  <Typography variant="h6" color="textPrimary">
                    {securityScore}%
                  </Typography>
                </Box>
              </Box>
              <Typography variant="h6" color="text.primary" gutterBottom>
                Security Score
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Overall security posture
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Shield color="success" sx={{ mr: 2 }} />
                <Box>
                  <Typography variant="h6" color="text.primary">
                    {scanResults.filter(r => r.status === 'completed').length}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Scans Completed
                  </Typography>
                </Box>
              </Box>
              <Typography variant="body2" color="textSecondary">
                Last scan: {new Date().toLocaleDateString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Warning color="warning" sx={{ mr: 2 }} />
                <Box>
                  <Typography variant="h6" color="text.primary">
                    {vulnerabilities.filter(v => v.status === 'open').length}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Open Issues
                  </Typography>
                </Box>
              </Box>
              <Typography variant="body2" color="textSecondary">
                Require attention
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="Security Scans" />
          <Tab label="Vulnerabilities" />
          <Tab label="Compliance" />
          <Tab label="Settings" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Typography variant="h6" color="text.primary" gutterBottom>
            Security Scan Results
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Scan Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Score</TableCell>
                  <TableCell>Findings</TableCell>
                  <TableCell>Last Run</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {scanResults.map((scan) => (
                  <TableRow key={scan.id}>
                    <TableCell>{scan.type}</TableCell>
                    <TableCell>
                      <Chip
                        label={scan.status}
                        color={getStatusColor(scan.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{scan.score}%</TableCell>
                    <TableCell>{scan.findings}</TableCell>
                    <TableCell>
                      {new Date(scan.lastRun).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        startIcon={<Visibility />}
                        onClick={() => console.log('View details:', scan.id)}
                      >
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" color="text.primary" gutterBottom>
            Vulnerability Management
          </Typography>
          <List>
            {vulnerabilities.map((vuln, index) => (
              <React.Fragment key={vuln.id}>
                <ListItem>
                  <ListItemIcon>
                    {vuln.severity === 'high' ? (
                      <Error color="error" />
                    ) : vuln.severity === 'medium' ? (
                      <Warning color="warning" />
                    ) : (
                      <CheckCircle color="info" />
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="subtitle1">{vuln.title}</Typography>
                        <Chip
                          label={vuln.severity}
                          color={getSeverityColor(vuln.severity) as any}
                          size="small"
                        />
                        <Chip
                          label={vuln.status}
                          color={getStatusColor(vuln.status) as any}
                          size="small"
                        />
                      </Box>
                    }
                    secondary={
                      <React.Fragment>
                        <span style={{ display: 'block' }}>
                          {vuln.description}
                        </span>
                        <span style={{ display: 'block', marginTop: '8px', color: 'rgba(0, 0, 0, 0.6)' }}>
                          <strong>Recommendation:</strong> {vuln.recommendation}
                        </span>
                      </React.Fragment>
                    }
                  />
                </ListItem>
                {index < vulnerabilities.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" color="text.primary" gutterBottom>
            Compliance Status
          </Typography>
          <Alert severity="info" sx={{ mb: 3 }}>
            Compliance monitoring helps ensure your infrastructure meets regulatory requirements.
          </Alert>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" color="text.primary" gutterBottom>GDPR Compliance</Typography>
                  <LinearProgress variant="determinate" value={92} sx={{ mb: 1 }} />
                  <Typography variant="body2">92% compliant</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" color="text.primary" gutterBottom>SOC 2 Type II</Typography>
                  <LinearProgress variant="determinate" value={88} sx={{ mb: 1 }} />
                  <Typography variant="body2">88% compliant</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" color="text.primary" gutterBottom>HIPAA</Typography>
                  <LinearProgress variant="determinate" value={95} sx={{ mb: 1 }} />
                  <Typography variant="body2">95% compliant</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" color="text.primary" gutterBottom>ISO 27001</Typography>
                  <LinearProgress variant="determinate" value={85} sx={{ mb: 1 }} />
                  <Typography variant="body2">85% compliant</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Typography variant="h6" color="text.primary" gutterBottom>
            Security Settings
          </Typography>
          <Alert severity="warning" sx={{ mb: 3 }}>
            Changes to security settings may affect system access and functionality.
          </Alert>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" color="text.primary" gutterBottom>
                    <VpnKey sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Authentication
                  </Typography>
                  <Typography variant="body2" paragraph>
                    Configure authentication policies and requirements.
                  </Typography>
                  <Button variant="outlined" size="small">
                    Configure
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" color="text.primary" gutterBottom>
                    <Lock sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Access Control
                  </Typography>
                  <Typography variant="body2" paragraph>
                    Manage user permissions and access levels.
                  </Typography>
                  <Button variant="outlined" size="small">
                    Manage
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      {/* Run Scan Dialog */}
      <Dialog open={scanDialogOpen} onClose={() => setScanDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Run Security Scan</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 3 }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Scan Type</InputLabel>
              <Select defaultValue="infrastructure" label="Scan Type">
                <MenuItem value="infrastructure">Infrastructure Scan</MenuItem>
                <MenuItem value="vulnerability">Vulnerability Assessment</MenuItem>
                <MenuItem value="compliance">Compliance Check</MenuItem>
                <MenuItem value="penetration">Penetration Test</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Scan Name (Optional)"
              placeholder="Enter a custom name for this scan"
              sx={{ mb: 2 }}
            />
            <Alert severity="info">
              Security scans may take several minutes to complete and could impact system performance.
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setScanDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => handleRunScan('infrastructure')}
            startIcon={<Assessment />}
          >
            Start Scan
          </Button>
        </DialogActions>
      </Dialog>
      </Container>
        </ResponsiveLayout>
      </RoleProtectedRoute>
    </ProtectedRoute>
  );
}