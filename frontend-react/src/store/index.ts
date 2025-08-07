import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import assessmentReducer from './slices/assessmentSlice';
import reportReducer from './slices/reportSlice';
import scenarioReducer from './slices/scenarioSlice';
import uiReducer from './slices/uiSlice';
import { apiSyncMiddleware } from './middleware/apiSyncMiddleware';

export const store = configureStore({
    reducer: {
        auth: authReducer,
        assessment: assessmentReducer,
        report: reportReducer,
        scenario: scenarioReducer,
        ui: uiReducer,
    },
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({
            serializableCheck: {
                ignoredActions: ['persist/PERSIST'],
            },
        }).concat(apiSyncMiddleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;