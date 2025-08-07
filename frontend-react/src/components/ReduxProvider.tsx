'use client';

import React from 'react';
import { Provider } from 'react-redux';
import { store } from '@/store';
import AuthInitializer from './AuthInitializer';

interface ReduxProviderProps {
    children: React.ReactNode;
}

export default function ReduxProvider({ children }: ReduxProviderProps) {
    return (
        <Provider store={store}>
            <AuthInitializer />
            {children}
        </Provider>
    );
}