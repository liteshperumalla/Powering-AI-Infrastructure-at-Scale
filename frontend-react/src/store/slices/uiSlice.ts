import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface NotificationState {
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    message: string;
    duration?: number;
    timestamp: number;
}

interface UIState {
    sidebarOpen: boolean;
    theme: 'light' | 'dark';
    notifications: NotificationState[];
    loading: {
        global: boolean;
        components: Record<string, boolean>;
    };
    modals: {
        reportExport: boolean;
        scenarioComparison: boolean;
        shareReport: boolean;
    };
    preferences: {
        chartType: 'bar' | 'line' | 'area';
        dataRefreshInterval: number;
        autoSave: boolean;
        compactView: boolean;
    };
}

const initialState: UIState = {
    sidebarOpen: true,
    theme: 'light',
    notifications: [],
    loading: {
        global: false,
        components: {},
    },
    modals: {
        reportExport: false,
        scenarioComparison: false,
        shareReport: false,
    },
    preferences: {
        chartType: 'bar',
        dataRefreshInterval: 30000,
        autoSave: true,
        compactView: false,
    },
};

const uiSlice = createSlice({
    name: 'ui',
    initialState,
    reducers: {
        toggleSidebar: (state) => {
            state.sidebarOpen = !state.sidebarOpen;
        },
        setSidebarOpen: (state, action: PayloadAction<boolean>) => {
            state.sidebarOpen = action.payload;
        },
        toggleTheme: (state) => {
            state.theme = state.theme === 'light' ? 'dark' : 'light';
        },
        setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
            state.theme = action.payload;
        },
        addNotification: (state, action: PayloadAction<Omit<NotificationState, 'id' | 'timestamp'>>) => {
            const notification: NotificationState = {
                ...action.payload,
                id: Date.now().toString(),
                timestamp: Date.now(),
            };
            state.notifications.push(notification);
        },
        removeNotification: (state, action: PayloadAction<string>) => {
            state.notifications = state.notifications.filter(n => n.id !== action.payload);
        },
        clearNotifications: (state) => {
            state.notifications = [];
        },
        setGlobalLoading: (state, action: PayloadAction<boolean>) => {
            state.loading.global = action.payload;
        },
        setComponentLoading: (state, action: PayloadAction<{ component: string; loading: boolean }>) => {
            state.loading.components[action.payload.component] = action.payload.loading;
        },
        clearComponentLoading: (state, action: PayloadAction<string>) => {
            delete state.loading.components[action.payload];
        },
        openModal: (state, action: PayloadAction<keyof UIState['modals']>) => {
            state.modals[action.payload] = true;
        },
        closeModal: (state, action: PayloadAction<keyof UIState['modals']>) => {
            state.modals[action.payload] = false;
        },
        closeAllModals: (state) => {
            Object.keys(state.modals).forEach(key => {
                state.modals[key as keyof UIState['modals']] = false;
            });
        },
        updatePreferences: (state, action: PayloadAction<Partial<UIState['preferences']>>) => {
            state.preferences = { ...state.preferences, ...action.payload };
        },
        resetPreferences: (state) => {
            state.preferences = initialState.preferences;
        },
    },
});

export const {
    toggleSidebar,
    setSidebarOpen,
    toggleTheme,
    setTheme,
    addNotification,
    removeNotification,
    clearNotifications,
    setGlobalLoading,
    setComponentLoading,
    clearComponentLoading,
    openModal,
    closeModal,
    closeAllModals,
    updatePreferences,
    resetPreferences,
} = uiSlice.actions;

export default uiSlice.reducer;