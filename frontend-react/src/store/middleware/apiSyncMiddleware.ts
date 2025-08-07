import { Middleware } from '@reduxjs/toolkit';
import { apiClient } from '../../services/api';
import { RootState } from '../index';

/**
 * Middleware to sync API client token with Redux auth state
 */
export const apiSyncMiddleware: Middleware<{}, RootState> = (store) => (next) => (action) => {
  const result = next(action);
  
  // Check if this action affected the auth state
  if (action.type?.startsWith('auth/')) {
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