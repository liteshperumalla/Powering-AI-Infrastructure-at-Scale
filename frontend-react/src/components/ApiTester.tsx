'use client';

import React, { useState, useEffect } from 'react';
import {
    Box,
    Button,
    Card,
    CardContent,
    Typography,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Chip,
    Alert,
    Collapse,
    Divider,
    CircularProgress,
} from '@mui/material';
import {
    CheckCircle,
    Error,
    Warning,
    ExpandMore,
    ExpandLess,
    PlayArrow,
    Refresh,
} from '@mui/icons-material';
import { apiClient } from '@/services/api';

interface ApiTest {
    name: string;
    description: string;
    test: () => Promise<any>;
    requiresAuth?: boolean;
}

interface TestResult {
    name: string;
    status: 'success' | 'error' | 'warning';
    message: string;
    duration: number;
    data?: any;
}

export default function ApiTester() {
    const [results, setResults] = useState<TestResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [expandedResults, setExpandedResults] = useState<string[]>([]);
    const [isAuthenticated, setIsAuthenticated] = useState(apiClient.isAuthenticated());

    const apiTests: ApiTest[] = [
        {
            name: 'Health Check',
            description: 'Test basic API connectivity',
            test: async () => {
                return await apiClient.checkHealth();
            },
        },
        {
            name: 'System Metrics',
            description: 'Test system metrics endpoint',
            test: async () => {
                return await apiClient.getSystemMetrics();
            },
            requiresAuth: true,
        },
        {
            name: 'Cloud Services',
            description: 'Test cloud services listing',
            test: async () => {
                return await apiClient.getCloudServices({ limit: 5 });
            },
            requiresAuth: true,
        },
        {
            name: 'Cloud Service Providers',
            description: 'Test providers endpoint',
            test: async () => {
                return await apiClient.getCloudServiceProviders();
            },
            requiresAuth: false,
        },
        {
            name: 'Cloud Service Categories',
            description: 'Test categories endpoint',
            test: async () => {
                return await apiClient.getCloudServiceCategories();
            },
            requiresAuth: false,
        },
        {
            name: 'Assessments List',
            description: 'Test assessments retrieval',
            test: async () => {
                return await apiClient.getAssessments();
            },
            requiresAuth: true,
        },
        {
            name: 'Reports List',
            description: 'Test reports retrieval',
            test: async () => {
                return await apiClient.getReports();
            },
            requiresAuth: true,
        },
        {
            name: 'Current User',
            description: 'Test user profile endpoint',
            test: async () => {
                return await apiClient.getCurrentUser();
            },
            requiresAuth: true,
        },
        {
            name: 'Chat Analytics',
            description: 'Test chat analytics endpoint',
            test: async () => {
                return await apiClient.getChatAnalytics(7);
            },
            requiresAuth: true,
        },
        {
            name: 'System Health Detailed',
            description: 'Test detailed health check',
            test: async () => {
                return await apiClient.getSystemHealth();
            },
            requiresAuth: true,
        },
    ];

    const quickLogin = async () => {
        try {
            await apiClient.login({
                email: 'liteshperumalla@gmail.com',
                password: 'Litesh@#12345'
            });
            setIsAuthenticated(true);
        } catch (error) {
            console.error('Quick login failed:', error);
        }
    };

    const runAllTests = async () => {
        setLoading(true);
        setResults([]);
        
        const testResults: TestResult[] = [];
        
        for (const test of apiTests) {
            const startTime = Date.now();
            
            try {
                // Skip auth-required tests if not authenticated
                if (test.requiresAuth && !apiClient.isAuthenticated()) {
                    testResults.push({
                        name: test.name,
                        status: 'warning',
                        message: 'Skipped - Authentication required',
                        duration: 0,
                    });
                    continue;
                }
                
                const result = await test.test();
                const duration = Date.now() - startTime;
                
                testResults.push({
                    name: test.name,
                    status: 'success',
                    message: 'Test passed successfully',
                    duration,
                    data: result,
                });
            } catch (error) {
                const duration = Date.now() - startTime;
                const errorMessage = error && typeof error === 'object' && 'message' in error ? String(error.message) : 'Unknown error';
                
                testResults.push({
                    name: test.name,
                    status: 'error',
                    message: errorMessage,
                    duration,
                });
            }
            
            // Update results in real-time
            setResults([...testResults]);
        }
        
        setLoading(false);
    };

    const toggleExpanded = (testName: string) => {
        setExpandedResults(prev => 
            prev.includes(testName) 
                ? prev.filter(name => name !== testName)
                : [...prev, testName]
        );
    };

    const getStatusIcon = (status: TestResult['status']) => {
        switch (status) {
            case 'success':
                return <CheckCircle color="success" />;
            case 'error':
                return <Error color="error" />;
            case 'warning':
                return <Warning color="warning" />;
            default:
                return <CircularProgress size={24} />;
        }
    };

    const getStatusColor = (status: TestResult['status']): 'success' | 'error' | 'warning' | 'default' => {
        return status === 'success' ? 'success' : 
               status === 'error' ? 'error' : 
               status === 'warning' ? 'warning' : 'default';
    };

    const successCount = results.filter(r => r.status === 'success').length;
    const errorCount = results.filter(r => r.status === 'error').length;
    const warningCount = results.filter(r => r.status === 'warning').length;

    return (
        <Card>
            <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                    <Typography variant="h6" color="text.primary">
                        API Integration Test Suite
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 2 }}>
                        {!isAuthenticated && (
                            <Button
                                variant="outlined"
                                onClick={quickLogin}
                                disabled={loading}
                            >
                                Quick Login
                            </Button>
                        )}
                        <Button
                            variant="contained"
                            startIcon={loading ? <CircularProgress size={16} /> : <PlayArrow />}
                            onClick={runAllTests}
                            disabled={loading}
                        >
                            {loading ? 'Running Tests...' : 'Run All Tests'}
                        </Button>
                    </Box>
                </Box>

                {results.length > 0 && (
                    <Box sx={{ mb: 3 }}>
                        <Typography variant="subtitle1" gutterBottom>
                            Test Results Summary
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                            <Chip 
                                label={`${successCount} Passed`} 
                                color="success" 
                                variant={successCount > 0 ? "filled" : "outlined"}
                            />
                            <Chip 
                                label={`${errorCount} Failed`} 
                                color="error" 
                                variant={errorCount > 0 ? "filled" : "outlined"}
                            />
                            <Chip 
                                label={`${warningCount} Skipped`} 
                                color="warning" 
                                variant={warningCount > 0 ? "filled" : "outlined"}
                            />
                        </Box>
                        
                        {!isAuthenticated && (
                            <Alert severity="info" sx={{ mb: 2 }}>
                                Some tests require authentication. Click "Quick Login" to authenticate and run all tests.
                            </Alert>
                        )}
                        {isAuthenticated && (
                            <Alert severity="success" sx={{ mb: 2 }}>
                                ✅ Authenticated - All tests can be run
                            </Alert>
                        )}
                    </Box>
                )}

                <List>
                    {apiTests.map((test, index) => {
                        const result = results.find(r => r.name === test.name);
                        const isExpanded = expandedResults.includes(test.name);
                        
                        return (
                            <Box key={test.name}>
                                <ListItem
                                    sx={{ 
                                        cursor: result ? 'pointer' : 'default',
                                        '&:hover': { bgcolor: 'action.hover' }
                                    }}
                                    onClick={() => result && toggleExpanded(test.name)}
                                >
                                    <ListItemIcon>
                                        {result ? getStatusIcon(result.status) : <Refresh />}
                                    </ListItemIcon>
                                    <ListItemText
                                        primary={
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Typography variant="body1">
                                                    {test.name}
                                                </Typography>
                                                {result && (
                                                    <Chip
                                                        size="small"
                                                        label={`${result.duration}ms`}
                                                        color={getStatusColor(result.status)}
                                                        variant="outlined"
                                                    />
                                                )}
                                                {test.requiresAuth && (
                                                    <Chip
                                                        size="small"
                                                        label="Auth Required"
                                                        color="primary"
                                                        variant="outlined"
                                                    />
                                                )}
                                            </Box>
                                        }
                                        secondary={test.description}
                                    />
                                    {result && (isExpanded ? <ExpandLess /> : <ExpandMore />)}
                                </ListItem>
                                
                                {result && (
                                    <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                                        <Box sx={{ pl: 4, pr: 2, pb: 2 }}>
                                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                                Status: {result.message}
                                            </Typography>
                                            {result.data && (
                                                <Box sx={{ mt: 1 }}>
                                                    <Typography variant="caption" color="text.secondary">
                                                        Response Data:
                                                    </Typography>
                                                    <Box
                                                        component="pre"
                                                        sx={{
                                                            fontSize: '0.75rem',
                                                            bgcolor: (theme) => theme.palette.mode === 'dark' ? 'grey.800' : 'grey.100',
                                                            p: 1,
                                                            borderRadius: 1,
                                                            overflow: 'auto',
                                                            maxHeight: 200,
                                                            mt: 0.5,
                                                        }}
                                                    >
                                                        {JSON.stringify(result.data, null, 2)}
                                                    </Box>
                                                </Box>
                                            )}
                                        </Box>
                                    </Collapse>
                                )}
                                
                                {index < apiTests.length - 1 && <Divider />}
                            </Box>
                        );
                    })}
                </List>
            </CardContent>
        </Card>
    );
}