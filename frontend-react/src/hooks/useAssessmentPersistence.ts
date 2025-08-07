'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAppSelector } from '@/store/hooks';
import { apiClient } from '@/services/api';

interface AssessmentDraft {
    formData: Record<string, unknown>;
    currentStep: number;
    lastSaved: string;
    userId: string;
    assessmentId?: string;
}

const STORAGE_KEY = 'assessment_draft';

export function useAssessmentPersistence() {
    const { user } = useAppSelector(state => state.auth);
    const [isLoading, setIsLoading] = useState(false);
    const [lastSaved, setLastSaved] = useState<Date | null>(null);

    // Save draft to both localStorage and API
    const saveDraft = useCallback(async (
        formData: Record<string, unknown>,
        currentStep: number,
        assessmentId?: string
    ) => {
        if (!user) return;

        const draft: AssessmentDraft = {
            formData,
            currentStep,
            lastSaved: new Date().toISOString(),
            userId: user.id,
            assessmentId
        };

        try {
            setIsLoading(true);

            // Save to localStorage for immediate persistence
            localStorage.setItem(STORAGE_KEY, JSON.stringify(draft));
            
            // Save to API for cross-device persistence
            if (assessmentId) {
                // Update existing draft assessment
                await apiClient.updateAssessment(assessmentId, {
                    draft_data: formData,
                    current_step: currentStep,
                    status: 'draft'
                });
            } else {
                // Create new draft assessment
                const response = await apiClient.createDraftAssessment({
                    title: `Draft Assessment - ${new Date().toLocaleDateString()}`,
                    draft_data: formData,
                    current_step: currentStep,
                    status: 'draft'
                });
                
                // Update the draft with the new assessment ID
                draft.assessmentId = response.id;
                localStorage.setItem(STORAGE_KEY, JSON.stringify(draft));
            }

            setLastSaved(new Date());
        } catch (error) {
            console.warn('Failed to save draft to API, saved locally only:', error);
            // Still saved to localStorage, so not a complete failure
            setLastSaved(new Date());
        } finally {
            setIsLoading(false);
        }
    }, [user]);

    // Load draft from localStorage or API
    const loadDraft = useCallback(async (): Promise<AssessmentDraft | null> => {
        if (!user) return null;

        try {
            setIsLoading(true);

            // First, try to load from localStorage for immediate response
            const localDraft = localStorage.getItem(STORAGE_KEY);
            let draft: AssessmentDraft | null = null;

            if (localDraft) {
                const parsed = JSON.parse(localDraft);
                if (parsed.userId === user.id) {
                    draft = parsed;
                }
            }

            // Then, try to load from API for the most recent version
            try {
                const assessments = await apiClient.getAssessments();
                const draftAssessment = assessments.find(a => a.status === 'draft');
                
                if (draftAssessment && draftAssessment.draft_data) {
                    const apiDraft: AssessmentDraft = {
                        formData: draftAssessment.draft_data,
                        currentStep: draftAssessment.current_step || 0,
                        lastSaved: draftAssessment.updated_at,
                        userId: user.id,
                        assessmentId: draftAssessment.id
                    };

                    // Compare timestamps and use the most recent
                    if (!draft || new Date(apiDraft.lastSaved) > new Date(draft.lastSaved)) {
                        draft = apiDraft;
                        // Update localStorage with the latest version
                        localStorage.setItem(STORAGE_KEY, JSON.stringify(draft));
                    }
                }
            } catch (error) {
                console.warn('Failed to load draft from API, using local version:', error);
                // Continue with local draft if available
            }

            return draft;
        } catch (error) {
            console.error('Failed to load assessment draft:', error);
            return null;
        } finally {
            setIsLoading(false);
        }
    }, [user]);

    // Clear draft from both localStorage and API
    const clearDraft = useCallback(async (assessmentId?: string) => {
        try {
            // Clear from localStorage
            localStorage.removeItem(STORAGE_KEY);

            // Clear from API if we have an assessment ID
            if (assessmentId) {
                await apiClient.deleteAssessment(assessmentId);
            }

            setLastSaved(null);
        } catch (error) {
            console.warn('Failed to clear draft from API:', error);
            // localStorage is still cleared
        }
    }, []);

    // Check if there's a draft available
    const hasDraft = useCallback((): boolean => {
        if (!user) return false;
        
        const localDraft = localStorage.getItem(STORAGE_KEY);
        if (localDraft) {
            try {
                const parsed = JSON.parse(localDraft);
                return parsed.userId === user.id;
            } catch {
                return false;
            }
        }
        return false;
    }, [user]);

    // Auto-save functionality
    const setupAutoSave = useCallback((
        getFormData: () => Record<string, unknown>,
        getCurrentStep: () => number,
        getAssessmentId: () => string | undefined,
        intervalMs: number = 30000 // 30 seconds
    ) => {
        const interval = setInterval(() => {
            const formData = getFormData();
            const currentStep = getCurrentStep();
            const assessmentId = getAssessmentId();
            
            // Only save if there's actual data
            if (Object.values(formData).some(value => 
                Array.isArray(value) ? value.length > 0 : Boolean(value)
            )) {
                saveDraft(formData, currentStep, assessmentId);
            }
        }, intervalMs);

        return () => clearInterval(interval);
    }, [saveDraft]);

    return {
        saveDraft,
        loadDraft,
        clearDraft,
        hasDraft,
        setupAutoSave,
        isLoading,
        lastSaved
    };
}