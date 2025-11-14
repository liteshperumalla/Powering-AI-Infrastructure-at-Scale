'use client';

import React from 'react';
import { Component, ReactNode } from 'react';
import {
    Box,
    Typography,
    Button,
    Card,
    CardContent,
    Alert,
} from '@mui/material';
import { Refresh, Warning } from '@mui/icons-material';

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error?: Error;
}

export default class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error('ErrorBoundary caught an error:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <Box
                    sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        minHeight: '400px',
                        p: 4,
                    }}
                >
                    <Card sx={{ maxWidth: 600, width: '100%' }}>
                        <CardContent sx={{ textAlign: 'center', p: 4 }}>
                            <Warning sx={{ fontSize: 64, color: '#f44336', mb: 2 }} />
                            <Typography variant="h5" color="text.primary" gutterBottom>
                                Oops! Something went wrong
                            </Typography>
                            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                                An unexpected error occurred. Please try refreshing the page or contact support if the problem persists.
                            </Typography>
                            
                            {process.env.NODE_ENV === 'development' && this.state.error && (
                                <Alert severity="error" sx={{ mb: 3, textAlign: 'left' }}>
                                    <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                                        {this.state.error.message}
                                    </Typography>
                                </Alert>
                            )}

                            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
                                <Button
                                    variant="contained"
                                    onClick={() => window.location.reload()}
                                    startIcon={<Refresh />}
                                >
                                    Refresh Page
                                </Button>
                                <Button
                                    variant="outlined"
                                    onClick={() => this.setState({ hasError: false })}
                                >
                                    Try Again
                                </Button>
                            </Box>
                        </CardContent>
                    </Card>
                </Box>
            );
        }

        return this.props.children;
    }
}

// Functional error boundary hook for React components
export function useErrorHandler() {
    return (error: Error, errorInfo?: React.ErrorInfo) => {
        console.error('Application error:', error, errorInfo);
        // You can also report to error tracking service here
    };
}

// Simple error fallback component
export function ErrorFallback({ error, resetError }: { error: Error; resetError: () => void }) {
    return (
        <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h6" color="error" gutterBottom>
                Something went wrong
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {error.message}
            </Typography>
            <Button variant="outlined" onClick={resetError}>
                Try again
            </Button>
        </Box>
    );
}