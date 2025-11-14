'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
    TextField,
    FormControl,
    Select,
    SelectChangeEvent,
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
    Checkbox,
    FormControlLabel,
    Collapse,
    Button,
    CircularProgress,
} from '@mui/material';
import {
    Help,
    AutoAwesome,
    Lightbulb,
    TipsAndUpdates,
    Info,
    Edit,
    Add,
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
    allowTextInput?: boolean;
    textInputLabel?: string;
    textInputPlaceholder?: string;
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
    allowTextInput = false,
    textInputLabel = "Other (please specify)",
    textInputPlaceholder = "Please specify...",
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
    const [inputValue, setInputValue] = useState(() => {
        if (typeof value === 'string') return value;
        if (Array.isArray(value)) return value.join(', ');
        return String(value || '');
    });
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [textInputValue, setTextInputValue] = useState('');
    const [showTextInput, setShowTextInput] = useState(false);
    const [isLoadingAI, setIsLoadingAI] = useState(false);

    // Removed automatic loading of smart defaults - now opt-in only

    // Load contextual help
    useEffect(() => {
        if (onGetContextualHelp) {
            loadContextualHelp();
        }
    }, [name, onGetContextualHelp]);

    // Update input value when value prop changes
    useEffect(() => {
        if (typeof value === 'string') {
            setInputValue(value);
        } else if (Array.isArray(value)) {
            setInputValue(value.join(', '));
        } else {
            setInputValue(String(value || ''));
        }
    }, [value]);

    const loadSmartDefaults = useCallback(async () => {
        if (!onGetSmartDefaults) return;

        try {
            const defaults = await onGetSmartDefaults(name);
            setSmartDefaults(defaults || []);
            setShowSmartDefaults((defaults && defaults.length > 0) && !value);
        } catch (error) {
            console.error('Error loading smart defaults:', error);
            setSmartDefaults([]);
            setShowSmartDefaults(false);
        }
    }, [name, onGetSmartDefaults, value]);

    const loadSuggestions = useCallback(async (query: string) => {
        if (!onGetSuggestions) return;

        try {
            // Ensure query is a string and not empty
            const queryString = String(query || '').trim();
            if (!queryString) {
                setSuggestions([]);
                return;
            }

            const suggestions = await onGetSuggestions(name, queryString);
            setSuggestions(suggestions || []);
        } catch (error) {
            console.error('Error loading suggestions:', error);
            setSuggestions([]);
        }
    }, [name, onGetSuggestions]);

    const loadContextualHelp = useCallback(async () => {
        if (!onGetContextualHelp) return;

        try {
            const help = await onGetContextualHelp(name);
            setContextualHelp(help || null);
        } catch (error) {
            console.error('Error loading contextual help:', error);
            setContextualHelp(null);
        }
    }, [name, onGetContextualHelp]);

    const handleInputChange = (newValue: unknown) => {
        onChange(newValue);
        setShowSmartDefaults(false);

        // Update input value but don't auto-load suggestions
        if (type === 'text' || type === 'autocomplete') {
            setInputValue(newValue as string);
        }
    };

    const applySmartDefault = (defaultValue: SmartDefault) => {
        onChange(defaultValue.value);
        setShowSmartDefaults(false);
    };

    // Manual AI suggestion triggers
    const handleLoadSmartDefaults = async () => {
        setIsLoadingAI(true);
        try {
            await loadSmartDefaults();
            setShowSmartDefaults(true);
        } finally {
            setIsLoadingAI(false);
        }
    };

    const handleLoadSuggestions = async () => {
        setIsLoadingAI(true);
        try {
            // Ensure query is always a string
            let query = '';
            if (typeof value === 'string') {
                query = value;
            } else if (Array.isArray(value)) {
                query = value.join(', ');
            } else if (value !== null && value !== undefined) {
                query = String(value);
            } else {
                query = inputValue || '';
            }

            // Ensure query is a string and has content
            const queryString = String(query || '');
            if (queryString.trim()) {
                await loadSuggestions(queryString);
                setShowSuggestions(true);
            } else {
                // If no query, load smart defaults instead
                await loadSmartDefaults();
                setShowSmartDefaults(true);
            }
        } finally {
            setIsLoadingAI(false);
        }
    };

    const handleHelpClick = (event: React.MouseEvent<HTMLElement>) => {
        setHelpAnchorEl(event.currentTarget);
    };

    const handleHelpClose = () => {
        setHelpAnchorEl(null);
    };

    const renderSmartDefaults = () => {
        if (!showSmartDefaults || !smartDefaults || smartDefaults.length === 0) return null;

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
                                    label={defaultValue.value as string}
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

    const renderAISuggestions = () => {
        if (!showSuggestions || suggestions.length === 0) return null;

        const applySuggestion = (suggestion: Suggestion) => {
            onChange(suggestion.value);
            setShowSuggestions(false);
        };

        return (
            <Fade in={showSuggestions}>
                <Alert
                    severity="success"
                    icon={<AutoAwesome />}
                    sx={{ mb: 1 }}
                    action={
                        <IconButton
                            size="small"
                            onClick={() => setShowSuggestions(false)}
                            color="inherit"
                        >
                            ×
                        </IconButton>
                    }
                >
                    <Typography variant="body2" gutterBottom>
                        AI suggestions for "{inputValue || value}":
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 1 }}>
                        {suggestions.slice(0, 4).map((suggestion, index) => (
                            <Box
                                key={index}
                                sx={{
                                    p: 1,
                                    border: 1,
                                    borderColor: 'divider',
                                    borderRadius: 1,
                                    cursor: 'pointer',
                                    '&:hover': { bgcolor: 'action.hover' }
                                }}
                                onClick={() => applySuggestion(suggestion)}
                            >
                                <Typography variant="body2" fontWeight="medium">
                                    {suggestion.label}
                                </Typography>
                                {suggestion.description && (
                                    <Typography variant="caption" color="text.secondary">
                                        {suggestion.description}
                                    </Typography>
                                )}
                                <Typography variant="caption" sx={{ ml: 1 }}>
                                    ({Math.round(suggestion.confidence * 100)}% confidence)
                                </Typography>
                            </Box>
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
                    <Typography variant="h6" color="text.primary" gutterBottom>
                        {contextualHelp.title}
                    </Typography>
                    <Typography variant="body2" paragraph>
                        {contextualHelp.content}
                    </Typography>

                    {contextualHelp.examples && contextualHelp.examples.length > 0 && (
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

                    {contextualHelp.tips && contextualHelp.tips.length > 0 && (
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
            onChange: (e: React.ChangeEvent<HTMLInputElement>) => handleInputChange(e.target.value),
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
                            onChange={(e: SelectChangeEvent<unknown>) => handleInputChange(e.target.value)}
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
                const selectedValues = Array.isArray(value) ? value : [];
                
                return (
                    <Box>
                        <FormControl fullWidth error={Boolean(error)}>
                            <InputLabel>{label}</InputLabel>
                            <Select
                                multiple
                                value={selectedValues}
                                onChange={(e: SelectChangeEvent<unknown>) => {
                                    const newValues = e.target.value as string[];
                                    handleInputChange(newValues);
                                }}
                                label={label}
                                renderValue={(selected) => (
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {(selected as string[]).map((val) => {
                                            // Handle text input values
                                            if (typeof val === 'object' && val && 'text_input' in val) {
                                                return (
                                                    <Chip
                                                        key={`text_${(val as any).text_input}`}
                                                        label={`${textInputLabel}: ${(val as any).text_input}`}
                                                        size="small"
                                                        icon={<Edit />}
                                                        color="secondary"
                                                    />
                                                );
                                            }
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
                                        <Checkbox 
                                            checked={selectedValues.includes(option.value)}
                                            size="small"
                                        />
                                        {option.label}
                                    </MenuItem>
                                ))}
                                {allowTextInput && (
                                    <MenuItem key="__text_input__" value="__text_input__">
                                        <Checkbox 
                                            checked={showTextInput}
                                            onChange={(e) => setShowTextInput(e.target.checked)}
                                            size="small"
                                        />
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Edit fontSize="small" />
                                            {textInputLabel}
                                        </Box>
                                    </MenuItem>
                                )}
                            </Select>
                        </FormControl>
                        
                        {allowTextInput && showTextInput && (
                            <Collapse in={showTextInput}>
                                <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'flex-end' }}>
                                    <TextField
                                        fullWidth
                                        size="small"
                                        placeholder={textInputPlaceholder}
                                        value={textInputValue}
                                        onChange={(e) => setTextInputValue(e.target.value)}
                                        label="Custom option"
                                    />
                                    <Button
                                        variant="outlined"
                                        size="small"
                                        startIcon={<Add />}
                                        onClick={() => {
                                            if (textInputValue.trim()) {
                                                const newTextInput = { text_input: textInputValue.trim() };
                                                const newValues = [...selectedValues, newTextInput];
                                                handleInputChange(newValues);
                                                setTextInputValue('');
                                            }
                                        }}
                                        disabled={!textInputValue.trim()}
                                    >
                                        Add
                                    </Button>
                                </Box>
                            </Collapse>
                        )}
                    </Box>
                );

            case 'autocomplete':
                return (
                    <Autocomplete
                        options={suggestions}
                        getOptionLabel={(option) => {
                            if (!option) return '';
                            return typeof option === 'string' ? option : (option as Suggestion)?.label || '';
                        }}
                        renderOption={(props, option) => {
                            const { key, ...otherProps } = props;
                            const suggestion = option as Suggestion;
                            return (
                                <Box component="li" key={key} {...otherProps}>
                                    <Box>
                                        <Typography variant="body2">
                                            {suggestion?.label || ''}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">
                                            {suggestion?.description || ''}
                                        </Typography>
                                    </Box>
                                </Box>
                            );
                        }}
                        renderInput={(params) => (
                            <TextField
                                {...params}
                                label={label}
                                error={Boolean(error)}
                                helperText={error}
                                placeholder={placeholder}
                            />
                        )}
                        value={value || ''}
                        onChange={(_, newValue) => {
                            // Handle both string values (freeSolo) and object values (suggestions)
                            const finalValue = typeof newValue === 'string'
                                ? newValue
                                : (newValue as { value?: string })?.value || newValue || '';
                            handleInputChange(finalValue);
                        }}
                        inputValue={inputValue || ''}
                        onInputChange={(_, newInputValue) => {
                            const safeInputValue = newInputValue || '';
                            setInputValue(safeInputValue);
                            // Update the form value immediately when typing (for freeSolo mode)
                            handleInputChange(safeInputValue);
                            // Removed automatic suggestion loading - now manual only
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
            {renderAISuggestions()}

            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                <Box sx={{ flexGrow: 1 }}>
                    {renderField()}
                </Box>

                {/* AI Suggestion Triggers */}
                {onGetSuggestions && (
                    <Tooltip title={isLoadingAI ? "Loading AI suggestions..." : "Get AI suggestions for this field"}>
                        <span>
                            <IconButton
                                onClick={handleLoadSuggestions}
                                size="small"
                                sx={{ mt: 1 }}
                                color="primary"
                                disabled={isLoadingAI}
                            >
                                {isLoadingAI ? <CircularProgress size={20} /> : <AutoAwesome />}
                            </IconButton>
                        </span>
                    </Tooltip>
                )}

                {onGetSmartDefaults && (
                    <Tooltip title={isLoadingAI ? "Loading smart defaults..." : "Get smart default values"}>
                        <span>
                            <IconButton
                                onClick={handleLoadSmartDefaults}
                                size="small"
                                sx={{ mt: 1 }}
                                color="secondary"
                                disabled={isLoadingAI}
                            >
                                {isLoadingAI ? <CircularProgress size={20} /> : <Lightbulb />}
                            </IconButton>
                        </span>
                    </Tooltip>
                )}

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
                                invisible={!contextualHelp.tips || !contextualHelp.tips.length}
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