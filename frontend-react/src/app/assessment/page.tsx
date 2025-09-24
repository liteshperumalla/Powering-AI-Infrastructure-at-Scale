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
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    DialogContentText,
    CircularProgress,
    Card,
    CardContent,
    Stepper,
    Step,
    StepLabel,
    useTheme,
    alpha,
    Grid,
    Stack,
} from '@mui/material';
import {
    Save,
    Restore,
    CheckCircle,
    Schedule,
    Assignment,
    Warning,
} from '@mui/icons-material';
import { useRouter, useSearchParams } from 'next/navigation';
import ProgressIndicator from '@/components/ProgressIndicator';
import IntelligentFormField from '@/components/IntelligentFormField';
import { useAppDispatch } from '@/store/hooks';
import { addNotification } from '@/store/slices/uiSlice';
import ProgressSaver from '@/components/ProgressSaver';
import ResponsiveLayout from '@/components/ResponsiveLayout';
import ProtectedRoute from '@/components/ProtectedRoute';
import { apiClient } from '@/services/api';
import { useAssessmentPersistence } from '@/hooks/useAssessmentPersistence';

const steps = [
    'Business Information',
    'Current Infrastructure', 
    'Technical Architecture',
    'AI Requirements & Use Cases',
    'Performance & Scalability',
    'Security & Compliance',
    'Budget & Timeline',
    'Review & Submit',
];

interface AssessmentFormData extends Record<string, unknown> {
    // Business Information
    companyName: string;
    industry: string;
    companySize: string;
    currentAIMaturity: string;
    businessGoal: string;
    geographicRegions: string[];
    customerBase: string;
    revenueModel: string;
    growthStage: string;
    keyCompetitors: string;
    missionCriticalSystems: string[];

    // Current Infrastructure
    currentCloudProvider: string[];
    currentServices: string[];
    monthlyBudget: string;
    technicalTeamSize: string;
    infrastructureAge: string;
    currentArchitecture: string;
    dataStorageSolution: string[];
    networkSetup: string;
    disasterRecoverySetup: string;
    monitoringTools: string[];

    // Technical Architecture
    applicationTypes: string[];
    developmentFrameworks: string[];
    programmingLanguages: string[];
    databaseTypes: string[];
    integrationPatterns: string[];
    deploymentStrategy: string;
    containerization: string;
    orchestrationPlatform: string;
    cicdTools: string[];
    versionControlSystem: string;

    // AI Requirements & Use Cases
    aiUseCases: string[];
    expectedDataVolume: string;
    dataTypes: string[];
    realTimeRequirements: string;
    mlModelTypes: string[];
    trainingFrequency: string;
    inferenceVolume: string;
    dataProcessingNeeds: string[];
    aiIntegrationComplexity: string;
    existingMLInfrastructure: string[];

    // Performance & Scalability
    performanceRequirements: string;
    currentUserLoad: string;
    peakTrafficPatterns: string;
    expectedGrowthRate: string;
    responseTimeRequirements: string;
    availabilityRequirements: string;
    globalDistribution: string;
    loadPatterns: string;
    failoverRequirements: string;
    scalingTriggers: string[];

    // Security & Compliance
    complianceRequirements: string[];
    dataLocation: string;
    securityLevel: string;
    auditRequirements: string;
    dataClassification: string[];
    securityIncidentHistory: string;
    accessControlRequirements: string[];
    encryptionRequirements: string[];
    securityMonitoring: string[];
    vulnerabilityManagement: string;

    // Budget & Timeline
    scalingTimeline: string;
    budgetFlexibility: string;
    costOptimizationPriority: string;
    totalBudgetRange: string;
    migrationBudget: string;
    operationalBudgetSplit: string;
    roiExpectations: string;
    paymentModel: string;

    // Custom "Other" text fields
    industryOther: string;
    companySizeOther: string;
    currentAIMaturityOther: string;
    currentCloudProviderOther: string;
    currentServicesOther: string;
    aiUseCasesOther: string;
    performanceRequirementsOther: string;
    complianceRequirementsOther: string;
    dataLocationOther: string;
    securityLevelOther: string;
    geographicRegionsOther: string;
    applicationTypesOther: string;
    developmentFrameworksOther: string;
    databaseTypesOther: string;
    mlModelTypesOther: string;
    dataTypesOther: string;
    missionCriticalSystemsOther: string;
    dataStorageSolutionOther: string;
    monitoringToolsOther: string;
    integrationPatternsOther: string;
    dataProcessingNeedsOther: string;
    existingMLInfrastructureOther: string;
    scalingTriggersOther: string;
    dataClassificationOther: string;
    accessControlRequirementsOther: string;
    encryptionRequirementsOther: string;
    securityMonitoringOther: string;
}

const initialFormData: AssessmentFormData = {
    // Business Information
    companyName: '',
    industry: '',
    companySize: '',
    currentAIMaturity: '',
    businessGoal: '',
    geographicRegions: [],
    customerBase: '',
    revenueModel: '',
    growthStage: '',
    keyCompetitors: '',
    missionCriticalSystems: [],

    // Current Infrastructure
    currentCloudProvider: [],
    currentServices: [],
    monthlyBudget: '',
    technicalTeamSize: '',
    infrastructureAge: '',
    currentArchitecture: '',
    dataStorageSolution: [],
    networkSetup: '',
    disasterRecoverySetup: '',
    monitoringTools: [],

    // Technical Architecture
    applicationTypes: [],
    developmentFrameworks: [],
    programmingLanguages: [],
    databaseTypes: [],
    integrationPatterns: [],
    deploymentStrategy: '',
    containerization: '',
    orchestrationPlatform: '',
    cicdTools: [],
    versionControlSystem: '',

    // AI Requirements & Use Cases
    aiUseCases: [],
    expectedDataVolume: '',
    dataTypes: [],
    realTimeRequirements: '',
    mlModelTypes: [],
    trainingFrequency: '',
    inferenceVolume: '',
    dataProcessingNeeds: [],
    aiIntegrationComplexity: '',
    existingMLInfrastructure: [],

    // Performance & Scalability
    performanceRequirements: '',
    currentUserLoad: '',
    peakTrafficPatterns: '',
    expectedGrowthRate: '',
    responseTimeRequirements: '',
    availabilityRequirements: '',
    globalDistribution: '',
    loadPatterns: '',
    failoverRequirements: '',
    scalingTriggers: [],

    // Security & Compliance
    complianceRequirements: [],
    dataLocation: '',
    securityLevel: '',
    auditRequirements: '',
    dataClassification: [],
    securityIncidentHistory: '',
    accessControlRequirements: [],
    encryptionRequirements: [],
    securityMonitoring: [],
    vulnerabilityManagement: '',

    // Budget & Timeline
    scalingTimeline: '',
    budgetFlexibility: '',
    costOptimizationPriority: '',
    totalBudgetRange: '',
    migrationBudget: '',
    operationalBudgetSplit: '',
    roiExpectations: '',
    paymentModel: '',

    // Initialize custom "Other" text fields
    industryOther: '',
    companySizeOther: '',
    currentAIMaturityOther: '',
    currentCloudProviderOther: '',
    currentServicesOther: '',
    aiUseCasesOther: '',
    performanceRequirementsOther: '',
    complianceRequirementsOther: '',
    dataLocationOther: '',
    securityLevelOther: '',
    geographicRegionsOther: '',
    applicationTypesOther: '',
    developmentFrameworksOther: '',
    databaseTypesOther: '',
    mlModelTypesOther: '',
    dataTypesOther: '',
    missionCriticalSystemsOther: '',
    dataStorageSolutionOther: '',
    monitoringToolsOther: '',
    integrationPatternsOther: '',
    dataProcessingNeedsOther: '',
    existingMLInfrastructureOther: '',
    scalingTriggersOther: '',
    dataClassificationOther: '',
    accessControlRequirementsOther: '',
    encryptionRequirementsOther: '',
    securityMonitoringOther: '',
};

function AssessmentPageInner() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const dispatch = useAppDispatch();
    const draftId = searchParams.get('draft');
    
    const [activeStep, setActiveStep] = useState(0);
    const [formData, setFormData] = useState<AssessmentFormData>(initialFormData);
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [formId] = useState(() => `assessment_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
    const [assessmentId, setAssessmentId] = useState<string | undefined>(draftId || undefined);
    const [showRestoreDialog, setShowRestoreDialog] = useState(false);
    const [isLoadingDraft, setIsLoadingDraft] = useState(false);
    const [showIndustryDialog, setShowIndustryDialog] = useState(false);
    const [customIndustry, setCustomIndustry] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submissionCount, setSubmissionCount] = useState(0);
    const [lastSubmissionTime, setLastSubmissionTime] = useState<number | null>(null);
    const [existingAssessmentId, setExistingAssessmentId] = useState<string | null>(null);
    const [showDuplicateDialog, setShowDuplicateDialog] = useState(false);
    
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
        } else {
            // Scroll to first error field
            const firstErrorField = document.querySelector('[aria-invalid="true"]');
            if (firstErrorField) {
                firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                (firstErrorField as HTMLElement).focus();
            }
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

    const handleIndustryChange = (value: string) => {
        if (value === 'other') {
            setShowIndustryDialog(true);
        } else {
            handleInputChange('industry', value);
            handleInputChange('industryOther', ''); // Clear other field
        }
    };

    const handleCustomIndustrySubmit = () => {
        if (customIndustry.trim()) {
            handleInputChange('industry', 'other');
            handleInputChange('industryOther', customIndustry.trim());
            setShowIndustryDialog(false);
            setCustomIndustry('');
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
            case 2: // Technical Architecture
                if (formData.applicationTypes.length === 0) newErrors.applicationTypes = 'Select at least one application type';
                if (formData.programmingLanguages.length === 0) newErrors.programmingLanguages = 'Select at least one programming language';
                break;
            case 3: // AI Requirements & Use Cases
                if (formData.aiUseCases.length === 0) newErrors.aiUseCases = 'Select at least one AI use case';
                if (!formData.expectedDataVolume) newErrors.expectedDataVolume = 'Expected data volume is required';
                break;
            case 4: // Performance & Scalability
                if (!formData.currentUserLoad) newErrors.currentUserLoad = 'Current user load is required';
                if (!formData.expectedGrowthRate) newErrors.expectedGrowthRate = 'Expected growth rate is required';
                break;
            case 5: // Security & Compliance
                if (!formData.dataLocation) newErrors.dataLocation = 'Data location preference is required';
                break;
            case 6: // Budget & Timeline
                if (!formData.budgetFlexibility) newErrors.budgetFlexibility = 'Budget flexibility is required';
                if (!formData.totalBudgetRange) newErrors.totalBudgetRange = 'Total budget range is required';
                break;
        }

        setErrors(newErrors);

        // If there are errors, show a helpful summary
        if (Object.keys(newErrors).length > 0) {
            const errorCount = Object.keys(newErrors).length;
            const fieldNames = Object.keys(newErrors).join(', ');

            // Show a non-intrusive notification
            dispatch(addNotification({
                type: 'warning',
                message: `Please complete ${errorCount} required field${errorCount > 1 ? 's' : ''}: ${fieldNames}`
            }));
        }

        return Object.keys(newErrors).length === 0;
    };

    // Helper function to get errors for current step
    const getCurrentStepErrors = (step: number) => {
        const stepErrors: Record<string, string> = {};

        switch (step) {
            case 0:
                if (errors.companyName) stepErrors.companyName = errors.companyName;
                if (errors.industry) stepErrors.industry = errors.industry;
                if (errors.companySize) stepErrors.companySize = errors.companySize;
                if (errors.currentAIMaturity) stepErrors.currentAIMaturity = errors.currentAIMaturity;
                break;
            case 1:
                if (errors.currentCloudProvider) stepErrors.currentCloudProvider = errors.currentCloudProvider;
                if (errors.monthlyBudget) stepErrors.monthlyBudget = errors.monthlyBudget;
                break;
            case 2:
                if (errors.applicationTypes) stepErrors.applicationTypes = errors.applicationTypes;
                if (errors.programmingLanguages) stepErrors.programmingLanguages = errors.programmingLanguages;
                break;
            case 3:
                if (errors.aiUseCases) stepErrors.aiUseCases = errors.aiUseCases;
                if (errors.expectedDataVolume) stepErrors.expectedDataVolume = errors.expectedDataVolume;
                break;
            case 4:
                if (errors.currentUserLoad) stepErrors.currentUserLoad = errors.currentUserLoad;
                if (errors.expectedGrowthRate) stepErrors.expectedGrowthRate = errors.expectedGrowthRate;
                break;
            case 5:
                if (errors.dataLocation) stepErrors.dataLocation = errors.dataLocation;
                break;
            case 6:
                if (errors.budgetFlexibility) stepErrors.budgetFlexibility = errors.budgetFlexibility;
                if (errors.totalBudgetRange) stepErrors.totalBudgetRange = errors.totalBudgetRange;
                break;
        }

        return stepErrors;
    };

    // Error summary component for the current step
    const ErrorSummary = ({ step }: { step: number }) => {
        const stepErrors = getCurrentStepErrors(step);
        const errorCount = Object.keys(stepErrors).length;

        if (errorCount === 0) return null;

        return (
            <Alert severity="warning" sx={{ mb: 2 }}>
                <Typography variant="body2" sx={{ fontWeight: 'medium', mb: 1 }}>
                    Please complete {errorCount} required field{errorCount > 1 ? 's' : ''}:
                </Typography>
                <Box component="ul" sx={{ pl: 2, m: 0 }}>
                    {Object.entries(stepErrors).map(([field, message]) => (
                        <li key={field}>
                            <Typography variant="body2" color="warning.dark">
                                {message}
                            </Typography>
                        </li>
                    ))}
                </Box>
            </Alert>
        );
    };

    const handleSubmit = async () => {
        // Enhanced submission prevention
        const now = Date.now();
        const SUBMISSION_COOLDOWN = 60000; // 1 minute cooldown

        if (isSubmitting) {
            console.log('Submission already in progress, ignoring duplicate request');
            return;
        }

        // Check if user is submitting too frequently
        if (lastSubmissionTime && (now - lastSubmissionTime) < SUBMISSION_COOLDOWN) {
            alert('Please wait a moment before submitting again. Your assessment may already be processing.');
            return;
        }

        // Check for recent submissions
        if (submissionCount >= 3) {
            alert('You have submitted multiple assessments recently. Please check your dashboard for existing assessments.');
            return;
        }

        if (validateStep(activeStep)) {
            setIsSubmitting(true);
            setSubmissionCount(prev => prev + 1);
            setLastSubmissionTime(now);

            try {
                console.log('Submitting form data:', formData);

                // Transform form data to match backend API schema with all enhanced fields
                const assessmentData = {
                    title: `${formData.companyName} Infrastructure Assessment`,
                    description: `AI infrastructure assessment for ${formData.companyName} in the ${formData.industry} industry`,
                    business_goal: formData.businessGoal,
                    priority: "medium",
                    business_requirements: {
                        // Core business fields
                        company_size: formData.companySize,
                        industry: formData.industry,
                        
                        // Enhanced business fields from Step 1
                        company_name: formData.companyName,
                        geographic_regions: formData.geographicRegions?.length > 0 ? formData.geographicRegions : ["North America"],
                        customer_base_size: formData.customerBaseSize || "medium",
                        revenue_model: formData.revenueModel || "subscription",
                        growth_stage: formData.growthStage || "growing",
                        key_competitors: formData.keyCompetitors || "",
                        mission_critical_systems: formData.missionCriticalSystems?.length > 0 ? formData.missionCriticalSystems : [],
                        
                        business_goals: [
                            {
                                goal: formData.aiUseCases?.join(', ') || "Improve AI infrastructure",
                                priority: "high",
                                timeline_months: parseInt(String(formData.scalingTimeline).replace(' months', '')) || 6,
                                success_metrics: ["Performance improvement", "Cost optimization"]
                            }
                        ],
                        growth_projection: {
                            current_users: parseInt(formData.currentUserLoad?.replace(/[^0-9]/g, '')) || 1000,
                            projected_users_6m: parseInt(formData.currentUserLoad?.replace(/[^0-9]/g, '')) * 2 || 2000,
                            projected_users_12m: parseInt(formData.currentUserLoad?.replace(/[^0-9]/g, '')) * 5 || 5000,
                            current_revenue: "500000",
                            projected_revenue_12m: "1000000"
                        },
                        budget_constraints: {
                            total_budget_range: (() => {
                                const budgetMap: Record<string, string> = {
                                    'under-1k': 'under_10k',
                                    '1k-5k': '10k_50k', 
                                    '5k-25k': '50k_100k',
                                    '25k-100k': '100k_500k',
                                    'over-100k': '500k_1m'
                                };
                                return budgetMap[formData.totalBudgetRange] || budgetMap[formData.monthlyBudget] || '50k_100k';
                            })(),
                            monthly_budget_limit: 25000,
                            cost_optimization_priority: formData.costOptimizationPriority || "high",
                            budget_flexibility: formData.budgetFlexibility || "medium"
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
                        compliance_requirements: formData.complianceRequirements?.length > 0 
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
                        project_timeline_months: parseInt(formData.implementationTimeline?.replace(' months', '')) || parseInt(formData.scalingTimeline?.replace(' months', '')) || 6,
                        urgency_level: "medium",
                        current_pain_points: ["Scalability challenges"],
                        success_criteria: ["Improved performance", "Cost reduction"],
                        multi_cloud_acceptable: true
                    },
                    technical_requirements: {
                        // Enhanced technical fields from Steps 2-6
                        workload_types: formData.applicationTypes?.length > 0 ? formData.applicationTypes : ["web_application"],
                        current_cloud_providers: formData.currentCloudProviders?.length > 0 ? formData.currentCloudProviders : [],
                        current_services: formData.currentServices?.length > 0 ? formData.currentServices : [],
                        technical_team_size: parseInt(formData.technicalTeamSize) || 5,
                        infrastructure_age: formData.infrastructureAge || "recent",
                        current_architecture: formData.currentArchitecture || "microservices",
                        ai_use_cases: formData.aiUseCases?.length > 0 ? formData.aiUseCases : [],
                        current_ai_maturity: formData.currentAiMaturity || "intermediate",
                        expected_data_volume: formData.expectedDataVolume || "100GB",
                        data_types: formData.dataTypes?.length > 0 ? formData.dataTypes : ["Text"],
                        current_user_load: formData.currentUserLoad || "1000_concurrent",
                        expected_growth_rate: formData.expectedGrowthRate || "50%_annually",
                        budget_flexibility: formData.budgetFlexibility || "medium",
                        total_budget_range: formData.totalBudgetRange || formData.monthlyBudget || "50k_100k",
                        
                        performance_requirements: {
                            api_response_time_ms: parseInt(formData.responseTimeRequirement?.replace(/[^0-9]/g, '')) || 200,
                            requests_per_second: parseInt(formData.requestsPerSecond?.replace(/[^0-9]/g, '')) || 1000,
                            concurrent_users: parseInt(formData.currentUserLoad?.replace(/[^0-9]/g, '')) || 500,
                            uptime_percentage: parseFloat(formData.uptimeRequirement?.replace('%', '')) || 99.9
                        },
                        scalability_requirements: {
                            current_data_size_gb: parseInt(formData.expectedDataVolume?.replace(/[^0-9]/g, '')) || 100,
                            current_daily_transactions: 10000,
                            expected_data_growth_rate: formData.expectedGrowthRate || "50% annually",
                            peak_load_multiplier: parseFloat(formData.peakLoadMultiplier) || 3.0,
                            auto_scaling_required: formData.autoScalingRequired || true,
                            global_distribution_required: formData.globalDistribution || false,
                            cdn_required: true,
                            planned_regions: formData.geographicRegions?.length > 0 ? formData.geographicRegions : ["us-east-1"]
                        },
                        security_requirements: {
                            encryption_at_rest_required: formData.encryptionRequirements?.includes('Data at Rest') || true,
                            encryption_in_transit_required: formData.encryptionRequirements?.includes('Data in Transit') || true,
                            multi_factor_auth_required: formData.accessControlMethods?.includes('Multi-Factor Authentication') || formData.securityLevel === "high",
                            single_sign_on_required: formData.accessControlMethods?.includes('Single Sign-On (SSO)') || false,
                            role_based_access_control: formData.accessControlMethods?.includes('Role-Based Access Control') || true,
                            vpc_isolation_required: formData.networkSecurity?.includes('VPC Isolation') || true,
                            firewall_required: formData.networkSecurity?.includes('Firewall') || true,
                            ddos_protection_required: formData.networkSecurity?.includes('DDoS Protection') || formData.securityLevel === "high",
                            security_monitoring_required: formData.monitoringTools?.includes('Security Monitoring') || true,
                            audit_logging_required: formData.complianceRequirements?.length > 0,
                            vulnerability_scanning_required: formData.securityLevel === "high",
                            data_loss_prevention_required: formData.dataClassification === "highly_sensitive",
                            backup_encryption_required: true
                        },
                        integration_requirements: {
                            existing_databases: formData.dataStorageSolution?.filter(db => db.includes('database')) || [],
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
                        preferred_programming_languages: formData.programmingLanguages?.length > 0 ? formData.programmingLanguages : ["Python", "JavaScript"],
                        monitoring_requirements: formData.monitoringTools?.length > 0 ? formData.monitoringTools : ["Performance monitoring", "Error tracking"],
                        backup_requirements: formData.backupRequirements?.length > 0 ? formData.backupRequirements : ["Daily backups", "Point-in-time recovery"],
                        ci_cd_requirements: formData.deploymentPreferences?.length > 0 ? formData.deploymentPreferences : ["Automated deployment", "Testing pipeline"]
                    },
                    source: "web_form"
                };

                // Make API call to create assessment using apiClient
                const createdAssessment = await apiClient.createAssessment(assessmentData);
                console.log('Assessment created successfully:', createdAssessment);

                // Check if response indicates a duplicate was found
                if (createdAssessment && createdAssessment.id && createdAssessment.id !== createdAssessment.title) {
                    // This might be an existing assessment
                    setExistingAssessmentId(createdAssessment.id);
                    setShowDuplicateDialog(true);
                    return;
                }

                // Clear the draft since assessment was successfully submitted
                await clearDraft(assessmentId);

                // Show enhanced success message
                alert('🎉 Assessment submitted successfully! Your AI infrastructure analysis is now being processed. You will be redirected to view the results.');

                // Redirect to the specific assessment or dashboard
                if (createdAssessment?.id) {
                    router.push(`/dashboard?highlight=${createdAssessment.id}`);
                } else {
                    router.push('/dashboard');
                }
            } catch (error) {
                console.error('Error submitting assessment:', error);
                
                // Handle authentication errors by redirecting to login
                if (error instanceof Error && (
                    error.message.includes('Access denied') ||
                    error.message.includes('403') ||
                    error.message.includes('authentication')
                )) {
                    alert('You need to be logged in to submit an assessment. Redirecting to login...');
                    router.push('/auth/login');
                    return;
                }

                // Handle duplicate assessment errors
                if (error instanceof Error && error.message.includes('Duplicate assessment')) {
                    const match = error.message.match(/existing ID: ([a-fA-F0-9]+)/);
                    if (match) {
                        setExistingAssessmentId(match[1]);
                        setShowDuplicateDialog(true);
                        return;
                    }
                    alert('You already have a similar assessment. Please check your dashboard.');
                    router.push('/dashboard');
                    return;
                }

                // Handle rate limiting
                if (error instanceof Error && (error.message.includes('Too Many Requests') || error.message.includes('429'))) {
                    alert('You are submitting assessments too quickly. Please wait a moment and try again.');
                    setSubmissionCount(prev => Math.max(0, prev - 1)); // Reduce submission count for rate limit
                    return;
                }

                // Handle other errors
                alert(`❌ Failed to submit assessment: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again or contact support if the problem persists.`);
            } finally {
                // Reset submission state
                setIsSubmitting(false);
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

    // Add caching to prevent excessive API calls
    const [formsCache, setFormsCache] = useState<any[] | null>(null);
    const [lastFetch, setLastFetch] = useState<number>(0);
    const CACHE_DURATION = 10000; // 10 seconds

    const listSavedForms = async () => {
        try {
            // Use cache if recent
            const now = Date.now();
            if (formsCache && (now - lastFetch) < CACHE_DURATION) {
                return formsCache;
            }

            // Try to get from backend first, fallback to localStorage
            try {
                const backendForms = await apiClient.request('/forms/list-saved');
                if (backendForms && Array.isArray(backendForms)) {
                    setFormsCache(backendForms);
                    setLastFetch(now);
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
                        <ErrorSummary step={0} />

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

                        <FormControl fullWidth error={!!errors.industry}>
                            <InputLabel>Industry *</InputLabel>
                            <Select
                                value={formData.industry}
                                onChange={(e) => handleIndustryChange(e.target.value)}
                                label="Industry *"
                            >
                                <MenuItem value="technology">Technology</MenuItem>
                                <MenuItem value="healthcare">Healthcare</MenuItem>
                                <MenuItem value="finance">Finance</MenuItem>
                                <MenuItem value="retail">Retail</MenuItem>
                                <MenuItem value="manufacturing">Manufacturing</MenuItem>
                                <MenuItem value="education">Education</MenuItem>
                                <MenuItem value="government">Government</MenuItem>
                                <MenuItem value="nonprofit">Non-Profit</MenuItem>
                                <MenuItem value="other">Other</MenuItem>
                            </Select>
                            {errors.industry && (
                                <Typography variant="caption" color="error" sx={{ mt: 1 }}>
                                    {errors.industry}
                                </Typography>
                            )}
                            {formData.industry === 'other' && formData.industryOther && (
                                <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                                    Custom industry: {formData.industryOther}
                                </Typography>
                            )}
                        </FormControl>

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

                        <TextField
                            fullWidth
                            label="Primary Business Goal"
                            multiline
                            rows={3}
                            value={formData.businessGoal}
                            onChange={(e) => handleInputChange('businessGoal', e.target.value)}
                            error={!!errors.businessGoal}
                            helperText={errors.businessGoal || "Describe your primary business objective for this infrastructure assessment"}
                            placeholder="e.g., Reduce infrastructure costs by 30%, Scale to handle 10x user growth, Improve system reliability and uptime"
                        />

                        <FormControl>
                            <FormLabel>Geographic Regions (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['North America', 'Europe', 'Asia Pacific', 'Latin America', 'Middle East & Africa', 'Global', 'Other'].map((region) => (
                                    <FormControlLabel
                                        key={region}
                                        control={
                                            <Checkbox
                                                checked={formData.geographicRegions.includes(region)}
                                                onChange={(e) => handleArrayChange('geographicRegions', region, e.target.checked)}
                                            />
                                        }
                                        label={region}
                                    />
                                ))}
                            </FormGroup>
                            {formData.geographicRegions.includes('Other') && (
                                <TextField
                                    fullWidth
                                    label="Please specify other regions"
                                    value={formData.geographicRegionsOther}
                                    onChange={(e) => handleInputChange('geographicRegionsOther', e.target.value)}
                                    sx={{ mt: 2 }}
                                    size="small"
                                />
                            )}
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Customer Base Size</InputLabel>
                            <Select
                                value={formData.customerBase}
                                onChange={(e) => handleInputChange('customerBase', e.target.value)}
                                label="Customer Base Size"
                            >
                                <MenuItem value="small">Small (&lt; 1,000 users)</MenuItem>
                                <MenuItem value="medium">Medium (1,000 - 100,000 users)</MenuItem>
                                <MenuItem value="large">Large (100,000 - 1M users)</MenuItem>
                                <MenuItem value="enterprise">Enterprise (1M+ users)</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Revenue Model</InputLabel>
                            <Select
                                value={formData.revenueModel}
                                onChange={(e) => handleInputChange('revenueModel', e.target.value)}
                                label="Revenue Model"
                            >
                                <MenuItem value="subscription">Subscription/SaaS</MenuItem>
                                <MenuItem value="transaction">Transaction-based</MenuItem>
                                <MenuItem value="advertising">Advertising</MenuItem>
                                <MenuItem value="ecommerce">E-commerce</MenuItem>
                                <MenuItem value="licensing">Licensing</MenuItem>
                                <MenuItem value="consulting">Consulting/Services</MenuItem>
                                <MenuItem value="freemium">Freemium</MenuItem>
                                <MenuItem value="other">Other</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Growth Stage</InputLabel>
                            <Select
                                value={formData.growthStage}
                                onChange={(e) => handleInputChange('growthStage', e.target.value)}
                                label="Growth Stage"
                            >
                                <MenuItem value="pre-seed">Pre-seed</MenuItem>
                                <MenuItem value="seed">Seed</MenuItem>
                                <MenuItem value="series-a">Series A</MenuItem>
                                <MenuItem value="series-b">Series B+</MenuItem>
                                <MenuItem value="growth">Growth stage</MenuItem>
                                <MenuItem value="mature">Mature</MenuItem>
                                <MenuItem value="enterprise">Enterprise</MenuItem>
                            </Select>
                        </FormControl>

                        <TextField
                            fullWidth
                            label="Key Competitors"
                            value={formData.keyCompetitors}
                            onChange={(e) => handleInputChange('keyCompetitors', e.target.value)}
                            placeholder="e.g., Company A, Company B, Company C"
                            helperText="Help us understand your competitive landscape"
                        />

                        <FormControl>
                            <FormLabel>Mission-Critical Systems (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['Customer-facing applications', 'Payment processing', 'Data analytics', 'Real-time communications', 'Inventory management', 'User authentication', 'Content delivery', 'API services', 'Other'].map((system) => (
                                    <FormControlLabel
                                        key={system}
                                        control={
                                            <Checkbox
                                                checked={formData.missionCriticalSystems.includes(system)}
                                                onChange={(e) => handleArrayChange('missionCriticalSystems', system, e.target.checked)}
                                            />
                                        }
                                        label={system}
                                    />
                                ))}
                            </FormGroup>
                            {formData.missionCriticalSystems.includes('Other') && (
                                <TextField
                                    fullWidth
                                    label="Please specify other mission-critical systems"
                                    value={formData.missionCriticalSystemsOther || ''}
                                    onChange={(e) => handleInputChange('missionCriticalSystemsOther', e.target.value)}
                                    margin="normal"
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
                        <ErrorSummary step={1} />

                        <FormControl error={!!errors.currentCloudProvider}>
                            <FormLabel>Current Cloud Providers (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['AWS', 'Azure', 'Google Cloud', 'IBM Cloud', 'Alibaba Cloud', 'On-premises', 'Other'].map((provider) => (
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

                        <FormControl fullWidth>
                            <InputLabel>Infrastructure Age</InputLabel>
                            <Select
                                value={formData.infrastructureAge}
                                onChange={(e) => handleInputChange('infrastructureAge', e.target.value)}
                                label="Infrastructure Age"
                            >
                                <MenuItem value="new">Less than 1 year</MenuItem>
                                <MenuItem value="recent">1-3 years</MenuItem>
                                <MenuItem value="established">3-5 years</MenuItem>
                                <MenuItem value="legacy">5+ years</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Current Architecture Pattern</InputLabel>
                            <Select
                                value={formData.currentArchitecture}
                                onChange={(e) => handleInputChange('currentArchitecture', e.target.value)}
                                label="Current Architecture Pattern"
                            >
                                <MenuItem value="monolithic">Monolithic</MenuItem>
                                <MenuItem value="microservices">Microservices</MenuItem>
                                <MenuItem value="serverless">Serverless</MenuItem>
                                <MenuItem value="hybrid">Hybrid</MenuItem>
                                <MenuItem value="soa">Service-Oriented Architecture (SOA)</MenuItem>
                                <MenuItem value="other">Other</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl>
                            <FormLabel>Data Storage Solutions (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['Relational databases (MySQL, PostgreSQL)', 'NoSQL databases (MongoDB, DynamoDB)', 'Data warehouses (Snowflake, BigQuery)', 'Object storage (S3, Blob)', 'File systems', 'Cache systems (Redis, Memcached)', 'Time-series databases', 'Graph databases', 'Other'].map((storage) => (
                                    <FormControlLabel
                                        key={storage}
                                        control={
                                            <Checkbox
                                                checked={formData.dataStorageSolution.includes(storage)}
                                                onChange={(e) => handleArrayChange('dataStorageSolution', storage, e.target.checked)}
                                            />
                                        }
                                        label={storage}
                                    />
                                ))}
                            </FormGroup>
                            {formData.dataStorageSolution.includes('Other') && (
                                <TextField
                                    fullWidth
                                    label="Please specify other data storage solutions"
                                    value={formData.dataStorageSolutionOther || ''}
                                    onChange={(e) => handleInputChange('dataStorageSolutionOther', e.target.value)}
                                    margin="normal"
                                />
                            )}
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Network Setup</InputLabel>
                            <Select
                                value={formData.networkSetup}
                                onChange={(e) => handleInputChange('networkSetup', e.target.value)}
                                label="Network Setup"
                            >
                                <MenuItem value="public-cloud">Public cloud default</MenuItem>
                                <MenuItem value="vpc">Virtual Private Cloud (VPC)</MenuItem>
                                <MenuItem value="hybrid">Hybrid (on-premise + cloud)</MenuItem>
                                <MenuItem value="multi-cloud">Multi-cloud</MenuItem>
                                <MenuItem value="on-premise">On-premise only</MenuItem>
                                <MenuItem value="edge">Edge computing</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Disaster Recovery Setup</InputLabel>
                            <Select
                                value={formData.disasterRecoverySetup}
                                onChange={(e) => handleInputChange('disasterRecoverySetup', e.target.value)}
                                label="Disaster Recovery Setup"
                            >
                                <MenuItem value="none">No formal DR plan</MenuItem>
                                <MenuItem value="basic">Basic backups</MenuItem>
                                <MenuItem value="automated">Automated backups & recovery</MenuItem>
                                <MenuItem value="multi-region">Multi-region failover</MenuItem>
                                <MenuItem value="active-active">Active-active setup</MenuItem>
                                <MenuItem value="comprehensive">Comprehensive DR strategy</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl>
                            <FormLabel>Current Monitoring Tools (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['CloudWatch', 'Datadog', 'New Relic', 'Splunk', 'Grafana', 'Prometheus', 'ELK Stack', 'Application Insights', 'Custom solutions', 'None', 'Other'].map((tool) => (
                                    <FormControlLabel
                                        key={tool}
                                        control={
                                            <Checkbox
                                                checked={formData.monitoringTools.includes(tool)}
                                                onChange={(e) => handleArrayChange('monitoringTools', tool, e.target.checked)}
                                            />
                                        }
                                        label={tool}
                                    />
                                ))}
                            </FormGroup>
                            {formData.monitoringTools.includes('Other') && (
                                <TextField
                                    fullWidth
                                    label="Please specify other monitoring tools"
                                    value={formData.monitoringToolsOther || ''}
                                    onChange={(e) => handleInputChange('monitoringToolsOther', e.target.value)}
                                    margin="normal"
                                />
                            )}
                        </FormControl>
                    </Box>
                );

            case 2:
                return (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Technical Architecture Details
                        </Typography>
                        <ErrorSummary step={2} />

                        <FormControl>
                            <FormLabel>Application Types (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['Web applications', 'Mobile apps', 'APIs/Microservices', 'Desktop applications', 'IoT applications', 'Real-time systems', 'Batch processing', 'Data pipelines', 'Machine learning models', 'Other'].map((appType) => (
                                    <FormControlLabel
                                        key={appType}
                                        control={
                                            <Checkbox
                                                checked={formData.applicationTypes.includes(appType)}
                                                onChange={(e) => handleArrayChange('applicationTypes', appType, e.target.checked)}
                                            />
                                        }
                                        label={appType}
                                    />
                                ))}
                            </FormGroup>
                            {formData.applicationTypes.includes('Other') && (
                                <TextField
                                    fullWidth
                                    label="Please specify other application types"
                                    value={formData.applicationTypesOther}
                                    onChange={(e) => handleInputChange('applicationTypesOther', e.target.value)}
                                    sx={{ mt: 2 }}
                                    size="small"
                                />
                            )}
                        </FormControl>

                        <FormControl>
                            <FormLabel>Development Frameworks (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['React/Angular/Vue', 'Node.js', 'Django/Flask', 'Spring Boot', 'ASP.NET', 'Ruby on Rails', 'Express.js', 'FastAPI', 'Laravel', 'Next.js', 'Other'].map((framework) => (
                                    <FormControlLabel
                                        key={framework}
                                        control={
                                            <Checkbox
                                                checked={formData.developmentFrameworks.includes(framework)}
                                                onChange={(e) => handleArrayChange('developmentFrameworks', framework, e.target.checked)}
                                            />
                                        }
                                        label={framework}
                                    />
                                ))}
                            </FormGroup>
                            {formData.developmentFrameworks.includes('Other') && (
                                <TextField
                                    fullWidth
                                    label="Please specify other frameworks"
                                    value={formData.developmentFrameworksOther}
                                    onChange={(e) => handleInputChange('developmentFrameworksOther', e.target.value)}
                                    sx={{ mt: 2 }}
                                    size="small"
                                />
                            )}
                        </FormControl>

                        <FormControl>
                            <FormLabel>Programming Languages (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['Python', 'JavaScript/TypeScript', 'Java', 'C#', 'Go', 'Rust', 'PHP', 'Ruby', 'C/C++', 'Scala', 'R', 'Other'].map((language) => (
                                    <FormControlLabel
                                        key={language}
                                        control={
                                            <Checkbox
                                                checked={formData.programmingLanguages.includes(language)}
                                                onChange={(e) => handleArrayChange('programmingLanguages', language, e.target.checked)}
                                            />
                                        }
                                        label={language}
                                    />
                                ))}
                            </FormGroup>
                        </FormControl>

                        <FormControl>
                            <FormLabel>Database Types (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch', 'DynamoDB', 'Cassandra', 'Neo4j', 'InfluxDB', 'BigQuery', 'Snowflake', 'Other'].map((db) => (
                                    <FormControlLabel
                                        key={db}
                                        control={
                                            <Checkbox
                                                checked={formData.databaseTypes.includes(db)}
                                                onChange={(e) => handleArrayChange('databaseTypes', db, e.target.checked)}
                                            />
                                        }
                                        label={db}
                                    />
                                ))}
                            </FormGroup>
                            {formData.databaseTypes.includes('Other') && (
                                <TextField
                                    fullWidth
                                    label="Please specify other database types"
                                    value={formData.databaseTypesOther}
                                    onChange={(e) => handleInputChange('databaseTypesOther', e.target.value)}
                                    sx={{ mt: 2 }}
                                    size="small"
                                />
                            )}
                        </FormControl>

                        <FormControl>
                            <FormLabel>Integration Patterns (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['REST APIs', 'GraphQL', 'WebSockets', 'Message queues', 'Event streaming', 'Service mesh', 'API Gateway', 'Webhooks', 'Database replication', 'ETL/ELT', 'Other'].map((pattern) => (
                                    <FormControlLabel
                                        key={pattern}
                                        control={
                                            <Checkbox
                                                checked={formData.integrationPatterns.includes(pattern)}
                                                onChange={(e) => handleArrayChange('integrationPatterns', pattern, e.target.checked)}
                                            />
                                        }
                                        label={pattern}
                                    />
                                ))}
                            </FormGroup>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Deployment Strategy</InputLabel>
                            <Select
                                value={formData.deploymentStrategy}
                                onChange={(e) => handleInputChange('deploymentStrategy', e.target.value)}
                                label="Deployment Strategy"
                            >
                                <MenuItem value="manual">Manual deployment</MenuItem>
                                <MenuItem value="basic-cicd">Basic CI/CD</MenuItem>
                                <MenuItem value="advanced-cicd">Advanced CI/CD with testing</MenuItem>
                                <MenuItem value="blue-green">Blue-green deployment</MenuItem>
                                <MenuItem value="canary">Canary deployment</MenuItem>
                                <MenuItem value="rolling">Rolling deployment</MenuItem>
                                <MenuItem value="gitops">GitOps</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Containerization</InputLabel>
                            <Select
                                value={formData.containerization}
                                onChange={(e) => handleInputChange('containerization', e.target.value)}
                                label="Containerization"
                            >
                                <MenuItem value="none">No containerization</MenuItem>
                                <MenuItem value="docker">Docker only</MenuItem>
                                <MenuItem value="docker-compose">Docker Compose</MenuItem>
                                <MenuItem value="kubernetes">Kubernetes</MenuItem>
                                <MenuItem value="managed-k8s">Managed Kubernetes (EKS, GKE, AKS)</MenuItem>
                                <MenuItem value="serverless">Serverless containers</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Orchestration Platform</InputLabel>
                            <Select
                                value={formData.orchestrationPlatform}
                                onChange={(e) => handleInputChange('orchestrationPlatform', e.target.value)}
                                label="Orchestration Platform"
                            >
                                <MenuItem value="none">None</MenuItem>
                                <MenuItem value="kubernetes">Kubernetes</MenuItem>
                                <MenuItem value="docker-swarm">Docker Swarm</MenuItem>
                                <MenuItem value="ecs">Amazon ECS</MenuItem>
                                <MenuItem value="fargate">AWS Fargate</MenuItem>
                                <MenuItem value="cloud-run">Google Cloud Run</MenuItem>
                                <MenuItem value="container-instances">Azure Container Instances</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl>
                            <FormLabel>CI/CD Tools (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['GitHub Actions', 'GitLab CI', 'Jenkins', 'CircleCI', 'Travis CI', 'Azure DevOps', 'AWS CodePipeline', 'Google Cloud Build', 'TeamCity', 'Bamboo', 'None', 'Other'].map((tool) => (
                                    <FormControlLabel
                                        key={tool}
                                        control={
                                            <Checkbox
                                                checked={formData.cicdTools.includes(tool)}
                                                onChange={(e) => handleArrayChange('cicdTools', tool, e.target.checked)}
                                            />
                                        }
                                        label={tool}
                                    />
                                ))}
                            </FormGroup>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Version Control System</InputLabel>
                            <Select
                                value={formData.versionControlSystem}
                                onChange={(e) => handleInputChange('versionControlSystem', e.target.value)}
                                label="Version Control System"
                            >
                                <MenuItem value="git">Git (GitHub/GitLab/Bitbucket)</MenuItem>
                                <MenuItem value="svn">Subversion (SVN)</MenuItem>
                                <MenuItem value="mercurial">Mercurial</MenuItem>
                                <MenuItem value="other">Other</MenuItem>
                            </Select>
                        </FormControl>
                    </Box>
                );

            case 3:
                return (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            AI Requirements & Use Cases
                        </Typography>
                        <ErrorSummary step={3} />

                        <FormControl error={!!errors.aiUseCases}>
                            <FormLabel>AI Use Cases (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['Natural Language Processing', 'Computer Vision', 'Machine Learning Models', 'Predictive Analytics', 'Recommendation Systems', 'Fraud Detection', 'Chatbots/Virtual Assistants', 'Data Analytics', 'Automation', 'Other'].map((useCase) => (
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
                                <MenuItem value="1TB">Up to 1TB</MenuItem>
                                <MenuItem value="10TB">1TB - 10TB</MenuItem>
                                <MenuItem value="100TB">10TB - 100TB</MenuItem>
                                <MenuItem value="500TB">100TB - 500TB</MenuItem>
                                <MenuItem value="1PB+">500TB - 1PB+</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl>
                            <FormLabel>Data Types (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['Text', 'Images', 'Videos', 'Audio', 'Time Series', 'User Behavior', 'Financial Data', 'IoT Sensor Data', 'Geospatial Data', 'Other'].map((dataType) => (
                                    <FormControlLabel
                                        key={dataType}
                                        control={
                                            <Checkbox
                                                checked={formData.dataTypes.includes(dataType)}
                                                onChange={(e) => handleArrayChange('dataTypes', dataType, e.target.checked)}
                                            />
                                        }
                                        label={dataType}
                                    />
                                ))}
                            </FormGroup>
                            {formData.dataTypes.includes('Other') && (
                                <TextField
                                    fullWidth
                                    label="Please specify other data types"
                                    value={formData.dataTypesOther}
                                    onChange={(e) => handleInputChange('dataTypesOther', e.target.value)}
                                    sx={{ mt: 2 }}
                                    size="small"
                                />
                            )}
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Real-time Requirements</InputLabel>
                            <Select
                                value={formData.realTimeRequirements}
                                onChange={(e) => handleInputChange('realTimeRequirements', e.target.value)}
                                label="Real-time Requirements"
                            >
                                <MenuItem value="batch">Batch processing only</MenuItem>
                                <MenuItem value="near_real_time">Near real-time (seconds)</MenuItem>
                                <MenuItem value="real_time">Real-time (milliseconds)</MenuItem>
                                <MenuItem value="ultra_low_latency">Ultra low latency (microseconds)</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl>
                            <FormLabel>ML Model Types (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['Large Language Models', 'Computer Vision Models', 'Time Series Models', 'Recommendation Engines', 'Classification Models', 'Regression Models', 'Clustering Models', 'Deep Learning', 'Traditional ML', 'Other'].map((modelType) => (
                                    <FormControlLabel
                                        key={modelType}
                                        control={
                                            <Checkbox
                                                checked={formData.mlModelTypes.includes(modelType)}
                                                onChange={(e) => handleArrayChange('mlModelTypes', modelType, e.target.checked)}
                                            />
                                        }
                                        label={modelType}
                                    />
                                ))}
                            </FormGroup>
                            {formData.mlModelTypes.includes('Other') && (
                                <TextField
                                    fullWidth
                                    label="Please specify other ML model types"
                                    value={formData.mlModelTypesOther}
                                    onChange={(e) => handleInputChange('mlModelTypesOther', e.target.value)}
                                    sx={{ mt: 2 }}
                                    size="small"
                                />
                            )}
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Training Frequency</InputLabel>
                            <Select
                                value={formData.trainingFrequency}
                                onChange={(e) => handleInputChange('trainingFrequency', e.target.value)}
                                label="Training Frequency"
                            >
                                <MenuItem value="hourly">Hourly</MenuItem>
                                <MenuItem value="daily">Daily</MenuItem>
                                <MenuItem value="weekly">Weekly</MenuItem>
                                <MenuItem value="monthly">Monthly</MenuItem>
                                <MenuItem value="quarterly">Quarterly</MenuItem>
                                <MenuItem value="on_demand">On-demand</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Inference Volume</InputLabel>
                            <Select
                                value={formData.inferenceVolume}
                                onChange={(e) => handleInputChange('inferenceVolume', e.target.value)}
                                label="Inference Volume"
                            >
                                <MenuItem value="100_per_day">Up to 100 requests/day</MenuItem>
                                <MenuItem value="1K_per_day">100 - 1K requests/day</MenuItem>
                                <MenuItem value="10K_per_day">1K - 10K requests/day</MenuItem>
                                <MenuItem value="100K_per_day">10K - 100K requests/day</MenuItem>
                                <MenuItem value="1M_per_day">100K - 1M requests/day</MenuItem>
                                <MenuItem value="10M_per_day">1M+ requests/day</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl>
                            <FormLabel>Data Processing Needs (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['ETL Pipelines', 'Real-time Streaming', 'Feature Engineering', 'Data Validation', 'Model Monitoring', 'A/B Testing', 'Data Lineage', 'Data Quality Checks', 'Other'].map((processing) => (
                                    <FormControlLabel
                                        key={processing}
                                        control={
                                            <Checkbox
                                                checked={formData.dataProcessingNeeds.includes(processing)}
                                                onChange={(e) => handleArrayChange('dataProcessingNeeds', processing, e.target.checked)}
                                            />
                                        }
                                        label={processing}
                                    />
                                ))}
                            </FormGroup>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>AI Integration Complexity</InputLabel>
                            <Select
                                value={formData.aiIntegrationComplexity}
                                onChange={(e) => handleInputChange('aiIntegrationComplexity', e.target.value)}
                                label="AI Integration Complexity"
                            >
                                <MenuItem value="simple">Simple (few models, basic integration)</MenuItem>
                                <MenuItem value="moderate">Moderate (multiple models, some dependencies)</MenuItem>
                                <MenuItem value="complex">Complex (many models, complex workflows)</MenuItem>
                                <MenuItem value="very_complex">Very Complex (enterprise-scale, critical systems)</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl>
                            <FormLabel>Existing ML Infrastructure (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['Kubeflow', 'MLflow', 'TensorFlow Serving', 'PyTorch Serve', 'SageMaker', 'Azure ML', 'Google AI Platform', 'Databricks', 'Apache Airflow', 'None', 'Other'].map((infrastructure) => (
                                    <FormControlLabel
                                        key={infrastructure}
                                        control={
                                            <Checkbox
                                                checked={formData.existingMLInfrastructure.includes(infrastructure)}
                                                onChange={(e) => handleArrayChange('existingMLInfrastructure', infrastructure, e.target.checked)}
                                            />
                                        }
                                        label={infrastructure}
                                    />
                                ))}
                            </FormGroup>
                        </FormControl>
                    </Box>
                );

            case 4:
                return (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Performance & Scalability Requirements
                        </Typography>
                        <ErrorSummary step={4} />

                        <TextField
                            fullWidth
                            label="Current User Load"
                            value={formData.currentUserLoad}
                            onChange={(e) => handleInputChange('currentUserLoad', e.target.value)}
                            placeholder="e.g., 1000 concurrent users, 50K daily active users"
                            helperText="Describe your current user load and traffic patterns"
                        />

                        <TextField
                            fullWidth
                            label="Peak Traffic Patterns"
                            value={formData.peakTrafficPatterns}
                            onChange={(e) => handleInputChange('peakTrafficPatterns', e.target.value)}
                            placeholder="e.g., 3x during business hours, 10x during product launches"
                            helperText="How does your traffic vary throughout the day/year?"
                        />

                        <FormControl fullWidth>
                            <InputLabel>Expected Growth Rate</InputLabel>
                            <Select
                                value={formData.expectedGrowthRate}
                                onChange={(e) => handleInputChange('expectedGrowthRate', e.target.value)}
                                label="Expected Growth Rate"
                            >
                                <MenuItem value="25%_annually">25% annually</MenuItem>
                                <MenuItem value="50%_annually">50% annually</MenuItem>
                                <MenuItem value="100%_annually">100% annually</MenuItem>
                                <MenuItem value="200%_annually">200% annually</MenuItem>
                                <MenuItem value="500%_annually">500%+ annually</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Response Time Requirements</InputLabel>
                            <Select
                                value={formData.responseTimeRequirements}
                                onChange={(e) => handleInputChange('responseTimeRequirements', e.target.value)}
                                label="Response Time Requirements"
                            >
                                <MenuItem value="sub_50ms">Sub-50ms</MenuItem>
                                <MenuItem value="sub_100ms">Sub-100ms</MenuItem>
                                <MenuItem value="sub_200ms">Sub-200ms</MenuItem>
                                <MenuItem value="sub_500ms">Sub-500ms</MenuItem>
                                <MenuItem value="sub_1s">Sub-1 second</MenuItem>
                                <MenuItem value="over_1s">Over 1 second acceptable</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Availability Requirements</InputLabel>
                            <Select
                                value={formData.availabilityRequirements}
                                onChange={(e) => handleInputChange('availabilityRequirements', e.target.value)}
                                label="Availability Requirements"
                            >
                                <MenuItem value="99%">99% (8.76 hours downtime/year)</MenuItem>
                                <MenuItem value="99.9%">99.9% (52.6 minutes downtime/year)</MenuItem>
                                <MenuItem value="99.95%">99.95% (26.3 minutes downtime/year)</MenuItem>
                                <MenuItem value="99.99%">99.99% (5.26 minutes downtime/year)</MenuItem>
                                <MenuItem value="99.999%">99.999% (31.5 seconds downtime/year)</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Global Distribution</InputLabel>
                            <Select
                                value={formData.globalDistribution}
                                onChange={(e) => handleInputChange('globalDistribution', e.target.value)}
                                label="Global Distribution"
                            >
                                <MenuItem value="single_region">Single region</MenuItem>
                                <MenuItem value="multi_region">Multi-region</MenuItem>
                                <MenuItem value="global_cdn">Global CDN</MenuItem>
                                <MenuItem value="edge_computing">Edge computing</MenuItem>
                                <MenuItem value="active_active">Active-active global</MenuItem>
                            </Select>
                        </FormControl>

                        <TextField
                            fullWidth
                            label="Load Patterns"
                            value={formData.loadPatterns}
                            onChange={(e) => handleInputChange('loadPatterns', e.target.value)}
                            placeholder="e.g., Predictable daily peaks, Seasonal spikes, Viral content bursts"
                            helperText="Describe your typical load patterns and characteristics"
                        />

                        <TextField
                            fullWidth
                            label="Failover Requirements"
                            value={formData.failoverRequirements}
                            onChange={(e) => handleInputChange('failoverRequirements', e.target.value)}
                            placeholder="e.g., Automatic failover within 30 seconds, Manual failover acceptable"
                            helperText="What are your requirements for system failover and recovery?"
                        />

                        <FormControl>
                            <FormLabel>Auto-scaling Triggers (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['CPU utilization &gt; 70%', 'Memory utilization &gt; 80%', 'Response time &gt; 200ms', 'Queue depth &gt; 100', 'Error rate &gt; 1%', 'Custom metrics', 'Manual scaling only'].map((trigger) => (
                                    <FormControlLabel
                                        key={trigger}
                                        control={
                                            <Checkbox
                                                checked={formData.scalingTriggers.includes(trigger)}
                                                onChange={(e) => handleArrayChange('scalingTriggers', trigger, e.target.checked)}
                                            />
                                        }
                                        label={trigger}
                                    />
                                ))}
                            </FormGroup>
                        </FormControl>
                    </Box>
                );

            case 5:
                return (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Security & Compliance Requirements
                        </Typography>
                        <ErrorSummary step={5} />

                        <FormControl>
                            <FormLabel>Compliance Requirements (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['GDPR', 'HIPAA', 'SOC 2', 'ISO 27001', 'PCI DSS', 'CCPA', 'FedRAMP', 'FISMA', 'Other'].map((compliance) => (
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

                        <FormControl>
                            <FormLabel>Data Classification (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['Public', 'Internal', 'Confidential', 'Restricted', 'PII (Personal Information)', 'PHI (Health Information)', 'Financial Data', 'Trade Secrets'].map((classification) => (
                                    <FormControlLabel
                                        key={classification}
                                        control={
                                            <Checkbox
                                                checked={formData.dataClassification.includes(classification)}
                                                onChange={(e) => handleArrayChange('dataClassification', classification, e.target.checked)}
                                            />
                                        }
                                        label={classification}
                                    />
                                ))}
                            </FormGroup>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Security Incident History</InputLabel>
                            <Select
                                value={formData.securityIncidentHistory}
                                onChange={(e) => handleInputChange('securityIncidentHistory', e.target.value)}
                                label="Security Incident History"
                            >
                                <MenuItem value="none">No security incidents</MenuItem>
                                <MenuItem value="minor">Minor incidents (resolved quickly)</MenuItem>
                                <MenuItem value="moderate">Moderate incidents (some impact)</MenuItem>
                                <MenuItem value="major">Major incidents (significant impact)</MenuItem>
                                <MenuItem value="prefer_not_to_say">Prefer not to say</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl>
                            <FormLabel>Access Control Requirements (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['Role-Based Access Control (RBAC)', 'Attribute-Based Access Control (ABAC)', 'Multi-Factor Authentication (MFA)', 'Single Sign-On (SSO)', 'Zero Trust Architecture', 'Privileged Access Management', 'Just-in-Time Access', 'Audit Logging'].map((accessControl) => (
                                    <FormControlLabel
                                        key={accessControl}
                                        control={
                                            <Checkbox
                                                checked={formData.accessControlRequirements.includes(accessControl)}
                                                onChange={(e) => handleArrayChange('accessControlRequirements', accessControl, e.target.checked)}
                                            />
                                        }
                                        label={accessControl}
                                    />
                                ))}
                            </FormGroup>
                        </FormControl>

                        <FormControl>
                            <FormLabel>Encryption Requirements (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['AES-256 encryption', 'TLS 1.3', 'End-to-end encryption', 'Field-level encryption', 'Key management service', 'Hardware security modules', 'Certificate management', 'Encryption at rest', 'Encryption in transit'].map((encryption) => (
                                    <FormControlLabel
                                        key={encryption}
                                        control={
                                            <Checkbox
                                                checked={formData.encryptionRequirements.includes(encryption)}
                                                onChange={(e) => handleArrayChange('encryptionRequirements', encryption, e.target.checked)}
                                            />
                                        }
                                        label={encryption}
                                    />
                                ))}
                            </FormGroup>
                        </FormControl>

                        <FormControl>
                            <FormLabel>Security Monitoring (Select all that apply)</FormLabel>
                            <FormGroup>
                                {['SIEM (Security Information and Event Management)', 'EDR (Endpoint Detection and Response)', 'UEBA (User and Entity Behavior Analytics)', 'Threat Intelligence', 'Network Monitoring', 'Application Security Monitoring', 'Cloud Security Posture Management', 'Container Security'].map((monitoring) => (
                                    <FormControlLabel
                                        key={monitoring}
                                        control={
                                            <Checkbox
                                                checked={formData.securityMonitoring.includes(monitoring)}
                                                onChange={(e) => handleArrayChange('securityMonitoring', monitoring, e.target.checked)}
                                            />
                                        }
                                        label={monitoring}
                                    />
                                ))}
                            </FormGroup>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Vulnerability Management</InputLabel>
                            <Select
                                value={formData.vulnerabilityManagement}
                                onChange={(e) => handleInputChange('vulnerabilityManagement', e.target.value)}
                                label="Vulnerability Management"
                            >
                                <MenuItem value="manual_quarterly">Manual quarterly scans</MenuItem>
                                <MenuItem value="automated_monthly">Automated monthly scans</MenuItem>
                                <MenuItem value="automated_weekly">Automated weekly scans</MenuItem>
                                <MenuItem value="continuous_scanning">Continuous vulnerability scanning</MenuItem>
                                <MenuItem value="real_time_monitoring">Real-time threat monitoring</MenuItem>
                            </Select>
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
                    </Box>
                );

            case 6:
                return (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Budget & Timeline Planning
                        </Typography>
                        <ErrorSummary step={6} />

                        <FormControl fullWidth>
                            <InputLabel>Budget Flexibility</InputLabel>
                            <Select
                                value={formData.budgetFlexibility}
                                onChange={(e) => handleInputChange('budgetFlexibility', e.target.value)}
                                label="Budget Flexibility"
                            >
                                <MenuItem value="strict">Strict budget limits</MenuItem>
                                <MenuItem value="moderate">Moderate flexibility</MenuItem>
                                <MenuItem value="flexible">Flexible within range</MenuItem>
                                <MenuItem value="very_flexible">Very flexible for right solution</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Cost Optimization Priority</InputLabel>
                            <Select
                                value={formData.costOptimizationPriority}
                                onChange={(e) => handleInputChange('costOptimizationPriority', e.target.value)}
                                label="Cost Optimization Priority"
                            >
                                <MenuItem value="very_high">Very High - Cost is primary concern</MenuItem>
                                <MenuItem value="high">High - Cost is important</MenuItem>
                                <MenuItem value="medium">Medium - Balance cost and performance</MenuItem>
                                <MenuItem value="low">Low - Performance over cost</MenuItem>
                                <MenuItem value="minimal">Minimal - Best solution regardless of cost</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Total Budget Range</InputLabel>
                            <Select
                                value={formData.totalBudgetRange}
                                onChange={(e) => handleInputChange('totalBudgetRange', e.target.value)}
                                label="Total Budget Range"
                            >
                                <MenuItem value="under_50k">Under $50K</MenuItem>
                                <MenuItem value="50k_100k">$50K - $100K</MenuItem>
                                <MenuItem value="100k_250k">$100K - $250K</MenuItem>
                                <MenuItem value="250k_500k">$250K - $500K</MenuItem>
                                <MenuItem value="500k_1m">$500K - $1M</MenuItem>
                                <MenuItem value="1m_5m">$1M - $5M</MenuItem>
                                <MenuItem value="over_5m">Over $5M</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Migration Budget</InputLabel>
                            <Select
                                value={formData.migrationBudget}
                                onChange={(e) => handleInputChange('migrationBudget', e.target.value)}
                                label="Migration Budget"
                            >
                                <MenuItem value="under_25k">Under $25K</MenuItem>
                                <MenuItem value="25k_50k">$25K - $50K</MenuItem>
                                <MenuItem value="50k_100k">$50K - $100K</MenuItem>
                                <MenuItem value="100k_250k">$100K - $250K</MenuItem>
                                <MenuItem value="250k_500k">$250K - $500K</MenuItem>
                                <MenuItem value="over_500k">Over $500K</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Operational vs Infrastructure Budget Split</InputLabel>
                            <Select
                                value={formData.operationalBudgetSplit}
                                onChange={(e) => handleInputChange('operationalBudgetSplit', e.target.value)}
                                label="Operational vs Infrastructure Budget Split"
                            >
                                <MenuItem value="90_10">90% Infrastructure / 10% Operations</MenuItem>
                                <MenuItem value="80_20">80% Infrastructure / 20% Operations</MenuItem>
                                <MenuItem value="70_30">70% Infrastructure / 30% Operations</MenuItem>
                                <MenuItem value="60_40">60% Infrastructure / 40% Operations</MenuItem>
                                <MenuItem value="50_50">50% Infrastructure / 50% Operations</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>ROI Expectations</InputLabel>
                            <Select
                                value={formData.roiExpectations}
                                onChange={(e) => handleInputChange('roiExpectations', e.target.value)}
                                label="ROI Expectations"
                            >
                                <MenuItem value="break_even_1_year">Break even within 1 year</MenuItem>
                                <MenuItem value="positive_roi_6_months">Positive ROI within 6 months</MenuItem>
                                <MenuItem value="positive_roi_12_months">Positive ROI within 12 months</MenuItem>
                                <MenuItem value="positive_roi_18_months">Positive ROI within 18 months</MenuItem>
                                <MenuItem value="positive_roi_24_months">Positive ROI within 24 months</MenuItem>
                                <MenuItem value="long_term_investment">Long-term strategic investment</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Preferred Payment Model</InputLabel>
                            <Select
                                value={formData.paymentModel}
                                onChange={(e) => handleInputChange('paymentModel', e.target.value)}
                                label="Preferred Payment Model"
                            >
                                <MenuItem value="pay_as_you_go">Pay-as-you-go</MenuItem>
                                <MenuItem value="reserved_instances">Reserved instances</MenuItem>
                                <MenuItem value="spot_instances">Spot instances for cost savings</MenuItem>
                                <MenuItem value="committed_use">Committed use discounts</MenuItem>
                                <MenuItem value="hybrid_model">Hybrid pricing model</MenuItem>
                                <MenuItem value="enterprise_agreement">Enterprise agreement</MenuItem>
                            </Select>
                        </FormControl>

                        <FormControl fullWidth>
                            <InputLabel>Implementation Timeline</InputLabel>
                            <Select
                                value={formData.scalingTimeline}
                                onChange={(e) => handleInputChange('scalingTimeline', e.target.value)}
                                label="Implementation Timeline"
                            >
                                <MenuItem value="immediate">Immediate (0-1 months)</MenuItem>
                                <MenuItem value="short">Short term (1-3 months)</MenuItem>
                                <MenuItem value="medium">Medium term (3-6 months)</MenuItem>
                                <MenuItem value="long">Long term (6-12 months)</MenuItem>
                                <MenuItem value="very_long">Extended (12+ months)</MenuItem>
                            </Select>
                        </FormControl>
                    </Box>
                );

            case 7:
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
                                <Chip label={`Customer Base: ${formData.customerBase}`} />
                                <Chip label={`Revenue Model: ${formData.revenueModel}`} />
                                <Chip label={`Growth Stage: ${formData.growthStage}`} />
                            </Box>
                            {formData.geographicRegions.length > 0 && (
                                <Box sx={{ mb: 1 }}>
                                    <Typography variant="body2" color="text.secondary">Geographic Regions:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.geographicRegions.map(region => (
                                            <Chip key={region} label={region} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                            {formData.missionCriticalSystems.length > 0 && (
                                <Box>
                                    <Typography variant="body2" color="text.secondary">Mission-Critical Systems:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.missionCriticalSystems.map(system => (
                                            <Chip key={system} label={system} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                        </Paper>

                        <Paper sx={{ p: 2 }}>
                            <Typography variant="subtitle1" gutterBottom>Current Infrastructure</Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                                <Chip label={`Monthly Budget: ${formData.monthlyBudget}`} />
                                <Chip label={`Team Size: ${formData.technicalTeamSize}`} />
                                <Chip label={`Infrastructure Age: ${formData.infrastructureAge}`} />
                                <Chip label={`Architecture: ${formData.currentArchitecture}`} />
                                <Chip label={`Network Setup: ${formData.networkSetup}`} />
                                <Chip label={`Disaster Recovery: ${formData.disasterRecoverySetup}`} />
                            </Box>
                            {formData.currentCloudProvider.length > 0 && (
                                <Box sx={{ mb: 1 }}>
                                    <Typography variant="body2" color="text.secondary">Cloud Providers:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.currentCloudProvider.map(provider => (
                                            <Chip key={provider} label={provider} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                            {formData.currentServices.length > 0 && (
                                <Box sx={{ mb: 1 }}>
                                    <Typography variant="body2" color="text.secondary">Current Services:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.currentServices.map(service => (
                                            <Chip key={service} label={service} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                            {formData.dataStorageSolution.length > 0 && (
                                <Box sx={{ mb: 1 }}>
                                    <Typography variant="body2" color="text.secondary">Data Storage:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.dataStorageSolution.map(storage => (
                                            <Chip key={storage} label={storage} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                            {formData.monitoringTools.length > 0 && (
                                <Box>
                                    <Typography variant="body2" color="text.secondary">Monitoring Tools:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.monitoringTools.map(tool => (
                                            <Chip key={tool} label={tool} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                        </Paper>

                        <Paper sx={{ p: 2 }}>
                            <Typography variant="subtitle1" gutterBottom>Technical Architecture</Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                                <Chip label={`Deployment Strategy: ${formData.deploymentStrategy}`} />
                                <Chip label={`Containerization: ${formData.containerization}`} />
                                <Chip label={`Orchestration: ${formData.orchestrationPlatform}`} />
                                <Chip label={`Version Control: ${formData.versionControlSystem}`} />
                            </Box>
                            {formData.applicationTypes.length > 0 && (
                                <Box sx={{ mb: 1 }}>
                                    <Typography variant="body2" color="text.secondary">Application Types:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.applicationTypes.map(app => (
                                            <Chip key={app} label={app} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                            {formData.developmentFrameworks.length > 0 && (
                                <Box sx={{ mb: 1 }}>
                                    <Typography variant="body2" color="text.secondary">Development Frameworks:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.developmentFrameworks.map(framework => (
                                            <Chip key={framework} label={framework} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                            {formData.programmingLanguages.length > 0 && (
                                <Box sx={{ mb: 1 }}>
                                    <Typography variant="body2" color="text.secondary">Programming Languages:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.programmingLanguages.map(lang => (
                                            <Chip key={lang} label={lang} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                            {formData.databaseTypes.length > 0 && (
                                <Box sx={{ mb: 1 }}>
                                    <Typography variant="body2" color="text.secondary">Database Types:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.databaseTypes.map(db => (
                                            <Chip key={db} label={db} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                            {formData.integrationPatterns.length > 0 && (
                                <Box sx={{ mb: 1 }}>
                                    <Typography variant="body2" color="text.secondary">Integration Patterns:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.integrationPatterns.map(pattern => (
                                            <Chip key={pattern} label={pattern} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                            {formData.cicdTools.length > 0 && (
                                <Box>
                                    <Typography variant="body2" color="text.secondary">CI/CD Tools:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.cicdTools.map(tool => (
                                            <Chip key={tool} label={tool} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                        </Paper>

                        <Paper sx={{ p: 2 }}>
                            <Typography variant="subtitle1" gutterBottom>AI Requirements & Use Cases</Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                                <Chip label={`Data Volume: ${formData.expectedDataVolume}`} />
                                <Chip label={`Real-time Requirements: ${formData.realTimeRequirements}`} />
                                <Chip label={`Training Frequency: ${formData.trainingFrequency}`} />
                                <Chip label={`Inference Volume: ${formData.inferenceVolume}`} />
                                <Chip label={`AI Integration Complexity: ${formData.aiIntegrationComplexity}`} />
                            </Box>
                            {formData.aiUseCases.length > 0 && (
                                <Box sx={{ mb: 1 }}>
                                    <Typography variant="body2" color="text.secondary">AI Use Cases:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.aiUseCases.map(useCase => (
                                            <Chip key={useCase} label={useCase} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                            {formData.dataTypes.length > 0 && (
                                <Box sx={{ mb: 1 }}>
                                    <Typography variant="body2" color="text.secondary">Data Types:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.dataTypes.map(type => (
                                            <Chip key={type} label={type} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                            {formData.mlModelTypes.length > 0 && (
                                <Box sx={{ mb: 1 }}>
                                    <Typography variant="body2" color="text.secondary">ML Model Types:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.mlModelTypes.map(model => (
                                            <Chip key={model} label={model} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                            {formData.dataProcessingNeeds.length > 0 && (
                                <Box sx={{ mb: 1 }}>
                                    <Typography variant="body2" color="text.secondary">Data Processing Needs:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.dataProcessingNeeds.map(need => (
                                            <Chip key={need} label={need} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                            {formData.existingMLInfrastructure.length > 0 && (
                                <Box>
                                    <Typography variant="body2" color="text.secondary">Existing ML Infrastructure:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.existingMLInfrastructure.map(infra => (
                                            <Chip key={infra} label={infra} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                        </Paper>

                        <Paper sx={{ p: 2 }}>
                            <Typography variant="subtitle1" gutterBottom>Performance & Scalability</Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                                <Chip label={`Performance Req: ${formData.performanceRequirements}`} />
                                <Chip label={`Current Users: ${formData.currentUserLoad}`} />
                                <Chip label={`Peak Traffic: ${formData.peakTrafficPatterns}`} />
                                <Chip label={`Growth Rate: ${formData.expectedGrowthRate}`} />
                                <Chip label={`Response Time: ${formData.responseTimeRequirements}`} />
                                <Chip label={`Availability: ${formData.availabilityRequirements}`} />
                                <Chip label={`Global Distribution: ${formData.globalDistribution}`} />
                                <Chip label={`Load Patterns: ${formData.loadPatterns}`} />
                                <Chip label={`Failover: ${formData.failoverRequirements}`} />
                            </Box>
                            {formData.scalingTriggers.length > 0 && (
                                <Box>
                                    <Typography variant="body2" color="text.secondary">Scaling Triggers:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.scalingTriggers.map(trigger => (
                                            <Chip key={trigger} label={trigger} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                        </Paper>

                        <Paper sx={{ p: 2 }}>
                            <Typography variant="subtitle1" gutterBottom>Security & Compliance</Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                                <Chip label={`Security Level: ${formData.securityLevel}`} />
                                <Chip label={`Data Location: ${formData.dataLocation}`} />
                                <Chip label={`Audit Requirements: ${formData.auditRequirements}`} />
                                <Chip label={`Security Incidents: ${formData.securityIncidentHistory}`} />
                                <Chip label={`Vulnerability Mgmt: ${formData.vulnerabilityManagement}`} />
                            </Box>
                            {formData.complianceRequirements.length > 0 && (
                                <Box sx={{ mb: 1 }}>
                                    <Typography variant="body2" color="text.secondary">Compliance Requirements:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.complianceRequirements.map(compliance => (
                                            <Chip key={compliance} label={compliance} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                            {formData.dataClassification.length > 0 && (
                                <Box sx={{ mb: 1 }}>
                                    <Typography variant="body2" color="text.secondary">Data Classification:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.dataClassification.map(classification => (
                                            <Chip key={classification} label={classification} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                            {formData.accessControlRequirements.length > 0 && (
                                <Box sx={{ mb: 1 }}>
                                    <Typography variant="body2" color="text.secondary">Access Control:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.accessControlRequirements.map(access => (
                                            <Chip key={access} label={access} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                            {formData.encryptionRequirements.length > 0 && (
                                <Box sx={{ mb: 1 }}>
                                    <Typography variant="body2" color="text.secondary">Encryption Requirements:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.encryptionRequirements.map(encryption => (
                                            <Chip key={encryption} label={encryption} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                            {formData.securityMonitoring.length > 0 && (
                                <Box>
                                    <Typography variant="body2" color="text.secondary">Security Monitoring:</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                        {formData.securityMonitoring.map(monitoring => (
                                            <Chip key={monitoring} label={monitoring} size="small" />
                                        ))}
                                    </Box>
                                </Box>
                            )}
                        </Paper>

                        <Paper sx={{ p: 2 }}>
                            <Typography variant="subtitle1" gutterBottom>Budget & Timeline</Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                <Chip label={`Scaling Timeline: ${formData.scalingTimeline}`} />
                                <Chip label={`Budget Flexibility: ${formData.budgetFlexibility}`} />
                                <Chip label={`Cost Optimization: ${formData.costOptimizationPriority}`} />
                                <Chip label={`Total Budget: ${formData.totalBudgetRange}`} />
                                <Chip label={`Migration Budget: ${formData.migrationBudget}`} />
                                <Chip label={`Operational Split: ${formData.operationalBudgetSplit}`} />
                                <Chip label={`ROI Expectations: ${formData.roiExpectations}`} />
                                <Chip label={`Payment Model: ${formData.paymentModel}`} />
                            </Box>
                        </Paper>
                    </Box>
                );

            default:
                return 'Unknown step';
        }
    };

    const getStepHelp = (step: number): string => {
        const helpTexts = [
            "Provide basic information about your company to help us understand your business context and generate relevant recommendations.",
            "Tell us about your current infrastructure setup. This helps us identify optimization opportunities and migration paths.",
            "Describe your technical architecture details. This information enables us to recommend compatible technologies and patterns.",
            "Share your AI and ML requirements. We'll use this to suggest appropriate compute resources and specialized services.",
            "Define your performance needs and scalability requirements. This helps us recommend the right sizing and scaling strategies.",
            "Specify your security and compliance requirements. We'll ensure our recommendations meet your regulatory and security standards.",
            "Share your budget and timeline constraints. This allows us to prioritize recommendations based on cost-effectiveness and urgency.",
            "Review all your inputs before submitting. You can go back to any step to make changes if needed."
        ];
        return helpTexts[step] || "Complete this step to continue with your assessment.";
    };

    const progress = ((activeStep + 1) / steps.length) * 100;
    const theme = useTheme();

    return (
        <>
            {/* Modern Header Card */}
            <Container maxWidth="lg" sx={{ py: 2 }}>
                <Card
                    sx={{
                        mb: 3,
                        background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
                        color: 'white',
                        position: 'relative',
                        overflow: 'visible'
                    }}
                >
                    <CardContent sx={{ pb: 2 }}>
                        <Grid container spacing={2} alignItems="center">
                            <Grid item xs={12} md={8}>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                                    <Assignment sx={{ fontSize: 32 }} />
                                    <Typography variant="h4" component="h1" fontWeight="bold">
                                        AI Infrastructure Assessment
                                    </Typography>
                                </Box>
                                <Typography variant="body1" sx={{ opacity: 0.9, mb: 2 }}>
                                    Get personalized recommendations for scaling your AI infrastructure
                                </Typography>

                                {/* Progress Bar */}
                                <Box sx={{ mb: 2 }}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                        <Typography variant="body2" sx={{ opacity: 0.9 }}>
                                            Step {activeStep + 1} of {steps.length}: {steps[activeStep]}
                                        </Typography>
                                        <Typography variant="body2" sx={{ opacity: 0.9 }}>
                                            {Math.round(progress)}% Complete
                                        </Typography>
                                    </Box>
                                    <LinearProgress
                                        variant="determinate"
                                        value={progress}
                                        sx={{
                                            height: 8,
                                            borderRadius: 4,
                                            backgroundColor: alpha(theme.palette.common.white, 0.3),
                                            '& .MuiLinearProgress-bar': {
                                                backgroundColor: theme.palette.common.white,
                                            }
                                        }}
                                    />
                                </Box>

                                {/* Horizontal Stepper */}
                                <Stepper
                                    activeStep={activeStep}
                                    alternativeLabel
                                    sx={{
                                        display: { xs: 'none', md: 'flex' },
                                        '& .MuiStepLabel-label': {
                                            color: 'white',
                                            opacity: 0.7,
                                            fontSize: '0.75rem',
                                            '&.Mui-active': {
                                                opacity: 1,
                                                fontWeight: 'bold'
                                            },
                                            '&.Mui-completed': {
                                                opacity: 0.9
                                            }
                                        },
                                        '& .MuiStepConnector-line': {
                                            borderColor: alpha(theme.palette.common.white, 0.3)
                                        },
                                        '& .Mui-active .MuiStepConnector-line': {
                                            borderColor: theme.palette.common.white
                                        },
                                        '& .Mui-completed .MuiStepConnector-line': {
                                            borderColor: theme.palette.common.white
                                        }
                                    }}
                                >
                                    {steps.map((label, index) => (
                                        <Step key={label}>
                                            <StepLabel
                                                StepIconComponent={({ active, completed }) => (
                                                    <Box
                                                        sx={{
                                                            width: 24,
                                                            height: 24,
                                                            borderRadius: '50%',
                                                            backgroundColor: completed
                                                                ? theme.palette.common.white
                                                                : active
                                                                    ? theme.palette.common.white
                                                                    : alpha(theme.palette.common.white, 0.3),
                                                            color: completed
                                                                ? theme.palette.primary.main
                                                                : active
                                                                    ? theme.palette.primary.main
                                                                    : theme.palette.common.white,
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            justifyContent: 'center',
                                                            fontSize: '0.875rem',
                                                            fontWeight: 'bold'
                                                        }}
                                                    >
                                                        {completed ? <CheckCircle sx={{ fontSize: 16 }} /> : index + 1}
                                                    </Box>
                                                )}
                                            >
                                                {label}
                                            </StepLabel>
                                        </Step>
                                    ))}
                                </Stepper>
                            </Grid>

                            <Grid item xs={12} md={4}>
                                <Stack direction="row" spacing={1} justifyContent={{ xs: 'center', md: 'flex-end' }}>
                                    {/* Save Status */}
                                    {lastSaved && (
                                        <Chip
                                            icon={<CheckCircle />}
                                            label={`Saved: ${lastSaved.toLocaleTimeString()}`}
                                            size="small"
                                            sx={{
                                                backgroundColor: alpha(theme.palette.common.white, 0.2),
                                                color: 'white',
                                                '& .MuiChip-icon': { color: 'white' }
                                            }}
                                        />
                                    )}

                                    {/* Restore Session Button */}
                                    {hasDraft() && !showRestoreDialog && (
                                        <Button
                                            variant="outlined"
                                            size="small"
                                            startIcon={<Restore />}
                                            onClick={() => setShowRestoreDialog(true)}
                                            sx={{
                                                color: 'white',
                                                borderColor: alpha(theme.palette.common.white, 0.5),
                                                '&:hover': {
                                                    borderColor: theme.palette.common.white,
                                                    backgroundColor: alpha(theme.palette.common.white, 0.1)
                                                }
                                            }}
                                        >
                                            Restore Session
                                        </Button>
                                    )}

                                    <Button
                                        variant="outlined"
                                        size="small"
                                        startIcon={isSaving ? <CircularProgress size={16} color="inherit" /> : <Save />}
                                        onClick={handleSaveDraft}
                                        disabled={isSaving}
                                        sx={{
                                            color: 'white',
                                            borderColor: alpha(theme.palette.common.white, 0.5),
                                            '&:hover': {
                                                borderColor: theme.palette.common.white,
                                                backgroundColor: alpha(theme.palette.common.white, 0.1)
                                            }
                                        }}
                                    >
                                        {isSaving ? 'Saving...' : 'Save Draft'}
                                    </Button>
                                </Stack>
                            </Grid>
                        </Grid>
                    </CardContent>
                </Card>
            </Container>

            <Container maxWidth="lg" sx={{ pb: 4 }}>
                {isLoadingDraft ? (
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
                                <CircularProgress />
                                <Typography variant="body1" sx={{ ml: 2 }}>
                                    Loading assessment...
                                </Typography>
                            </Box>
                        </CardContent>
                    </Card>
                ) : (
                    <Grid container spacing={3}>
                        {/* Main Content */}
                        <Grid item xs={12} md={8}>
                            <Card sx={{ minHeight: 600 }}>
                                <CardContent sx={{ p: 4 }}>
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

                                    <Box sx={{ display: 'flex', flexDirection: 'row', pt: 4, gap: 2 }}>
                                        <Button
                                            variant="outlined"
                                            disabled={activeStep === 0}
                                            onClick={handleBack}
                                            size="large"
                                        >
                                            Back
                                        </Button>
                                        <Box sx={{ flex: '1 1 auto' }} />
                                        {activeStep === steps.length - 1 ? (
                                            <Button
                                                onClick={handleSubmit}
                                                variant="contained"
                                                size="large"
                                                sx={{ minWidth: 140 }}
                                                disabled={isSubmitting}
                                                startIcon={isSubmitting ? <CircularProgress size={20} color="inherit" /> : undefined}
                                            >
                                                {isSubmitting ? 'Submitting...' : 'Submit Assessment'}
                                            </Button>
                                        ) : (
                                            <Button
                                                onClick={handleNext}
                                                variant="contained"
                                                size="large"
                                                sx={{ minWidth: 100 }}
                                            >
                                                Next
                                            </Button>
                                        )}
                                    </Box>
                                </CardContent>
                            </Card>
                        </Grid>

                        {/* Sidebar with Progress and Help */}
                        <Grid item xs={12} md={4}>
                            <Stack spacing={3}>
                                {/* Progress Card */}
                                <Card>
                                    <CardContent>
                                        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Schedule color="primary" />
                                            Progress Overview
                                        </Typography>
                                        <ProgressIndicator
                                            title=""
                                            steps={steps.map((label, index) => ({
                                                label,
                                                status: index === activeStep ? 'active' : index < activeStep ? 'completed' : 'pending',
                                            }))}
                                            variant="vertical"
                                            showPercentage={false}
                                        />
                                    </CardContent>
                                </Card>

                                {/* Help Card */}
                                <Card>
                                    <CardContent>
                                        <Typography variant="h6" gutterBottom color="primary">
                                            💡 Tips & Guidance
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary" paragraph>
                                            {getStepHelp(activeStep)}
                                        </Typography>
                                        <Alert severity="info" sx={{ mt: 2 }}>
                                            <Typography variant="body2">
                                                Smart suggestions will appear as you type to help you fill out forms faster.
                                            </Typography>
                                        </Alert>
                                    </CardContent>
                                </Card>
                            </Stack>
                        </Grid>
                    </Grid>
                )}
            </Container>

            {/* Custom Industry Dialog */}
            <Dialog
                open={showIndustryDialog}
                onClose={() => {
                    setShowIndustryDialog(false);
                    setCustomIndustry('');
                }}
                aria-labelledby="industry-dialog-title"
                maxWidth="sm"
                fullWidth
            >
                <DialogTitle id="industry-dialog-title">
                    Specify Your Industry
                </DialogTitle>
                <DialogContent>
                    <DialogContentText sx={{ mb: 2 }}>
                        Please provide details about your industry to help us give you more accurate recommendations.
                    </DialogContentText>
                    <TextField
                        autoFocus
                        fullWidth
                        label="Industry"
                        variant="outlined"
                        value={customIndustry}
                        onChange={(e) => setCustomIndustry(e.target.value)}
                        placeholder="e.g., E-commerce, Gaming, Real Estate, Consulting"
                        onKeyPress={(e) => {
                            if (e.key === 'Enter' && customIndustry.trim()) {
                                handleCustomIndustrySubmit();
                            }
                        }}
                    />
                </DialogContent>
                <DialogActions>
                    <Button 
                        onClick={() => {
                            setShowIndustryDialog(false);
                            setCustomIndustry('');
                        }}
                        color="secondary"
                    >
                        Cancel
                    </Button>
                    <Button 
                        onClick={handleCustomIndustrySubmit}
                        variant="contained"
                        disabled={!customIndustry.trim()}
                    >
                        Save
                    </Button>
                </DialogActions>
            </Dialog>

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

            {/* Duplicate Assessment Dialog */}
            <Dialog
                open={showDuplicateDialog}
                onClose={() => setShowDuplicateDialog(false)}
                maxWidth="sm"
                fullWidth
            >
                <DialogTitle>
                    <Box display="flex" alignItems="center" gap={2}>
                        <Warning color="warning" />
                        Similar Assessment Found
                    </Box>
                </DialogTitle>
                <DialogContent>
                    <DialogContentText sx={{ mb: 2 }}>
                        We found an existing assessment with similar information that you submitted recently.
                        Would you like to view the existing assessment instead of creating a duplicate?
                    </DialogContentText>
                    <Box sx={{ mt: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                            Creating duplicate assessments with identical information uses unnecessary resources.
                            We recommend viewing your existing assessment results.
                        </Typography>
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button
                        onClick={() => setShowDuplicateDialog(false)}
                        color="secondary"
                    >
                        Cancel
                    </Button>
                    <Button
                        onClick={() => {
                            setShowDuplicateDialog(false);
                            router.push('/dashboard');
                        }}
                        color="primary"
                    >
                        View Dashboard
                    </Button>
                    {existingAssessmentId && (
                        <Button
                            onClick={() => {
                                setShowDuplicateDialog(false);
                                router.push(`/dashboard?highlight=${existingAssessmentId}`);
                            }}
                            variant="contained"
                            color="primary"
                        >
                            View Existing Assessment
                        </Button>
                    )}
                </DialogActions>
            </Dialog>
        </>
    );
}

function AssessmentPageWithLayout() {
    return (
        <ProtectedRoute>
            <ResponsiveLayout title="AI Infrastructure Assessment">
                <Suspense fallback={<div>Loading...</div>}>
                    <AssessmentPageInner />
                </Suspense>
            </ResponsiveLayout>
        </ProtectedRoute>
    );
}

export default AssessmentPageWithLayout;