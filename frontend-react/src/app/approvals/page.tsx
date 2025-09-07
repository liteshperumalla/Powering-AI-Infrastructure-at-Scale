'use client';

import ResponsiveLayout from '../../components/ResponsiveLayout';
import ApprovalWorkflows from '../../components/ApprovalWorkflows';

export default function ApprovalsPage() {
    return (
        <ResponsiveLayout title="Approval Workflows">
            <ApprovalWorkflows />
        </ResponsiveLayout>
    );
}