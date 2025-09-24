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
    Grid,
    Paper,
    Alert,
    LinearProgress,
    CircularProgress,
    Stepper,
    Step,
    StepLabel,
    StepContent,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    Divider,
    Tooltip,
    IconButton,
    Badge,
    TreeView,
    TreeItem,
} from '@mui/material';
import {
    ExpandMore as ExpandMoreIcon,
    ChevronRight as ChevronRightIcon,
    Warning as WarningIcon,
    Error as ErrorIcon,
    Info as InfoIcon,
    CheckCircle as SuccessIcon,
    Assessment as AnalysisIcon,
    Timeline as TimelineIcon,
    Security as SecurityIcon,
    AttachMoney as CostIcon,
    Speed as PerformanceIcon,
    People as UsersIcon,
    CloudQueue as InfraIcon,
    Policy as PolicyIcon,
    Schedule as ScheduleIcon,
    Compare as CompareIcon,
    PlayArrow as SimulateIcon,
    GetApp as ExportIcon,
    Visibility as ViewIcon,
    AccountTree as DependencyIcon,
    TrendingUp as TrendingUpIcon,
    TrendingDown as TrendingDownIcon,
} from '@mui/icons-material';
import { 
    getChangeImpactService, 
    ChangeRequest, 
    ImpactAnalysisResult, 
    Resource,
    ResourceImpact
} from '../services/changeImpactAnalysis';
import InteractiveCharts from './InteractiveCharts';

interface ChangeImpactAnalysisProps {
    initialChangeRequest?: ChangeRequest;
    onAnalysisComplete?: (result: ImpactAnalysisResult) => void;
}

const ChangeImpactAnalysis: React.FC<ChangeImpactAnalysisProps> = ({
    initialChangeRequest,
    onAnalysisComplete,
}) => {
    const [activeStep, setActiveStep] = useState(0);
    const [loading, setLoading] = useState(false);
    const [analysisResult, setAnalysisResult] = useState<ImpactAnalysisResult | null>(null);
    const [resources, setResources] = useState<Resource[]>([]);
    const [selectedResources, setSelectedResources] = useState<string[]>([]);
    
    // Form states
    const [changeForm, setChangeForm] = useState({
        title: initialChangeRequest?.title || '',
        description: initialChangeRequest?.description || '',
        change_type: initialChangeRequest?.change_type || 'update',
        target_environment: initialChangeRequest?.target_environment || 'dev',
        urgency: initialChangeRequest?.urgency || 'medium',
        change_category: initialChangeRequest?.change_category || 'configuration',
    });

    // Dialog states
    const [simulationDialog, setSimulationDialog] = useState(false);
    const [exportDialog, setExportDialog] = useState(false);
    const [detailDialog, setDetailDialog] = useState(false);
    const [selectedDetail, setSelectedDetail] = useState<any>(null);

    const impactService = getChangeImpactService();

    useEffect(() => {
        loadResources();
    }, [changeForm.target_environment]);

    const loadResources = async () => {
        try {
            const resourceData = await impactService.discoverResources(changeForm.target_environment);
            setResources(Array.isArray(resourceData) ? resourceData : []);
        } catch (error) {
            console.error('Failed to load resources:', error);
            setResources([]);
        }
    };

    const runAnalysis = async () => {
        if (selectedResources.length === 0) {
            alert('Please select at least one resource to analyze');
            return;
        }

        setLoading(true);
        try {
            const changeRequest: ChangeRequest = {
                id: Date.now().toString(),
                title: changeForm.title,
                description: changeForm.description,
                change_type: changeForm.change_type as any,
                resources: selectedResources.map(resourceId => ({
                    resource_id: resourceId,
                    action: changeForm.change_type as any,
                    change_details: {
                        modified_attributes: [],
                        configuration_diff: '',
                        risk_factors: [],
                    },
                })),
                requester: {
                    id: '1',
                    name: 'Current User',
                    email: 'user@example.com',
                },
                target_environment: changeForm.target_environment,
                urgency: changeForm.urgency as any,
                change_category: changeForm.change_category as any,
                created_at: new Date().toISOString(),
            };

            const result = await impactService.analyzeChange(changeRequest);
            setAnalysisResult(result);
            setActiveStep(1);
            onAnalysisComplete?.(result);
        } catch (error) {
            console.error('Analysis failed:', error);
        } finally {
            setLoading(false);
        }
    };

    const getRiskColor = (level: string) => {
        switch (level) {
            case 'low': return 'success';
            case 'medium': return 'info';
            case 'high': return 'warning';
            case 'critical': return 'error';
            default: return 'default';
        }
    };

    const getRiskIcon = (level: string) => {
        switch (level) {
            case 'low': return <SuccessIcon />;
            case 'medium': return <InfoIcon />;
            case 'high': return <WarningIcon />;
            case 'critical': return <ErrorIcon />;
            default: return <InfoIcon />;
        }
    };

    const generateDependencyGraphData = () => {
        if (!analysisResult) return [];
        
        return analysisResult.dependency_analysis.upstream_dependencies.map(dep => ({
            name: dep.resource_name,
            value: dep.impact_propagation_risk * 100,
            category: 'upstream',
        })).concat(
            analysisResult.dependency_analysis.downstream_dependencies.map(dep => ({
                name: dep.resource_name,
                value: dep.impact_propagation_risk * 100,
                category: 'downstream',
            }))
        );
    };

    const generateImpactDistribution = () => {
        if (!analysisResult) return [];
        
        const directImpacts = analysisResult.blast_radius.directly_affected.length;
        const indirectImpacts = analysisResult.blast_radius.indirectly_affected.length;
        
        return [
            { name: 'Direct Impact', value: directImpacts, category: 'impact' },
            { name: 'Indirect Impact', value: indirectImpacts, category: 'impact' },
        ];
    };

    const generateRiskBreakdown = () => {
        if (!analysisResult) return [];
        
        return [
            { name: 'Technical Risk', value: 70, category: 'risk' },
            { name: 'Business Risk', value: 45, category: 'risk' },
            { name: 'Compliance Risk', value: 30, category: 'risk' },
            { name: 'Operational Risk', value: 60, category: 'risk' },
        ];
    };

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" fontWeight={600} sx={{ mb: 3 }}>
                Change Impact Analysis
            </Typography>

            <Stepper activeStep={activeStep} orientation="vertical">
                {/* Step 1: Configuration */}
                <Step>
                    <StepLabel>Configure Change Request</StepLabel>
                    <StepContent>
                        <Card>
                            <CardContent>
                                <Grid container spacing={3}>
                                    <Grid item xs={12} md={6}>
                                        <TextField
                                            fullWidth
                                            label="Change Title"
                                            value={changeForm.title}
                                            onChange={(e) => setChangeForm(prev => ({ ...prev, title: e.target.value }))}
                                            margin="normal"
                                        />
                                        <TextField
                                            fullWidth
                                            label="Description"
                                            value={changeForm.description}
                                            onChange={(e) => setChangeForm(prev => ({ ...prev, description: e.target.value }))}
                                            multiline
                                            rows={3}
                                            margin="normal"
                                        />
                                    </Grid>
                                    <Grid item xs={12} md={6}>
                                        <FormControl fullWidth margin="normal">
                                            <InputLabel>Change Type</InputLabel>
                                            <Select
                                                value={changeForm.change_type}
                                                label="Change Type"
                                                onChange={(e) => setChangeForm(prev => ({ ...prev, change_type: e.target.value }))}
                                            >
                                                <MenuItem value="create">Create</MenuItem>
                                                <MenuItem value="update">Update</MenuItem>
                                                <MenuItem value="delete">Delete</MenuItem>
                                                <MenuItem value="replace">Replace</MenuItem>
                                            </Select>
                                        </FormControl>
                                        
                                        <FormControl fullWidth margin="normal">
                                            <InputLabel>Target Environment</InputLabel>
                                            <Select
                                                value={changeForm.target_environment}
                                                label="Target Environment"
                                                onChange={(e) => setChangeForm(prev => ({ ...prev, target_environment: e.target.value }))}
                                            >
                                                <MenuItem value="dev">Development</MenuItem>
                                                <MenuItem value="staging">Staging</MenuItem>
                                                <MenuItem value="prod">Production</MenuItem>
                                            </Select>
                                        </FormControl>
                                        
                                        <FormControl fullWidth margin="normal">
                                            <InputLabel>Urgency</InputLabel>
                                            <Select
                                                value={changeForm.urgency}
                                                label="Urgency"
                                                onChange={(e) => setChangeForm(prev => ({ ...prev, urgency: e.target.value }))}
                                            >
                                                <MenuItem value="low">Low</MenuItem>
                                                <MenuItem value="medium">Medium</MenuItem>
                                                <MenuItem value="high">High</MenuItem>
                                                <MenuItem value="critical">Critical</MenuItem>
                                            </Select>
                                        </FormControl>
                                    </Grid>
                                </Grid>

                                {/* Resource Selection */}
                                <Box sx={{ mt: 3 }}>
                                    <Typography variant="h6" sx={{ mb: 2 }}>
                                        Select Resources to Analyze
                                    </Typography>
                                    <Grid container spacing={2}>
                                        {resources.map((resource) => (
                                            <Grid item xs={12} sm={6} md={4} key={resource.id}>
                                                <Card
                                                    sx={{
                                                        cursor: 'pointer',
                                                        border: selectedResources.includes(resource.id) ? 2 : 1,
                                                        borderColor: selectedResources.includes(resource.id) ? 'primary.main' : 'divider',
                                                        '&:hover': { boxShadow: 4 },
                                                    }}
                                                    onClick={() => {
                                                        setSelectedResources(prev =>
                                                            prev.includes(resource.id)
                                                                ? prev.filter(id => id !== resource.id)
                                                                : [...prev, resource.id]
                                                        );
                                                    }}
                                                >
                                                    <CardContent>
                                                        <Stack spacing={1}>
                                                            <Typography variant="subtitle2" noWrap>
                                                                {resource.name}
                                                            </Typography>
                                                            <Typography variant="caption" color="text.secondary">
                                                                {resource.type} • {resource.provider}
                                                            </Typography>
                                                            <Chip
                                                                size="small"
                                                                label={resource.environment}
                                                                color={resource.environment === 'prod' ? 'error' : 'primary'}
                                                                variant="outlined"
                                                            />
                                                        </Stack>
                                                    </CardContent>
                                                </Card>
                                            </Grid>
                                        ))}
                                    </Grid>
                                </Box>

                                <Stack direction="row" spacing={2} sx={{ mt: 3 }}>
                                    <Button
                                        variant="contained"
                                        onClick={runAnalysis}
                                        disabled={loading || selectedResources.length === 0}
                                        startIcon={loading ? <CircularProgress size={20} /> : <AnalysisIcon />}
                                    >
                                        {loading ? 'Analyzing...' : 'Run Impact Analysis'}
                                    </Button>
                                    <Button
                                        variant="outlined"
                                        startIcon={<SimulateIcon />}
                                        onClick={() => setSimulationDialog(true)}
                                        disabled={selectedResources.length === 0}
                                    >
                                        Run Simulation
                                    </Button>
                                </Stack>
                            </CardContent>
                        </Card>
                    </StepContent>
                </Step>

                {/* Step 2: Analysis Results */}
                <Step>
                    <StepLabel>Impact Analysis Results</StepLabel>
                    <StepContent>
                        {analysisResult && (
                            <Grid container spacing={3}>
                                {/* Risk Overview */}
                                <Grid item xs={12} md={4}>
                                    <Card>
                                        <CardContent>
                                            <Stack spacing={2} alignItems="center">
                                                <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                                                    <CircularProgress
                                                        variant="determinate"
                                                        value={analysisResult.overall_risk_score}
                                                        size={120}
                                                        thickness={8}
                                                        color={getRiskColor(analysisResult.risk_level) as any}
                                                    />
                                                    <Box
                                                        sx={{
                                                            top: 0,
                                                            left: 0,
                                                            bottom: 0,
                                                            right: 0,
                                                            position: 'absolute',
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            justifyContent: 'center',
                                                        }}
                                                    >
                                                        <Typography variant="h4" component="div" color="text.secondary">
                                                            {analysisResult.overall_risk_score}
                                                        </Typography>
                                                    </Box>
                                                </Box>
                                                <Chip
                                                    icon={getRiskIcon(analysisResult.risk_level)}
                                                    label={`${analysisResult.risk_level.toUpperCase()} RISK`}
                                                    color={getRiskColor(analysisResult.risk_level) as any}
                                                    size="medium"
                                                />
                                                <Typography variant="body2" color="text.secondary" textAlign="center">
                                                    Confidence: {Math.round(analysisResult.confidence_score * 100)}%
                                                </Typography>
                                            </Stack>
                                        </CardContent>
                                    </Card>
                                </Grid>

                                {/* Key Metrics */}
                                <Grid item xs={12} md={8}>
                                    <Card>
                                        <CardContent>
                                            <Typography variant="h6" sx={{ mb: 2 }}>
                                                Impact Summary
                                            </Typography>
                                            <Grid container spacing={3}>
                                                <Grid item xs={6} md={3}>
                                                    <Stack alignItems="center" spacing={1}>
                                                        <InfraIcon color="primary" fontSize="large" />
                                                        <Typography variant="h4">
                                                            {analysisResult.blast_radius.total_affected_count}
                                                        </Typography>
                                                        <Typography variant="caption" textAlign="center">
                                                            Resources Affected
                                                        </Typography>
                                                    </Stack>
                                                </Grid>
                                                <Grid item xs={6} md={3}>
                                                    <Stack alignItems="center" spacing={1}>
                                                        <UsersIcon color="warning" fontSize="large" />
                                                        <Typography variant="h4">
                                                            {analysisResult.business_impact.user_impact_assessment.affected_users.toLocaleString()}
                                                        </Typography>
                                                        <Typography variant="caption" textAlign="center">
                                                            Users Impacted
                                                        </Typography>
                                                    </Stack>
                                                </Grid>
                                                <Grid item xs={6} md={3}>
                                                    <Stack alignItems="center" spacing={1}>
                                                        <CostIcon color="error" fontSize="large" />
                                                        <Typography variant="h4">
                                                            ${analysisResult.business_impact.financial_impact.potential_cost_change.toLocaleString()}
                                                        </Typography>
                                                        <Typography variant="caption" textAlign="center">
                                                            Potential Cost Impact
                                                        </Typography>
                                                    </Stack>
                                                </Grid>
                                                <Grid item xs={6} md={3}>
                                                    <Stack alignItems="center" spacing={1}>
                                                        <ScheduleIcon color="info" fontSize="large" />
                                                        <Typography variant="h4">
                                                            {analysisResult.timeline_analysis.estimated_duration}
                                                        </Typography>
                                                        <Typography variant="caption" textAlign="center">
                                                            Estimated Duration
                                                        </Typography>
                                                    </Stack>
                                                </Grid>
                                            </Grid>
                                        </CardContent>
                                    </Card>
                                </Grid>

                                {/* Charts */}
                                <Grid item xs={12} md={6}>
                                    <Card>
                                        <CardContent>
                                            <Typography variant="h6" sx={{ mb: 2 }}>
                                                Impact Distribution
                                            </Typography>
                                            <InteractiveCharts
                                                config={{
                                                    type: 'pie',
                                                    title: '',
                                                    data: generateImpactDistribution(),
                                                    colors: ['#f44336', '#ff9800'],
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
                                            <Typography variant="h6" sx={{ mb: 2 }}>
                                                Risk Breakdown
                                            </Typography>
                                            <InteractiveCharts
                                                config={{
                                                    type: 'bar',
                                                    title: '',
                                                    data: generateRiskBreakdown(),
                                                    colors: ['#2196f3'],
                                                }}
                                                height={300}
                                                exportable={false}
                                            />
                                        </CardContent>
                                    </Card>
                                </Grid>

                                {/* Detailed Analysis Sections */}
                                <Grid item xs={12}>
                                    <Stack spacing={2}>
                                        {/* Blast Radius */}
                                        <Accordion>
                                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                                <Stack direction="row" alignItems="center" spacing={2}>
                                                    <DependencyIcon />
                                                    <Typography variant="h6">
                                                        Blast Radius Analysis
                                                    </Typography>
                                                    <Badge
                                                        badgeContent={analysisResult.blast_radius.total_affected_count}
                                                        color="error"
                                                        showZero
                                                    />
                                                </Stack>
                                            </AccordionSummary>
                                            <AccordionDetails>
                                                <Grid container spacing={3}>
                                                    <Grid item xs={12} md={6}>
                                                        <Typography variant="subtitle2" sx={{ mb: 2 }}>
                                                            Directly Affected Resources
                                                        </Typography>
                                                        <List dense>
                                                            {analysisResult.blast_radius.directly_affected.slice(0, 5).map((impact, idx) => (
                                                                <ListItem key={idx}>
                                                                    <ListItemIcon>
                                                                        {getRiskIcon(impact.impact_severity)}
                                                                    </ListItemIcon>
                                                                    <ListItemText
                                                                        primary={impact.resource_name}
                                                                        secondary={impact.impact_description}
                                                                    />
                                                                </ListItem>
                                                            ))}
                                                        </List>
                                                    </Grid>
                                                    <Grid item xs={12} md={6}>
                                                        <Typography variant="subtitle2" sx={{ mb: 2 }}>
                                                            Indirectly Affected Resources
                                                        </Typography>
                                                        <List dense>
                                                            {analysisResult.blast_radius.indirectly_affected.slice(0, 5).map((impact, idx) => (
                                                                <ListItem key={idx}>
                                                                    <ListItemIcon>
                                                                        {getRiskIcon(impact.impact_severity)}
                                                                    </ListItemIcon>
                                                                    <ListItemText
                                                                        primary={impact.resource_name}
                                                                        secondary={impact.impact_description}
                                                                    />
                                                                </ListItem>
                                                            ))}
                                                        </List>
                                                    </Grid>
                                                </Grid>
                                            </AccordionDetails>
                                        </Accordion>

                                        {/* Business Impact */}
                                        <Accordion>
                                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                                <Stack direction="row" alignItems="center" spacing={2}>
                                                    <UsersIcon />
                                                    <Typography variant="h6">
                                                        Business Impact Assessment
                                                    </Typography>
                                                </Stack>
                                            </AccordionSummary>
                                            <AccordionDetails>
                                                <Grid container spacing={3}>
                                                    <Grid item xs={12} md={4}>
                                                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                                                            <Typography variant="subtitle2" color="text.secondary">
                                                                Service Disruption Risk
                                                            </Typography>
                                                            <Typography variant="h4" color="warning.main">
                                                                {Math.round(analysisResult.business_impact.service_disruption_risk * 100)}%
                                                            </Typography>
                                                        </Paper>
                                                    </Grid>
                                                    <Grid item xs={12} md={4}>
                                                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                                                            <Typography variant="subtitle2" color="text.secondary">
                                                                Downtime Cost
                                                            </Typography>
                                                            <Typography variant="h4" color="error.main">
                                                                ${analysisResult.business_impact.financial_impact.downtime_cost_estimate.toLocaleString()}
                                                            </Typography>
                                                        </Paper>
                                                    </Grid>
                                                    <Grid item xs={12} md={4}>
                                                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                                                            <Typography variant="subtitle2" color="text.secondary">
                                                                Recovery Cost
                                                            </Typography>
                                                            <Typography variant="h4" color="info.main">
                                                                ${analysisResult.business_impact.financial_impact.recovery_cost_estimate.toLocaleString()}
                                                            </Typography>
                                                        </Paper>
                                                    </Grid>
                                                </Grid>
                                            </AccordionDetails>
                                        </Accordion>

                                        {/* Recommendations */}
                                        <Accordion>
                                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                                <Stack direction="row" alignItems="center" spacing={2}>
                                                    <InfoIcon />
                                                    <Typography variant="h6">
                                                        Risk Mitigation Recommendations
                                                    </Typography>
                                                    <Badge
                                                        badgeContent={analysisResult.risk_mitigation.recommendations.length}
                                                        color="info"
                                                        showZero
                                                    />
                                                </Stack>
                                            </AccordionSummary>
                                            <AccordionDetails>
                                                <List>
                                                    {analysisResult.risk_mitigation.recommendations.map((rec, idx) => (
                                                        <React.Fragment key={idx}>
                                                            <ListItem>
                                                                <ListItemIcon>
                                                                    <Chip
                                                                        size="small"
                                                                        label={rec.priority}
                                                                        color={getRiskColor(rec.priority) as any}
                                                                    />
                                                                </ListItemIcon>
                                                                <ListItemText
                                                                    primary={rec.title}
                                                                    secondary={rec.description}
                                                                />
                                                            </ListItem>
                                                            <Divider />
                                                        </React.Fragment>
                                                    ))}
                                                </List>
                                            </AccordionDetails>
                                        </Accordion>
                                    </Stack>
                                </Grid>

                                {/* Action Buttons */}
                                <Grid item xs={12}>
                                    <Stack direction="row" spacing={2} justifyContent="center">
                                        <Button
                                            variant="contained"
                                            startIcon={<ExportIcon />}
                                            onClick={() => setExportDialog(true)}
                                        >
                                            Export Report
                                        </Button>
                                        <Button
                                            variant="outlined"
                                            startIcon={<SimulateIcon />}
                                            onClick={() => setSimulationDialog(true)}
                                        >
                                            Run Simulation
                                        </Button>
                                        <Button
                                            variant="outlined"
                                            startIcon={<CompareIcon />}
                                        >
                                            Compare Alternatives
                                        </Button>
                                    </Stack>
                                </Grid>
                            </Grid>
                        )}
                    </StepContent>
                </Step>
            </Stepper>
        </Box>
    );
};

export default ChangeImpactAnalysis;