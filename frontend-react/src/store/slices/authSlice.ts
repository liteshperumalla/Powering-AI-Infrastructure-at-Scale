import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { apiClient } from '../../services/api';

export interface User {
    id: string;
    email: string;
    full_name: string;
    role: string;
    created_at: string;
    last_login: string;
}

interface AuthState {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    loading: boolean;
    error: string | null;
}

const initialState: AuthState = {
    user: null,
    token: null,
    isAuthenticated: false,
    loading: false,
    error: null,
};

// Async thunks for authentication
export const login = createAsyncThunk(
    'auth/login',
    async (credentials: { email: string; password: string }, { rejectWithValue }) => {
        try {
            const response = await apiClient.login(credentials);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Login failed');
        }
    }
);

export const register = createAsyncThunk(
    'auth/register',
    async (userData: {
        email: string;
        password: string;
        full_name: string;
        company?: string;
    }, { rejectWithValue }) => {
        try {
            const response = await apiClient.register(userData);
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Registration failed');
        }
    }
);

export const logout = createAsyncThunk(
    'auth/logout',
    async (_, { rejectWithValue }) => {
        try {
            await apiClient.logout();
        } catch (error) {
            // Even if logout fails on server, clear local state
            console.warn('Logout request failed:', error);
        }
    }
);

export const refreshToken = createAsyncThunk(
    'auth/refreshToken',
    async (_, { rejectWithValue }) => {
        try {
            const response = await apiClient.refreshToken();
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Token refresh failed');
        }
    }
);

export const getCurrentUser = createAsyncThunk(
    'auth/getCurrentUser',
    async (_, { rejectWithValue }) => {
        try {
            const response = await apiClient.getCurrentUser();
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Failed to get user info');
        }
    }
);

export const updateProfile = createAsyncThunk(
    'auth/updateProfile',
    async (updates: {
        full_name?: string;
        company?: string;
        preferences?: Record<string, unknown>;
    }, { rejectWithValue }) => {
        try {
            await apiClient.updateUserProfile(updates);
            // Fetch updated user data
            const response = await apiClient.getCurrentUser();
            return response;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Failed to update profile');
        }
    }
);

export const initializeAuth = createAsyncThunk(
    'auth/initialize',
    async (_, { dispatch }) => {
        try {
            // Check if there's a stored token
            const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
            if (token) {
                // Set the token in Redux state, which will trigger the middleware to sync with API client
                dispatch(setToken(token));
                
                // Try to get current user to validate the token
                const response = await apiClient.getCurrentUser();
                return { token, user: response };
            }
            return null;
        } catch (error) {
            // Token is invalid, clear it
            if (typeof window !== 'undefined') {
                localStorage.removeItem('auth_token');
            }
            dispatch(clearAuth());
            return null;
        }
    }
);

const authSlice = createSlice({
    name: 'auth',
    initialState,
    reducers: {
        clearError: (state) => {
            state.error = null;
        },
        setToken: (state, action: PayloadAction<string | null>) => {
            state.token = action.payload;
            state.isAuthenticated = !!action.payload;
        },
        clearAuth: (state) => {
            state.user = null;
            state.token = null;
            state.isAuthenticated = false;
            state.error = null;
        },
    },
    extraReducers: (builder) => {
        builder
            // Login
            .addCase(login.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(login.fulfilled, (state, action) => {
                state.loading = false;
                state.user = {
                    id: action.payload.user_id,
                    email: action.payload.email,
                    full_name: action.payload.full_name,
                    role: 'user', // default role
                    created_at: new Date().toISOString(),
                    last_login: new Date().toISOString()
                };
                state.token = action.payload.access_token;
                state.isAuthenticated = true;
                state.error = null;
            })
            .addCase(login.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
                state.isAuthenticated = false;
            })
            // Register
            .addCase(register.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(register.fulfilled, (state, action) => {
                state.loading = false;
                state.user = {
                    id: action.payload.user_id,
                    email: action.payload.email,
                    full_name: action.payload.full_name,
                    role: 'user', // default role
                    created_at: new Date().toISOString(),
                    last_login: new Date().toISOString()
                };
                state.token = action.payload.access_token;
                state.isAuthenticated = true;
                state.error = null;
            })
            .addCase(register.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
                state.isAuthenticated = false;
            })
            // Logout
            .addCase(logout.pending, (state) => {
                state.loading = true;
            })
            .addCase(logout.fulfilled, (state) => {
                state.loading = false;
                state.user = null;
                state.token = null;
                state.isAuthenticated = false;
                state.error = null;
            })
            .addCase(logout.rejected, (state) => {
                state.loading = false;
                // Clear state even if logout request failed
                state.user = null;
                state.token = null;
                state.isAuthenticated = false;
                state.error = null;
            })
            // Refresh token
            .addCase(refreshToken.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(refreshToken.fulfilled, (state, action) => {
                state.loading = false;
                state.user = {
                    id: action.payload.user_id,
                    email: action.payload.email,
                    full_name: action.payload.full_name,
                    role: 'user', // default role
                    created_at: new Date().toISOString(),
                    last_login: new Date().toISOString()
                };
                state.token = action.payload.access_token;
                state.isAuthenticated = true;
                state.error = null;
            })
            .addCase(refreshToken.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
                // Clear auth state on refresh failure
                state.user = null;
                state.token = null;
                state.isAuthenticated = false;
            })
            // Get current user
            .addCase(getCurrentUser.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(getCurrentUser.fulfilled, (state, action) => {
                state.loading = false;
                state.user = {
                    id: action.payload.id,
                    email: action.payload.email,
                    full_name: action.payload.full_name,
                    role: action.payload.role,
                    created_at: action.payload.created_at,
                    last_login: new Date().toISOString()
                };
                state.error = null;
            })
            .addCase(getCurrentUser.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            // Update profile
            .addCase(updateProfile.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(updateProfile.fulfilled, (state, action) => {
                state.loading = false;
                state.user = {
                    id: action.payload.id,
                    email: action.payload.email,
                    full_name: action.payload.full_name,
                    role: action.payload.role,
                    created_at: action.payload.created_at,
                    last_login: new Date().toISOString()
                };
                state.error = null;
            })
            .addCase(updateProfile.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            // Initialize auth
            .addCase(initializeAuth.pending, (state) => {
                state.loading = true;
            })
            .addCase(initializeAuth.fulfilled, (state, action) => {
                state.loading = false;
                if (action.payload) {
                    state.token = action.payload.token;
                    state.user = {
                        id: action.payload.user.id,
                        email: action.payload.user.email,
                        full_name: action.payload.user.full_name,
                        role: action.payload.user.role,
                        created_at: action.payload.user.created_at,
                        last_login: new Date().toISOString()
                    };
                    state.isAuthenticated = true;
                }
                state.error = null;
            })
            .addCase(initializeAuth.rejected, (state) => {
                state.loading = false;
                state.token = null;
                state.user = null;
                state.isAuthenticated = false;
                state.error = null;
            });
    },
});

export const { clearError, setToken, clearAuth } = authSlice.actions;
export default authSlice.reducer;