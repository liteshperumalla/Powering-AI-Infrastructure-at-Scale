/**
 * Compliance Dashboard Component
 * 
 * Provides comprehensive compliance management interface including:
 * - Consent management
 * - Data retention policies
 * - Data export/portability
 * - Privacy controls
 * - Audit trail access
 */

import React, { useState, useEffect } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Grid,
    Switch,
    FormControlLabel,
    Button,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Alert,
    Chip,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    LinearProgress,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    TextField,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Checkbox,
    ListItemText,
    Divider,
    IconButton,
    Tooltip
} from '@mui/material';
import {
    ExpandMore as ExpandMoreIcon,
    Download as DownloadIcon,
    Delete as DeleteIcon,
    Security as SecurityIcon,
    Policy as PolicyIcon,
    Assessment as AssessmentIcon,
    Visibility as VisibilityIcon,
    Warning as WarningIcon,
    CheckCircle as CheckCircleIcon,
    Cancel as CancelIcon
} from '@mui/icons-material';

// Types
interface ConsentStatus {
    status: 'granted' | 'denied' | 'withdrawn' | 'pending';
    granted_at?: string;
    withdrawn_at?: string;
    legal_basis?: string;
    purpose?: string;
}

interface ConsentSummary {
    [key: string]: ConsentStatus;
}

interface DataCategory {
    value: string;
    label: string;
    description: string;
}

interface RetentionPolicy {
    data_category: string;
    retention_period: string;
    legal_basis: string;
    description: string;
    auto_delete: boolean;
    exceptions: string[];
}

interface AuditEvent {
    timestamp: string;
    event_type: string;
    user_id: string;
    action: string;
    resource_type: string;
    outcome: string;
    severity: string;
}

const ComplianceDashboard: React.FC = () => {
    // State management
    const [consentSummary, setConsentSummary] = useState<ConsentSummary>({});
    const [retentionPolicies, setRetentionPolicies] = useState<Record<string, RetentionPolicy>>({});
    const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Dialog states
    const [exportDialogOpen, setExportDialogOpen] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [consentDialogOpen, setConsentDialogOpen] = useState(false);

    // Form states
    const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
    const [deleteReason, setDeleteReason] = useState('');
    const [deleteConfirm, setDeleteConfirm] = useState(false);
    const [exportFormat, setExportFormat] = useState('json');

    // Data categories
    const dataCategories: DataCategory[] = [
        { value: 'personal_data', label: 'Personal Data', description: 'Name, email, profile information' },
        { value: 'business_data', label: 'Business Data', description: 'Company information and business details' },
        { value: 'assessment_data', label: 'Assessment Data', description: 'Infrastructure assessments and requirements' },
        { value: 'recommendation_data', label: 'Recommendation Data', description: 'AI-generated recommendations' },
        { value: 'report_data', label: 'Report Data', description: 'Generated reports and documents' },
        { value: 'technical_data', label: 'Technical Data', description: 'Technical logs and system data' }
    ];

    // Consent types
    const consentTypes = [
        { key: 'data_processing', label: 'Data Processing', description: 'Process your data for service provision' },
        { key: 'marketing', label: 'Marketing', description: 'Send marketing communications' },
        { key: 'analytics', label: 'Analytics', description: 'Analyze usage patterns for improvement' },
        { key: 'third_party_sharing', label: 'Third Party Sharing', description: 'Share data with trusted partners' },
        { key: 'cookies', label: 'Cookies', description: 'Use cookies for functionality and analytics' },
        { key: 'profiling', label: 'Profiling', description: 'Create profiles for personalization' }
    ];

    // Load data on component mount
    useEffect(() => {
        loadComplianceData();
    }, []);

    const loadComplianceData = async () => {
        try {
            setLoading(true);

            // Load consent status
            const consentResponse = await fetch('/api/compliance/consent', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            if (consentResponse.ok) {
                const consentData = await consentResponse.json();
                setConsentSummary(consentData.consent_summary || {});
            }

            // Load retention policies (admin only)
            try {
                const policiesResponse = await fetch('/api/compliance/retention/policies', {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
                });
                if (policiesResponse.ok) {
                    const policiesData = await policiesResponse.json();
                    setRetentionPolicies(policiesData.policies || {});
                }
            } catch (e) {
                // User might not have admin access
                console.log('Retention policies not accessible (admin only)');
            }

            // Load recent audit events (admin only)
            try {
                const auditResponse = await fetch('/api/compliance/audit/summary?days=7', {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
                });
                if (auditResponse.ok) {
                    const auditData = await auditResponse.json();
                    setAuditEvents(auditData.audit_summary?.recent_events || []);
                }
            } catch (e) {
                // User might not have admin access
                console.log('Audit data not accessible (admin only)');
            }

        } catch (err) {
            setError('Failed to load compliance data');
            console.error('Error loading compliance data:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleConsentChange = async (consentType: string, granted: boolean) => {
        try {
            const response = await fetch('/api/compliance/consent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    consent_type: consentType,
                    status: granted ? 'granted' : 'denied',
                    legal_basis: 'User consent',
                    purpose: 'Service provision and improvement'
                })
            });

            if (response.ok) {
                // Reload consent data
                loadComplianceData();
            } else {
                setError('Failed to update consent');
            }
        } catch (err) {
            setError('Failed to update consent');
            console.error('Error updating consent:', err);
        }
    };

    const handleDataExport = async () => {
        try {
            const response = await fetch('/api/compliance/data/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    data_categories: selectedCategories.length > 0 ? selectedCategories : undefined,
                    format: exportFormat
                })
            });

            if (response.ok) {
                const data = await response.json();

                // Download the exported data
                const blob = new Blob([JSON.stringify(data.export_data, null, 2)], {
                    type: 'application/json'
                });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `user_data_export_${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);

                setExportDialogOpen(false);
                setSelectedCategories([]);
            } else {
                setError('Failed to export data');
            }
        } catch (err) {
            setError('Failed to export data');
            console.error('Error exporting data:', err);
        }
    };

    const handleDataDeletion = async () => {
        if (!deleteConfirm || !deleteReason.trim()) {
            setError('Please confirm deletion and provide a reason');
            return;
        }

        try {
            const response = await fetch('/api/compliance/data/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    data_categories: selectedCategories.length > 0 ? selectedCategories : undefined,
                    reason: deleteReason,
                    confirm: deleteConfirm
                })
            });

            if (response.ok) {
                setDeleteDialogOpen(false);
                setSelectedCategories([]);
                setDeleteReason('');
                setDeleteConfirm(false);

                // Show success message
                alert('Data deletion request submitted successfully. Processing will begin shortly.');
            } else {
                setError('Failed to submit deletion request');
            }
        } catch (err) {
            setError('Failed to submit deletion request');
            console.error('Error deleting data:', err);
        }
    };

    const getConsentStatusColor = (status: string) => {
        switch (status) {
            case 'granted': return 'success';
            case 'denied': return 'error';
            case 'withdrawn': return 'warning';
            default: return 'default';
        }
    };

    const getConsentStatusIcon = (status: string) => {
        switch (status) {
            case 'granted': return <CheckCircleIcon />;
            case 'denied': return <CancelIcon />;
            case 'withdrawn': return <WarningIcon />;
            default: return <VisibilityIcon />;
        }
    };

    if (loading) {
        return (
            <Box sx={{ width: '100%', mt: 2 }}>
                <LinearProgress />
                <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
                    Loading compliance data...
                </Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
                <SecurityIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Compliance Dashboard
            </Typography>

            {error && (
                <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            <Grid container spacing={3}>
                {/* Consent Management */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                <PolicyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                                Consent Management
                            </Typography>

                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                Manage your consent for different types of data processing
                            </Typography>

                            {consentTypes.map((type) => {
                                const consent = consentSummary[type.key];
                                const isGranted = consent?.status === 'granted';

                                return (
                                    <Box key={type.key} sx={{ mb: 2 }}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                            <Box sx={{ flex: 1 }}>
                                                <Typography variant="subtitle2">{type.label}</Typography>
                                                <Typography variant="body2" color="text.secondary">
                                                    {type.description}
                                                </Typography>
                                            </Box>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Chip
                                                    icon={getConsentStatusIcon(consent?.status || 'pending')}
                                                    label={consent?.status || 'pending'}
                                                    color={getConsentStatusColor(consent?.status || 'pending') as any}
                                                    size="small"
                                                />
                                                <Switch
                                                    checked={isGranted}
                                                    onChange={(e) => handleConsentChange(type.key, e.target.checked)}
                                                />
                                            </Box>
                                        </Box>
                                        {consent?.granted_at && (
                                            <Typography variant="caption" color="text.secondary">
                                                Granted: {new Date(consent.granted_at).toLocaleDateString()}
                                            </Typography>
                                        )}
                                        <Divider sx={{ mt: 1 }} />
                                    </Box>
                                );
                            })}

                            <Button
                                variant="outlined"
                                fullWidth
                                onClick={() => setConsentDialogOpen(true)}
                                sx={{ mt: 2 }}
                            >
                                Manage All Consent
                            </Button>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Data Rights */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                <AssessmentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                                Your Data Rights
                            </Typography>

                            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                                Exercise your rights regarding your personal data
                            </Typography>

                            <Grid container spacing={2}>
                                <Grid item xs={12}>
                                    <Button
                                        variant="outlined"
                                        startIcon={<DownloadIcon />}
                                        fullWidth
                                        onClick={() => setExportDialogOpen(true)}
                                    >
                                        Export My Data
                                    </Button>
                                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                                        Download all your data in a portable format (GDPR Article 20)
                                    </Typography>
                                </Grid>

                                <Grid item xs={12}>
                                    <Button
                                        variant="outlined"
                                        color="error"
                                        startIcon={<DeleteIcon />}
                                        fullWidth
                                        onClick={() => setDeleteDialogOpen(true)}
                                    >
                                        Delete My Data
                                    </Button>
                                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                                        Request deletion of your personal data (GDPR Article 17)
                                    </Typography>
                                </Grid>
                            </Grid>

                            <Divider sx={{ my: 2 }} />

                            <Typography variant="subtitle2" gutterBottom>
                                Data Retention Information
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                • Personal data: Retained for 3 years after account closure
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                • Assessment data: Retained for 3 years
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                • Audit logs: Retained for 7 years for compliance
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Retention Policies (Admin Only) */}
                {Object.keys(retentionPolicies).length > 0 && (
                    <Grid item xs={12}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Data Retention Policies
                                </Typography>

                                <TableContainer component={Paper} variant="outlined">
                                    <Table size="small">
                                        <TableHead>
                                            <TableRow>
                                                <TableCell>Data Category</TableCell>
                                                <TableCell>Retention Period</TableCell>
                                                <TableCell>Auto Delete</TableCell>
                                                <TableCell>Legal Basis</TableCell>
                                                <TableCell>Description</TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {Object.entries(retentionPolicies).map(([category, policy]) => (
                                                <TableRow key={category}>
                                                    <TableCell>
                                                        <Chip label={category.replace('_', ' ')} size="small" />
                                                    </TableCell>
                                                    <TableCell>{policy.retention_period.replace('_', ' ')}</TableCell>
                                                    <TableCell>
                                                        {policy.auto_delete ? (
                                                            <CheckCircleIcon color="success" />
                                                        ) : (
                                                            <CancelIcon color="error" />
                                                        )}
                                                    </TableCell>
                                                    <TableCell>{policy.legal_basis}</TableCell>
                                                    <TableCell>{policy.description}</TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </TableContainer>
                            </CardContent>
                        </Card>
                    </Grid>
                )}

                {/* Recent Audit Events (Admin Only) */}
                {auditEvents.length > 0 && (
                    <Grid item xs={12}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Recent Audit Events
                                </Typography>

                                <TableContainer component={Paper} variant="outlined">
                                    <Table size="small">
                                        <TableHead>
                                            <TableRow>
                                                <TableCell>Timestamp</TableCell>
                                                <TableCell>Event Type</TableCell>
                                                <TableCell>Action</TableCell>
                                                <TableCell>Resource</TableCell>
                                                <TableCell>Outcome</TableCell>
                                                <TableCell>Severity</TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {auditEvents.slice(0, 10).map((event, index) => (
                                                <TableRow key={index}>
                                                    <TableCell>
                                                        {new Date(event.timestamp).toLocaleString()}
                                                    </TableCell>
                                                    <TableCell>{event.event_type}</TableCell>
                                                    <TableCell>{event.action}</TableCell>
                                                    <TableCell>{event.resource_type}</TableCell>
                                                    <TableCell>
                                                        <Chip
                                                            label={event.outcome}
                                                            color={event.outcome === 'success' ? 'success' : 'error'}
                                                            size="small"
                                                        />
                                                    </TableCell>
                                                    <TableCell>
                                                        <Chip
                                                            label={event.severity}
                                                            color={
                                                                event.severity === 'high' ? 'error' :
                                                                    event.severity === 'medium' ? 'warning' : 'default'
                                                            }
                                                            size="small"
                                                        />
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </TableContainer>
                            </CardContent>
                        </Card>
                    </Grid>
                )}
            </Grid>

            {/* Data Export Dialog */}
            <Dialog open={exportDialogOpen} onClose={() => setExportDialogOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Export Your Data</DialogTitle>
                <DialogContent>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Select the data categories you want to export. Leave empty to export all data.
                    </Typography>

                    <FormControl fullWidth sx={{ mb: 2 }}>
                        <InputLabel>Data Categories</InputLabel>
                        <Select
                            multiple
                            value={selectedCategories}
                            onChange={(e) => setSelectedCategories(e.target.value as string[])}
                            renderValue={(selected) => (
                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                    {selected.map((value) => (
                                        <Chip key={value} label={value.replace('_', ' ')} size="small" />
                                    ))}
                                </Box>
                            )}
                        >
                            {dataCategories.map((category) => (
                                <MenuItem key={category.value} value={category.value}>
                                    <Checkbox checked={selectedCategories.indexOf(category.value) > -1} />
                                    <ListItemText
                                        primary={category.label}
                                        secondary={category.description}
                                    />
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    <FormControl fullWidth>
                        <InputLabel>Export Format</InputLabel>
                        <Select
                            value={exportFormat}
                            onChange={(e) => setExportFormat(e.target.value)}
                        >
                            <MenuItem value="json">JSON</MenuItem>
                            <MenuItem value="csv">CSV</MenuItem>
                        </Select>
                    </FormControl>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setExportDialogOpen(false)}>Cancel</Button>
                    <Button onClick={handleDataExport} variant="contained">
                        Export Data
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Data Deletion Dialog */}
            <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Delete Your Data</DialogTitle>
                <DialogContent>
                    <Alert severity="warning" sx={{ mb: 2 }}>
                        This action cannot be undone. Your data will be permanently deleted.
                    </Alert>

                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Select the data categories you want to delete. Leave empty to delete all eligible data.
                    </Typography>

                    <FormControl fullWidth sx={{ mb: 2 }}>
                        <InputLabel>Data Categories</InputLabel>
                        <Select
                            multiple
                            value={selectedCategories}
                            onChange={(e) => setSelectedCategories(e.target.value as string[])}
                            renderValue={(selected) => (
                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                    {selected.map((value) => (
                                        <Chip key={value} label={value.replace('_', ' ')} size="small" />
                                    ))}
                                </Box>
                            )}
                        >
                            {dataCategories.filter(cat => cat.value !== 'audit_data').map((category) => (
                                <MenuItem key={category.value} value={category.value}>
                                    <Checkbox checked={selectedCategories.indexOf(category.value) > -1} />
                                    <ListItemText
                                        primary={category.label}
                                        secondary={category.description}
                                    />
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    <TextField
                        fullWidth
                        label="Reason for Deletion"
                        multiline
                        rows={3}
                        value={deleteReason}
                        onChange={(e) => setDeleteReason(e.target.value)}
                        sx={{ mb: 2 }}
                        required
                    />

                    <FormControlLabel
                        control={
                            <Checkbox
                                checked={deleteConfirm}
                                onChange={(e) => setDeleteConfirm(e.target.checked)}
                            />
                        }
                        label="I understand that this action cannot be undone and my data will be permanently deleted."
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
                    <Button
                        onClick={handleDataDeletion}
                        variant="contained"
                        color="error"
                        disabled={!deleteConfirm || !deleteReason.trim()}
                    >
                        Delete Data
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default ComplianceDashboard;