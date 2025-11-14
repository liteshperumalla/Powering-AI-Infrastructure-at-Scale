/**
 * Error Boundary Wrapper - Prevents component crashes from breaking entire app
 *
 * Usage:
 * <ErrorBoundaryWrapper fallback={<ErrorFallback />}>
 *   <YourComponent />
 * </ErrorBoundaryWrapper>
 */

'use client';

import React, { Component, ReactNode } from 'react';
import { Box, Button, Typography, Paper } from '@mui/material';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundaryWrapper extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Paper sx={{ p: 3, m: 2, textAlign: 'center' }}>
          <ErrorOutlineIcon sx={{ fontSize: 48, color: 'error.main', mb: 2 }} />
          <Typography variant="h6" color="text.primary" gutterBottom>
            Something went wrong
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {this.state.error?.message || 'An unexpected error occurred'}
          </Typography>
          <Button variant="contained" onClick={this.handleReset}>
            Try Again
          </Button>
        </Paper>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundaryWrapper;
