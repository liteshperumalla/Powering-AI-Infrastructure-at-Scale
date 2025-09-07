'use client';

import ResponsiveLayout from '../../components/ResponsiveLayout';
import BudgetForecasting from '../../components/BudgetForecasting';

export default function BudgetForecastingPage() {
    return (
        <ResponsiveLayout title="Budget Forecasting">
            <BudgetForecasting />
        </ResponsiveLayout>
    );
}