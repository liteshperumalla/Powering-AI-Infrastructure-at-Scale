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
 * Actions that mean "signed out". Only these may delete the stored token: a null
 * token in state is also the normal state before auth/initialize has read storage,
 * and clearing on that (e.g. on auth/initialize/pending) logged users out on every reload.
 */
const SIGN_OUT_ACTIONS = new Set(['auth/clearAuth', 'auth/logout/fulfilled', 'auth/logout/rejected']);

/**
 * Middleware to sync API client token with Redux auth state
 */
export const apiSyncMiddleware: Middleware<{}, AuthTokenState> = (store) => (next) => (action) => {
  const result = next(action);

  // Check if this action affected the auth state
  if (isAction(action) && action.type.startsWith('auth/')) {
    const { token } = store.getState().auth;
    const explicitSignOut = SIGN_OUT_ACTIONS.has(action.type) ||
      (action.type === 'auth/setToken' && (action as { payload?: unknown }).payload === null);

    // Update API client token
    if (token) {
      apiClient.setStoredToken(token);
    } else if (explicitSignOut) {
      apiClient.removeStoredToken();
    }
  }

  return result;
};
