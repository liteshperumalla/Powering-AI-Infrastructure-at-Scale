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
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Rating,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Feedback,
  Send,
  Analytics,
  TrendingUp,
  ThumbUp,
  ThumbDown,
  Face as Sentiment,
} from '@mui/icons-material';
import { 
  submitFeedback, 
  getFeedbackAnalytics, 
  getFeedbackSummary, 
  getFeedbackList, 
  UserFeedback,
  FeedbackType,
  FeedbackAnalytics,
  useFeedbackSubmission 
} from '../../services/feedback';

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
      id={`feedback-tabpanel-${index}`}
      aria-labelledby={`feedback-tab-${index}`}
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

export default function FeedbackPage() {
  const [tabValue, setTabValue] = useState(0);
  const [analytics, setAnalytics] = useState<FeedbackAnalytics | null>(null);
  const [recentFeedback, setRecentFeedback] = useState<UserFeedback[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Feedback form state
  const [feedbackForm, setFeedbackForm] = useState({
    feedback_type: 'general' as FeedbackType,
    rating: 5,
    comments: '',
  });

  const { submit: submitFeedbackForm, loading: submitting, error: submitError, success, reset } = useFeedbackSubmission();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [analyticsData, feedbackData] = await Promise.all([
        getFeedbackAnalytics().catch(() => null),
        getFeedbackList({ limit: 10 }).catch(() => [])
      ]);
      
      setAnalytics(analyticsData);
      setRecentFeedback(feedbackData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitFeedback = async () => {
    try {
      await submitFeedbackForm(feedbackForm);
      // Reset form on success
      setFeedbackForm({
        feedback_type: 'general' as FeedbackType,
        rating: 5,
        comments: '',
      });
      // Reload data to show new feedback
      loadData();
    } catch (err) {
      // Error handled by hook
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'success';
      case 'negative': return 'error';
      case 'neutral': return 'default';
      default: return 'default';
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return <ThumbUp fontSize="small" />;
      case 'negative': return <ThumbDown fontSize="small" />;
      case 'neutral': return <Sentiment fontSize="small" />;
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
    <ResponsiveLayout title="User Feedback">
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" color="text.primary" component="h1" gutterBottom>
            <Feedback sx={{ mr: 2, verticalAlign: 'middle' }} />
            User Feedback
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Collect and analyze user feedback for continuous improvement
          </Typography>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Analytics Cards */}
      {analytics && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <Feedback color="primary" sx={{ mr: 2 }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Total Feedback
                    </Typography>
                    <Typography variant="h5" color="text.primary">
                      {analytics.total_feedback.toLocaleString()}
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
                      Average Rating
                    </Typography>
                    <Box display="flex" alignItems="center">
                      <Typography variant="h5" color="text.primary" sx={{ mr: 1 }}>
                        {analytics.average_rating.toFixed(1)}
                      </Typography>
                      <Rating value={analytics.average_rating} readOnly size="small" />
                    </Box>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <ThumbUp color="success" sx={{ mr: 2 }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Positive Sentiment
                    </Typography>
                    <Typography variant="h5" color="text.primary">
                      {analytics.sentiment_breakdown.positive}%
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
                  <Analytics color="info" sx={{ mr: 2 }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Response Rate
                    </Typography>
                    <Typography variant="h5" color="text.primary">
                      {((analytics.total_feedback / 1000) * 100).toFixed(1)}%
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
          <Tab label="Submit Feedback" />
          <Tab label="Recent Feedback" />
          <Tab label="Analytics" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          {/* Submit Feedback Form */}
          <Box maxWidth="md">
            <Typography variant="h6" color="text.primary" gutterBottom>
              Share Your Feedback
            </Typography>
            <Typography variant="body2" color="textSecondary" paragraph>
              Your feedback helps us improve the platform. Please share your thoughts and experiences.
            </Typography>

            {success && (
              <Alert severity="success" sx={{ mb: 3 }}>
                Thank you for your feedback! It has been submitted successfully.
              </Alert>
            )}

            {submitError && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {submitError}
              </Alert>
            )}

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <FormControl fullWidth>
                <InputLabel>Feedback Type</InputLabel>
                <Select
                  value={feedbackForm.feedback_type}
                  onChange={(e) => setFeedbackForm(prev => ({ ...prev, feedback_type: e.target.value as FeedbackType }))}
                  label="Feedback Type"
                >
                  <MenuItem value="assessment_quality">Assessment Quality</MenuItem>
                  <MenuItem value="ui_experience">UI Experience</MenuItem>
                  <MenuItem value="performance">Performance</MenuItem>
                  <MenuItem value="feature_request">Feature Request</MenuItem>
                  <MenuItem value="bug_report">Bug Report</MenuItem>
                  <MenuItem value="general">General</MenuItem>
                </Select>
              </FormControl>

              <Box>
                <Typography component="legend" gutterBottom>
                  Overall Rating
                </Typography>
                <Rating
                  value={feedbackForm.rating}
                  onChange={(_, value) => setFeedbackForm(prev => ({ ...prev, rating: value || 5 }))}
                  size="large"
                />
              </Box>

              <TextField
                label="Comments"
                multiline
                rows={4}
                fullWidth
                value={feedbackForm.comments}
                onChange={(e) => setFeedbackForm(prev => ({ ...prev, comments: e.target.value }))}
                placeholder="Please share your detailed feedback, suggestions, or report any issues..."
                helperText={`${feedbackForm.comments.length}/500 characters`}
                inputProps={{ maxLength: 500 }}
              />

              <Box display="flex" justifyContent="flex-start">
                <Button
                  variant="contained"
                  startIcon={<Send />}
                  onClick={handleSubmitFeedback}
                  disabled={submitting || !feedbackForm.comments.trim()}
                  sx={{ minWidth: 150 }}
                >
                  {submitting ? <CircularProgress size={20} /> : 'Submit Feedback'}
                </Button>
              </Box>
            </Box>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {/* Recent Feedback */}
          <Typography variant="h6" color="text.primary" gutterBottom>Recent Feedback</Typography>
          
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Type</TableCell>
                  <TableCell>Rating</TableCell>
                  <TableCell>Comments</TableCell>
                  <TableCell>Sentiment</TableCell>
                  <TableCell>Date</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {recentFeedback.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                      <Typography color="textSecondary">
                        No recent feedback found.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  recentFeedback.map((feedback, index) => (
                    <TableRow key={feedback.id || index}>
                      <TableCell>
                        <Chip
                          label={feedback.feedback_type.replace('_', ' ')}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Rating value={feedback.rating || 0} readOnly size="small" />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ maxWidth: 300 }}>
                          {feedback.comments || 'No comments'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {feedback.sentiment && (
                          <Chip
                            icon={getSentimentIcon(feedback.sentiment)}
                            label={feedback.sentiment}
                            color={getSentimentColor(feedback.sentiment) as any}
                            size="small"
                          />
                        )}
                      </TableCell>
                      <TableCell>
                        {feedback.created_at ? new Date(feedback.created_at).toLocaleDateString() : 'N/A'}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          {/* Analytics */}
          <Typography variant="h6" color="text.primary" gutterBottom>Feedback Analytics</Typography>
          
          {analytics && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" color="text.primary" gutterBottom>
                      Feedback by Type
                    </Typography>
                    {Object.entries(analytics.by_type).map(([type, data]) => (
                      <Box key={type} sx={{ mb: 2 }}>
                        <Box display="flex" justifyContent="space-between" mb={1}>
                          <Typography variant="body2">
                            {type.replace('_', ' ')}
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            {data.count} ({data.average_rating.toFixed(1)} avg)
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={(data.count / analytics.total_feedback) * 100}
                          sx={{ height: 8, borderRadius: 4 }}
                        />
                      </Box>
                    ))}
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" color="text.primary" gutterBottom>
                      Sentiment Distribution
                    </Typography>
                    <Box sx={{ mb: 3 }}>
                      <Box display="flex" alignItems="center" mb={2}>
                        <ThumbUp color="success" sx={{ mr: 2 }} />
                        <Box flex={1}>
                          <Box display="flex" justifyContent="space-between" mb={1}>
                            <Typography variant="body2">Positive</Typography>
                            <Typography variant="body2" color="textSecondary">
                              {analytics.sentiment_breakdown.positive}%
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={analytics.sentiment_breakdown.positive}
                            color="success"
                            sx={{ height: 8, borderRadius: 4 }}
                          />
                        </Box>
                      </Box>
                      
                      <Box display="flex" alignItems="center" mb={2}>
                        <Sentiment color="action" sx={{ mr: 2 }} />
                        <Box flex={1}>
                          <Box display="flex" justifyContent="space-between" mb={1}>
                            <Typography variant="body2">Neutral</Typography>
                            <Typography variant="body2" color="textSecondary">
                              {analytics.sentiment_breakdown.neutral}%
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={analytics.sentiment_breakdown.neutral}
                            color="inherit"
                            sx={{ height: 8, borderRadius: 4 }}
                          />
                        </Box>
                      </Box>
                      
                      <Box display="flex" alignItems="center">
                        <ThumbDown color="error" sx={{ mr: 2 }} />
                        <Box flex={1}>
                          <Box display="flex" justifyContent="space-between" mb={1}>
                            <Typography variant="body2">Negative</Typography>
                            <Typography variant="body2" color="textSecondary">
                              {analytics.sentiment_breakdown.negative}%
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={analytics.sentiment_breakdown.negative}
                            color="error"
                            sx={{ height: 8, borderRadius: 4 }}
                          />
                        </Box>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </TabPanel>
      </Paper>
    </Container>
    </ResponsiveLayout>
  );
}

<system-reminder>
The TodoWrite tool hasn't been used recently. If you're working on tasks that would benefit from tracking progress, consider using the TodoWrite tool to track progress. Also consider cleaning up the todo list if has become stale and no longer matches what you are working on. Only use it if it's relevant to the current work. This is just a gentle reminder - ignore if not applicable.


Here are the existing contents of your todo list:

[1. [completed] Enhance test coverage across the platform
2. [completed] Optimize database queries for production scale
3. [completed] Complete API documentation
4. [pending] Production deployment preparation
5. [in_progress] User acceptance testing and refinements]
</system-reminder>