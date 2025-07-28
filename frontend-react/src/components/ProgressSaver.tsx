'use client';

import React, { useState, useEffect } from 'react';
import {
    Box,
    Button,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    List,
    ListItem,
    ListItemText,
    ListItemSecondaryAction,
    IconButton,
    Typography,
    Chip,
    Alert,
    LinearProgress,
    Snackbar,
    Fade,
} from '@mui/material';
import {
    Save,
    Restore,
    Delete,
    CheckCircle,
} from '@mui/icons-material';

interface SavedForm {
    form_id: string;
    current_step: number;
    saved_at: string;
    completion_percentage: number;
    metadata: Record<string, unknown>;
}

interface ProgressSaverProps {
    formId: string;
    currentStep: number;
    formData: Record<string, unknown>;
    totalSteps: number;
    onSave?: (formId: string, formData: Record<string, unknown>, currentStep: number) => Promise<boolean>;
    onLoad?: (formId: string) => Promise<Record<string, unknown> | null>;
    onDelete?: (formId: string) => Promise<boolean>;
    onListSaved?: () => Promise<SavedForm[]>;
    autoSaveInterval?: number; // in milliseconds
}

export default function ProgressSaver({
    formId,
    currentStep,
    formData,
    totalSteps,
    onSave,
    onLoad,
    onDelete,
    onListSaved,
    autoSaveInterval = 30000, // 30 seconds
}: ProgressSaverProps) {
    const [savedForms, setSavedForms] = useState<SavedForm[]>([]);
    const [showSavedForms, setShowSavedForms] = useState(false);
    const [saving, setSaving] = useState(false);
    const [loading, setLoading] = useState(false);
    const [lastSaved, setLastSaved] = useState<Date | null>(null);
    const [autoSaveEnabled, setAutoSaveEnabled] = useState(true);
    const [snackbarOpen, setSnackbarOpen] = useState(false);
    const [snackbarMessage, setSnackbarMessage] = useState('');
    const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'info'>('info');

    // Auto-save functionality
    useEffect(() => {
        if (!autoSaveEnabled || !onSave) return;

        const interval = setInterval(() => {
            handleAutoSave();
        }, autoSaveInterval);

        return () => clearInterval(interval);
    }, [formData, currentStep, autoSaveEnabled, autoSaveInterval, onSave]);

    // Load saved forms on mount
    useEffect(() => {
        if (onListSaved) {
            loadSavedForms();
        }
    }, [onListSaved]);

    const handleAutoSave = async () => {
        if (!onSave || saving) return;

        // Only auto-save if there's meaningful progress
        const hasData = Object.values(formData).some(value =>
            value !== null && value !== undefined && value !== ''
        );

        if (!hasData) return;

        try {
            setSaving(true);
            const success = await onSave(formId, formData, currentStep);
            if (success) {
                setLastSaved(new Date());
            }
        } catch (error) {
            console.error('Auto-save failed:', error);
        } finally {
            setSaving(false);
        }
    };

    const handleManualSave = async () => {
        if (!onSave || saving) return;

        try {
            setSaving(true);
            const success = await onSave(formId, formData, currentStep);
            if (success) {
                setLastSaved(new Date());
                showSnackbar('Progress saved successfully', 'success');
            } else {
                showSnackbar('Failed to save progress', 'error');
            }
        } catch (error) {
            console.error('Manual save failed:', error);
            showSnackbar('Failed to save progress', 'error');
        } finally {
            setSaving(false);
        }
    };

    const loadSavedForms = async () => {
        if (!onListSaved) return;

        try {
            const forms = await onListSaved();
            setSavedForms(forms);
        } catch (error) {
            console.error('Failed to load saved forms:', error);
        }
    };

    const handleLoadForm = async (savedFormId: string) => {
        if (!onLoad || loading) return;

        try {
            setLoading(true);
            const formData = await onLoad(savedFormId);
            if (formData) {
                showSnackbar('Progress restored successfully', 'success');
                setShowSavedForms(false);
                // The parent component should handle the actual form data update
            } else {
                showSnackbar('Failed to restore progress', 'error');
            }
        } catch (error) {
            console.error('Failed to load form:', error);
            showSnackbar('Failed to restore progress', 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteForm = async (savedFormId: string) => {
        if (!onDelete) return;

        try {
            const success = await onDelete(savedFormId);
            if (success) {
                setSavedForms(forms => forms.filter(form => form.form_id !== savedFormId));
                showSnackbar('Saved progress deleted', 'info');
            } else {
                showSnackbar('Failed to delete saved progress', 'error');
            }
        } catch (error) {
            console.error('Failed to delete form:', error);
            showSnackbar('Failed to delete saved progress', 'error');
        }
    };

    const showSnackbar = (message: string, severity: 'success' | 'error' | 'info') => {
        setSnackbarMessage(message);
        setSnackbarSeverity(severity);
        setSnackbarOpen(true);
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleString();
    };

    const getStepName = (stepIndex: number) => {
        const stepNames = [
            'Business Information',
            'Current Infrastructure',
            'AI Requirements',
            'Compliance & Security',
            'Review & Submit'
        ];
        return stepNames[stepIndex] || `Step ${stepIndex + 1}`;
    };

    // const currentCompletion = Math.round((currentStep / totalSteps) * 100);

    return (
        <Box>
            {/* Auto-save indicator */}
            <Fade in={saving}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <LinearProgress size={16} />
                    <Typography variant="caption" color="text.secondary">
                        Saving progress...
                    </Typography>
                </Box>
            </Fade>

            {/* Last saved indicator */}
            {lastSaved && !saving && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <CheckCircle color="success" fontSize="small" />
                    <Typography variant="caption" color="text.secondary">
                        Last saved: {lastSaved.toLocaleTimeString()}
                    </Typography>
                </Box>
            )}

            {/* Save and restore buttons */}
            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <Button
                    variant="outlined"
                    startIcon={<Save />}
                    onClick={handleManualSave}
                    disabled={saving}
                    size="small"
                >
                    Save Progress
                </Button>

                {savedForms.length > 0 && (
                    <Button
                        variant="outlined"
                        startIcon={<Restore />}
                        onClick={() => setShowSavedForms(true)}
                        size="small"
                    >
                        Restore Progress
                    </Button>
                )}
            </Box>

            {/* Auto-save toggle */}
            <Alert
                severity="info"
                sx={{ mb: 2 }}
                action={
                    <Button
                        color="inherit"
                        size="small"
                        onClick={() => setAutoSaveEnabled(!autoSaveEnabled)}
                    >
                        {autoSaveEnabled ? 'Disable' : 'Enable'}
                    </Button>
                }
            >
                Auto-save is {autoSaveEnabled ? 'enabled' : 'disabled'}.
                Your progress is automatically saved every {autoSaveInterval / 1000} seconds.
            </Alert>

            {/* Saved forms dialog */}
            <Dialog
                open={showSavedForms}
                onClose={() => setShowSavedForms(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>
                    Restore Saved Progress
                </DialogTitle>
                <DialogContent>
                    {savedForms.length === 0 ? (
                        <Typography color="text.secondary">
                            No saved progress found.
                        </Typography>
                    ) : (
                        <List>
                            {savedForms.map((form) => (
                                <ListItem key={form.form_id} divider>
                                    <ListItemText
                                        primary={
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Typography variant="subtitle1">
                                                    {getStepName(form.current_step)}
                                                </Typography>
                                                <Chip
                                                    label={`${form.completion_percentage}% complete`}
                                                    size="small"
                                                    color={form.completion_percentage > 50 ? 'primary' : 'default'}
                                                />
                                            </Box>
                                        }
                                        secondary={
                                            <Box>
                                                <Typography variant="body2" color="text.secondary">
                                                    Saved: {formatDate(form.saved_at)}
                                                </Typography>
                                                <LinearProgress
                                                    variant="determinate"
                                                    value={form.completion_percentage}
                                                    sx={{ mt: 1, height: 4, borderRadius: 2 }}
                                                />
                                            </Box>
                                        }
                                    />
                                    <ListItemSecondaryAction>
                                        <Box sx={{ display: 'flex', gap: 1 }}>
                                            <Button
                                                variant="contained"
                                                size="small"
                                                onClick={() => handleLoadForm(form.form_id)}
                                                disabled={loading}
                                            >
                                                Restore
                                            </Button>
                                            <IconButton
                                                edge="end"
                                                onClick={() => handleDeleteForm(form.form_id)}
                                                size="small"
                                            >
                                                <Delete />
                                            </IconButton>
                                        </Box>
                                    </ListItemSecondaryAction>
                                </ListItem>
                            ))}
                        </List>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setShowSavedForms(false)}>
                        Cancel
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Snackbar for notifications */}
            <Snackbar
                open={snackbarOpen}
                autoHideDuration={4000}
                onClose={() => setSnackbarOpen(false)}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
            >
                <Alert
                    onClose={() => setSnackbarOpen(false)}
                    severity={snackbarSeverity}
                    sx={{ width: '100%' }}
                >
                    {snackbarMessage}
                </Alert>
            </Snackbar>
        </Box>
    );
}