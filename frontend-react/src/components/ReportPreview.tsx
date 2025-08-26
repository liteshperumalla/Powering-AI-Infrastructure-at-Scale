'use client';

import React, { useState } from 'react';
import {
    Card,
    CardContent,
    Typography,
    Box,
    Divider,
    Chip,
    Button,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    Menu,
    MenuItem,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    FormControl,
    InputLabel,
    Select,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    IconButton,
    Tooltip,
} from '@mui/material';
import {
    GetApp,
    Visibility,
    TrendingUp,
    Security,
    CloudQueue,
    Assessment,
    Share,
    MoreVert,
    History,
    Edit,
    FileCopy,
    ExpandMore,
    Compare,
    Public,
    People,
} from '@mui/icons-material';

interface ReportSection {
    title: string;
    content: string;
    type: 'executive' | 'technical' | 'financial' | 'compliance';
}

interface ReportVersion {
    id: string;
    version: string;
    createdDate: string;
    status: 'draft' | 'final' | 'in-progress';
    isCurrent: boolean;
}

export interface ReportData {
    id: string;
    title: string;
    generatedDate?: string;
    status: 'draft' | 'final' | 'in-progress' | 'completed';
    sections: ReportSection[] | string[];  // Can be either objects or strings
    keyFindings?: string[];
    recommendations?: string[];
    estimatedSavings?: number;
    complianceScore?: number;
    version?: string;
    versions?: ReportVersion[];
    sharedWith?: string[];
    isPublic?: boolean;
    canEdit?: boolean;
    canShare?: boolean;
    hasInteractiveContent?: boolean;
}

interface ReportPreviewProps {
    report: ReportData;
    onDownload?: (reportId: string) => void;
    onView?: (reportId: string) => void;
    onShare?: (reportId: string) => void;
    onCreateVersion?: (reportId: string) => void;
    onCompareVersions?: (reportId1: string, reportId2: string) => void;
    onCreateTemplate?: (reportId: string) => void;
    onEdit?: (reportId: string) => void;
}

const getSectionIcon = (type: string) => {
    switch (type) {
        case 'executive': return <TrendingUp />;
        case 'technical': return <CloudQueue />;
        case 'financial': return <Assessment />;
        case 'compliance': return <Security />;
        default: return <Visibility />;
    }
};

const getStatusColor = (status: string) => {
    switch (status) {
        case 'final': return 'success';
        case 'draft': return 'warning';
        case 'in-progress': return 'info';
        default: return 'default';
    }
};

const ReportPreview: React.FC<ReportPreviewProps> = ({
    report,
    onDownload,
    onView,
    onShare,
    onCreateVersion,
    onCompareVersions,
    onCreateTemplate,
    onEdit
}) => {
    // Component initialization - removed excessive debug logging
    
    const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
    const [shareDialogOpen, setShareDialogOpen] = useState(false);
    const [versionDialogOpen, setVersionDialogOpen] = useState(false);
    const [compareDialogOpen, setCompareDialogOpen] = useState(false);
    const [selectedVersionForCompare, setSelectedVersionForCompare] = useState<string>('');
    const [newVersionName, setNewVersionName] = useState('');
    const [shareEmail, setShareEmail] = useState('');
    const [sharePermission, setSharePermission] = useState('view');
    
    // Debug logging
    // Report validation - removed excessive debug logging
    
    // Guard clause to handle undefined report
    if (!report) {
        console.log('❌ Report is null/undefined, showing fallback');
        return (
            <Card>
                <CardContent>
                    <Typography variant="h6" color="text.secondary">
                        No report data available
                    </Typography>
                </CardContent>
            </Card>
        );
    }

    // Ensure all required properties exist with defaults
    const safeReport = {
        // First spread the report to get all properties
        ...report,
        // Then override with safe defaults to ensure arrays are always defined
        id: report.id || '',
        title: report.title || 'Unknown Report',
        status: report.status || 'draft',
        generatedDate: report.generatedDate || new Date().toISOString(),
        sections: Array.isArray(report.sections) ? report.sections : [],
        keyFindings: Array.isArray(report.keyFindings) ? report.keyFindings : [],
        recommendations: Array.isArray(report.recommendations) ? report.recommendations : [],
        estimatedSavings: report.estimatedSavings || 0,
        complianceScore: report.complianceScore || 0,
        versions: Array.isArray(report.versions) ? report.versions : [],
        sharedWith: Array.isArray(report.sharedWith) ? report.sharedWith : [],
        isPublic: report.isPublic || false,
        canEdit: report.canEdit !== false,
        canShare: report.canShare !== false,
        hasInteractiveContent: report.hasInteractiveContent || false
    };
    
    // Debug the safe report
    // SafeReport created - removed excessive debug logging
    
    return (
        <Card>
            <CardContent>
                {/* Header */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box>
                        <Typography variant="h6" gutterBottom>
                            {safeReport.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Generated: {safeReport.generatedDate ? new Date(safeReport.generatedDate).toLocaleDateString() : 'Unknown'}
                        </Typography>
                    </Box>
                    <Chip
                        label={safeReport.status.toUpperCase()}
                        color={getStatusColor(safeReport.status) as 'success' | 'warning' | 'info' | 'default'}
                        size="small"
                    />
                </Box>

                <Divider sx={{ my: 2 }} />

                {/* Key Metrics */}
                {(safeReport.estimatedSavings || safeReport.complianceScore) && (
                    <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                        {safeReport.estimatedSavings && (
                            <Card variant="outlined" sx={{ flex: 1 }}>
                                <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                                    <Typography variant="body2" color="text.secondary">
                                        Estimated Savings
                                    </Typography>
                                    <Typography variant="h6" color="success.main">
                                        ${safeReport.estimatedSavings.toLocaleString()}
                                    </Typography>
                                </CardContent>
                            </Card>
                        )}
                        {safeReport.complianceScore && (
                            <Card variant="outlined" sx={{ flex: 1 }}>
                                <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                                    <Typography variant="body2" color="text.secondary">
                                        Compliance Score
                                    </Typography>
                                    <Typography variant="h6" color="primary.main">
                                        {safeReport.complianceScore}%
                                    </Typography>
                                </CardContent>
                            </Card>
                        )}
                    </Box>
                )}

                {/* Report Sections */}
                <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                        Report Sections
                    </Typography>
                    <List dense>
                        {(safeReport.sections || []).map((section, index) => {
                            // Handle both string arrays and section objects
                            const sectionData = typeof section === 'string' 
                                ? { title: section.replace('_', ' ').toUpperCase(), content: '', type: section }
                                : section;
                            
                            return (
                                <ListItem key={index} sx={{ pl: 0 }}>
                                    <ListItemIcon sx={{ minWidth: 36 }}>
                                        {getSectionIcon(sectionData.type || 'executive')}
                                    </ListItemIcon>
                                    <ListItemText
                                        primary={sectionData.title}
                                        secondary={sectionData.content ? sectionData.content.substring(0, 100) + '...' : 'Report section available'}
                                    />
                                </ListItem>
                            );
                        })}
                    </List>
                </Box>

                {/* Key Findings */}
                {safeReport.keyFindings && Array.isArray(safeReport.keyFindings) && safeReport.keyFindings.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                            Key Findings
                        </Typography>
                        <List dense>
                            {(safeReport.keyFindings || []).slice(0, 3).map((finding, index) => (
                                <ListItem key={index} sx={{ pl: 0 }}>
                                    <ListItemText
                                        primary={
                                            <Typography variant="body2">
                                                {finding}
                                            </Typography>
                                        }
                                    />
                                </ListItem>
                            ))}
                        </List>
                    </Box>
                )}

                {/* Top Recommendations */}
                {safeReport.recommendations && Array.isArray(safeReport.recommendations) && safeReport.recommendations.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                            Top Recommendations
                        </Typography>
                        <List dense>
                            {(safeReport.recommendations || []).slice(0, 3).map((rec, index) => (
                                <ListItem key={index} sx={{ pl: 0 }}>
                                    <ListItemText
                                        primary={
                                            <Typography variant="body2">
                                                {rec}
                                            </Typography>
                                        }
                                    />
                                </ListItem>
                            ))}
                        </List>
                    </Box>
                )}

                <Divider sx={{ my: 2 }} />

                {/* Version History */}
                {safeReport.versions && Array.isArray(safeReport.versions) && safeReport.versions.length > 1 && (
                    <Box sx={{ mb: 2 }}>
                        <Accordion>
                            <AccordionSummary expandIcon={<ExpandMore />}>
                                <Typography variant="subtitle2">
                                    Version History ({(safeReport.versions || []).length} versions)
                                </Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                <List dense>
                                    {(safeReport.versions || []).map((version) => (
                                        <ListItem key={version.id} sx={{ pl: 0 }}>
                                            <ListItemText
                                                primary={
                                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                        <Typography variant="body2">
                                                            Version {version.version}
                                                        </Typography>
                                                        {version.isCurrent && (
                                                            <Chip label="Current" size="small" color="primary" />
                                                        )}
                                                    </Box>
                                                }
                                                secondary={new Date(version.createdDate).toLocaleDateString()}
                                            />
                                            <Button
                                                size="small"
                                                onClick={() => {
                                                    setSelectedVersionForCompare(version.id);
                                                    setCompareDialogOpen(true);
                                                }}
                                            >
                                                Compare
                                            </Button>
                                        </ListItem>
                                    ))}
                                </List>
                            </AccordionDetails>
                        </Accordion>
                    </Box>
                )}

                {/* Sharing Info */}
                {(safeReport.sharedWith && Array.isArray(safeReport.sharedWith) && safeReport.sharedWith.length > 0) || safeReport.isPublic && (
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                            Sharing
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                            {safeReport.isPublic && (
                                <Chip
                                    icon={<Public />}
                                    label="Public"
                                    size="small"
                                    color="info"
                                />
                            )}
                            {safeReport.sharedWith && Array.isArray(safeReport.sharedWith) && safeReport.sharedWith.length > 0 && (
                                <Chip
                                    icon={<People />}
                                    label={`Shared with ${safeReport.sharedWith.length} users`}
                                    size="small"
                                    color="secondary"
                                />
                            )}
                        </Box>
                    </Box>
                )}

                {/* Interactive Content Indicator */}
                {safeReport.hasInteractiveContent && (
                    <Box sx={{ mb: 2 }}>
                        <Chip
                            label="Interactive Content Available"
                            size="small"
                            color="success"
                            variant="outlined"
                        />
                    </Box>
                )}

                <Divider sx={{ my: 2 }} />

                {/* Actions */}
                <Box sx={{ display: 'flex', gap: 1, justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button
                            variant="outlined"
                            startIcon={<Visibility />}
                            onClick={() => onView?.(safeReport.id)}
                        >
                            {safeReport.hasInteractiveContent ? 'Interactive View' : 'View Report'}
                        </Button>
                        <Button
                            variant="contained"
                            startIcon={<GetApp />}
                            onClick={() => onDownload?.(safeReport.id)}
                        >
                            Download
                        </Button>
                    </Box>

                    <Box>
                        {safeReport.canShare && (
                            <Tooltip title="Share Report">
                                <IconButton
                                    onClick={() => setShareDialogOpen(true)}
                                    color="primary"
                                >
                                    <Share />
                                </IconButton>
                            </Tooltip>
                        )}

                        <Tooltip title="More Actions">
                            <IconButton
                                onClick={(e) => setMenuAnchor(e.currentTarget)}
                            >
                                <MoreVert />
                            </IconButton>
                        </Tooltip>

                        <Menu
                            anchorEl={menuAnchor}
                            open={Boolean(menuAnchor)}
                            onClose={() => setMenuAnchor(null)}
                        >
                            {safeReport.canEdit && (
                                <MenuItem onClick={() => {
                                    setMenuAnchor(null);
                                    onEdit?.(safeReport.id);
                                }}>
                                    <Edit sx={{ mr: 1 }} />
                                    Edit Report
                                </MenuItem>
                            )}

                            <MenuItem onClick={() => {
                                setMenuAnchor(null);
                                setVersionDialogOpen(true);
                            }}>
                                <History sx={{ mr: 1 }} />
                                Create Version
                            </MenuItem>

                            {safeReport.versions && Array.isArray(safeReport.versions) && safeReport.versions.length > 1 && (
                                <MenuItem onClick={() => {
                                    setMenuAnchor(null);
                                    setCompareDialogOpen(true);
                                }}>
                                    <Compare sx={{ mr: 1 }} />
                                    Compare Versions
                                </MenuItem>
                            )}

                            <MenuItem onClick={() => {
                                setMenuAnchor(null);
                                onCreateTemplate?.(safeReport.id);
                            }}>
                                <FileCopy sx={{ mr: 1 }} />
                                Create Template
                            </MenuItem>
                        </Menu>
                    </Box>
                </Box>

                {/* Share Dialog */}
                <Dialog open={shareDialogOpen} onClose={() => setShareDialogOpen(false)}>
                    <DialogTitle>Share Report</DialogTitle>
                    <DialogContent>
                        <TextField
                            fullWidth
                            label="Email Address"
                            value={shareEmail}
                            onChange={(e) => setShareEmail(e.target.value)}
                            margin="normal"
                        />
                        <FormControl fullWidth margin="normal">
                            <InputLabel>Permission</InputLabel>
                            <Select
                                value={sharePermission}
                                onChange={(e) => setSharePermission(e.target.value)}
                            >
                                <MenuItem value="view">View Only</MenuItem>
                                <MenuItem value="edit">Edit</MenuItem>
                                <MenuItem value="admin">Admin</MenuItem>
                            </Select>
                        </FormControl>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setShareDialogOpen(false)}>Cancel</Button>
                        <Button
                            onClick={() => {
                                onShare?.(safeReport.id);
                                setShareDialogOpen(false);
                                setShareEmail('');
                            }}
                            variant="contained"
                        >
                            Share
                        </Button>
                    </DialogActions>
                </Dialog>

                {/* Version Dialog */}
                <Dialog open={versionDialogOpen} onClose={() => setVersionDialogOpen(false)}>
                    <DialogTitle>Create New Version</DialogTitle>
                    <DialogContent>
                        <TextField
                            fullWidth
                            label="Version Name"
                            value={newVersionName}
                            onChange={(e) => setNewVersionName(e.target.value)}
                            margin="normal"
                            placeholder="e.g., 2.0, Draft-2024-01"
                        />
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setVersionDialogOpen(false)}>Cancel</Button>
                        <Button
                            onClick={() => {
                                onCreateVersion?.(safeReport.id);
                                setVersionDialogOpen(false);
                                setNewVersionName('');
                            }}
                            variant="contained"
                        >
                            Create Version
                        </Button>
                    </DialogActions>
                </Dialog>

                {/* Compare Dialog */}
                <Dialog open={compareDialogOpen} onClose={() => setCompareDialogOpen(false)}>
                    <DialogTitle>Compare Versions</DialogTitle>
                    <DialogContent>
                        <FormControl fullWidth margin="normal">
                            <InputLabel>Compare with Version</InputLabel>
                            <Select
                                value={selectedVersionForCompare}
                                onChange={(e) => setSelectedVersionForCompare(e.target.value)}
                            >
                                {(safeReport.versions || []).map((version) => (
                                    <MenuItem key={version.id} value={version.id}>
                                        Version {version.version} ({new Date(version.createdDate).toLocaleDateString()})
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setCompareDialogOpen(false)}>Cancel</Button>
                        <Button
                            onClick={() => {
                                onCompareVersions?.(safeReport.id, selectedVersionForCompare);
                                setCompareDialogOpen(false);
                            }}
                            variant="contained"
                            disabled={!selectedVersionForCompare}
                        >
                            Compare
                        </Button>
                    </DialogActions>
                </Dialog>
            </CardContent>
        </Card>
    );
};

export default ReportPreview;