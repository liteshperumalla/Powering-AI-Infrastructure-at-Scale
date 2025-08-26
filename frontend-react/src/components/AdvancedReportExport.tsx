'use client';

import React, { useState } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Box,
    Typography,
    FormControl,
    FormGroup,
    FormControlLabel,
    Checkbox,
    RadioGroup,
    Radio,
    TextField,
    Chip,
    LinearProgress,
    Alert,
    Switch,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    IconButton,
    Tooltip,
} from '@mui/material';
import {
    GetApp,
    Share,
    PictureAsPdf,
    Code,
    TableChart,
    Description,
    ExpandMore,
    ContentCopy,
    Email,
    Link,
    Schedule,
    Security,
    Visibility,
    VisibilityOff,
} from '@mui/icons-material';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { exportReport, shareReport, setExportProgress, clearShareUrl } from '@/store/slices/reportSlice';
import { addNotification, closeModal } from '@/store/slices/uiSlice';

interface AdvancedReportExportProps {
    open: boolean;
    onClose: () => void;
    reportId: string;
}

export default function AdvancedReportExport({ open, onClose, reportId }: AdvancedReportExportProps) {
    const dispatch = useAppDispatch();
    const { currentReport, exportProgress, shareUrl, loading } = useAppSelector(state => state.report);

    const [exportOptions, setExportOptions] = useState({
        formats: ['pdf'] as string[],
        sections: ['executive', 'technical', 'financial', 'compliance'] as string[],
        includeCharts: true,
        includeRawData: false,
        includeAppendices: true,
        customBranding: false,
        watermark: false,
    });

    const [shareOptions, setShareOptions] = useState({
        isPublic: false,
        requireAuth: true,
        allowDownload: true,
        allowComments: false,
        expiresIn: '30' as string,
        notifyEmails: [] as string[],
        customMessage: '',
    });

    const [emailInput, setEmailInput] = useState('');
    const [activeTab, setActiveTab] = useState<'export' | 'share'>('export');

    const formatOptions = [
        { value: 'pdf', label: 'PDF Document', icon: <PictureAsPdf />, description: 'Professional PDF report' },
        { value: 'json', label: 'JSON Data', icon: <Code />, description: 'Structured data format' },
        { value: 'csv', label: 'CSV Export', icon: <TableChart />, description: 'Spreadsheet compatible' },
        { value: 'markdown', label: 'Markdown', icon: <Description />, description: 'Text-based format' },
    ];

    const sectionOptions = [
        { value: 'executive', label: 'Executive Summary', description: 'High-level overview and recommendations' },
        { value: 'technical', label: 'Technical Details', description: 'Implementation specifications' },
        { value: 'financial', label: 'Financial Analysis', description: 'Cost projections and ROI' },
        { value: 'compliance', label: 'Compliance Assessment', description: 'Regulatory requirements' },
    ];

    const handleFormatChange = (format: string) => {
        setExportOptions(prev => ({
            ...prev,
            formats: prev.formats.includes(format)
                ? prev.formats.filter(f => f !== format)
                : [...prev.formats, format]
        }));
    };

    const handleSectionChange = (section: string) => {
        setExportOptions(prev => ({
            ...prev,
            sections: prev.sections.includes(section)
                ? prev.sections.filter(s => s !== section)
                : [...prev.sections, section]
        }));
    };

    const handleExport = async () => {
        if (!exportOptions.formats.length) {
            dispatch(addNotification({
                type: 'warning',
                message: 'Please select at least one export format',
            }));
            return;
        }

        try {
            for (const format of exportOptions.formats) {
                await dispatch(exportReport({ reportId, format })).unwrap();
            }

            dispatch(addNotification({
                type: 'success',
                message: `Report exported successfully in ${exportOptions.formats.length} format(s)`,
            }));
        } catch (error) {
            dispatch(addNotification({
                type: 'error',
                message: 'Failed to export report',
            }));
        }
    };

    const handleShare = async () => {
        try {
            const settings = {
                isPublic: shareOptions.isPublic,
                sharedWith: shareOptions.notifyEmails,
                expiresAt: shareOptions.expiresIn !== 'never'
                    ? new Date(Date.now() + parseInt(shareOptions.expiresIn) * 24 * 60 * 60 * 1000).toISOString()
                    : undefined,
                requireAuth: shareOptions.requireAuth,
                allowDownload: shareOptions.allowDownload,
                allowComments: shareOptions.allowComments,
                customMessage: shareOptions.customMessage,
            };

            await dispatch(shareReport({ reportId, settings })).unwrap();

            dispatch(addNotification({
                type: 'success',
                message: 'Report shared successfully',
            }));
        } catch (error) {
            dispatch(addNotification({
                type: 'error',
                message: 'Failed to share report',
            }));
        }
    };

    const handleAddEmail = () => {
        if (emailInput && !shareOptions.notifyEmails.includes(emailInput)) {
            setShareOptions(prev => ({
                ...prev,
                notifyEmails: [...prev.notifyEmails, emailInput]
            }));
            setEmailInput('');
        }
    };

    const handleRemoveEmail = (email: string) => {
        setShareOptions(prev => ({
            ...prev,
            notifyEmails: prev.notifyEmails.filter(e => e !== email)
        }));
    };

    const handleCopyShareUrl = () => {
        if (shareUrl) {
            navigator.clipboard.writeText(shareUrl);
            dispatch(addNotification({
                type: 'success',
                message: 'Share URL copied to clipboard',
            }));
        }
    };

    const handleClose = () => {
        dispatch(clearShareUrl());
        onClose();
    };

    return (
        <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
            <DialogTitle>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <GetApp />
                    Export & Share Report
                </Box>
            </DialogTitle>

            <DialogContent>
                <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
                    <Box sx={{ display: 'flex', gap: 2 }}>
                        <Button
                            variant={activeTab === 'export' ? 'contained' : 'text'}
                            onClick={() => setActiveTab('export')}
                            startIcon={<GetApp />}
                        >
                            Export
                        </Button>
                        <Button
                            variant={activeTab === 'share' ? 'contained' : 'text'}
                            onClick={() => setActiveTab('share')}
                            startIcon={<Share />}
                        >
                            Share
                        </Button>
                    </Box>
                </Box>

                {activeTab === 'export' && (
                    <Box>
                        {/* Export Formats */}
                        <Accordion defaultExpanded>
                            <AccordionSummary expandIcon={<ExpandMore />}>
                                <Typography variant="h6">Export Formats</Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                <FormGroup>
                                    {formatOptions.map(format => (
                                        <FormControlLabel
                                            key={format.value}
                                            control={
                                                <Checkbox
                                                    checked={exportOptions.formats.includes(format.value)}
                                                    onChange={() => handleFormatChange(format.value)}
                                                />
                                            }
                                            label={
                                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                    {format.icon}
                                                    <Box>
                                                        <Typography variant="body2">{format.label}</Typography>
                                                        <Typography variant="caption" color="text.secondary">
                                                            {format.description}
                                                        </Typography>
                                                    </Box>
                                                </Box>
                                            }
                                        />
                                    ))}
                                </FormGroup>
                            </AccordionDetails>
                        </Accordion>

                        {/* Report Sections */}
                        <Accordion>
                            <AccordionSummary expandIcon={<ExpandMore />}>
                                <Typography variant="h6">Report Sections</Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                <FormGroup>
                                    {sectionOptions.map(section => (
                                        <FormControlLabel
                                            key={section.value}
                                            control={
                                                <Checkbox
                                                    checked={exportOptions.sections.includes(section.value)}
                                                    onChange={() => handleSectionChange(section.value)}
                                                />
                                            }
                                            label={
                                                <Box>
                                                    <Typography variant="body2">{section.label}</Typography>
                                                    <Typography variant="caption" color="text.secondary">
                                                        {section.description}
                                                    </Typography>
                                                </Box>
                                            }
                                        />
                                    ))}
                                </FormGroup>
                            </AccordionDetails>
                        </Accordion>

                        {/* Additional Options */}
                        <Accordion>
                            <AccordionSummary expandIcon={<ExpandMore />}>
                                <Typography variant="h6">Additional Options</Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                <FormGroup>
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={exportOptions.includeCharts}
                                                onChange={(e) => setExportOptions(prev => ({
                                                    ...prev,
                                                    includeCharts: e.target.checked
                                                }))}
                                            />
                                        }
                                        label="Include Charts and Visualizations"
                                    />
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={exportOptions.includeRawData}
                                                onChange={(e) => setExportOptions(prev => ({
                                                    ...prev,
                                                    includeRawData: e.target.checked
                                                }))}
                                            />
                                        }
                                        label="Include Raw Data Tables"
                                    />
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={exportOptions.includeAppendices}
                                                onChange={(e) => setExportOptions(prev => ({
                                                    ...prev,
                                                    includeAppendices: e.target.checked
                                                }))}
                                            />
                                        }
                                        label="Include Appendices"
                                    />
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={exportOptions.customBranding}
                                                onChange={(e) => setExportOptions(prev => ({
                                                    ...prev,
                                                    customBranding: e.target.checked
                                                }))}
                                            />
                                        }
                                        label="Apply Custom Branding"
                                    />
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={exportOptions.watermark}
                                                onChange={(e) => setExportOptions(prev => ({
                                                    ...prev,
                                                    watermark: e.target.checked
                                                }))}
                                            />
                                        }
                                        label="Add Watermark"
                                    />
                                </FormGroup>
                            </AccordionDetails>
                        </Accordion>

                        {exportProgress > 0 && exportProgress < 100 && (
                            <Box sx={{ mt: 2 }}>
                                <Typography variant="body2" gutterBottom>
                                    Exporting... {exportProgress}%
                                </Typography>
                                <LinearProgress variant="determinate" value={exportProgress} />
                            </Box>
                        )}
                    </Box>
                )}

                {activeTab === 'share' && (
                    <Box>
                        {/* Share Settings */}
                        <Accordion defaultExpanded>
                            <AccordionSummary expandIcon={<ExpandMore />}>
                                <Typography variant="h6">Share Settings</Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                <FormGroup>
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={shareOptions.isPublic}
                                                onChange={(e) => setShareOptions(prev => ({
                                                    ...prev,
                                                    isPublic: e.target.checked
                                                }))}
                                            />
                                        }
                                        label={
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                {shareOptions.isPublic ? <Visibility /> : <VisibilityOff />}
                                                Public Access
                                            </Box>
                                        }
                                    />
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={shareOptions.requireAuth}
                                                onChange={(e) => setShareOptions(prev => ({
                                                    ...prev,
                                                    requireAuth: e.target.checked
                                                }))}
                                            />
                                        }
                                        label={
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Security />
                                                Require Authentication
                                            </Box>
                                        }
                                    />
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={shareOptions.allowDownload}
                                                onChange={(e) => setShareOptions(prev => ({
                                                    ...prev,
                                                    allowDownload: e.target.checked
                                                }))}
                                            />
                                        }
                                        label="Allow Download"
                                    />
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={shareOptions.allowComments}
                                                onChange={(e) => setShareOptions(prev => ({
                                                    ...prev,
                                                    allowComments: e.target.checked
                                                }))}
                                            />
                                        }
                                        label="Allow Comments"
                                    />
                                </FormGroup>
                            </AccordionDetails>
                        </Accordion>

                        {/* Expiration */}
                        <Accordion>
                            <AccordionSummary expandIcon={<ExpandMore />}>
                                <Typography variant="h6">
                                    <Schedule sx={{ mr: 1 }} />
                                    Expiration
                                </Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                <FormControl component="fieldset">
                                    <RadioGroup
                                        value={shareOptions.expiresIn}
                                        onChange={(e) => setShareOptions(prev => ({
                                            ...prev,
                                            expiresIn: e.target.value
                                        }))}
                                    >
                                        <FormControlLabel value="1" control={<Radio />} label="1 day" />
                                        <FormControlLabel value="7" control={<Radio />} label="1 week" />
                                        <FormControlLabel value="30" control={<Radio />} label="1 month" />
                                        <FormControlLabel value="90" control={<Radio />} label="3 months" />
                                        <FormControlLabel value="never" control={<Radio />} label="Never expires" />
                                    </RadioGroup>
                                </FormControl>
                            </AccordionDetails>
                        </Accordion>

                        {/* Notify Recipients */}
                        <Accordion>
                            <AccordionSummary expandIcon={<ExpandMore />}>
                                <Typography variant="h6">
                                    <Email sx={{ mr: 1 }} />
                                    Notify Recipients
                                </Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                                <Box sx={{ mb: 2 }}>
                                    <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                                        <TextField
                                            size="small"
                                            placeholder="Enter email address"
                                            value={emailInput}
                                            onChange={(e) => setEmailInput(e.target.value)}
                                            onKeyPress={(e) => e.key === 'Enter' && handleAddEmail()}
                                            fullWidth
                                        />
                                        <Button onClick={handleAddEmail} variant="outlined">
                                            Add
                                        </Button>
                                    </Box>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                        {shareOptions.notifyEmails.map(email => (
                                            <Chip
                                                key={email}
                                                label={email}
                                                onDelete={() => handleRemoveEmail(email)}
                                                size="small"
                                            />
                                        ))}
                                    </Box>
                                </Box>
                                <TextField
                                    fullWidth
                                    multiline
                                    rows={3}
                                    placeholder="Custom message (optional)"
                                    value={shareOptions.customMessage}
                                    onChange={(e) => setShareOptions(prev => ({
                                        ...prev,
                                        customMessage: e.target.value
                                    }))}
                                />
                            </AccordionDetails>
                        </Accordion>

                        {shareUrl && (
                            <Alert
                                severity="success"
                                sx={{ mt: 2 }}
                                action={
                                    <Tooltip title="Copy URL">
                                        <IconButton onClick={handleCopyShareUrl} size="small">
                                            <ContentCopy />
                                        </IconButton>
                                    </Tooltip>
                                }
                            >
                                <Typography variant="body2">
                                    Share URL: <Link href={shareUrl} target="_blank">{shareUrl}</Link>
                                </Typography>
                            </Alert>
                        )}
                    </Box>
                )}
            </DialogContent>

            <DialogActions>
                <Button onClick={handleClose}>Cancel</Button>
                {activeTab === 'export' ? (
                    <Button
                        onClick={handleExport}
                        variant="contained"
                        disabled={loading || !exportOptions.formats.length}
                        startIcon={<GetApp />}
                    >
                        Export Report
                    </Button>
                ) : (
                    <Button
                        onClick={handleShare}
                        variant="contained"
                        disabled={loading}
                        startIcon={<Share />}
                    >
                        Share Report
                    </Button>
                )}
            </DialogActions>
        </Dialog>
    );
}