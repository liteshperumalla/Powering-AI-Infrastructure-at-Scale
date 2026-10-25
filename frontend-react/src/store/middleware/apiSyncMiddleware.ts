import { Middleware, isAction } from '@reduxjs/toolkit';
import { apiClient } from '../../services/api';

/**
 * Minimal slice of the root state this middleware reads. Typed locally rather
 * than via RootState to avoid a circular type reference with the store.
 */
interface AuthTokenState {
  auth: { token: string | null };
}

/**
 * Middleware to sync API client token with Redux auth state
 */
export const apiSyncMiddleware: Middleware<{}, AuthTokenState> = (store) => (next) => (action) => {
  const result = next(action);
  
  // Check if this action affected the auth state
  if (isAction(action) && action.type.startsWith('auth/')) {
    const state = store.getState();
    const { token } = state.auth;
    
    // Update API client token
    if (token) {
      apiClient.setStoredToken(token);
    } else {
      apiClient.removeStoredToken();
    }
  }
  
  return result;
};
