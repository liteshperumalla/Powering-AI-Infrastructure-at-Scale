'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  Alert,
  Tabs,
  Tab,
  CircularProgress,
  Rating,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  Dashboard,
  TrendingUp,
  Assessment,
  BugReport,
  CheckCircle,
  Warning,
  Error,
  Speed,
  Security,
  Visibility,
  Add,
  Refresh
} from '@mui/icons-material';
import {
  getQualityOverview,
  getQualityMetrics,
  createQualityMetric,
  getQualityReports,
  generateQualityReport,
  QualityOverview,
  QualityMetric,
  QualityReport,
  QualityThreshold,
  CreateQualityMetricRequest
} from '../../services/quality';

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
      id={`quality-tabpanel-${index}`}
      aria-labelledby={`quality-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function QualityPage() {
  const [currentTab, setCurrentTab] = useState(0);
  const [overview, setOverview] = useState<QualityOverview | null>(null);
  const [metrics, setMetrics] = useState<QualityMetric[]>([]);
  const [reports, setReports] = useState<QualityReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createMetricOpen, setCreateMetricOpen] = useState(false);
  const [generateReportLoading, setGenerateReportLoading] = useState(false);

  // Create Metric Form State
  const [newMetric, setNewMetric] = useState<CreateQualityMetricRequest>({
    target_type: 'assessment',
    target_id: '',
    metric_name: '',
    metric_value: 0,
    quality_score: 0
  });

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [overviewData, metricsData, reportsData] = await Promise.all([
        getQualityOverview(),
        getQualityMetrics(),
        getQualityReports()
      ]);
      setOverview(overviewData);
      setMetrics(metricsData);
      setReports(reportsData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load quality data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleCreateMetric = async () => {
    try {
      await createQualityMetric(newMetric);
      setCreateMetricOpen(false);
      setNewMetric({
        target_type: 'assessment',
        target_id: '',
        metric_name: '',
        metric_value: 0,
        quality_score: 0
      });
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create quality metric');
    }
  };

  const handleGenerateReport = async () => {
    try {
      setGenerateReportLoading(true);
      await generateQualityReport({
        report_type: 'comprehensive',
        target_types: ['assessment', 'recommendation', 'report'],
        date_range: 30
      });
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate quality report');
    } finally {
      setGenerateReportLoading(false);
    }
  };

  const getQualityScoreColor = (score: number) => {
    if (score >= 90) return 'success';
    if (score >= 70) return 'warning';
    return 'error';
  };

  const getQualityScoreIcon = (score: number) => {
    if (score >= 90) return <CheckCircle color="success" />;
    if (score >= 70) return <Warning color="warning" />;
    return <Error color="error" />;
  };

  if (loading) {
    return (
      <Container>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Quality Assurance Dashboard
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Monitor and manage quality metrics across your infrastructure assessments
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={handleTabChange}>
          <Tab label="Overview" icon={<Dashboard />} />
          <Tab label="Metrics" icon={<TrendingUp />} />
          <Tab label="Reports" icon={<Assessment />} />
        </Tabs>
      </Box>

      <TabPanel value={currentTab} index={0}>
        {overview && (
          <>
            <Grid container spacing={3} sx={{ mb: 4 }}>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Speed color="primary" sx={{ mr: 1 }} />
                      <Typography variant="h6">Overall Score</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography variant="h3" color="primary" sx={{ mr: 1 }}>
                        {overview.overall_quality_score}
                      </Typography>
                      {getQualityScoreIcon(overview.overall_quality_score)}
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={overview.overall_quality_score}
                      color={getQualityScoreColor(overview.overall_quality_score)}
                      sx={{ mt: 1 }}
                    />
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Assessment color="secondary" sx={{ mr: 1 }} />
                      <Typography variant="h6">Total Metrics</Typography>
                    </Box>
                    <Typography variant="h3" color="secondary">
                      {overview.total_metrics}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <CheckCircle color="success" sx={{ mr: 1 }} />
                      <Typography variant="h6">Passing</Typography>
                    </Box>
                    <Typography variant="h3" color="success.main">
                      {overview.metrics_above_threshold}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Warning color="warning" sx={{ mr: 1 }} />
                      <Typography variant="h6">Below Threshold</Typography>
                    </Box>
                    <Typography variant="h3" color="warning.main">
                      {overview.metrics_below_threshold}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Quality by Category
              </Typography>
              <Grid container spacing={2}>
                {Object.entries(overview.quality_by_target_type).map(([type, score]) => (
                  <Grid item xs={12} md={4} key={type}>
                    <Box sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                          {type}
                        </Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {score}%
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={score}
                        color={getQualityScoreColor(score)}
                      />
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </Paper>

            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Quality Thresholds
              </Typography>
              <List>
                {overview.thresholds.map((threshold: QualityThreshold, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      {threshold.operator === '>=' ? <TrendingUp /> : <Speed />}
                    </ListItemIcon>
                    <ListItemText
                      primary={`${threshold.metric_name}`}
                      secondary={`${threshold.operator} ${threshold.threshold_value}`}
                    />
                    <Chip
                      label={threshold.is_active ? 'Active' : 'Inactive'}
                      color={threshold.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </>
        )}
      </TabPanel>

      <TabPanel value={currentTab} index={1}>
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">Quality Metrics</Typography>
          <Box>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={fetchData}
              sx={{ mr: 2 }}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setCreateMetricOpen(true)}
            >
              Add Metric
            </Button>
          </Box>
        </Box>

        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Target Type</TableCell>
                <TableCell>Target ID</TableCell>
                <TableCell>Metric Name</TableCell>
                <TableCell align="right">Metric Value</TableCell>
                <TableCell align="right">Quality Score</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created At</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {metrics.map((metric, index) => (
                <TableRow key={index}>
                  <TableCell>
                    <Chip
                      label={metric.target_type}
                      size="small"
                      variant="outlined"
                      sx={{ textTransform: 'capitalize' }}
                    />
                  </TableCell>
                  <TableCell>{metric.target_id}</TableCell>
                  <TableCell>{metric.metric_name}</TableCell>
                  <TableCell align="right">{metric.metric_value}</TableCell>
                  <TableCell align="right">
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                      <Typography variant="body2" sx={{ mr: 1 }}>
                        {metric.quality_score}
                      </Typography>
                      {getQualityScoreIcon(metric.quality_score)}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={metric.quality_score >= 70 ? 'Passing' : 'Below Threshold'}
                      color={metric.quality_score >= 70 ? 'success' : 'error'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {new Date(metric.created_at).toLocaleDateString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      <TabPanel value={currentTab} index={2}>
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">Quality Reports</Typography>
          <Button
            variant="contained"
            startIcon={generateReportLoading ? <CircularProgress size={20} /> : <Add />}
            onClick={handleGenerateReport}
            disabled={generateReportLoading}
          >
            {generateReportLoading ? 'Generating...' : 'Generate Report'}
          </Button>
        </Box>

        <Grid container spacing={3}>
          {reports.map((report, index) => (
            <Grid item xs={12} md={6} key={index}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {report.report_type} Report
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Generated: {new Date(report.generated_at).toLocaleString()}
                  </Typography>
                  
                  <Box sx={{ mt: 2, mb: 2 }}>
                    <Typography variant="body2" gutterBottom>
                      Overall Score: <strong>{report.overall_score}</strong>
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={report.overall_score}
                      color={getQualityScoreColor(report.overall_score)}
                    />
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  <Typography variant="subtitle2" gutterBottom>
                    Key Findings:
                  </Typography>
                  <List dense>
                    {report.findings.slice(0, 3).map((finding, findingIndex) => (
                      <ListItem key={findingIndex} sx={{ px: 0 }}>
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          {finding.severity === 'high' && <Error color="error" fontSize="small" />}
                          {finding.severity === 'medium' && <Warning color="warning" fontSize="small" />}
                          {finding.severity === 'low' && <CheckCircle color="success" fontSize="small" />}
                        </ListItemIcon>
                        <ListItemText
                          primary={finding.title}
                          secondary={finding.description}
                          primaryTypographyProps={{ variant: 'body2' }}
                          secondaryTypographyProps={{ variant: 'caption' }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </TabPanel>

      <Dialog open={createMetricOpen} onClose={() => setCreateMetricOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Quality Metric</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                select
                fullWidth
                label="Target Type"
                value={newMetric.target_type}
                onChange={(e) => setNewMetric({ ...newMetric, target_type: e.target.value as any })}
              >
                <MenuItem value="assessment">Assessment</MenuItem>
                <MenuItem value="recommendation">Recommendation</MenuItem>
                <MenuItem value="report">Report</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Target ID"
                value={newMetric.target_id}
                onChange={(e) => setNewMetric({ ...newMetric, target_id: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Metric Name"
                value={newMetric.metric_name}
                onChange={(e) => setNewMetric({ ...newMetric, metric_name: e.target.value })}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                type="number"
                label="Metric Value"
                value={newMetric.metric_value}
                onChange={(e) => setNewMetric({ ...newMetric, metric_value: parseFloat(e.target.value) })}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                type="number"
                label="Quality Score"
                value={newMetric.quality_score}
                onChange={(e) => setNewMetric({ ...newMetric, quality_score: parseFloat(e.target.value) })}
                inputProps={{ min: 0, max: 100 }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateMetricOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateMetric} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}