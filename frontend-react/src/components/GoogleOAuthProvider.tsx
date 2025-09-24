'use client';

import { GoogleOAuthProvider as GoogleProvider } from '@react-oauth/google';

interface GoogleOAuthProviderProps {
    children: React.ReactNode;
}

const GoogleOAuthProvider: React.FC<GoogleOAuthProviderProps> = ({ children }) => {
    // Use environment variable for Google OAuth client ID
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID || '';

    if (!clientId || clientId.trim() === '') {
        console.warn('Google OAuth Client ID not configured. Please set NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID environment variable.');
        return <>{children}</>;
    }

    try {
        return (
            <GoogleProvider clientId={clientId}>
                {children}
            </GoogleProvider>
        );
    } catch (error) {
        console.error('Error initializing Google OAuth Provider:', error);
        return <>{children}</>;
    }
};

export default GoogleOAuthProvider;