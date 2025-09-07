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
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Tooltip,
    Switch,
    FormControlLabel,
} from '@mui/material';
import {
    GitHub,
    GitLab,
    Add as AddIcon,
    Delete as DeleteIcon,
    Refresh as RefreshIcon,
    Launch as LaunchIcon,
    Code as CodeIcon,
    Branch as BranchIcon,
    PullRequest as PullRequestIcon,
    PlayArrow as DeployIcon,
    Visibility as PreviewIcon,
    Settings as SettingsIcon,
    ExpandMore as ExpandMoreIcon,
    CheckCircle as CheckIcon,
    Error as ErrorIcon,
    Schedule as PendingIcon,
    CloudUpload as UploadIcon,
} from '@mui/icons-material';
import { getGitOpsService, GitRepository, PullRequest, IaCTemplate, DeploymentPlan } from '../services/gitOpsIntegration';
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

const GitOpsIntegration: React.FC = () => {
    const [tabValue, setTabValue] = useState(0);
    const [repositories, setRepositories] = useState<GitRepository[]>([]);
    const [pullRequests, setPullRequests] = useState<PullRequest[]>([]);
    const [templates, setTemplates] = useState<IaCTemplate[]>([]);
    const [deploymentPlans, setDeploymentPlans] = useState<DeploymentPlan[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedRepo, setSelectedRepo] = useState<GitRepository | null>(null);
    
    // Dialog states
    const [connectRepoDialog, setConnectRepoDialog] = useState(false);
    const [createTemplateDialog, setCreateTemplateDialog] = useState(false);
    const [deployDialog, setDeployDialog] = useState(false);
    const [previewDialog, setPreviewDialog] = useState(false);
    
    // Form states
    const [repoForm, setRepoForm] = useState({
        provider: 'github' as 'github' | 'gitlab',
        url: '',
        accessToken: '',
    });
    
    const [templateForm, setTemplateForm] = useState({
        name: '',
        description: '',
        provider: 'terraform' as 'terraform' | 'cloudformation',
        template: '',
        variables: '{}',
    });

    const [deployForm, setDeployForm] = useState({
        templateId: '',
        environment: 'dev' as 'dev' | 'staging' | 'prod',
        variables: '{}',
        autoApprove: false,
    });

    const gitOpsService = getGitOpsService();

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [repos, templates, plans] = await Promise.all([
                gitOpsService.getRepositories(),
                gitOpsService.getIaCTemplates(),
                gitOpsService.getDeploymentPlans(),
            ]);
            setRepositories(repos);
            setTemplates(templates);
            setDeploymentPlans(plans);
            
            if (repos.length > 0 && selectedRepo) {
                const prs = await gitOpsService.getPullRequests(selectedRepo.id);
                setPullRequests(prs);
            }
        } catch (error) {
            console.error('Failed to load GitOps data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleConnectRepository = async () => {
        try {
            const newRepo = await gitOpsService.connectRepository(
                repoForm.provider,
                repoForm.url,
                repoForm.accessToken
            );
            setRepositories(prev => [...prev, newRepo]);
            setConnectRepoDialog(false);
            setRepoForm({ provider: 'github', url: '', accessToken: '' });
        } catch (error) {
            console.error('Failed to connect repository:', error);
        }
    };

    const handleCreateTemplate = async () => {
        try {
            const newTemplate = await gitOpsService.createIaCTemplate({
                name: templateForm.name,
                description: templateForm.description,
                provider: templateForm.provider,
                language: templateForm.provider === 'terraform' ? 'hcl' : 'yaml',
                template: templateForm.template,
                variables: JSON.parse(templateForm.variables),
                outputs: {},
                tags: [],
                version: '1.0.0',
            });
            setTemplates(prev => [...prev, newTemplate]);
            setCreateTemplateDialog(false);
            setTemplateForm({ name: '', description: '', provider: 'terraform', template: '', variables: '{}' });
        } catch (error) {
            console.error('Failed to create template:', error);
        }
    };

    const handleDeploy = async () => {
        try {
            const selectedTemplate = templates.find(t => t.id === deployForm.templateId);
            if (!selectedTemplate || !selectedRepo) return;

            const plan: Omit<DeploymentPlan, 'id'> = {
                name: `${selectedTemplate.name}-${deployForm.environment}`,
                repository: selectedRepo,
                branch: 'main',
                template: selectedTemplate,
                environment: deployForm.environment,
                variables: JSON.parse(deployForm.variables),
                approval_required: !deployForm.autoApprove,
                auto_deploy: deployForm.autoApprove,
                rollback_enabled: true,
                notification_settings: {
                    channels: ['email'],
                    on_success: true,
                    on_failure: true,
                    on_approval_needed: true,
                },
            };

            const createdPlan = await gitOpsService.createDeploymentPlan(plan);
            const deployment = await gitOpsService.executeDeployment(createdPlan.id, deployForm.environment);
            
            setDeploymentPlans(prev => [...prev, createdPlan]);
            setDeployDialog(false);
            console.log('Deployment started:', deployment.deployment_id);
        } catch (error) {
            console.error('Failed to deploy:', error);
        }
    };

    const generateDeploymentMetrics = () => {
        return [
            { name: 'Success', value: 85, category: 'deployment' },
            { name: 'Failed', value: 10, category: 'deployment' },
            { name: 'Pending', value: 5, category: 'deployment' },
        ];
    };

    const generateActivityMetrics = () => {
        return [
            { name: 'Jan', value: 12, category: 'commits' },
            { name: 'Feb', value: 18, category: 'commits' },
            { name: 'Mar', value: 25, category: 'commits' },
            { name: 'Apr', value: 20, category: 'commits' },
            { name: 'May', value: 30, category: 'commits' },
            { name: 'Jun', value: 28, category: 'commits' },
        ];
    };

    return (
        <Box sx={{ p: 3 }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
                <Typography variant="h4" fontWeight={600}>
                    GitOps Integration
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setConnectRepoDialog(true)}
                >
                    Connect Repository
                </Button>
            </Stack>

            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
                <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
                    <Tab icon={<GitHub />} label="Repositories" />
                    <Tab icon={<PullRequestIcon />} label="Pull Requests" />
                    <Tab icon={<CodeIcon />} label="IaC Templates" />
                    <Tab icon={<DeployIcon />} label="Deployments" />
                    <Tab icon={<SettingsIcon />} label="Settings" />
                </Tabs>
            </Box>

            {loading && <LinearProgress sx={{ mb: 2 }} />}

            {/* Repositories Tab */}
            <TabPanel value={tabValue} index={0}>
                <Grid container spacing={3}>
                    <Grid item xs={12} md={8}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" sx={{ mb: 2 }}>
                                    Connected Repositories
                                </Typography>
                                {repositories.length === 0 ? (
                                    <Alert severity="info">
                                        No repositories connected. Connect your first repository to get started.
                                    </Alert>
                                ) : (
                                    <List>
                                        {repositories.map((repo) => (
                                            <React.Fragment key={repo.id}>
                                                <ListItem>
                                                    <ListItemIcon>
                                                        {repo.provider === 'github' ? <GitHub /> : <GitLab />}
                                                    </ListItemIcon>
                                                    <ListItemText
                                                        primary={repo.full_name}
                                                        secondary={
                                                            <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                                                                <Chip
                                                                    size="small"
                                                                    label={repo.provider}
                                                                    color="primary"
                                                                    variant="outlined"
                                                                />
                                                                <Chip
                                                                    size="small"
                                                                    label={repo.private ? 'Private' : 'Public'}
                                                                    color={repo.private ? 'warning' : 'success'}
                                                                    variant="outlined"
                                                                />
                                                                <Chip
                                                                    size="small"
                                                                    label={`Default: ${repo.default_branch}`}
                                                                    variant="outlined"
                                                                />
                                                            </Stack>
                                                        }
                                                    />
                                                    <ListItemSecondaryAction>
                                                        <Stack direction="row" spacing={1}>
                                                            <Tooltip title="View Repository">
                                                                <IconButton
                                                                    size="small"
                                                                    onClick={() => window.open(repo.url, '_blank')}
                                                                >
                                                                    <LaunchIcon />
                                                                </IconButton>
                                                            </Tooltip>
                                                            <Tooltip title="Select Repository">
                                                                <IconButton
                                                                    size="small"
                                                                    color={selectedRepo?.id === repo.id ? 'primary' : 'default'}
                                                                    onClick={() => setSelectedRepo(repo)}
                                                                >
                                                                    <CheckIcon />
                                                                </IconButton>
                                                            </Tooltip>
                                                            <Tooltip title="Remove Repository">
                                                                <IconButton
                                                                    size="small"
                                                                    color="error"
                                                                    onClick={() => gitOpsService.disconnectRepository(repo.id)}
                                                                >
                                                                    <DeleteIcon />
                                                                </IconButton>
                                                            </Tooltip>
                                                        </Stack>
                                                    </ListItemSecondaryAction>
                                                </ListItem>
                                                <Divider />
                                            </React.Fragment>
                                        ))}
                                    </List>
                                )}
                            </CardContent>
                        </Card>
                    </Grid>
                    
                    <Grid item xs={12} md={4}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" sx={{ mb: 2 }}>
                                    Deployment Success Rate
                                </Typography>
                                <InteractiveCharts
                                    config={{
                                        type: 'pie',
                                        title: '',
                                        data: generateDeploymentMetrics(),
                                        colors: ['#4caf50', '#f44336', '#ff9800'],
                                    }}
                                    height={250}
                                    exportable={false}
                                />
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            </TabPanel>

            {/* Pull Requests Tab */}
            <TabPanel value={tabValue} index={1}>
                <Card>
                    <CardContent>
                        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
                            <Typography variant="h6">
                                Pull Requests
                                {selectedRepo && ` - ${selectedRepo.name}`}
                            </Typography>
                            {selectedRepo && (
                                <Button
                                    startIcon={<AddIcon />}
                                    onClick={() => {
                                        // Create new PR logic
                                    }}
                                >
                                    New Pull Request
                                </Button>
                            )}
                        </Stack>
                        
                        {!selectedRepo ? (
                            <Alert severity="info">
                                Please select a repository to view pull requests.
                            </Alert>
                        ) : pullRequests.length === 0 ? (
                            <Alert severity="info">
                                No pull requests found for this repository.
                            </Alert>
                        ) : (
                            <List>
                                {pullRequests.map((pr) => (
                                    <React.Fragment key={pr.id}>
                                        <ListItem alignItems="flex-start">
                                            <ListItemIcon>
                                                <PullRequestIcon color={
                                                    pr.state === 'merged' ? 'success' :
                                                    pr.state === 'closed' ? 'error' : 'primary'
                                                } />
                                            </ListItemIcon>
                                            <ListItemText
                                                primary={pr.title}
                                                secondary={
                                                    <Box>
                                                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                                            {pr.description}
                                                        </Typography>
                                                        <Stack direction="row" spacing={1}>
                                                            <Chip
                                                                size="small"
                                                                label={pr.state}
                                                                color={
                                                                    pr.state === 'merged' ? 'success' :
                                                                    pr.state === 'closed' ? 'error' : 'primary'
                                                                }
                                                            />
                                                            <Chip
                                                                size="small"
                                                                label={`${pr.source_branch} → ${pr.target_branch}`}
                                                                variant="outlined"
                                                            />
                                                            <Chip
                                                                size="small"
                                                                label={pr.checks_status}
                                                                color={
                                                                    pr.checks_status === 'success' ? 'success' :
                                                                    pr.checks_status === 'failure' ? 'error' : 'warning'
                                                                }
                                                                variant="outlined"
                                                            />
                                                        </Stack>
                                                    </Box>
                                                }
                                            />
                                            <ListItemSecondaryAction>
                                                <Button
                                                    size="small"
                                                    onClick={() => window.open(pr.url, '_blank')}
                                                >
                                                    View
                                                </Button>
                                            </ListItemSecondaryAction>
                                        </ListItem>
                                        <Divider />
                                    </React.Fragment>
                                ))}
                            </List>
                        )}
                    </CardContent>
                </Card>
            </TabPanel>

            {/* IaC Templates Tab */}
            <TabPanel value={tabValue} index={2}>
                <Stack spacing={3}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Typography variant="h6">
                            Infrastructure as Code Templates
                        </Typography>
                        <Button
                            variant="contained"
                            startIcon={<AddIcon />}
                            onClick={() => setCreateTemplateDialog(true)}
                        >
                            Create Template
                        </Button>
                    </Stack>

                    <Grid container spacing={3}>
                        {templates.map((template) => (
                            <Grid item xs={12} md={6} lg={4} key={template.id}>
                                <Card>
                                    <CardContent>
                                        <Stack spacing={2}>
                                            <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                                                <Typography variant="h6" noWrap>
                                                    {template.name}
                                                </Typography>
                                                <Chip
                                                    size="small"
                                                    label={template.provider}
                                                    color="primary"
                                                    variant="outlined"
                                                />
                                            </Stack>
                                            
                                            <Typography variant="body2" color="text.secondary">
                                                {template.description}
                                            </Typography>
                                            
                                            <Stack direction="row" spacing={1} flexWrap="wrap">
                                                {template.tags.map((tag) => (
                                                    <Chip key={tag} size="small" label={tag} variant="outlined" />
                                                ))}
                                            </Stack>
                                            
                                            <Stack direction="row" spacing={1}>
                                                <Button
                                                    size="small"
                                                    startIcon={<PreviewIcon />}
                                                    onClick={() => setPreviewDialog(true)}
                                                >
                                                    Preview
                                                </Button>
                                                <Button
                                                    size="small"
                                                    startIcon={<DeployIcon />}
                                                    variant="contained"
                                                    onClick={() => {
                                                        setDeployForm(prev => ({ ...prev, templateId: template.id }));
                                                        setDeployDialog(true);
                                                    }}
                                                >
                                                    Deploy
                                                </Button>
                                            </Stack>
                                        </Stack>
                                    </CardContent>
                                </Card>
                            </Grid>
                        ))}
                    </Grid>
                </Stack>
            </TabPanel>

            {/* Deployments Tab */}
            <TabPanel value={tabValue} index={3}>
                <Grid container spacing={3}>
                    <Grid item xs={12} lg={8}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" sx={{ mb: 2 }}>
                                    Deployment History
                                </Typography>
                                {deploymentPlans.length === 0 ? (
                                    <Alert severity="info">
                                        No deployments found. Create and deploy your first IaC template.
                                    </Alert>
                                ) : (
                                    <List>
                                        {deploymentPlans.map((plan) => (
                                            <React.Fragment key={plan.id}>
                                                <ListItem>
                                                    <ListItemIcon>
                                                        <DeployIcon color="primary" />
                                                    </ListItemIcon>
                                                    <ListItemText
                                                        primary={plan.name}
                                                        secondary={
                                                            <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                                                                <Chip
                                                                    size="small"
                                                                    label={plan.environment}
                                                                    color={
                                                                        plan.environment === 'prod' ? 'error' :
                                                                        plan.environment === 'staging' ? 'warning' : 'primary'
                                                                    }
                                                                />
                                                                <Chip
                                                                    size="small"
                                                                    label={plan.template.provider}
                                                                    variant="outlined"
                                                                />
                                                                {plan.auto_deploy && (
                                                                    <Chip
                                                                        size="small"
                                                                        label="Auto Deploy"
                                                                        color="success"
                                                                        variant="outlined"
                                                                    />
                                                                )}
                                                            </Stack>
                                                        }
                                                    />
                                                    <ListItemSecondaryAction>
                                                        <Stack direction="row" spacing={1}>
                                                            <Button size="small" color="error">
                                                                Rollback
                                                            </Button>
                                                            <Button size="small" variant="outlined">
                                                                Logs
                                                            </Button>
                                                        </Stack>
                                                    </ListItemSecondaryAction>
                                                </ListItem>
                                                <Divider />
                                            </React.Fragment>
                                        ))}
                                    </List>
                                )}
                            </CardContent>
                        </Card>
                    </Grid>
                    
                    <Grid item xs={12} lg={4}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" sx={{ mb: 2 }}>
                                    Activity Timeline
                                </Typography>
                                <InteractiveCharts
                                    config={{
                                        type: 'line',
                                        title: '',
                                        data: generateActivityMetrics(),
                                        colors: ['#2196f3'],
                                    }}
                                    height={300}
                                    exportable={false}
                                />
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            </TabPanel>

            {/* Settings Tab */}
            <TabPanel value={tabValue} index={4}>
                <Stack spacing={3}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" sx={{ mb: 2 }}>
                                Notification Settings
                            </Typography>
                            <Stack spacing={2}>
                                <FormControlLabel
                                    control={<Switch defaultChecked />}
                                    label="Email notifications for deployment success"
                                />
                                <FormControlLabel
                                    control={<Switch defaultChecked />}
                                    label="Email notifications for deployment failures"
                                />
                                <FormControlLabel
                                    control={<Switch defaultChecked />}
                                    label="Slack notifications for pull request reviews"
                                />
                                <FormControlLabel
                                    control={<Switch />}
                                    label="SMS notifications for critical failures"
                                />
                            </Stack>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardContent>
                            <Typography variant="h6" sx={{ mb: 2 }}>
                                Security Settings
                            </Typography>
                            <Stack spacing={2}>
                                <FormControlLabel
                                    control={<Switch defaultChecked />}
                                    label="Require approval for production deployments"
                                />
                                <FormControlLabel
                                    control={<Switch defaultChecked />}
                                    label="Enable branch protection rules"
                                />
                                <FormControlLabel
                                    control={<Switch />}
                                    label="Require signed commits"
                                />
                                <FormControlLabel
                                    control={<Switch defaultChecked />}
                                    label="Enable deployment rollback protection"
                                />
                            </Stack>
                        </CardContent>
                    </Card>
                </Stack>
            </TabPanel>

            {/* Connect Repository Dialog */}
            <Dialog open={connectRepoDialog} onClose={() => setConnectRepoDialog(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Connect Repository</DialogTitle>
                <DialogContent>
                    <Stack spacing={3} sx={{ mt: 1 }}>
                        <FormControl fullWidth>
                            <InputLabel>Provider</InputLabel>
                            <Select
                                value={repoForm.provider}
                                label="Provider"
                                onChange={(e) => setRepoForm(prev => ({ ...prev, provider: e.target.value as any }))}
                            >
                                <MenuItem value="github">GitHub</MenuItem>
                                <MenuItem value="gitlab">GitLab</MenuItem>
                            </Select>
                        </FormControl>
                        
                        <TextField
                            fullWidth
                            label="Repository URL"
                            value={repoForm.url}
                            onChange={(e) => setRepoForm(prev => ({ ...prev, url: e.target.value }))}
                            placeholder="https://github.com/username/repo"
                        />
                        
                        <TextField
                            fullWidth
                            label="Access Token"
                            type="password"
                            value={repoForm.accessToken}
                            onChange={(e) => setRepoForm(prev => ({ ...prev, accessToken: e.target.value }))}
                            helperText="Personal access token with repo permissions"
                        />
                    </Stack>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setConnectRepoDialog(false)}>Cancel</Button>
                    <Button variant="contained" onClick={handleConnectRepository}>
                        Connect
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Create Template Dialog */}
            <Dialog open={createTemplateDialog} onClose={() => setCreateTemplateDialog(false)} maxWidth="md" fullWidth>
                <DialogTitle>Create IaC Template</DialogTitle>
                <DialogContent>
                    <Stack spacing={3} sx={{ mt: 1 }}>
                        <Stack direction="row" spacing={2}>
                            <TextField
                                fullWidth
                                label="Template Name"
                                value={templateForm.name}
                                onChange={(e) => setTemplateForm(prev => ({ ...prev, name: e.target.value }))}
                            />
                            <FormControl sx={{ minWidth: 150 }}>
                                <InputLabel>Provider</InputLabel>
                                <Select
                                    value={templateForm.provider}
                                    label="Provider"
                                    onChange={(e) => setTemplateForm(prev => ({ ...prev, provider: e.target.value as any }))}
                                >
                                    <MenuItem value="terraform">Terraform</MenuItem>
                                    <MenuItem value="cloudformation">CloudFormation</MenuItem>
                                </Select>
                            </FormControl>
                        </Stack>
                        
                        <TextField
                            fullWidth
                            label="Description"
                            value={templateForm.description}
                            onChange={(e) => setTemplateForm(prev => ({ ...prev, description: e.target.value }))}
                            multiline
                            rows={2}
                        />
                        
                        <TextField
                            fullWidth
                            label="Template Code"
                            value={templateForm.template}
                            onChange={(e) => setTemplateForm(prev => ({ ...prev, template: e.target.value }))}
                            multiline
                            rows={10}
                            sx={{ fontFamily: 'monospace' }}
                        />
                        
                        <TextField
                            fullWidth
                            label="Variables (JSON)"
                            value={templateForm.variables}
                            onChange={(e) => setTemplateForm(prev => ({ ...prev, variables: e.target.value }))}
                            multiline
                            rows={3}
                            sx={{ fontFamily: 'monospace' }}
                        />
                    </Stack>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setCreateTemplateDialog(false)}>Cancel</Button>
                    <Button variant="contained" onClick={handleCreateTemplate}>
                        Create
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Deploy Dialog */}
            <Dialog open={deployDialog} onClose={() => setDeployDialog(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Deploy Infrastructure</DialogTitle>
                <DialogContent>
                    <Stack spacing={3} sx={{ mt: 1 }}>
                        <FormControl fullWidth>
                            <InputLabel>Environment</InputLabel>
                            <Select
                                value={deployForm.environment}
                                label="Environment"
                                onChange={(e) => setDeployForm(prev => ({ ...prev, environment: e.target.value as any }))}
                            >
                                <MenuItem value="dev">Development</MenuItem>
                                <MenuItem value="staging">Staging</MenuItem>
                                <MenuItem value="prod">Production</MenuItem>
                            </Select>
                        </FormControl>
                        
                        <TextField
                            fullWidth
                            label="Variables (JSON)"
                            value={deployForm.variables}
                            onChange={(e) => setDeployForm(prev => ({ ...prev, variables: e.target.value }))}
                            multiline
                            rows={4}
                            sx={{ fontFamily: 'monospace' }}
                        />
                        
                        <FormControlLabel
                            control={
                                <Switch
                                    checked={deployForm.autoApprove}
                                    onChange={(e) => setDeployForm(prev => ({ ...prev, autoApprove: e.target.checked }))}
                                />
                            }
                            label="Auto-approve deployment (skip manual approval)"
                        />
                    </Stack>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeployDialog(false)}>Cancel</Button>
                    <Button variant="contained" onClick={handleDeploy} color="primary">
                        Deploy
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default GitOpsIntegration;