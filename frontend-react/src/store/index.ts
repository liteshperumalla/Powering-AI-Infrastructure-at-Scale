import { configureStore } from '@reduxjs/toolkit';
import assessmentReducer from './slices/assessmentSlice';
import reportReducer from './slices/reportSlice';
import scenarioReducer from './slices/scenarioSlice';
import uiReducer from './slices/uiSlice';

export const store = configureStore({
    reducer: {
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
        }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;