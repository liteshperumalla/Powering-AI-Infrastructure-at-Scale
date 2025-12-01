'use client';

import { useSearchParams } from 'next/navigation';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import ResponsiveLayout from '../../components/ResponsiveLayout';
import ProtectedRoute from '../../components/ProtectedRoute';
import ComplianceAutomation from '../../components/ComplianceAutomation';

export default function CompliancePage() {
    const searchParams = useSearchParams();
    const currentAssessment = useSelector((state: RootState) => state.assessment.currentAssessment);

    // Priority: URL param > Redux state
    const urlAssessmentId = searchParams?.get('assessment_id');
    const assessmentId = urlAssessmentId || currentAssessment?.id;

    console.log('🔍 Compliance Page - URL Param:', urlAssessmentId);
    console.log('🔍 Compliance Page - Redux Assessment:', currentAssessment?.id);
    console.log('🔍 Compliance Page - Final Assessment ID:', assessmentId);

    return (
        <ProtectedRoute>
            <ResponsiveLayout title="Compliance Automation">
                <ComplianceAutomation assessmentId={assessmentId} />
            </ResponsiveLayout>
        </ProtectedRoute>
    );
}