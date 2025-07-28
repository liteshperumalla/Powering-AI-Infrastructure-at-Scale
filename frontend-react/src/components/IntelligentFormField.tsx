'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
    TextField,
    FormControl,
    Select,
    MenuItem,
    InputLabel,
    Autocomplete,
    Chip,
    Box,
    Typography,
    IconButton,
    Tooltip,
    Popover,
    Paper,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    Badge,
    Fade,
    Alert,
} from '@mui/material';
import {
    Help,
    AutoAwesome,
    Lightbulb,
    TipsAndUpdates,
    Info,
} from '@mui/icons-material';

interface SmartDefault {
    value: unknown;
    confidence: number;
    reason: string;
    source: string;
}

interface Suggestion {
    value: string;
    label: string;
    description: string;
    confidence: number;
    category?: string;
}

interface ContextualHelp {
    title: string;
    content: string;
    examples: string[];
    tips: string[];
    related_fields: string[];
    help_type: string;
}

interface IntelligentFormFieldProps {
    name: string;
    label: string;
    type: 'text' | 'select' | 'multiselect' | 'autocomplete';
    value: unknown;
    onChange: (value: unknown) => void;
    options?: Array<{ value: string; label: string }>;
    required?: boolean;
    error?: string;
    placeholder?: string;
    multiline?: boolean;
    rows?: number;
    formContext?: Record<string, unknown>;
    onGetSmartDefaults?: (fieldName: string) => Promise<SmartDefault[]>;
    onGetSuggestions?: (fieldName: string, query: string) => Promise<Suggestion[]>;
    onGetContextualHelp?: (fieldName: string) => Promise<ContextualHelp | null>;
}

export default function IntelligentFormField({
    name,
    label,
    type,
    value,
    onChange,
    options = [],
    required = false,
    error,
    placeholder,
    multiline = false,
    rows = 1,
    formContext = {},
    onGetSmartDefaults,
    onGetSuggestions,
    onGetContextualHelp,
}: IntelligentFormFieldProps) {
    const [smartDefaults, setSmartDefaults] = useState<SmartDefault[]>([]);
    const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
    const [contextualHelp, setContextualHelp] = useState<ContextualHelp | null>(null);
    const [showSmartDefaults, setShowSmartDefaults] = useState(false);
    const [helpAnchorEl, setHelpAnchorEl] = useState<HTMLElement | null>(null);
    const [inputValue, setInputValue] = useState('');
    const [showSuggestions, setShowSuggestions] = useState(false);

    // Load smart defaults when form context changes
    useEffect(() => {
        if (onGetSmartDefaults && !value) {
            loadSmartDefaults();
        }
    }, [formContext, name, onGetSmartDefaults, value]);

    // Load contextual help
    useEffect(() => {
        if (onGetContextualHelp) {
            loadContextualHelp();
        }
    }, [name, onGetContextualHelp]);

    const loadSmartDefaults = useCallback(async () => {
        if (!onGetSmartDefaults) return;

        try {
            const defaults = await onGetSmartDefaults(name);
            setSmartDefaults(defaults);
            setShowSmartDefaults(defaults.length > 0 && !value);
        } catch (error) {
            console.error('Error loading smart defaults:', error);
        }
    }, [name, onGetSmartDefaults, value]);

    const loadSuggestions = useCallback(async (query: string) => {
        if (!onGetSuggestions) return;

        try {
            const suggestions = await onGetSuggestions(name, query);
            setSuggestions(suggestions);
        } catch (error) {
            console.error('Error loading suggestions:', error);
        }
    }, [name, onGetSuggestions]);

    const loadContextualHelp = useCallback(async () => {
        if (!onGetContextualHelp) return;

        try {
            const help = await onGetContextualHelp(name);
            setContextualHelp(help);
        } catch (error) {
            console.error('Error loading contextual help:', error);
        }
    }, [name, onGetContextualHelp]);

    const handleInputChange = (newValue: unknown) => {
        onChange(newValue);
        setShowSmartDefaults(false);

        // Load suggestions for text inputs
        if (type === 'text' || type === 'autocomplete') {
            setInputValue(newValue);
            if (newValue && newValue.length > 1) {
                loadSuggestions(newValue);
                setShowSuggestions(true);
            } else {
                setShowSuggestions(false);
            }
        }
    };

    const applySmartDefault = (defaultValue: SmartDefault) => {
        onChange(defaultValue.value);
        setShowSmartDefaults(false);
    };

    const handleHelpClick = (event: React.MouseEvent<HTMLElement>) => {
        setHelpAnchorEl(event.currentTarget);
    };

    const handleHelpClose = () => {
        setHelpAnchorEl(null);
    };

    const renderSmartDefaults = () => {
        if (!showSmartDefaults || smartDefaults.length === 0) return null;

        return (
            <Fade in={showSmartDefaults}>
                <Alert
                    severity="info"
                    icon={<AutoAwesome />}
                    sx={{ mb: 1 }}
                    action={
                        <IconButton
                            size="small"
                            onClick={() => setShowSmartDefaults(false)}
                        >
                            ×
                        </IconButton>
                    }
                >
                    <Typography variant="body2" sx={{ mb: 1 }}>
                        Smart suggestions based on your profile:
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {smartDefaults.map((defaultValue, index) => (
                            <Tooltip
                                key={index}
                                title={`${defaultValue.reason} (${Math.round(defaultValue.confidence * 100)}% confidence)`}
                            >
                                <Chip
                                    label={defaultValue.value}
                                    onClick={() => applySmartDefault(defaultValue)}
                                    color="primary"
                                    variant="outlined"
                                    size="small"
                                    icon={<Lightbulb />}
                                    sx={{ cursor: 'pointer' }}
                                />
                            </Tooltip>
                        ))}
                    </Box>
                </Alert>
            </Fade>
        );
    };

    const renderContextualHelp = () => {
        if (!contextualHelp) return null;

        return (
            <Popover
                open={Boolean(helpAnchorEl)}
                anchorEl={helpAnchorEl}
                onClose={handleHelpClose}
                anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'left',
                }}
                transformOrigin={{
                    vertical: 'top',
                    horizontal: 'left',
                }}
            >
                <Paper sx={{ p: 2, maxWidth: 400 }}>
                    <Typography variant="h6" gutterBottom>
                        {contextualHelp.title}
                    </Typography>
                    <Typography variant="body2" paragraph>
                        {contextualHelp.content}
                    </Typography>

                    {contextualHelp.examples.length > 0 && (
                        <>
                            <Typography variant="subtitle2" gutterBottom>
                                Examples:
                            </Typography>
                            <List dense>
                                {contextualHelp.examples.map((example, index) => (
                                    <ListItem key={index}>
                                        <ListItemIcon>
                                            <Info fontSize="small" />
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={example}
                                            primaryTypographyProps={{ variant: 'body2' }}
                                        />
                                    </ListItem>
                                ))}
                            </List>
                        </>
                    )}

                    {contextualHelp.tips.length > 0 && (
                        <>
                            <Typography variant="subtitle2" gutterBottom>
                                Tips:
                            </Typography>
                            <List dense>
                                {contextualHelp.tips.map((tip, index) => (
                                    <ListItem key={index}>
                                        <ListItemIcon>
                                            <TipsAndUpdates fontSize="small" />
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={tip}
                                            primaryTypographyProps={{ variant: 'body2' }}
                                        />
                                    </ListItem>
                                ))}
                            </List>
                        </>
                    )}
                </Paper>
            </Popover>
        );
    };

    const renderField = () => {
        const fieldProps = {
            fullWidth: true,
            label,
            value: value || '',
            onChange: (e: any) => handleInputChange(e.target.value),
            error: Boolean(error),
            helperText: error,
            required,
            placeholder,
        };

        switch (type) {
            case 'text':
                return (
                    <TextField
                        {...fieldProps}
                        multiline={multiline}
                        rows={rows}
                    />
                );

            case 'select':
                return (
                    <FormControl fullWidth error={Boolean(error)}>
                        <InputLabel>{label}</InputLabel>
                        <Select
                            value={value || ''}
                            onChange={(e) => handleInputChange(e.target.value)}
                            label={label}
                        >
                            {options.map((option) => (
                                <MenuItem key={option.value} value={option.value}>
                                    {option.label}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                );

            case 'multiselect':
                return (
                    <FormControl fullWidth error={Boolean(error)}>
                        <InputLabel>{label}</InputLabel>
                        <Select
                            multiple
                            value={value || []}
                            onChange={(e) => handleInputChange(e.target.value)}
                            label={label}
                            renderValue={(selected) => (
                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                    {(selected as string[]).map((val) => {
                                        const option = options.find(opt => opt.value === val);
                                        return (
                                            <Chip
                                                key={val}
                                                label={option?.label || val}
                                                size="small"
                                            />
                                        );
                                    })}
                                </Box>
                            )}
                        >
                            {options.map((option) => (
                                <MenuItem key={option.value} value={option.value}>
                                    {option.label}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                );

            case 'autocomplete':
                return (
                    <Autocomplete
                        options={suggestions}
                        getOptionLabel={(option) => typeof option === 'string' ? option : option.label}
                        renderOption={(props, option) => (
                            <Box component="li" {...props}>
                                <Box>
                                    <Typography variant="body2">
                                        {option.label}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        {option.description}
                                    </Typography>
                                </Box>
                            </Box>
                        )}
                        renderInput={(params) => (
                            <TextField
                                {...params}
                                label={label}
                                error={Boolean(error)}
                                helperText={error}
                                placeholder={placeholder}
                            />
                        )}
                        value={value || null}
                        onChange={(_, newValue) => handleInputChange((newValue as { value?: string })?.value || newValue)}
                        inputValue={inputValue}
                        onInputChange={(_, newInputValue) => {
                            setInputValue(newInputValue);
                            if (newInputValue && newInputValue.length > 1) {
                                loadSuggestions(newInputValue);
                            }
                        }}
                        freeSolo
                    />
                );

            default:
                return <TextField {...fieldProps} />;
        }
    };

    return (
        <Box sx={{ mb: 2 }}>
            {renderSmartDefaults()}

            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                <Box sx={{ flexGrow: 1 }}>
                    {renderField()}
                </Box>

                {contextualHelp && (
                    <Tooltip title="Get help with this field">
                        <IconButton
                            onClick={handleHelpClick}
                            size="small"
                            sx={{ mt: 1 }}
                        >
                            <Badge
                                color="primary"
                                variant="dot"
                                invisible={!contextualHelp.tips.length}
                            >
                                <Help />
                            </Badge>
                        </IconButton>
                    </Tooltip>
                )}
            </Box>

            {renderContextualHelp()}
        </Box>
    );
}