'use client';

import { useSearchParams } from 'next/navigation';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import ResponsiveLayout from '../../components/ResponsiveLayout';
import ComplianceAutomation from '../../components/ComplianceAutomation';

export default function CompliancePage() {
    const searchParams = useSearchParams();
    const currentAssessment = useSelector((state: RootState) => state.assessment.currentAssessment);

    // Priority: URL param > Redux state
    const urlAssessmentId = searchParams?.get('assessment_id');
    const assessmentId = urlAssessmentId || currentAssessment?.id;

    // No redirect - just handle the case when there's no assessment

    return (
        <ResponsiveLayout title="Compliance Automation">
            <ComplianceAutomation assessmentId={assessmentId} />
        </ResponsiveLayout>
    );
}