'use client';

import React, { useState, useEffect } from 'react';
import ResponsiveLayout from '../../components/ResponsiveLayout';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  useTheme,
} from '@mui/material';
import {
  Science,
  Add,
  TrendingUp,
  People,
  Timeline,
  PlayArrow,
  Pause,
  Stop,
} from '@mui/icons-material';
import { getExperiments, createExperiment, getExperimentDashboard, Experiment } from '../../services/experiments';

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
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
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

export default function ExperimentsPage() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const theme = useTheme();

  // New experiment form state
  const [newExperiment, setNewExperiment] = useState({
    name: '',
    description: '',
    feature_flag: '',
    target_metric: 'conversion_rate',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [experimentsData, dashData] = await Promise.all([
        getExperiments().catch(() => []),
        getExperimentDashboard().catch(() => null)
      ]);
      
      setExperiments(experimentsData);
      setDashboardData(dashData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateExperiment = async () => {
    try {
      const created = await createExperiment({
        ...newExperiment,
        variants: ['control', 'treatment'], // Default variants
        status: 'draft',
      });
      
      setExperiments(prev => [...prev, created]);
      setCreateDialogOpen(false);
      setNewExperiment({
        name: '',
        description: '',
        feature_flag: '',
        target_metric: 'conversion_rate',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create experiment');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'success';
      case 'draft': return 'default';
      case 'completed': return 'info';
      case 'paused': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <PlayArrow fontSize="small" />;
      case 'paused': return <Pause fontSize="small" />;
      case 'completed': return <Stop fontSize="small" />;
      default: return null;
    }
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <ResponsiveLayout>
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            <Science sx={{ mr: 2, verticalAlign: 'middle' }} />
            A/B Testing & Experiments
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Design and run experiments to test infrastructure changes safely
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setCreateDialogOpen(true)}
          sx={{ height: 'fit-content' }}
        >
          Create Experiment
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Dashboard Stats */}
      {dashboardData && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <Science color="primary" sx={{ mr: 2 }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Active Experiments
                    </Typography>
                    <Typography variant="h5">
                      {experiments.filter(e => e.status === 'running').length}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <TrendingUp color="success" sx={{ mr: 2 }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Conversion Rate
                    </Typography>
                    <Typography variant="h5">
                      {dashboardData.overall_conversion_rate || '12.5'}%
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <People color="info" sx={{ mr: 2 }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Total Users
                    </Typography>
                    <Typography variant="h5">
                      {dashboardData.total_users || '1,234'}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <Timeline color="warning" sx={{ mr: 2 }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Avg. Test Duration
                    </Typography>
                    <Typography variant="h5">
                      {dashboardData.avg_duration || '14'} days
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="All Experiments" />
          <Tab label="Running" />
          <Tab label="Results" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          {/* All Experiments Table */}
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Feature Flag</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Target Metric</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {experiments.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                      <Typography color="textSecondary">
                        No experiments found. Create your first experiment to get started.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  experiments.map((experiment) => (
                    <TableRow key={experiment.id}>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {experiment.name}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {experiment.description}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <code style={{ 
                          background: theme.palette.grey[100], 
                          padding: '2px 8px', 
                          borderRadius: 4,
                          fontSize: '0.875rem'
                        }}>
                          {experiment.feature_flag}
                        </code>
                      </TableCell>
                      <TableCell>
                        <Chip
                          icon={getStatusIcon(experiment.status)}
                          label={experiment.status.toUpperCase()}
                          color={getStatusColor(experiment.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{experiment.target_metric}</TableCell>
                      <TableCell>
                        {new Date(experiment.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Button size="small" variant="outlined">
                          View Details
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>Running Experiments</Typography>
          <Typography color="textSecondary">
            {experiments.filter(e => e.status === 'running').length} active experiments
          </Typography>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>Experiment Results</Typography>
          <Typography color="textSecondary">
            View detailed results and statistical significance
          </Typography>
        </TabPanel>
      </Paper>

      {/* Create Experiment Dialog */}
      <Dialog 
        open={createDialogOpen} 
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New Experiment</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="Experiment Name"
              fullWidth
              value={newExperiment.name}
              onChange={(e) => setNewExperiment(prev => ({ ...prev, name: e.target.value }))}
              placeholder="e.g., New Recommendation Algorithm"
            />
            
            <TextField
              label="Description"
              multiline
              rows={3}
              fullWidth
              value={newExperiment.description}
              onChange={(e) => setNewExperiment(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Describe what this experiment tests..."
            />
            
            <TextField
              label="Feature Flag"
              fullWidth
              value={newExperiment.feature_flag}
              onChange={(e) => setNewExperiment(prev => ({ ...prev, feature_flag: e.target.value }))}
              placeholder="e.g., new-recommendation-algorithm"
              helperText="Use lowercase with hyphens"
            />
            
            <FormControl fullWidth>
              <InputLabel>Target Metric</InputLabel>
              <Select
                value={newExperiment.target_metric}
                onChange={(e) => setNewExperiment(prev => ({ ...prev, target_metric: e.target.value }))}
                label="Target Metric"
              >
                <MenuItem value="conversion_rate">Conversion Rate</MenuItem>
                <MenuItem value="click_through_rate">Click Through Rate</MenuItem>
                <MenuItem value="user_engagement">User Engagement</MenuItem>
                <MenuItem value="performance_improvement">Performance Improvement</MenuItem>
                <MenuItem value="cost_reduction">Cost Reduction</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={handleCreateExperiment}
            disabled={!newExperiment.name || !newExperiment.feature_flag}
          >
            Create Experiment
          </Button>
        </DialogActions>
      </Dialog>
      </Container>
    </ResponsiveLayout>
  );
}