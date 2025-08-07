'use client';

import React, { useState, useEffect, Suspense } from 'react';
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
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    DialogContentText,
    CircularProgress,
} from '@mui/material';
import {
    ArrowBack,
    Save,
    Restore,
} from '@mui/icons-material';
import { useRouter, useSearchParams } from 'next/navigation';
import ProgressIndicator from '@/components/ProgressIndicator';
import IntelligentFormField from '@/components/IntelligentFormField';
import ProgressSaver from '@/components/ProgressSaver';
import { apiClient } from '@/services/api';
import { useAssessmentPersistence } from '@/hooks/useAssessmentPersistence';

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

    // Custom "Other" text fields
    companySizeOther: string;
    currentAIMaturityOther: string;
    currentCloudProviderOther: string;
    currentServicesOther: string;
    aiUseCasesOther: string;
    performanceRequirementsOther: string;
    complianceRequirementsOther: string;
    dataLocationOther: string;
    securityLevelOther: string;
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
    // Initialize custom "Other" text fields
    companySizeOther: '',
    currentAIMaturityOther: '',
    currentCloudProviderOther: '',
    currentServicesOther: '',
    aiUseCasesOther: '',
    performanceRequirementsOther: '',
    complianceRequirementsOther: '',
    dataLocationOther: '',
    securityLevelOther: '',
};

function AssessmentPageInner() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const draftId = searchParams.get('draft');
    
    const [activeStep, setActiveStep] = useState(0);
    const [formData, setFormData] = useState<AssessmentFormData>(initialFormData);
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [formId] = useState(() => `assessment_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
    const [assessmentId, setAssessmentId] = useState<string | undefined>(draftId || undefined);
    const [showRestoreDialog, setShowRestoreDialog] = useState(false);
    const [isLoadingDraft, setIsLoadingDraft] = useState(false);
    
    // Initialize assessment persistence hook
    const {
        saveDraft,
        loadDraft,
        clearDraft,
        hasDraft,
        setupAutoSave,
        isLoading: isSaving,
        lastSaved
    } = useAssessmentPersistence();

    // Check for existing draft on component mount
    useEffect(() => {
        const checkForDraft = async () => {
            setIsLoadingDraft(true);
            
            // If there's a draft ID in URL, load that specific draft
            if (draftId) {
                try {
                    const assessment = await apiClient.getAssessment(draftId);
                    if (assessment && assessment.draft_data) {
                        setFormData(assessment.draft_data as AssessmentFormData);
                        setActiveStep(assessment.current_step || 0);
                        setAssessmentId(assessment.id);
                    }
                } catch (error) {
                    console.error('Failed to load draft from URL:', error);
                }
            } else if (hasDraft()) {
                // Show restore dialog for localStorage drafts
                setShowRestoreDialog(true);
            }
            
            setIsLoadingDraft(false);
        };
        
        checkForDraft();
    }, [draftId, hasDraft]);

    // Set up auto-save functionality
    useEffect(() => {
        const cleanup = setupAutoSave(
            () => formData,
            () => activeStep,
            () => assessmentId,
            30000 // Auto-save every 30 seconds
        );

        return cleanup;
    }, [formData, activeStep, assessmentId, setupAutoSave]);

    // Handle draft restoration
    const handleRestoreDraft = async () => {
        try {
            const draft = await loadDraft();
            if (draft) {
                setFormData(draft.formData as AssessmentFormData);
                setActiveStep(draft.currentStep);
                setAssessmentId(draft.assessmentId);
            }
        } catch (error) {
            console.error('Failed to restore draft:', error);
        } finally {
            setShowRestoreDialog(false);
        }
    };

    // Handle manual save
    const handleSaveDraft = async () => {
        await saveDraft(formData, activeStep, assessmentId);
    };

    const handleNext = () => {
        if (validateStep(activeStep)) {
            setActiveStep((prevActiveStep) => prevActiveStep + 1);
        }
    };

    const handleBack = () => {
        setActiveStep((prevActiveStep) => prevActiveStep - 1);
    };

    const handleInputChange = (field: keyof AssessmentFormData, value: string | string[]) => {
        console.log('handleInputChange called:', field, value);
        setFormData(prev => {
            const newData = {
                ...prev,
                [field]: value,
            };
            console.log('Updated form data:', newData);
            return newData;
        });
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

        console.log('Validating step:', step, 'Form data:', formData);

        switch (step) {
            case 0: // Business Information
                console.log('Checking companyName:', formData.companyName, 'Type:', typeof formData.companyName);
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
            try {
                console.log('Submitting form data:', formData);

                // Transform form data to match backend API schema exactly
                const assessmentData = {
                    title: `${formData.companyName} Infrastructure Assessment`,
                    description: `AI infrastructure assessment for ${formData.companyName} in the ${formData.industry} industry`,
                    priority: "medium",
                    business_requirements: {
                        company_size: formData.companySize,
                        industry: formData.industry,
                        business_goals: [
                            {
                                goal: formData.aiUseCases?.join(', ') || "Improve AI infrastructure",
                                priority: "high",
                                timeline_months: parseInt(String(formData.scalingTimeline).replace(' months', '')) || 6,
                                success_metrics: ["Performance improvement", "Cost optimization"]
                            }
                        ],
                        growth_projection: {
                            current_users: 1000,
                            projected_users_6m: 2000,
                            projected_users_12m: 5000,
                            current_revenue: "500000",
                            projected_revenue_12m: "1000000"
                        },
                        budget_constraints: {
                            total_budget_range: (() => {
                                const budgetMap: Record<string, string> = {
                                    'under-1k': 'under_10k',
                                    '1k-5k': '10k_50k', 
                                    '5k-25k': '10k_50k',
                                    '25k-100k': '50k_100k',
                                    'over-100k': '100k_500k'
                                };
                                return budgetMap[formData.monthlyBudget] || '10k_50k';
                            })(),
                            monthly_budget_limit: 25000,
                            cost_optimization_priority: "high"
                        },
                        team_structure: {
                            total_developers: parseInt(formData.technicalTeamSize) || 5,
                            senior_developers: Math.ceil((parseInt(formData.technicalTeamSize) || 5) * 0.4),
                            devops_engineers: 1,
                            data_engineers: 1,
                            cloud_expertise_level: 3,
                            kubernetes_expertise: 2,
                            database_expertise: 3
                        },
                        compliance_requirements: formData.complianceRequirements.length > 0 
                            ? formData.complianceRequirements.map(req => {
                                const complianceMap: Record<string, string> = {
                                    'GDPR': 'gdpr',
                                    'HIPAA': 'hipaa', 
                                    'SOC 2': 'soc2',
                                    'ISO 27001': 'iso27001',
                                    'PCI DSS': 'pci_dss',
                                    'CCPA': 'ccpa'
                                };
                                return complianceMap[req] || 'none';
                            })
                            : ["none"],
                        project_timeline_months: parseInt(formData.scalingTimeline.replace(' months', '')) || 6,
                        urgency_level: "medium",
                        current_pain_points: ["Scalability challenges"],
                        success_criteria: ["Improved performance", "Cost reduction"],
                        multi_cloud_acceptable: true
                    },
                    technical_requirements: {
                        workload_types: ["web_application", "api_service"],
                        performance_requirements: {
                            api_response_time_ms: 200,
                            requests_per_second: 1000,
                            concurrent_users: 500,
                            uptime_percentage: 99.9
                        },
                        scalability_requirements: {
                            current_data_size_gb: parseInt(formData.expectedDataVolume.replace(/[^0-9]/g, '')) || 100,
                            current_daily_transactions: 10000,
                            expected_data_growth_rate: "20% monthly",
                            peak_load_multiplier: 3.0,
                            auto_scaling_required: true,
                            global_distribution_required: false,
                            cdn_required: true,
                            planned_regions: ["us-east-1"]
                        },
                        security_requirements: {
                            encryption_at_rest_required: true,
                            encryption_in_transit_required: true,
                            multi_factor_auth_required: formData.securityLevel === "high",
                            single_sign_on_required: false,
                            role_based_access_control: true,
                            vpc_isolation_required: true,
                            firewall_required: true,
                            ddos_protection_required: formData.securityLevel === "high",
                            security_monitoring_required: true,
                            audit_logging_required: formData.complianceRequirements.length > 0,
                            vulnerability_scanning_required: formData.securityLevel === "high",
                            data_loss_prevention_required: false,
                            backup_encryption_required: true
                        },
                        integration_requirements: {
                            existing_databases: [],
                            existing_apis: [],
                            legacy_systems: [],
                            payment_processors: [],
                            analytics_platforms: [],
                            marketing_tools: [],
                            rest_api_required: true,
                            graphql_api_required: false,
                            websocket_support_required: false,
                            real_time_sync_required: false,
                            batch_sync_acceptable: true
                        },
                        preferred_programming_languages: ["Python", "JavaScript"],
                        monitoring_requirements: ["Performance monitoring", "Error tracking"],
                        backup_requirements: ["Daily backups", "Point-in-time recovery"],
                        ci_cd_requirements: ["Automated deployment", "Testing pipeline"]
                    },
                    source: "web_form"
                };

                // Make API call to create assessment using apiClient
                const createdAssessment = await apiClient.createAssessment(assessmentData);
                console.log('Assessment created successfully:', createdAssessment);

                // Clear the draft since assessment was successfully submitted
                await clearDraft(assessmentId);

                // Show success message and redirect to dashboard to see the assessment
                alert('Assessment submitted successfully! Redirecting to dashboard...');
                router.push('/dashboard');
            } catch (error) {
                console.error('Error submitting assessment:', error);
                // You could add a toast notification here to show the error to the user
                alert(`Failed to submit assessment: ${error instanceof Error ? error.message : 'Unknown error'}`);
            }
        }
    };

    // Intelligent form service functions
    const getSmartDefaults = async (fieldName: string) => {
        try {
            return await apiClient.getSmartDefaults(fieldName, formData);
        } catch (error) {
            console.error('Failed to get smart defaults:', error);
            return [];
        }
    };

    const getSuggestions = async (fieldName: string, query: string) => {
        try {
            return await apiClient.getFieldSuggestions(fieldName, query, formData);
        } catch (error) {
            console.error('Failed to get field suggestions:', error);
            return [];
        }
    };

    const getContextualHelp = async (fieldName: string) => {
        try {
            return await apiClient.getContextualHelp(fieldName, formData);
        } catch (error) {
            console.error('Failed to get contextual help:', error);
            return null;
        }
    };

    // Progress saving functions
    const saveProgress = async (formId: string, formData: Record<string, unknown>, currentStep: number) => {
        try {
            // Try to save to backend first, fallback to localStorage
            try {
                await apiClient.request('/forms/save-progress', {
                    method: 'POST',
                    body: JSON.stringify({
                        form_id: formId,
                        form_data: formData,
                        current_step: currentStep,
                        saved_at: new Date().toISOString()
                    })
                });
                return true;
            } catch (apiError) {
                console.warn('Backend save failed, using localStorage:', apiError);
                // Fallback to localStorage
                localStorage.setItem(`form_${formId}`, JSON.stringify({
                    formData,
                    currentStep,
                    savedAt: new Date().toISOString()
                }));
                return true;
            }
        } catch (error) {
            console.error('Failed to save progress:', error);
            return false;
        }
    };

    const loadProgress = async (formId: string) => {
        try {
            // Try to load from backend first, fallback to localStorage
            try {
                const data = await apiClient.request(`/forms/load-progress/${formId}`);
                if (data && data.form_data) {
                    setFormData(data.form_data);
                    setActiveStep(data.current_step || 0);
                    return data.form_data;
                }
            } catch (apiError) {
                console.warn('Backend load failed, using localStorage:', apiError);
                // Fallback to localStorage
                const saved = localStorage.getItem(`form_${formId}`);
                if (saved) {
                    const data = JSON.parse(saved);
                    setFormData(data.formData);
                    setActiveStep(data.currentStep);
                    return data.formData;
                }
            }
            return null;
        } catch (error) {
            console.error('Failed to load progress:', error);
            return null;
        }
    };

    const deleteProgress = async (formId: string) => {
        try {
            // Try to delete from backend first, then localStorage
            try {
                await apiClient.request(`/forms/delete-progress/${formId}`, {
                    method: 'DELETE'
                });
            } catch (apiError) {
                console.warn('Backend delete failed:', apiError);
            }
            // Always remove from localStorage as well
            localStorage.removeItem(`form_${formId}`);
            return true;
        } catch (error) {
            console.error('Failed to delete progress:', error);
            return false;
        }
    };

    const listSavedForms = async () => {
        try {
            // Try to get from backend first, fallback to localStorage
            try {
                const backendForms = await apiClient.request('/forms/list-saved');
                if (backendForms && Array.isArray(backendForms)) {
                    return backendForms;
                }
            } catch (apiError) {
                console.warn('Backend list failed, using localStorage:', apiError);
            }
            
            // Fallback to localStorage
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
                                <FormControlLabel value="other" control={<Radio />} label="Other" />
                            </RadioGroup>
                            {formData.companySize === 'other' && (
                                <TextField
                                    fullWidth
                                    label="Please specify company size"
                                    value={formData.companySizeOther}
                                    onChange={(e) => handleInputChange('companySizeOther', e.target.value)}
                                    sx={{ mt: 2 }}
                                    size="small"
                                />
                            )}
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
                                <FormControlLabel value="other" control={<Radio />} label="Other" />
                            </RadioGroup>
                            {formData.currentAIMaturity === 'other' && (
                                <TextField
                                    fullWidth
                                    label="Please specify AI maturity level"
                                    value={formData.currentAIMaturityOther}
                                    onChange={(e) => handleInputChange('currentAIMaturityOther', e.target.value)}
                                    sx={{ mt: 2 }}
                                    size="small"
                                />
                            )}
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
                            {formData.currentCloudProvider.includes('Other') && (
                                <TextField
                                    fullWidth
                                    label="Please specify other cloud provider"
                                    value={formData.currentCloudProviderOther}
                                    onChange={(e) => handleInputChange('currentCloudProviderOther', e.target.value)}
                                    sx={{ mt: 2 }}
                                    size="small"
                                />
                            )}
                        </FormControl>

                        <FormControl fullWidth>
                            <FormLabel>Current Services (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['Compute (VMs/Containers)', 'Storage', 'Databases', 'ML/AI Services', 'Analytics', 'Networking', 'Other'].map((service) => (
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
                            {formData.currentServices.includes('Other') && (
                                <TextField
                                    fullWidth
                                    label="Please specify other services"
                                    value={formData.currentServicesOther}
                                    onChange={(e) => handleInputChange('currentServicesOther', e.target.value)}
                                    sx={{ mt: 2 }}
                                    size="small"
                                />
                            )}
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
                                {['Machine Learning Models', 'Natural Language Processing', 'Computer Vision', 'Predictive Analytics', 'Recommendation Systems', 'Chatbots/Virtual Assistants', 'Other'].map((useCase) => (
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
                            {formData.aiUseCases.includes('Other') && (
                                <TextField
                                    fullWidth
                                    label="Please specify other AI use cases"
                                    value={formData.aiUseCasesOther}
                                    onChange={(e) => handleInputChange('aiUseCasesOther', e.target.value)}
                                    sx={{ mt: 2 }}
                                    size="small"
                                />
                            )}
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
                                <FormControlLabel value="other" control={<Radio />} label="Other" />
                            </RadioGroup>
                            {formData.performanceRequirements === 'other' && (
                                <TextField
                                    fullWidth
                                    label="Please specify performance requirements"
                                    value={formData.performanceRequirementsOther}
                                    onChange={(e) => handleInputChange('performanceRequirementsOther', e.target.value)}
                                    sx={{ mt: 2 }}
                                    size="small"
                                />
                            )}
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
                                {['GDPR', 'HIPAA', 'SOC 2', 'ISO 27001', 'PCI DSS', 'CCPA', 'Other'].map((compliance) => (
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
                            {formData.complianceRequirements.includes('Other') && (
                                <TextField
                                    fullWidth
                                    label="Please specify other compliance requirements"
                                    value={formData.complianceRequirementsOther}
                                    onChange={(e) => handleInputChange('complianceRequirementsOther', e.target.value)}
                                    sx={{ mt: 2 }}
                                    size="small"
                                />
                            )}
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
                                <FormControlLabel value="other" control={<Radio />} label="Other" />
                            </RadioGroup>
                            {formData.dataLocation === 'other' && (
                                <TextField
                                    fullWidth
                                    label="Please specify data location preference"
                                    value={formData.dataLocationOther}
                                    onChange={(e) => handleInputChange('dataLocationOther', e.target.value)}
                                    sx={{ mt: 2 }}
                                    size="small"
                                />
                            )}
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
                                <FormControlLabel value="other" control={<Radio />} label="Other" />
                            </RadioGroup>
                            {formData.securityLevel === 'other' && (
                                <TextField
                                    fullWidth
                                    label="Please specify security level requirements"
                                    value={formData.securityLevelOther}
                                    onChange={(e) => handleInputChange('securityLevelOther', e.target.value)}
                                    sx={{ mt: 2 }}
                                    size="small"
                                />
                            )}
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
                        onClick={() => router.push('/')}
                        sx={{ mr: 2 }}
                    >
                        <ArrowBack />
                    </IconButton>
                    <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                        AI Infrastructure Assessment
                    </Typography>
                    
                    {/* Save Status and Button */}
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mr: 2 }}>
                        {lastSaved && (
                            <Typography variant="caption" color="text.secondary">
                                Saved: {lastSaved.toLocaleTimeString()}
                            </Typography>
                        )}
                        
                        {/* Restore Session Button */}
                        {hasDraft() && !showRestoreDialog && (
                            <Button
                                variant="outlined"
                                size="small"
                                startIcon={<Restore />}
                                onClick={() => setShowRestoreDialog(true)}
                                color="inherit"
                                sx={{ mr: 1 }}
                            >
                                Restore Session
                            </Button>
                        )}
                        
                        <Button
                            variant="outlined"
                            size="small"
                            startIcon={isSaving ? <CircularProgress size={16} /> : <Save />}
                            onClick={handleSaveDraft}
                            disabled={isSaving}
                            color="inherit"
                        >
                            {isSaving ? 'Saving...' : 'Save Draft'}
                        </Button>
                    </Box>
                    
                    <Typography variant="body2">
                        Step {activeStep + 1} of {steps.length}
                    </Typography>
                </Toolbar>
                <LinearProgress variant="determinate" value={progress} />
            </AppBar>

            <Container maxWidth="md" sx={{ py: 4 }}>
                <Paper sx={{ p: 4 }}>
                    {isLoadingDraft ? (
                        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
                            <CircularProgress />
                            <Typography variant="body1" sx={{ ml: 2 }}>
                                Loading assessment...
                            </Typography>
                        </Box>
                    ) : (
                        <>
                            <ProgressIndicator
                        title="Assessment Progress"
                        steps={steps.map((label, index) => ({
                            label,
                            status: index === activeStep ? 'active' : index < activeStep ? 'completed' : 'pending',
                        }))}
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
                        </>
                    )}
                </Paper>
            </Container>

            {/* Draft Restore Dialog */}
            <Dialog
                open={showRestoreDialog}
                onClose={() => setShowRestoreDialog(false)}
                aria-labelledby="restore-dialog-title"
                aria-describedby="restore-dialog-description"
            >
                <DialogTitle id="restore-dialog-title">
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Restore color="primary" />
                        Restore Previous Assessment
                    </Box>
                </DialogTitle>
                <DialogContent>
                    <DialogContentText id="restore-dialog-description">
                        We found a saved draft of your assessment. Would you like to continue where you left off?
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button 
                        onClick={() => setShowRestoreDialog(false)}
                        color="secondary"
                    >
                        Start Fresh
                    </Button>
                    <Button 
                        onClick={handleRestoreDraft}
                        variant="contained"
                        startIcon={<Restore />}
                        autoFocus
                    >
                        Restore Draft
                    </Button>
                </DialogActions>
            </Dialog>
        </>
    );
}

export default function AssessmentPage() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <AssessmentPageInner />
        </Suspense>
    );
}