'use client';

import React from 'react';
import ResponsiveLayout from '@/components/ResponsiveLayout';
import ModernHomePage from '@/components/ModernHomePage';

export default function HomePage() {
  return (
    <ResponsiveLayout title="Home">
      <ModernHomePage />
    </ResponsiveLayout>
  );
}