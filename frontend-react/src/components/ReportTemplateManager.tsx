'use client';

import React, { useState } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Button,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Chip,
    Grid,
    IconButton,
    Menu,
    List,
    ListItem,
    ListItemText,
    ListItemSecondaryAction,
    Divider,
    Switch,
    FormControlLabel,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Paper,
    Tooltip,
} from '@mui/material';
import {
    Add,
    Edit,
    Delete,
    MoreVert,
    Visibility,
    FileCopy,
    Public,
    Business,
    ExpandMore,
    DragIndicator,
    ColorLens,
    Code,
    Preview,
} from '@mui/icons-material';

interface ReportTemplate {
    id: string;
    name: string;
    description?: string;
    reportType: 'executive_summary' | 'technical_roadmap' | 'cost_analysis' | 'full_assessment';
    version: string;
    isPublic: boolean;
    usageCount: number;
    createdBy: string;
    createdAt: string;
    sectionsConfig: SectionConfig[];
    brandingConfig: BrandingConfig;
    cssTemplate?: string;
    htmlTemplate?: string;
}

interface SectionConfig {
    title: string;
    order: number;
    contentType: 'markdown' | 'html';
    isInteractive: boolean;
    generatedBy: string;
}

interface BrandingConfig {
    primaryColor?: string;
    secondaryColor?: string;
    logoUrl?: string;
    fontFamily?: string;
    headerStyle?: Record<string, unknown>;
    footerStyle?: Record<string, unknown>;
}

interface ReportTemplateManagerProps {
    templates: ReportTemplate[];
    onCreateTemplate: (template: Partial<ReportTemplate>) => void;
    onUpdateTemplate: (id: string, template: Partial<ReportTemplate>) => void;
    onDeleteTemplate: (id: string) => void;
    onDuplicateTemplate: (id: string) => void;
    onPreviewTemplate: (id: string) => void;
}

const ReportTemplateManager: React.FC<ReportTemplateManagerProps> = ({
    templates,
    onCreateTemplate,
    onUpdateTemplate,
    onDeleteTemplate,
    onDuplicateTemplate,
    onPreviewTemplate
}) => {
    const [createDialogOpen, setCreateDialogOpen] = useState(false);
    const [editDialogOpen, setEditDialogOpen] = useState(false);
    const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate | null>(null);
    const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
    const [menuTemplateId, setMenuTemplateId] = useState<string>('');

    // Form state
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        reportType: 'full_assessment' as const,
        isPublic: false,
        sectionsConfig: [] as SectionConfig[],
        brandingConfig: {} as BrandingConfig,
        cssTemplate: '',
        htmlTemplate: ''
    });

    const handleCreateTemplate = () => {
        onCreateTemplate(formData);
        setCreateDialogOpen(false);
        resetForm();
    };

    const handleUpdateTemplate = () => {
        if (selectedTemplate) {
            onUpdateTemplate(selectedTemplate.id, formData);
            setEditDialogOpen(false);
            resetForm();
        }
    };

    const resetForm = () => {
        setFormData({
            name: '',
            description: '',
            reportType: 'full_assessment',
            isPublic: false,
            sectionsConfig: [],
            brandingConfig: {},
            cssTemplate: '',
            htmlTemplate: ''
        });
        setSelectedTemplate(null);
    };

    const openEditDialog = (template: ReportTemplate) => {
        setSelectedTemplate(template);
        setFormData({
            name: template.name,
            description: template.description || '',
            reportType: template.reportType,
            isPublic: template.isPublic,
            sectionsConfig: template.sectionsConfig,
            brandingConfig: template.brandingConfig,
            cssTemplate: template.cssTemplate || '',
            htmlTemplate: template.htmlTemplate || ''
        });
        setEditDialogOpen(true);
    };

    const addSection = () => {
        const newSection: SectionConfig = {
            title: 'New Section',
            order: formData.sectionsConfig.length + 1,
            contentType: 'markdown',
            isInteractive: false,
            generatedBy: 'user'
        };
        setFormData({
            ...formData,
            sectionsConfig: [...formData.sectionsConfig, newSection]
        });
    };

    const updateSection = (index: number, section: SectionConfig) => {
        const updatedSections = [...formData.sectionsConfig];
        updatedSections[index] = section;
        setFormData({
            ...formData,
            sectionsConfig: updatedSections
        });
    };

    const removeSection = (index: number) => {
        const updatedSections = formData.sectionsConfig.filter((_, i) => i !== index);
        setFormData({
            ...formData,
            sectionsConfig: updatedSections
        });
    };

    const getReportTypeLabel = (type: string) => {
        switch (type) {
            case 'executive_summary': return 'Executive Summary';
            case 'technical_roadmap': return 'Technical Roadmap';
            case 'cost_analysis': return 'Cost Analysis';
            case 'full_assessment': return 'Full Assessment';
            default: return type;
        }
    };

    const renderTemplateCard = (template: ReportTemplate) => (
        <Card key={template.id} sx={{ height: '100%' }}>
            <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box>
                        <Typography variant="h6" color="text.primary" gutterBottom>
                            {template.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" paragraph>
                            {template.description || 'No description provided'}
                        </Typography>
                    </Box>
                    <IconButton
                        onClick={(e) => {
                            setMenuAnchor(e.currentTarget);
                            setMenuTemplateId(template.id);
                        }}
                    >
                        <MoreVert />
                    </IconButton>
                </Box>

                <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                    <Chip
                        label={getReportTypeLabel(template.reportType)}
                        size="small"
                        color="primary"
                    />
                    <Chip
                        label={`v${template.version}`}
                        size="small"
                        variant="outlined"
                    />
                    {template.isPublic && (
                        <Chip
                            icon={<Public />}
                            label="Public"
                            size="small"
                            color="info"
                        />
                    )}
                </Box>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                    {template.sectionsConfig.length} sections • Used {template.usageCount} times
                </Typography>

                <Typography variant="caption" color="text.secondary">
                    Created {new Date(template.createdAt).toLocaleDateString()}
                </Typography>

                <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                    <Button
                        size="small"
                        startIcon={<Preview />}
                        onClick={() => onPreviewTemplate(template.id)}
                    >
                        Preview
                    </Button>
                    <Button
                        size="small"
                        startIcon={<Edit />}
                        onClick={() => openEditDialog(template)}
                    >
                        Edit
                    </Button>
                </Box>
            </CardContent>
        </Card>
    );

    const renderSectionEditor = (section: SectionConfig, index: number) => (
        <Paper key={index} sx={{ p: 2, mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <DragIndicator sx={{ mr: 1, color: 'text.secondary' }} />
                <TextField
                    label="Section Title"
                    value={section.title}
                    onChange={(e) => updateSection(index, { ...section, title: e.target.value })}
                    size="small"
                    sx={{ flexGrow: 1, mr: 2 }}
                />
                <TextField
                    label="Order"
                    type="number"
                    value={section.order}
                    onChange={(e) => updateSection(index, { ...section, order: parseInt(e.target.value) })}
                    size="small"
                    sx={{ width: 80, mr: 2 }}
                />
                <IconButton onClick={() => removeSection(index)} color="error">
                    <Delete />
                </IconButton>
            </Box>

            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                <FormControl size="small" sx={{ minWidth: 120 }}>
                    <InputLabel>Content Type</InputLabel>
                    <Select
                        value={section.contentType}
                        onChange={(e) => updateSection(index, { ...section, contentType: e.target.value as 'markdown' | 'html' })}
                    >
                        <MenuItem value="markdown">Markdown</MenuItem>
                        <MenuItem value="html">HTML</MenuItem>
                    </Select>
                </FormControl>

                <FormControlLabel
                    control={
                        <Switch
                            checked={section.isInteractive}
                            onChange={(e) => updateSection(index, { ...section, isInteractive: e.target.checked })}
                        />
                    }
                    label="Interactive"
                />
            </Box>
        </Paper>
    );

    const renderBrandingEditor = () => (
        <Box>
            <Typography variant="h6" color="text.primary" gutterBottom>
                Branding Configuration
            </Typography>

            <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                    <TextField
                        fullWidth
                        label="Primary Color"
                        value={formData.brandingConfig.primaryColor || ''}
                        onChange={(e) => setFormData({
                            ...formData,
                            brandingConfig: {
                                ...formData.brandingConfig,
                                primaryColor: e.target.value
                            }
                        })}
                        placeholder="#1976d2"
                    />
                </Grid>

                <Grid item xs={12} sm={6}>
                    <TextField
                        fullWidth
                        label="Secondary Color"
                        value={formData.brandingConfig.secondaryColor || ''}
                        onChange={(e) => setFormData({
                            ...formData,
                            brandingConfig: {
                                ...formData.brandingConfig,
                                secondaryColor: e.target.value
                            }
                        })}
                        placeholder="#dc004e"
                    />
                </Grid>

                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        label="Logo URL"
                        value={formData.brandingConfig.logoUrl || ''}
                        onChange={(e) => setFormData({
                            ...formData,
                            brandingConfig: {
                                ...formData.brandingConfig,
                                logoUrl: e.target.value
                            }
                        })}
                        placeholder="https://example.com/logo.png"
                    />
                </Grid>

                <Grid item xs={12}>
                    <TextField
                        fullWidth
                        label="Font Family"
                        value={formData.brandingConfig.fontFamily || ''}
                        onChange={(e) => setFormData({
                            ...formData,
                            brandingConfig: {
                                ...formData.brandingConfig,
                                fontFamily: e.target.value
                            }
                        })}
                        placeholder="Roboto, Arial, sans-serif"
                    />
                </Grid>
            </Grid>
        </Box>
    );

    return (
        <Box>
            {/* Header */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h4" color="text.primary">Report Templates</Typography>
                <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={() => setCreateDialogOpen(true)}
                >
                    Create Template
                </Button>
            </Box>

            {/* Templates Grid */}
            <Grid container spacing={3}>
                {templates.map((template) => (
                    <Grid item xs={12} sm={6} md={4} key={template.id}>
                        {renderTemplateCard(template)}
                    </Grid>
                ))}
            </Grid>

            {/* Context Menu */}
            <Menu
                anchorEl={menuAnchor}
                open={Boolean(menuAnchor)}
                onClose={() => setMenuAnchor(null)}
            >
                <MenuItem onClick={() => {
                    onPreviewTemplate(menuTemplateId);
                    setMenuAnchor(null);
                }}>
                    <Visibility sx={{ mr: 1 }} />
                    Preview
                </MenuItem>
                <MenuItem onClick={() => {
                    const template = templates.find(t => t.id === menuTemplateId);
                    if (template) openEditDialog(template);
                    setMenuAnchor(null);
                }}>
                    <Edit sx={{ mr: 1 }} />
                    Edit
                </MenuItem>
                <MenuItem onClick={() => {
                    onDuplicateTemplate(menuTemplateId);
                    setMenuAnchor(null);
                }}>
                    <FileCopy sx={{ mr: 1 }} />
                    Duplicate
                </MenuItem>
                <Divider />
                <MenuItem onClick={() => {
                    onDeleteTemplate(menuTemplateId);
                    setMenuAnchor(null);
                }} sx={{ color: 'error.main' }}>
                    <Delete sx={{ mr: 1 }} />
                    Delete
                </MenuItem>
            </Menu>

            {/* Create Template Dialog */}
            <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="md" fullWidth>
                <DialogTitle>Create New Template</DialogTitle>
                <DialogContent>
                    <Box sx={{ pt: 1 }}>
                        <Grid container spacing={2}>
                            <Grid item xs={12} sm={6}>
                                <TextField
                                    fullWidth
                                    label="Template Name"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <FormControl fullWidth>
                                    <InputLabel>Report Type</InputLabel>
                                    <Select
                                        value={formData.reportType}
                                        onChange={(e) => setFormData({ ...formData, reportType: e.target.value as ReportTemplate['reportType'] })}
                                    >
                                        <MenuItem value="executive_summary">Executive Summary</MenuItem>
                                        <MenuItem value="technical_roadmap">Technical Roadmap</MenuItem>
                                        <MenuItem value="cost_analysis">Cost Analysis</MenuItem>
                                        <MenuItem value="full_assessment">Full Assessment</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>
                            <Grid item xs={12}>
                                <TextField
                                    fullWidth
                                    label="Description"
                                    multiline
                                    rows={2}
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                />
                            </Grid>
                            <Grid item xs={12}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={formData.isPublic}
                                            onChange={(e) => setFormData({ ...formData, isPublic: e.target.checked })}
                                        />
                                    }
                                    label="Make template public"
                                />
                            </Grid>
                        </Grid>

                        <Divider sx={{ my: 3 }} />

                        {/* Sections Configuration */}
                        <Box sx={{ mb: 3 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                                <Typography variant="h6" color="text.primary">Sections</Typography>
                                <Button startIcon={<Add />} onClick={addSection}>
                                    Add Section
                                </Button>
                            </Box>
                            {formData.sectionsConfig.map((section, index) => renderSectionEditor(section, index))}
                        </Box>

                        <Divider sx={{ my: 3 }} />

                        {/* Branding Configuration */}
                        <Accordion>
                            <AccordionSummary expandIcon={<ExpandMore />}>
                                <ColorLens sx={{ mr: 1 }} />
                                <Typography>Branding & Styling</Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                {renderBrandingEditor()}
                            </AccordionDetails>
                        </Accordion>

                        {/* Custom CSS */}
                        <Accordion>
                            <AccordionSummary expandIcon={<ExpandMore />}>
                                <Code sx={{ mr: 1 }} />
                                <Typography>Custom CSS</Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                <TextField
                                    fullWidth
                                    multiline
                                    rows={6}
                                    label="Custom CSS"
                                    value={formData.cssTemplate}
                                    onChange={(e) => setFormData({ ...formData, cssTemplate: e.target.value })}
                                    placeholder="/* Custom CSS styles */"
                                />
                            </AccordionDetails>
                        </Accordion>
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
                    <Button onClick={handleCreateTemplate} variant="contained">
                        Create Template
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Edit Template Dialog */}
            <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
                <DialogTitle>Edit Template</DialogTitle>
                <DialogContent>
                    {/* Same content as create dialog */}
                    <Box sx={{ pt: 1 }}>
                        <Grid container spacing={2}>
                            <Grid item xs={12} sm={6}>
                                <TextField
                                    fullWidth
                                    label="Template Name"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <FormControl fullWidth>
                                    <InputLabel>Report Type</InputLabel>
                                    <Select
                                        value={formData.reportType}
                                        onChange={(e) => setFormData({ ...formData, reportType: e.target.value as ReportTemplate['reportType'] })}
                                    >
                                        <MenuItem value="executive_summary">Executive Summary</MenuItem>
                                        <MenuItem value="technical_roadmap">Technical Roadmap</MenuItem>
                                        <MenuItem value="cost_analysis">Cost Analysis</MenuItem>
                                        <MenuItem value="full_assessment">Full Assessment</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>
                            <Grid item xs={12}>
                                <TextField
                                    fullWidth
                                    label="Description"
                                    multiline
                                    rows={2}
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                />
                            </Grid>
                            <Grid item xs={12}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={formData.isPublic}
                                            onChange={(e) => setFormData({ ...formData, isPublic: e.target.checked })}
                                        />
                                    }
                                    label="Make template public"
                                />
                            </Grid>
                        </Grid>

                        <Divider sx={{ my: 3 }} />

                        {/* Sections Configuration */}
                        <Box sx={{ mb: 3 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                                <Typography variant="h6" color="text.primary">Sections</Typography>
                                <Button startIcon={<Add />} onClick={addSection}>
                                    Add Section
                                </Button>
                            </Box>
                            {formData.sectionsConfig.map((section, index) => renderSectionEditor(section, index))}
                        </Box>

                        <Divider sx={{ my: 3 }} />

                        {/* Branding Configuration */}
                        <Accordion>
                            <AccordionSummary expandIcon={<ExpandMore />}>
                                <ColorLens sx={{ mr: 1 }} />
                                <Typography>Branding & Styling</Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                {renderBrandingEditor()}
                            </AccordionDetails>
                        </Accordion>

                        {/* Custom CSS */}
                        <Accordion>
                            <AccordionSummary expandIcon={<ExpandMore />}>
                                <Code sx={{ mr: 1 }} />
                                <Typography>Custom CSS</Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                <TextField
                                    fullWidth
                                    multiline
                                    rows={6}
                                    label="Custom CSS"
                                    value={formData.cssTemplate}
                                    onChange={(e) => setFormData({ ...formData, cssTemplate: e.target.value })}
                                    placeholder="/* Custom CSS styles */"
                                />
                            </AccordionDetails>
                        </Accordion>
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
                    <Button onClick={handleUpdateTemplate} variant="contained">
                        Update Template
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default ReportTemplateManager;