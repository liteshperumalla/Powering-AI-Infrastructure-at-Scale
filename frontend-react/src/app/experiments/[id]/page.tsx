'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';

interface Experiment {
  id: string;
  name: string;
  description: string;
  feature_flag: string;
  status: string;
  target_metric: string;
  created_at: string;
  started_at?: string;
  ended_at?: string;
  created_by: string;
  variants: Array<{
    id: string;
    name: string;
    type: string;
    traffic_percentage: number;
    configuration?: any;
    description?: string;
  }>;
  minimum_sample_size?: number;
  confidence_level?: number;
}

export default function ExperimentDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const experimentId = params.id as string;

  const [experiment, setExperiment] = useState<Experiment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadExperiment();
  }, [experimentId]);

  const loadExperiment = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/v2/experiments/${experimentId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token') || localStorage.getItem('access_token') || localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load experiment');
      }

      const data = await response.json();
      setExperiment(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load experiment details');
    } finally {
      setLoading(false);
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

  if (error || !experiment) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error">
          {error || 'Experiment not found'}
        </Alert>
        <Button startIcon={<ArrowBack />} onClick={() => router.back()} sx={{ mt: 2 }}>
          Back to Experiments
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => router.back()} sx={{ mb: 2 }}>
          Back to Experiments
        </Button>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
          <Box>
            <Typography variant="h4" gutterBottom>
              {experiment.name}
            </Typography>
            <Typography variant="body1" color="textSecondary">
              {experiment.description}
            </Typography>
          </Box>
          <Chip
            label={experiment.status.toUpperCase()}
            color={experiment.status === 'running' ? 'success' : experiment.status === 'completed' ? 'info' : 'default'}
            size="medium"
          />
        </Box>
      </Box>

      {/* Overview */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Feature Flag
              </Typography>
              <Typography variant="h6" component="code" sx={{
                background: 'rgba(255, 255, 255, 0.08)',
                padding: '4px 8px',
                borderRadius: 1,
                fontSize: '0.9rem'
              }}>
                {experiment.feature_flag}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Target Metric
              </Typography>
              <Typography variant="h6">
                {experiment.target_metric}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Sample Size
              </Typography>
              <Typography variant="h6">
                {experiment.minimum_sample_size || 1000}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Confidence Level
              </Typography>
              <Typography variant="h6">
                {((experiment.confidence_level || 0.95) * 100).toFixed(0)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Variants */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Experiment Variants
        </Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Variant Name</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Traffic %</TableCell>
                <TableCell>Description</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {experiment.variants.map((variant) => (
                <TableRow key={variant.id}>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {variant.name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip label={variant.type} size="small" />
                  </TableCell>
                  <TableCell>{variant.traffic_percentage}%</TableCell>
                  <TableCell>
                    <Typography variant="body2" color="textSecondary">
                      {variant.description || 'No description'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Variant Configurations */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Variant Configurations
        </Typography>
        <Grid container spacing={2}>
          {experiment.variants.map((variant) => (
            <Grid item xs={12} md={6} key={variant.id}>
              <Card sx={{ backgroundColor: 'rgba(255, 255, 255, 0.02)' }}>
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    {variant.name}
                  </Typography>
                  <Box component="pre" sx={{
                    mt: 2,
                    p: 2,
                    backgroundColor: 'rgba(0, 0, 0, 0.2)',
                    borderRadius: 1,
                    fontSize: '0.75rem',
                    overflow: 'auto',
                    maxHeight: 400
                  }}>
                    {JSON.stringify(variant.configuration || {}, null, 2)}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Metadata */}
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Metadata
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <Typography color="textSecondary">Created By</Typography>
            <Typography variant="body1">{experiment.created_by}</Typography>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography color="textSecondary">Created At</Typography>
            <Typography variant="body1">{new Date(experiment.created_at).toLocaleString()}</Typography>
          </Grid>
          {experiment.started_at && (
            <Grid item xs={12} sm={4}>
              <Typography color="textSecondary">Started At</Typography>
              <Typography variant="body1">{new Date(experiment.started_at).toLocaleString()}</Typography>
            </Grid>
          )}
          {experiment.ended_at && (
            <Grid item xs={12} sm={4}>
              <Typography color="textSecondary">Ended At</Typography>
              <Typography variant="body1">{new Date(experiment.ended_at).toLocaleString()}</Typography>
            </Grid>
          )}
        </Grid>
      </Paper>
    </Container>
  );
}
