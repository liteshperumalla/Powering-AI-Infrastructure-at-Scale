'use client';

import React, { useState } from 'react';
import {
    Container,
    Paper,
    Typography,
    Box,
    Button,
    TextField,
    FormControl,
    FormLabel,
    RadioGroup,
    FormControlLabel,
    Radio,
    Checkbox,
    FormGroup,
    Select,
    MenuItem,
    InputLabel,
    Chip,
    LinearProgress,
    Alert,
    AppBar,
    Toolbar,
    IconButton,
} from '@mui/material';
import {
    ArrowBack,
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import ProgressIndicator from '@/components/ProgressIndicator';
import IntelligentFormField from '@/components/IntelligentFormField';
import ProgressSaver from '@/components/ProgressSaver';

const steps = [
    'Business Information',
    'Current Infrastructure',
    'AI Requirements',
    'Compliance & Security',
    'Review & Submit',
];

interface AssessmentFormData extends Record<string, unknown> {
    // Business Information
    companyName: string;
    industry: string;
    companySize: string;
    currentAIMaturity: string;

    // Current Infrastructure
    currentCloudProvider: string[];
    currentServices: string[];
    monthlyBudget: string;
    technicalTeamSize: string;

    // AI Requirements
    aiUseCases: string[];
    expectedDataVolume: string;
    performanceRequirements: string;
    scalingTimeline: string;

    // Compliance & Security
    complianceRequirements: string[];
    dataLocation: string;
    securityLevel: string;
    auditRequirements: string;
}

const initialFormData: AssessmentFormData = {
    companyName: '',
    industry: '',
    companySize: '',
    currentAIMaturity: '',
    currentCloudProvider: [],
    currentServices: [],
    monthlyBudget: '',
    technicalTeamSize: '',
    aiUseCases: [],
    expectedDataVolume: '',
    performanceRequirements: '',
    scalingTimeline: '',
    complianceRequirements: [],
    dataLocation: '',
    securityLevel: '',
    auditRequirements: '',
};

export default function AssessmentPage() {
    const router = useRouter();
    const [activeStep, setActiveStep] = useState(0);
    const [formData, setFormData] = useState<AssessmentFormData>(initialFormData);
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [formId] = useState(() => `assessment_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

    const handleNext = () => {
        if (validateStep(activeStep)) {
            setActiveStep((prevActiveStep) => prevActiveStep + 1);
        }
    };

    const handleBack = () => {
        setActiveStep((prevActiveStep) => prevActiveStep - 1);
    };

    const handleInputChange = (field: keyof AssessmentFormData, value: string | string[]) => {
        setFormData(prev => ({
            ...prev,
            [field]: value,
        }));
        // Clear error when user starts typing
        if (errors[field]) {
            setErrors(prev => ({
                ...prev,
                [field]: '',
            }));
        }
    };

    const handleArrayChange = (field: keyof AssessmentFormData, value: string, checked: boolean) => {
        const currentArray = formData[field] as string[];
        if (checked) {
            handleInputChange(field, [...currentArray, value]);
        } else {
            handleInputChange(field, currentArray.filter(item => item !== value));
        }
    };

    const validateStep = (step: number): boolean => {
        const newErrors: Record<string, string> = {};

        switch (step) {
            case 0: // Business Information
                if (!formData.companyName) newErrors.companyName = 'Company name is required';
                if (!formData.industry) newErrors.industry = 'Industry is required';
                if (!formData.companySize) newErrors.companySize = 'Company size is required';
                if (!formData.currentAIMaturity) newErrors.currentAIMaturity = 'AI maturity level is required';
                break;
            case 1: // Current Infrastructure
                if (formData.currentCloudProvider.length === 0) newErrors.currentCloudProvider = 'Select at least one cloud provider';
                if (!formData.monthlyBudget) newErrors.monthlyBudget = 'Monthly budget is required';
                break;
            case 2: // AI Requirements
                if (formData.aiUseCases.length === 0) newErrors.aiUseCases = 'Select at least one AI use case';
                if (!formData.expectedDataVolume) newErrors.expectedDataVolume = 'Expected data volume is required';
                break;
            case 3: // Compliance & Security
                if (!formData.securityLevel) newErrors.securityLevel = 'Security level is required';
                if (!formData.dataLocation) newErrors.dataLocation = 'Data location preference is required';
                break;
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async () => {
        if (validateStep(activeStep)) {
            // TODO: Submit form data to backend
            console.log('Submitting form data:', formData);

            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000));

            // Redirect to results or dashboard
            router.push('/dashboard');
        }
    };

    // Intelligent form service functions
    const getSmartDefaults = async (fieldName: string) => {
        // Mock implementation - in real app, this would call the backend API
        const mockDefaults = {
            industry: [
                { value: 'technology', confidence: 0.8, reason: 'Common choice for new assessments', source: 'usage_patterns' }
            ],
            companySize: [
                { value: 'small', confidence: 0.7, reason: 'Most common company size', source: 'industry_patterns' }
            ],
            monthlyBudget: [
                { value: '10k-50k', confidence: 0.6, reason: 'Typical for small companies', source: 'size_patterns' }
            ]
        };

        return mockDefaults[fieldName as keyof typeof mockDefaults] || [];
    };

    const getSuggestions = async (fieldName: string, query: string) => {
        // Mock implementation - in real app, this would call the backend API
        const mockSuggestions = {
            companyName: [
                { value: 'TechCorp Inc', label: 'TechCorp Inc', description: 'Technology company', confidence: 0.8 },
                { value: 'InnovateLabs', label: 'InnovateLabs', description: 'Innovation laboratory', confidence: 0.7 }
            ]
        };

        const suggestions = mockSuggestions[fieldName as keyof typeof mockSuggestions] || [];
        return suggestions.filter(s =>
            s.value.toLowerCase().includes(query.toLowerCase()) ||
            s.label.toLowerCase().includes(query.toLowerCase())
        );
    };

    const getContextualHelp = async (fieldName: string) => {
        // Mock implementation - in real app, this would call the backend API
        const mockHelp = {
            companySize: {
                title: 'Company Size',
                content: 'Select the size category that best matches your organization.',
                examples: [
                    'Startup: 1-50 employees, early stage',
                    'Small: 51-200 employees, established',
                    'Medium: 201-1000 employees, multiple departments'
                ],
                tips: [
                    'Consider total employee count, not just technical team',
                    'This affects budget recommendations and complexity levels'
                ],
                related_fields: ['monthlyBudget', 'technicalTeamSize'],
                help_type: 'tooltip'
            },
            industry: {
                title: 'Industry',
                content: 'Select the industry that best describes your business.',
                examples: [
                    'Technology: Software, hardware, IT services',
                    'Healthcare: Medical, pharmaceutical, health services',
                    'Finance: Banking, insurance, fintech'
                ],
                tips: [
                    'This affects compliance requirements and service recommendations',
                    'Choose the primary industry if you operate in multiple sectors'
                ],
                related_fields: ['complianceRequirements'],
                help_type: 'tooltip'
            }
        };

        return mockHelp[fieldName as keyof typeof mockHelp] || null;
    };

    // Progress saving functions
    const saveProgress = async (formId: string, formData: Record<string, unknown>, currentStep: number) => {
        try {
            // Mock implementation - in real app, this would call the backend API
            localStorage.setItem(`form_${formId}`, JSON.stringify({
                formData,
                currentStep,
                savedAt: new Date().toISOString()
            }));
            return true;
        } catch (error) {
            console.error('Failed to save progress:', error);
            return false;
        }
    };

    const loadProgress = async (formId: string) => {
        try {
            // Mock implementation - in real app, this would call the backend API
            const saved = localStorage.getItem(`form_${formId}`);
            if (saved) {
                const data = JSON.parse(saved);
                setFormData(data.formData);
                setActiveStep(data.currentStep);
                return data.formData;
            }
            return null;
        } catch (error) {
            console.error('Failed to load progress:', error);
            return null;
        }
    };

    const deleteProgress = async (formId: string) => {
        try {
            localStorage.removeItem(`form_${formId}`);
            return true;
        } catch (error) {
            console.error('Failed to delete progress:', error);
            return false;
        }
    };

    const listSavedForms = async () => {
        try {
            const saved = [];
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key?.startsWith('form_')) {
                    const data = JSON.parse(localStorage.getItem(key) || '{}');
                    saved.push({
                        form_id: key.replace('form_', ''),
                        current_step: data.currentStep || 0,
                        saved_at: data.savedAt || new Date().toISOString(),
                        completion_percentage: Math.round((data.currentStep || 0) / steps.length * 100),
                        metadata: {}
                    });
                }
            }
            return saved;
        } catch (error) {
            console.error('Failed to list saved forms:', error);
            return [];
        }
    };

    const getStepContent = (step: number) => {
        switch (step) {
            case 0:
                return (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Tell us about your business
                        </Typography>

                        <IntelligentFormField
                            name="companyName"
                            label="Company Name"
                            type="autocomplete"
                            value={formData.companyName}
                            onChange={(value) => handleInputChange('companyName', value as string)}
                            required
                            error={errors.companyName}
                            placeholder="Enter your company name"
                            formContext={formData}
                            onGetSmartDefaults={getSmartDefaults}
                            onGetSuggestions={getSuggestions}
                            onGetContextualHelp={getContextualHelp}
                        />

                        <IntelligentFormField
                            name="industry"
                            label="Industry"
                            type="select"
                            value={formData.industry}
                            onChange={(value) => handleInputChange('industry', value as string)}
                            required
                            error={errors.industry}
                            options={[
                                { value: 'technology', label: 'Technology' },
                                { value: 'healthcare', label: 'Healthcare' },
                                { value: 'finance', label: 'Finance' },
                                { value: 'retail', label: 'Retail' },
                                { value: 'manufacturing', label: 'Manufacturing' },
                                { value: 'other', label: 'Other' }
                            ]}
                            formContext={formData}
                            onGetSmartDefaults={getSmartDefaults}
                            onGetSuggestions={getSuggestions}
                            onGetContextualHelp={getContextualHelp}
                        />

                        <FormControl error={!!errors.companySize}>
                            <FormLabel>Company Size</FormLabel>
                            <RadioGroup
                                value={formData.companySize}
                                onChange={(e) => handleInputChange('companySize', e.target.value)}
                            >
                                <FormControlLabel value="startup" control={<Radio />} label="Startup (1-50 employees)" />
                                <FormControlLabel value="small" control={<Radio />} label="Small (51-200 employees)" />
                                <FormControlLabel value="medium" control={<Radio />} label="Medium (201-1000 employees)" />
                                <FormControlLabel value="large" control={<Radio />} label="Large (1000+ employees)" />
                            </RadioGroup>
                        </FormControl>

                        <FormControl error={!!errors.currentAIMaturity}>
                            <FormLabel>Current AI Maturity Level</FormLabel>
                            <RadioGroup
                                value={formData.currentAIMaturity}
                                onChange={(e) => handleInputChange('currentAIMaturity', e.target.value)}
                            >
                                <FormControlLabel value="none" control={<Radio />} label="No AI implementation" />
                                <FormControlLabel value="pilot" control={<Radio />} label="Pilot projects" />
                                <FormControlLabel value="production" control={<Radio />} label="Production AI systems" />
                                <FormControlLabel value="advanced" control={<Radio />} label="Advanced AI operations" />
                            </RadioGroup>
                        </FormControl>
                    </Box>
                );

            case 1:
                return (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Current Infrastructure Setup
                        </Typography>

                        <FormControl error={!!errors.currentCloudProvider}>
                            <FormLabel>Current Cloud Providers (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['AWS', 'Azure', 'Google Cloud', 'On-premises', 'Other'].map((provider) => (
                                    <FormControlLabel
                                        key={provider}
                                        control={
                                            <Checkbox
                                                checked={formData.currentCloudProvider.includes(provider)}
                                                onChange={(e) => handleArrayChange('currentCloudProvider', provider, e.target.checked)}
                                            />
                                        }
                                        label={provider}
                                    />
                                ))}
                            </FormGroup>
                        </FormControl>

                        <FormControl fullWidth>
                            <FormLabel>Current Services (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['Compute (VMs/Containers)', 'Storage', 'Databases', 'ML/AI Services', 'Analytics', 'Networking'].map((service) => (
                                    <FormControlLabel
                                        key={service}
                                        control={
                                            <Checkbox
                                                checked={formData.currentServices.includes(service)}
                                                onChange={(e) => handleArrayChange('currentServices', service, e.target.checked)}
                                            />
                                        }
                                        label={service}
                                    />
                                ))}
                            </FormGroup>
                        </FormControl>

                        <FormControl fullWidth error={!!errors.monthlyBudget}>
                            <InputLabel>Monthly Cloud Budget</InputLabel>
                            <Select
                                value={formData.monthlyBudget}
                                onChange={(e) => handleInputChange('monthlyBudget', e.target.value)}
                                label="Monthly Cloud Budget"
                            >
                                <MenuItem value="under-1k">Under $1,000</MenuItem>
                                <MenuItem value="1k-5k">$1,000 - $5,000</MenuItem>
                                <MenuItem value="5k-25k">$5,000 - $25,000</MenuItem>
                                <MenuItem value="25k-100k">$25,000 - $100,000</MenuItem>
                                <MenuItem value="over-100k">Over $100,000</MenuItem>
                            </Select>
                        </FormControl>

                        <TextField
                            fullWidth
                            label="Technical Team Size"
                            type="number"
                            value={formData.technicalTeamSize}
                            onChange={(e) => handleInputChange('technicalTeamSize', e.target.value)}
                        />
                    </Box>
                );

            case 2:
                return (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            AI Requirements & Use Cases
                        </Typography>

                        <FormControl error={!!errors.aiUseCases}>
                            <FormLabel>AI Use Cases (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['Machine Learning Models', 'Natural Language Processing', 'Computer Vision', 'Predictive Analytics', 'Recommendation Systems', 'Chatbots/Virtual Assistants'].map((useCase) => (
                                    <FormControlLabel
                                        key={useCase}
                                        control={
                                            <Checkbox
                                                checked={formData.aiUseCases.includes(useCase)}
                                                onChange={(e) => handleArrayChange('aiUseCases', useCase, e.target.checked)}
                                            />
                                        }
                                        label={useCase}
                                    />
                                ))}
                            </FormGroup>
                        </FormControl>

                        <FormControl fullWidth error={!!errors.expectedDataVolume}>
                            <InputLabel>Expected Data Volume</InputLabel>
                            <Select
                                value={formData.expectedDataVolume}
                                onChange={(e) => handleInputChange('expectedDataVolume', e.target.value)}
                                label="Expected Data Volume"
                            >
                                <MenuItem value="small">{`Small (< 1TB)`}</MenuItem>
                                <MenuItem value="medium">Medium (1TB - 100TB)</MenuItem>
                                <MenuItem value="large">Large (100TB - 1PB)</MenuItem>
                                <MenuItem value="very-large">{`Very Large (> 1PB)`}</MenuItem>
                            </Select>
                        </FormControl>


                        <FormControl>
                            <FormLabel>Performance Requirements</FormLabel>
                            <RadioGroup
                                value={formData.performanceRequirements}
                                onChange={(e) => handleInputChange('performanceRequirements', e.target.value)}
                            >
                                <FormControlLabel value="standard" control={<Radio />} label="Standard performance" />
                                <FormControlLabel value="high" control={<Radio />} label="High performance" />
                                <FormControlLabel value="real-time" control={<Radio />} label="Real-time processing" />
                            </RadioGroup>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Scaling Timeline</InputLabel>
                            <Select
                                value={formData.scalingTimeline}
                                onChange={(e) => handleInputChange('scalingTimeline', e.target.value)}
                                label="Scaling Timeline"
                            >
                                <MenuItem value="immediate">Immediate (0-3 months)</MenuItem>
                                <MenuItem value="short">Short term (3-6 months)</MenuItem>
                                <MenuItem value="medium">Medium term (6-12 months)</MenuItem>
                                <MenuItem value="long">Long term (12+ months)</MenuItem>
                            </Select>
                        </FormControl>
                    </Box>
                );

            case 3:
                return (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Compliance & Security Requirements
                        </Typography>

                        <FormControl>
                            <FormLabel>Compliance Requirements (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['GDPR', 'HIPAA', 'SOC 2', 'ISO 27001', 'PCI DSS', 'CCPA'].map((compliance) => (
                                    <FormControlLabel
                                        key={compliance}
                                        control={
                                            <Checkbox
                                                checked={formData.complianceRequirements.includes(compliance)}
                                                onChange={(e) => handleArrayChange('complianceRequirements', compliance, e.target.checked)}
                                            />
                                        }
                                        label={compliance}
                                    />
                                ))}
                            </FormGroup>
                        </FormControl>

                        <FormControl error={!!errors.dataLocation}>
                            <FormLabel>Data Location Preference</FormLabel>
                            <RadioGroup
                                value={formData.dataLocation}
                                onChange={(e) => handleInputChange('dataLocation', e.target.value)}
                            >
                                <FormControlLabel value="us" control={<Radio />} label="United States" />
                                <FormControlLabel value="eu" control={<Radio />} label="European Union" />
                                <FormControlLabel value="asia" control={<Radio />} label="Asia Pacific" />
                                <FormControlLabel value="multi" control={<Radio />} label="Multi-region" />
                            </RadioGroup>
                        </FormControl>

                        <FormControl error={!!errors.securityLevel}>
                            <FormLabel>Required Security Level</FormLabel>
                            <RadioGroup
                                value={formData.securityLevel}
                                onChange={(e) => handleInputChange('securityLevel', e.target.value)}
                            >
                                <FormControlLabel value="standard" control={<Radio />} label="Standard security" />
                                <FormControlLabel value="enhanced" control={<Radio />} label="Enhanced security" />
                                <FormControlLabel value="enterprise" control={<Radio />} label="Enterprise security" />
                            </RadioGroup>
                        </FormControl>

                        <TextField
                            fullWidth
                            label="Audit Requirements"
                            multiline
                            rows={3}
                            value={formData.auditRequirements}
                            onChange={(e) => handleInputChange('auditRequirements', e.target.value)}
                            placeholder="Describe any specific audit or reporting requirements..."
                        />
                    </Box>
                );

            case 4:
                return (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Review Your Information
                        </Typography>

                        <Alert severity="info">
                            Please review your information before submitting. Our AI agents will analyze your requirements and generate personalized recommendations.
                        </Alert>

                        <Paper sx={{ p: 2 }}>
                            <Typography variant="subtitle1" gutterBottom>Business Information</Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                                <Chip label={`Company: ${formData.companyName}`} />
                                <Chip label={`Industry: ${formData.industry}`} />
                                <Chip label={`Size: ${formData.companySize}`} />
                                <Chip label={`AI Maturity: ${formData.currentAIMaturity}`} />
                            </Box>
                        </Paper>

                        <Paper sx={{ p: 2 }}>
                            <Typography variant="subtitle1" gutterBottom>Infrastructure</Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                                {formData.currentCloudProvider.map(provider => (
                                    <Chip key={provider} label={provider} />
                                ))}
                                <Chip label={`Budget: ${formData.monthlyBudget}`} />
                            </Box>
                        </Paper>

                        <Paper sx={{ p: 2 }}>
                            <Typography variant="subtitle1" gutterBottom>AI Requirements</Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                                {formData.aiUseCases.map(useCase => (
                                    <Chip key={useCase} label={useCase} />
                                ))}
                                <Chip label={`Data Volume: ${formData.expectedDataVolume}`} />
                            </Box>
                        </Paper>

                        <Paper sx={{ p: 2 }}>
                            <Typography variant="subtitle1" gutterBottom>Compliance & Security</Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                                {formData.complianceRequirements.map(compliance => (
                                    <Chip key={compliance} label={compliance} />
                                ))}
                                <Chip label={`Security: ${formData.securityLevel}`} />
                                <Chip label={`Location: ${formData.dataLocation}`} />
                            </Box>
                        </Paper>
                    </Box>
                );

            default:
                return 'Unknown step';
        }
    };

    const progress = ((activeStep + 1) / steps.length) * 100;

    return (
        <>
            <AppBar position="static">
                <Toolbar>
                    <IconButton
                        edge="start"
                        color="inherit"
                        onClick={() => router.push('/dashboard')}
                        sx={{ mr: 2 }}
                    >
                        <ArrowBack />
                    </IconButton>
                    <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                        AI Infrastructure Assessment
                    </Typography>
                    <Typography variant="body2">
                        Step {activeStep + 1} of {steps.length}
                    </Typography>
                </Toolbar>
                <LinearProgress variant="determinate" value={progress} />
            </AppBar>

            <Container maxWidth="md" sx={{ py: 4 }}>
                <Paper sx={{ p: 4 }}>
                    <ProgressIndicator
                        steps={steps}
                        activeStep={activeStep}
                        variant="stepper"
                    />

                    <ProgressSaver
                        formId={formId}
                        currentStep={activeStep}
                        formData={formData}
                        totalSteps={steps.length}
                        onSave={saveProgress}
                        onLoad={loadProgress}
                        onDelete={deleteProgress}
                        onListSaved={listSavedForms}
                        autoSaveInterval={30000}
                    />

                    {getStepContent(activeStep)}

                    <Box sx={{ display: 'flex', flexDirection: 'row', pt: 4 }}>
                        <Button
                            color="inherit"
                            disabled={activeStep === 0}
                            onClick={handleBack}
                            sx={{ mr: 1 }}
                        >
                            Back
                        </Button>
                        <Box sx={{ flex: '1 1 auto' }} />
                        {activeStep === steps.length - 1 ? (
                            <Button onClick={handleSubmit} variant="contained">
                                Submit Assessment
                            </Button>
                        ) : (
                            <Button onClick={handleNext} variant="contained">
                                Next
                            </Button>
                        )}
                    </Box>
                </Paper>
            </Container>
        </>
    );
}