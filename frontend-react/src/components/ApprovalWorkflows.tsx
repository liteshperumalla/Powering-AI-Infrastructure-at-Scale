'use client';

import React, { useState, useEffect } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Button,
    TextField,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Stack,
    Chip,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    IconButton,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    ListItemSecondaryAction,
    Divider,
    Alert,
    LinearProgress,
    Tab,
    Tabs,
    Grid,
    Paper,
    Stepper,
    Step,
    StepLabel,
    StepContent,
    Timeline,
    TimelineItem,
    TimelineSeparator,
    TimelineConnector,
    TimelineContent,
    TimelineDot,
    Avatar,
    AvatarGroup,
    Tooltip,
    Badge,
    Menu,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Switch,
    FormControlLabel,
} from '@mui/material';
import {
    Add as AddIcon,
    Delete as DeleteIcon,
    Edit as EditIcon,
    Approval as ApprovalIcon,
    Schedule as PendingIcon,
    CheckCircle as ApprovedIcon,
    Cancel as RejectedIcon,
    Warning as WarningIcon,
    Person as PersonIcon,
    Group as GroupIcon,
    AccessTime as TimeIcon,
    Comment as CommentIcon,
    AttachFile as AttachIcon,
    Send as SendIcon,
    Escalation as EscalateIcon,
    Emergency as EmergencyIcon,
    ExpandMore as ExpandMoreIcon,
    FilterList as FilterIcon,
    Sort as SortIcon,
    MoreVert as MoreIcon,
    Assignment as RuleIcon,
    Timeline as TimelineIcon,
    Analytics as AnalyticsIcon,
} from '@mui/icons-material';
import { getApprovalWorkflowService, ApprovalRequest, ApprovalRule, ApprovalAction } from '../services/approvalWorkflows';
import InteractiveCharts from './InteractiveCharts';

interface TabPanelProps {
    children?: React.ReactNode;
    index: number;
    value: number;
}

function TabPanel({ children, value, index }: TabPanelProps) {
    return (
        <div hidden={value !== index}>
            {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
        </div>
    );
}

const ApprovalWorkflows: React.FC = () => {
    const [tabValue, setTabValue] = useState(0);
    const [requests, setRequests] = useState<ApprovalRequest[]>([]);
    const [rules, setRules] = useState<ApprovalRule[]>([]);
    const [selectedRequest, setSelectedRequest] = useState<ApprovalRequest | null>(null);
    const [loading, setLoading] = useState(false);
    
    // Dialog states
    const [createRuleDialog, setCreateRuleDialog] = useState(false);
    const [requestDetailDialog, setRequestDetailDialog] = useState(false);
    const [bulkActionDialog, setBulkActionDialog] = useState(false);
    
    // Filter states
    const [statusFilter, setStatusFilter] = useState('all');
    const [environmentFilter, setEnvironmentFilter] = useState('all');
    const [assignedFilter, setAssignedFilter] = useState('all');
    
    // Selection state for bulk operations
    const [selectedRequests, setSelectedRequests] = useState<string[]>([]);
    
    const approvalService = getApprovalWorkflowService();

    useEffect(() => {
        loadData();
    }, [statusFilter, environmentFilter, assignedFilter]);

    const loadData = async () => {
        setLoading(true);
        try {
            const filters: any = {};
            if (statusFilter !== 'all') filters.status = statusFilter;
            if (environmentFilter !== 'all') filters.environment = environmentFilter;
            if (assignedFilter === 'me') filters.assigned_to_me = true;
            
            const [requestsData, rulesData] = await Promise.all([
                approvalService.getApprovalRequests(filters),
                approvalService.getApprovalRules(),
            ]);
            
            // Ensure requests have proper structure
            const formattedRequests = Array.isArray(requestsData) ? requestsData.map(request => ({
                ...request,
                workflow: request.workflow || {
                    status: request.status || 'pending',
                    current_level: request.current_level || 1,
                    approval_progress: request.approval_progress || [{
                        level: 1,
                        name: 'Review',
                        status: request.status || 'pending',
                        approvals: Array.isArray(request.approved_by) ? request.approved_by.map(email => ({ email })) : [],
                        required_approvals: request.required_approvers || []
                    }]
                }
            })) : [];
            setRequests(formattedRequests);
            setRules(rulesData);
        } catch (error) {
            console.error('Failed to load approval data:', error);
            // Set fallback data
            setRequests([]);
            setRules([]);
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (requestId: string, levelId: number, comment?: string) => {
        try {
            await approvalService.approveRequest(requestId, levelId, comment);
            await loadData();
        } catch (error) {
            console.error('Failed to approve request:', error);
        }
    };

    const handleReject = async (requestId: string, levelId: number, comment: string) => {
        try {
            await approvalService.rejectRequest(requestId, levelId, comment);
            await loadData();
        } catch (error) {
            console.error('Failed to reject request:', error);
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'approved': return <ApprovedIcon color="success" />;
            case 'rejected': return <RejectedIcon color="error" />;
            case 'pending': 
            case 'in_progress': return <PendingIcon color="warning" />;
            default: return <ApprovalIcon />;
        }
    };

    const getStatusColor = (status: string): "success" | "error" | "warning" | "info" | "default" => {
        switch (status) {
            case 'approved': return 'success';
            case 'rejected': return 'error';
            case 'pending': 
            case 'in_progress': return 'warning';
            case 'expired': return 'error';
            default: return 'default';
        }
    };

    const getRiskColor = (risk: string): "success" | "error" | "warning" | "info" => {
        switch (risk) {
            case 'low': return 'success';
            case 'medium': return 'info';
            case 'high': return 'warning';
            case 'critical': return 'error';
            default: return 'info';
        }
    };

    const generateApprovalMetrics = () => {
        const safeRequests = Array.isArray(requests) ? requests : [];
        return [
            { name: 'Approved', value: safeRequests.filter(r => r.workflow?.status === 'approved').length, category: 'status' },
            { name: 'Pending', value: safeRequests.filter(r => r.workflow?.status === 'pending' || r.workflow?.status === 'in_progress').length, category: 'status' },
            { name: 'Rejected', value: safeRequests.filter(r => r.workflow?.status === 'rejected').length, category: 'status' },
        ];
    };

    const generateTimelineData = () => {
        const last30Days = Array.from({ length: 30 }, (_, i) => {
            const date = new Date();
            date.setDate(date.getDate() - (29 - i));
            return {
                name: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                value: Math.floor(Math.random() * 10),
                category: 'requests'
            };
        });
        return last30Days;
    };

    return (
        <Box sx={{ p: 3 }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
                <Typography variant="h4" color="text.primary" fontWeight={600}>
                    Approval Workflows
                </Typography>
                <Stack direction="row" spacing={2}>
                    <Button
                        variant="outlined"
                        startIcon={<RuleIcon />}
                        onClick={() => setCreateRuleDialog(true)}
                    >
                        Create Rule
                    </Button>
                    <Button
                        variant="contained"
                        startIcon={<AddIcon />}
                        disabled={selectedRequests.length === 0}
                        onClick={() => setBulkActionDialog(true)}
                    >
                        Bulk Actions ({selectedRequests.length})
                    </Button>
                </Stack>
            </Stack>

            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
                <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
                    <Tab icon={<ApprovalIcon />} label="Requests" />
                    <Tab icon={<RuleIcon />} label="Rules" />
                    <Tab icon={<TimelineIcon />} label="Activity" />
                    <Tab icon={<AnalyticsIcon />} label="Analytics" />
                </Tabs>
            </Box>

            {loading && <LinearProgress sx={{ mb: 2 }} />}

            {/* Requests Tab */}
            <TabPanel value={tabValue} index={0}>
                <Grid container spacing={3}>
                    <Grid item xs={12}>
                        <Card>
                            <CardContent>
                                {/* Filters */}
                                <Stack direction="row" spacing={2} sx={{ mb: 3 }} alignItems="center">
                                    <FormControl size="small" sx={{ minWidth: 120 }}>
                                        <InputLabel>Status</InputLabel>
                                        <Select
                                            value={statusFilter}
                                            label="Status"
                                            onChange={(e) => setStatusFilter(e.target.value)}
                                        >
                                            <MenuItem value="all">All Status</MenuItem>
                                            <MenuItem value="pending">Pending</MenuItem>
                                            <MenuItem value="in_progress">In Progress</MenuItem>
                                            <MenuItem value="approved">Approved</MenuItem>
                                            <MenuItem value="rejected">Rejected</MenuItem>
                                        </Select>
                                    </FormControl>
                                    
                                    <FormControl size="small" sx={{ minWidth: 120 }}>
                                        <InputLabel>Environment</InputLabel>
                                        <Select
                                            value={environmentFilter}
                                            label="Environment"
                                            onChange={(e) => setEnvironmentFilter(e.target.value)}
                                        >
                                            <MenuItem value="all">All Environments</MenuItem>
                                            <MenuItem value="dev">Development</MenuItem>
                                            <MenuItem value="staging">Staging</MenuItem>
                                            <MenuItem value="prod">Production</MenuItem>
                                        </Select>
                                    </FormControl>
                                    
                                    <FormControl size="small" sx={{ minWidth: 120 }}>
                                        <InputLabel>Assignment</InputLabel>
                                        <Select
                                            value={assignedFilter}
                                            label="Assignment"
                                            onChange={(e) => setAssignedFilter(e.target.value)}
                                        >
                                            <MenuItem value="all">All Requests</MenuItem>
                                            <MenuItem value="me">Assigned to Me</MenuItem>
                                        </Select>
                                    </FormControl>
                                </Stack>

                                {/* Request List */}
                                <List>
                                    {Array.isArray(requests) && requests.length > 0 ? requests.map((request) => (
                                        <React.Fragment key={request.id}>
                                            <ListItem
                                                alignItems="flex-start"
                                                sx={{
                                                    border: selectedRequests.includes(request.id) ? 2 : 1,
                                                    borderColor: selectedRequests.includes(request.id) ? 'primary.main' : 'divider',
                                                    borderRadius: 2,
                                                    mb: 1,
                                                    backgroundColor: selectedRequests.includes(request.id) ? 'action.hover' : 'transparent',
                                                }}
                                            >
                                                <ListItemIcon>
                                                    <input
                                                        type="checkbox"
                                                        checked={selectedRequests.includes(request.id)}
                                                        onChange={(e) => {
                                                            if (e.target.checked) {
                                                                setSelectedRequests(prev => [...prev, request.id]);
                                                            } else {
                                                                setSelectedRequests(prev => prev.filter(id => id !== request.id));
                                                            }
                                                        }}
                                                    />
                                                </ListItemIcon>
                                                <ListItemText
                                                    primary={
                                                        <Stack direction="row" alignItems="center" spacing={1}>
                                                            {getStatusIcon(request.workflow?.status || 'pending')}
                                                            <Typography variant="h6" color="text.primary">
                                                                {request.title}
                                                            </Typography>
                                                            <Chip
                                                                size="small"
                                                                label={request.resource_details?.environment || 'Unknown'}
                                                                color={request.resource_details?.environment === 'prod' ? 'error' : 'primary'}
                                                                variant="outlined"
                                                            />
                                                            <Chip
                                                                size="small"
                                                                label={request.resource_details?.risk_assessment?.level || 'Unknown'}
                                                                color={getRiskColor(request.resource_details?.risk_assessment?.level || 'low')}
                                                                variant="filled"
                                                            />
                                                        </Stack>
                                                    }
                                                    secondary={
                                                        <Box sx={{ mt: 1 }}>
                                                            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                                                {request.description}
                                                            </Typography>
                                                            
                                                            {/* Progress Bar */}
                                                            <Box sx={{ mb: 2 }}>
                                                                <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 0.5 }}>
                                                                    <Typography variant="caption">
                                                                        Level {request.workflow.current_level} of {request.workflow.total_levels}
                                                                    </Typography>
                                                                    <Typography variant="caption">
                                                                        {Math.round((request.workflow.current_level / request.workflow.total_levels) * 100)}%
                                                                    </Typography>
                                                                </Stack>
                                                                <LinearProgress
                                                                    variant="determinate"
                                                                    value={(request.workflow.current_level / request.workflow.total_levels) * 100}
                                                                    sx={{ height: 6, borderRadius: 3 }}
                                                                />
                                                            </Box>
                                                            
                                                            {/* Approvers */}
                                                            <Stack direction="row" spacing={2} alignItems="center">
                                                                <Stack direction="row" alignItems="center" spacing={1}>
                                                                    <Typography variant="caption">Requested by:</Typography>
                                                                    <Avatar sx={{ width: 24, height: 24 }}>
                                                                        {request.requester?.name?.charAt(0) || '?'}
                                                                    </Avatar>
                                                                    <Typography variant="caption">{request.requester?.name || 'Unknown'}</Typography>
                                                                </Stack>
                                                                
                                                                <Stack direction="row" alignItems="center" spacing={1}>
                                                                    <Typography variant="caption">Pending approvals:</Typography>
                                                                    <AvatarGroup max={3} sx={{ '& .MuiAvatar-root': { width: 24, height: 24 } }}>
                                                                        {Array.isArray(request.workflow?.approval_progress) 
                                                                            ? request.workflow.approval_progress
                                                                                .filter(p => p.status === 'pending' || p.status === 'in_progress')
                                                                                .flatMap(p => Array.isArray(p.approvals) ? p.approvals : [])
                                                                                .map((approval, idx) => (
                                                                                    <Avatar key={idx}>
                                                                                        {approval.approver?.name?.charAt(0) || '?'}
                                                                                    </Avatar>
                                                                                ))
                                                                            : []}
                                                                    </AvatarGroup>
                                                                </Stack>
                                                                
                                                                <Typography variant="caption" color="text.secondary">
                                                                    Created: {new Date(request.created_at).toLocaleDateString()}
                                                                </Typography>
                                                            </Stack>
                                                        </Box>
                                                    }
                                                />
                                                <ListItemSecondaryAction>
                                                    <Stack direction="row" spacing={1}>
                                                        <Button
                                                            size="small"
                                                            onClick={() => {
                                                                setSelectedRequest(request);
                                                                setRequestDetailDialog(true);
                                                            }}
                                                        >
                                                            Details
                                                        </Button>
                                                        {(request.workflow?.status === 'pending' || request.workflow?.status === 'in_progress') ? (
                                                            <>
                                                                <Button
                                                                    size="small"
                                                                    color="success"
                                                                    onClick={() => handleApprove(request.id, request.workflow.current_level)}
                                                                >
                                                                    Approve
                                                                </Button>
                                                                <Button
                                                                    size="small"
                                                                    color="error"
                                                                    onClick={() => handleReject(request.id, request.workflow.current_level, 'Rejected via quick action')}
                                                                >
                                                                    Reject
                                                                </Button>
                                                            </>
                                                        ) : (
                                                            <Chip
                                                                size="small"
                                                                label={request.workflow?.status || 'pending'}
                                                                color={getStatusColor(request.workflow?.status || 'pending')}
                                                                variant="filled"
                                                            />
                                                        )}
                                                    </Stack>
                                                </ListItemSecondaryAction>
                                            </ListItem>
                                        </React.Fragment>
                                    )) : (
                                        <Box textAlign="center" py={3}>
                                            <Typography color="textSecondary">
                                                No approval requests found
                                            </Typography>
                                        </Box>
                                    )}
                                </List>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            </TabPanel>

            {/* Rules Tab */}
            <TabPanel value={tabValue} index={1}>
                <Grid container spacing={3}>
                    {Array.isArray(rules) && rules.length > 0 ? rules.map((rule) => (
                        <Grid item xs={12} md={6} lg={4} key={rule.id}>
                            <Card>
                                <CardContent>
                                    <Stack spacing={2}>
                                        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                                            <Typography variant="h6" color="text.primary" noWrap>
                                                {rule.name}
                                            </Typography>
                                            <Chip
                                                size="small"
                                                label={rule.active ? 'Active' : 'Inactive'}
                                                color={rule.active ? 'success' : 'default'}
                                                variant={rule.active ? 'filled' : 'outlined'}
                                            />
                                        </Stack>
                                        
                                        <Typography variant="body2" color="text.secondary">
                                            {rule.description}
                                        </Typography>
                                        
                                        <Stack direction="row" spacing={1}>
                                            <Chip size="small" label={`${rule.approval_levels.length} levels`} />
                                            <Chip size="small" label={`${rule.timeout_hours}h timeout`} />
                                        </Stack>
                                        
                                        <Stack direction="row" justifyContent="space-between">
                                            <Button size="small" startIcon={<EditIcon />}>
                                                Edit
                                            </Button>
                                            <Button size="small" color="error" startIcon={<DeleteIcon />}>
                                                Delete
                                            </Button>
                                        </Stack>
                                    </Stack>
                                </CardContent>
                            </Card>
                        </Grid>
                    )) : (
                        <Grid item xs={12}>
                            <Box textAlign="center" py={3}>
                                <Typography color="textSecondary">
                                    No approval rules configured
                                </Typography>
                            </Box>
                        </Grid>
                    )}
                </Grid>
            </TabPanel>

            {/* Activity Tab */}
            <TabPanel value={tabValue} index={2}>
                <Card>
                    <CardContent>
                        <Typography variant="h6" color="text.primary" sx={{ mb: 3 }}>
                            Approval Activity Timeline
                        </Typography>
                        <InteractiveCharts
                            config={{
                                type: 'line',
                                title: 'Daily Approval Requests',
                                data: generateTimelineData(),
                                colors: ['#2196f3'],
                                showBrush: true,
                            }}
                            height={400}
                            exportable={true}
                        />
                    </CardContent>
                </Card>
            </TabPanel>

            {/* Analytics Tab */}
            <TabPanel value={tabValue} index={3}>
                <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" color="text.primary" sx={{ mb: 2 }}>
                                    Request Status Distribution
                                </Typography>
                                <InteractiveCharts
                                    config={{
                                        type: 'pie',
                                        title: '',
                                        data: generateApprovalMetrics(),
                                        colors: ['#4caf50', '#ff9800', '#f44336'],
                                    }}
                                    height={300}
                                    exportable={false}
                                />
                            </CardContent>
                        </Card>
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" color="text.primary" sx={{ mb: 2 }}>
                                    Key Metrics
                                </Typography>
                                <Stack spacing={2}>
                                    <Box>
                                        <Typography variant="body2" color="text.secondary">Average Approval Time</Typography>
                                        <Typography variant="h4" color="primary">2.4 days</Typography>
                                    </Box>
                                    <Box>
                                        <Typography variant="body2" color="text.secondary">Approval Rate</Typography>
                                        <Typography variant="h4" color="success.main">85%</Typography>
                                    </Box>
                                    <Box>
                                        <Typography variant="body2" color="text.secondary">Escalation Rate</Typography>
                                        <Typography variant="h4" color="warning.main">12%</Typography>
                                    </Box>
                                </Stack>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            </TabPanel>

            {/* Request Detail Dialog */}
            <Dialog
                open={requestDetailDialog}
                onClose={() => setRequestDetailDialog(false)}
                maxWidth="lg"
                fullWidth
            >
                <DialogTitle>
                    {selectedRequest?.title}
                </DialogTitle>
                <DialogContent>
                    {selectedRequest && (
                        <Stack spacing={3} sx={{ mt: 1 }}>
                            <Alert severity={getRiskColor(selectedRequest.resource_details?.risk_assessment?.level || 'low')}>
                                <Typography variant="subtitle2">
                                    Risk Level: {(selectedRequest.resource_details?.risk_assessment?.level || 'unknown').toUpperCase()}
                                </Typography>
                                <Typography variant="body2">
                                    Impact Score: {selectedRequest.resource_details?.risk_assessment?.impact_score || 0}/100
                                </Typography>
                            </Alert>

                            <Stepper activeStep={selectedRequest.workflow.current_level - 1} orientation="vertical">
                                {Array.isArray(selectedRequest.workflow?.approval_progress) ? selectedRequest.workflow.approval_progress.map((progress, index) => (
                                    <Step key={index} completed={progress.status === 'approved'}>
                                        <StepLabel
                                            error={progress.status === 'rejected'}
                                            StepIconComponent={() => 
                                                progress.status === 'approved' ? <ApprovedIcon color="success" /> :
                                                progress.status === 'rejected' ? <RejectedIcon color="error" /> :
                                                progress.status === 'in_progress' ? <PendingIcon color="warning" /> :
                                                <PendingIcon />
                                            }
                                        >
                                            {progress.level_name}
                                        </StepLabel>
                                        <StepContent>
                                            <Typography variant="body2" sx={{ mb: 1 }}>
                                                Required: {progress.required_approvals} approvals | 
                                                Current: {progress.current_approvals} approvals
                                            </Typography>
                                            {Array.isArray(progress.approvals) && progress.approvals.length > 0 && (
                                                <List dense>
                                                    {progress.approvals.map((approval, idx) => (
                                                        <ListItem key={idx}>
                                                            <ListItemIcon>
                                                                {approval.action === 'approve' ? 
                                                                    <ApprovedIcon color="success" /> : 
                                                                    <RejectedIcon color="error" />}
                                                            </ListItemIcon>
                                                            <ListItemText
                                                                primary={approval.approver.name}
                                                                secondary={approval.comment}
                                                            />
                                                            <Typography variant="caption" color="text.secondary">
                                                                {new Date(approval.timestamp).toLocaleString()}
                                                            </Typography>
                                                        </ListItem>
                                                    ))}
                                                </List>
                                            )}
                                        </StepContent>
                                    </Step>
                                )) : (
                                    <Typography color="textSecondary">
                                        No approval progress available
                                    </Typography>
                                )}
                            </Stepper>
                        </Stack>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setRequestDetailDialog(false)}>Close</Button>
                    {selectedRequest && (selectedRequest.workflow.status === 'pending' || selectedRequest.workflow.status === 'in_progress') && (
                        <>
                            <Button 
                                color="success" 
                                onClick={() => {
                                    handleApprove(selectedRequest.id, selectedRequest.workflow.current_level);
                                    setRequestDetailDialog(false);
                                }}
                            >
                                Approve
                            </Button>
                            <Button 
                                color="error"
                                onClick={() => {
                                    handleReject(selectedRequest.id, selectedRequest.workflow.current_level, 'Rejected from detail view');
                                    setRequestDetailDialog(false);
                                }}
                            >
                                Reject
                            </Button>
                        </>
                    )}
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default ApprovalWorkflows;