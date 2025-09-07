'use client';

import ResponsiveLayout from '../../components/ResponsiveLayout';
import GitOpsIntegration from '../../components/GitOpsIntegration';

export default function GitOpsPage() {
    return (
        <ResponsiveLayout title="GitOps Integration">
            <GitOpsIntegration />
        </ResponsiveLayout>
    );
}