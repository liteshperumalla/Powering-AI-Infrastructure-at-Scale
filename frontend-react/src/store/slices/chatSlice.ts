import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { apiClient } from '../../services/api';

// Interfaces
export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    metadata?: any;
}

export interface Conversation {
    id: string;
    title: string;
    status: string;
    context: string;
    message_count: number;
    started_at: string;
    last_activity: string;
    assessment_id?: string;
    report_id?: string;
    escalated: boolean;
}

export interface ConversationDetail extends Conversation {
    messages: ChatMessage[];
    total_tokens_used: number;
    topics_discussed: string[];
}

interface ChatState {
    conversations: Conversation[];
    currentConversation: ConversationDetail | null;
    loading: boolean;
    error: string | null;
    sendingMessage: boolean;
}

const initialState: ChatState = {
    conversations: [],
    currentConversation: null,
    loading: false,
    error: null,
    sendingMessage: false,
};

// Async Thunks
export const startConversation = createAsyncThunk(
    'chat/startConversation',
    async (request: {
        title?: string;
        context?: string;
        assessment_id?: string;
        report_id?: string;
        initial_message?: string;
    }, { rejectWithValue }) => {
        try {
            const response = await apiClient.startConversation(request);
            return response;
        } catch (error: unknown) {
            return rejectWithValue(error instanceof Error ? error.message : 'Failed to start conversation');
        }
    }
);

export const getConversations = createAsyncThunk(
    'chat/getConversations',
    async (params?: {
        page?: number;
        limit?: number;
        status_filter?: string;
        context_filter?: string;
    }, { rejectWithValue }) => {
        try {
            const response = await apiClient.getConversations(params);
            return response;
        } catch (error: unknown) {
            return rejectWithValue(error instanceof Error ? error.message : 'Failed to fetch conversations');
        }
    }
);

export const getConversation = createAsyncThunk(
    'chat/getConversation',
    async (conversationId: string, { rejectWithValue }) => {
        try {
            const response = await apiClient.getConversation(conversationId);
            return response;
        } catch (error: unknown) {
            return rejectWithValue(error instanceof Error ? error.message : 'Failed to fetch conversation');
        }
    }
);

export const sendMessage = createAsyncThunk(
    'chat/sendMessage',
    async ({ conversationId, request }: {
        conversationId: string;
        request: {
            content: string;
            context?: string;
            assessment_id?: string;
            report_id?: string;
        };
    }, { rejectWithValue }) => {
        try {
            const response = await apiClient.sendMessage(conversationId, request);
            return { conversationId, message: response };
        } catch (error: unknown) {
            return rejectWithValue(error instanceof Error ? error.message : 'Failed to send message');
        }
    }
);

export const deleteConversation = createAsyncThunk(
    'chat/deleteConversation',
    async (conversationId: string, { rejectWithValue }) => {
        try {
            await apiClient.deleteConversation(conversationId);
            return conversationId;
        } catch (error: unknown) {
            return rejectWithValue(error instanceof Error ? error.message : 'Failed to delete conversation');
        }
    }
);

export const endConversation = createAsyncThunk(
    'chat/endConversation',
    async ({ conversationId, rating }: { conversationId: string, rating?: number }, { rejectWithValue }) => {
        try {
            await apiClient.endConversation(conversationId, rating);
            return conversationId;
        } catch (error: unknown) {
            return rejectWithValue(error instanceof Error ? error.message : 'Failed to end conversation');
        }
    }
);

const chatSlice = createSlice({
    name: 'chat',
    initialState,
    reducers: {
        clearChatError: (state) => {
            state.error = null;
        },
        addMessageOptimistically: (state, action: PayloadAction<ChatMessage>) => {
            if (state.currentConversation) {
                state.currentConversation.messages.push(action.payload);
            }
        },
        removeMessageOptimistically: (state, action: PayloadAction<string>) => {
            if (state.currentConversation) {
                state.currentConversation.messages = state.currentConversation.messages.filter(
                    (msg) => msg.id !== action.payload
                );
            }
        }
    },
    extraReducers: (builder) => {
        builder
            // startConversation
            .addCase(startConversation.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(startConversation.fulfilled, (state, action: PayloadAction<ConversationDetail>) => {
                state.loading = false;
                state.currentConversation = action.payload;
                state.conversations.unshift(action.payload);
            })
            .addCase(startConversation.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            // getConversations
            .addCase(getConversations.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(getConversations.fulfilled, (state, action) => {
                state.loading = false;
                state.conversations = action.payload.conversations;
            })
            .addCase(getConversations.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            // getConversation
            .addCase(getConversation.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(getConversation.fulfilled, (state, action: PayloadAction<ConversationDetail>) => {
                state.loading = false;
                state.currentConversation = action.payload;
            })
            .addCase(getConversation.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            // sendMessage
            .addCase(sendMessage.pending, (state) => {
                state.sendingMessage = true;
                state.error = null;
            })
            .addCase(sendMessage.fulfilled, (state, action) => {
                state.sendingMessage = false;
                if (state.currentConversation && state.currentConversation.id === action.payload.conversationId) {
                    state.currentConversation.messages.push(action.payload.message);
                }
            })
            .addCase(sendMessage.rejected, (state, action) => {
                state.sendingMessage = false;
                state.error = action.payload as string;
            })
            // deleteConversation
            .addCase(deleteConversation.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(deleteConversation.fulfilled, (state, action: PayloadAction<string>) => {
                state.loading = false;
                state.conversations = state.conversations.filter(c => c.id !== action.payload);
                if (state.currentConversation?.id === action.payload) {
                    state.currentConversation = null;
                }
            })
            .addCase(deleteConversation.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            })
            // endConversation
            .addCase(endConversation.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(endConversation.fulfilled, (state, action: PayloadAction<string>) => {
                state.loading = false;
                const conversation = state.conversations.find(c => c.id === action.payload);
                if (conversation) {
                    conversation.status = 'resolved';
                }
                if (state.currentConversation?.id === action.payload) {
                    state.currentConversation.status = 'resolved';
                }
            })
            .addCase(endConversation.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload as string;
            });
    },
});

export const { clearChatError, addMessageOptimistically, removeMessageOptimistically } = chatSlice.actions;

export default chatSlice.reducer;
