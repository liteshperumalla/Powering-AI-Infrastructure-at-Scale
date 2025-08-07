import React, { useEffect, useState, useCallback } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    LinearProgress,
    Chip,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Alert,
    Collapse,
    IconButton,
} from '@mui/material';
import {
    CheckCircle,
    RadioButtonUnchecked,
    Error,
    Warning,
    ExpandMore,
    ExpandLess,
    PlayArrow,
} from '@mui/icons-material';
import { useAssessmentWebSocket } from '@/hooks/useWebSocket';

interface WorkflowStep {
    name: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    started_at?: string;
    completed_at?: string;
    error?: string;
}

interface WorkflowProgress {
    id: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    progress: number;
    current_step: string;
    steps: WorkflowStep[];
    created_at: string;
    updated_at: string;
}

interface AgentStatus {
    workflow_id: string;
    agent_name: string;
    status: 'started' | 'completed' | 'failed';
    step_id?: string;
    estimated_duration?: number;
    execution_time?: number;
    results_summary?: string;
    error?: string;
}

interface RealTimeProgressProps {
    assessmentId: string;
    workflowId?: string;
    onComplete?: (results: WorkflowProgress) => void;
    onError?: (error: string) => void;
}

interface Notification {
    type: 'info' | 'warning' | 'error' | 'alert';
    title: string;
    message: string;
}

export default function RealTimeProgress({
    assessmentId,
    workflowId,
    onComplete,
    onError,
}: RealTimeProgressProps) {
    const [progress, setProgress] = useState<WorkflowProgress | null>(null);
    const [agentStatuses, setAgentStatuses] = useState<Record<string, AgentStatus>>({});
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [expanded, setExpanded] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // WebSocket connection for real-time updates
    const {
        isConnected,
        sendTypedMessage,
        lastMessage,
        error: wsError,
    } = useAssessmentWebSocket(assessmentId);

    // Handle WebSocket messages
    const handleMessage = useCallback((event: MessageEvent) => {
        try {
            const message = JSON.parse(event.data);

            switch (message.type) {
                case 'workflow_progress':
                    const progressData = {
                        id: message.data.workflow_id || assessmentId,
                        status: message.data.status,
                        progress: message.data.progress_percentage || 0,
                        current_step: message.data.current_step,
                        steps: message.data.steps || [],
                        created_at: message.data.timestamp,
                        updated_at: message.data.timestamp
                    };
                    setProgress(progressData);
                    
                    if (message.data.status === 'completed') {
                        onComplete?.(progressData);
                    } else if (message.data.status === 'failed') {
                        setError(message.data.error || 'Workflow failed');
                        onError?.(message.data.error || 'Workflow failed');
                    }
                    break;

                case 'agent_status':
                    setAgentStatuses(prev => ({
                        ...prev,
                        [message.data.agent_name]: message.data
                    }));
                    break;

                case 'step_completed':
                    // Update progress for specific step
                    setProgress(prev => prev ? {
                        ...prev,
                        progress: message.data.progress,
                        current_step: message.data.step_id || prev.current_step
                    } : null);
                    break;

                case 'notification':
                    setNotifications(prev => [message.data, ...(prev || []).slice(0, 4)]); // Keep last 5
                    break;

                case 'alert':
                    setNotifications(prev => [
                        { ...message.data, type: 'alert' },
                        ...(prev || []).slice(0, 4)
                    ]);
                    break;

                case 'error':
                    setError(message.data.error);
                    onError?.(message.data.error);
                    break;
            }
        } catch (err) {
            console.error('Error parsing WebSocket message:', err);
        }
    }, [onComplete, onError]);

    // Subscribe to WebSocket messages
    useEffect(() => {
        if (lastMessage) {
            handleMessage(lastMessage);
        }
    }, [lastMessage, handleMessage]);

    // Subscribe to workflow updates when connected
    useEffect(() => {
        if (isConnected) {
            if (workflowId) {
                sendTypedMessage('subscribe', { workflow_id: workflowId });
            } else if (assessmentId) {
                sendTypedMessage('subscribe', { assessment_id: assessmentId });
            }
        }
    }, [isConnected, workflowId, assessmentId, sendTypedMessage]);

    // Handle WebSocket errors
    useEffect(() => {
        if (wsError) {
            setError(`Connection error: ${wsError}`);
        }
    }, [wsError]);

    // Fallback polling for progress updates when WebSocket is not available
    useEffect(() => {
        let pollInterval: NodeJS.Timeout;
        
        const pollForProgress = async () => {
            if (!isConnected && assessmentId) {
                try {
                    // Poll assessment status from API
                    const response = await fetch(`/api/assessments/${assessmentId}`);
                    if (response.ok) {
                        const assessment = await response.json();
                        
                        if (assessment.progress) {
                            const progressData = {
                                id: assessmentId,
                                status: assessment.status === 'completed' ? 'completed' : 
                                       assessment.status === 'failed' ? 'failed' : 'running',
                                progress: assessment.progress.progress_percentage || 0,
                                current_step: assessment.progress.current_step || 'created',
                                steps: assessment.progress.steps || [],
                                created_at: assessment.created_at,
                                updated_at: assessment.updated_at
                            };
                            
                            setProgress(progressData);
                            
                            // Check for completion
                            if (assessment.status === 'completed') {
                                onComplete?.(progressData);
                                clearInterval(pollInterval);
                            } else if (assessment.status === 'failed') {
                                setError(assessment.progress?.message || 'Assessment failed');
                                onError?.(assessment.progress?.message || 'Assessment failed');
                                clearInterval(pollInterval);
                            }
                        }
                    }
                } catch (error) {
                    console.error('Failed to poll assessment progress:', error);
                }
            }
        };
        
        // Start polling if WebSocket is not connected and we have an assessment ID
        if (!isConnected && assessmentId) {
            pollInterval = setInterval(pollForProgress, 2000); // Poll every 2 seconds
        }
        
        return () => {
            if (pollInterval) {
                clearInterval(pollInterval);
            }
        };
    }, [isConnected, assessmentId, onComplete, onError]);

    const getStepIcon = (step: WorkflowStep) => {
        switch (step.status) {
            case 'completed':
                return <CheckCircle color="success" />;
            case 'running':
                return <PlayArrow color="primary" />;
            case 'failed':
                return <Error color="error" />;
            default:
                return <RadioButtonUnchecked color="disabled" />;
        }
    };

    type ChipColor = 'success' | 'primary' | 'error' | 'default';

    const getStatusColor = (status: string): ChipColor => {
        switch (status) {
            case 'completed':
                return 'success';
            case 'running':
                return 'primary';
            case 'failed':
                return 'error';
            default:
                return 'default';
        }
    };

    if (!progress && !error) {
        return (
            <Card>
                <CardContent>
                    <Typography variant="h6" gutterBottom>
                        Workflow Progress
                    </Typography>
                    <Typography color="text.secondary">
                        {isConnected ? 'Waiting for workflow to start...' : 'Connecting...'}
                    </Typography>
                    <LinearProgress sx={{ mt: 2 }} />
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="h6">
                        Workflow Progress
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {progress && (
                            <Chip
                            label={progress.status}
                            color={getStatusColor(progress.status)}
                            size="small"
                        />
                        )}
                        <IconButton
                            size="small"
                            onClick={() => setExpanded(!expanded)}
                        >
                            {expanded ? <ExpandLess /> : <ExpandMore />}
                        </IconButton>
                    </Box>
                </Box>

                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}

                {!isConnected && (
                    <Alert severity="warning" sx={{ mb: 2 }}>
                        Connection lost. Attempting to reconnect...
                    </Alert>
                )}

                {progress && (
                    <>
                        <Box sx={{ mb: 2 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                <Typography variant="body2" color="text.secondary">
                                    Current Step: {progress.current_step}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    {Math.round(progress.progress)}%
                                </Typography>
                            </Box>
                            <LinearProgress
                                variant="determinate"
                                value={progress.progress}
                                color={getStatusColor(progress.status)}
                            />
                        </Box>

                        <Collapse in={expanded}>
                            {progress.steps && progress.steps.length > 0 && (
                                <Box sx={{ mb: 2 }}>
                                    <Typography variant="subtitle2" gutterBottom>
                                        Steps
                                    </Typography>
                                    <List dense>
                                        {progress.steps.map((step, index) => (
                                            <ListItem key={index}>
                                                <ListItemIcon>
                                                    {getStepIcon(step)}
                                                </ListItemIcon>
                                                <ListItemText
                                                    primary={step.name}
                                                    secondary={
                                                        step.error ||
                                                        (step.completed_at && `Completed at ${new Date(step.completed_at).toLocaleTimeString()}`) ||
                                                        (step.started_at && `Started at ${new Date(step.started_at).toLocaleTimeString()}`)
                                                    }
                                                />
                                            </ListItem>
                                        ))}
                                    </List>
                                </Box>
                            )}

                            {Object.keys(agentStatuses).length > 0 && (
                                <Box sx={{ mb: 2 }}>
                                    <Typography variant="subtitle2" gutterBottom>
                                        Agent Status
                                    </Typography>
                                    <List dense>
                                        {Object.entries(agentStatuses).map(([agentName, status]) => (
                                            <ListItem key={agentName}>
                                                <ListItemIcon>
                                                    {status.status === 'completed' ? (
                                                        <CheckCircle color="success" />
                                                    ) : status.status === 'failed' ? (
                                                        <Error color="error" />
                                                    ) : (
                                                        <PlayArrow color="primary" />
                                                    )}
                                                </ListItemIcon>
                                                <ListItemText
                                                    primary={agentName.replace('_', ' ').toUpperCase()}
                                                    secondary={
                                                        status.error ||
                                                        status.results_summary ||
                                                        `Status: ${status.status}`
                                                    }
                                                />
                                            </ListItem>
                                        ))}
                                    </List>
                                </Box>
                            )}

                            {notifications.length > 0 && (
                                <Box>
                                    <Typography variant="subtitle2" gutterBottom>
                                        Recent Updates
                                    </Typography>
                                    {notifications.map((notification, index) => (
                                        <Alert
                                            key={index}
                                            severity={
                                                notification.type === 'error' ? 'error' :
                                                    notification.type === 'warning' ? 'warning' :
                                                        notification.type === 'alert' ? 'warning' :
                                                            'info'
                                            }
                                            sx={{ mb: 1 }}
                                        >
                                            <Typography variant="body2">
                                                <strong>{notification.title}</strong>
                                            </Typography>
                                            <Typography variant="caption">
                                                {notification.message}
                                            </Typography>
                                        </Alert>
                                    ))}
                                </Box>
                            )}
                        </Collapse>
                    </>
                )}
            </CardContent>
        </Card>
    );
}