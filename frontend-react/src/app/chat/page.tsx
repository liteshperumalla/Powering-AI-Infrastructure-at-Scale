'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
    Box,
    Container,
    Paper,
    TextField,
    IconButton,
    Typography,
    Avatar,
    Chip,
    CircularProgress,
    Button,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Menu,
    MenuItem,
    Alert,
    FormControl,
    InputLabel,
    Select,
    Rating,
    Drawer,
    Tooltip,
} from '@mui/material';
import {
    Send as SendIcon,
    Add as AddIcon,
    History as HistoryIcon,
    Settings as SettingsIcon,
    Delete as DeleteIcon,
    Edit as EditIcon,
    Assessment as AssessmentIcon,
    Description as ReportIcon,
    Psychology as AIIcon,
    SmartToy as BotIcon,
    Person as UserIcon,
    MoreVert as MoreVertIcon,
    Close as CloseIcon,
    Menu as MenuIcon,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import ResponsiveLayout from '@/components/ResponsiveLayout';
import ProtectedRoute from '@/components/ProtectedRoute';
import TooltipButton from '@/components/TooltipButton';
import { useAppSelector } from '@/store/hooks';
import Link from 'next/link';
import { apiClient } from '@/services/api';

interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    metadata?: any;
}

interface Conversation {
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

interface ConversationDetail extends Conversation {
    messages: ChatMessage[];
    total_tokens_used: number;
    topics_discussed: string[];
}

const CONVERSATION_CONTEXTS = [
    { value: 'general_inquiry', label: 'General Questions', icon: '💬' },
    { value: 'assessment_help', label: 'Assessment Help', icon: '📊' },
    { value: 'report_analysis', label: 'Report Analysis', icon: '📄' },
    { value: 'technical_support', label: 'Technical Support', icon: '🔧' },
    { value: 'platform_guidance', label: 'Platform Guidance', icon: '🎯' },
    { value: 'decision_making', label: 'Decision Making', icon: '🤔' },
];

export default function ChatPage() {
    const { user, isAuthenticated, loading: authLoading } = useAppSelector(state => state.auth);

    // Debug authentication state
    console.log('🔍 Chat Page Auth State:', {
        isAuthenticated,
        user: user?.email || 'none',
        authLoading,
        userObject: user
    });
    
    // State management
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [currentConversation, setCurrentConversation] = useState<ConversationDetail | null>(null);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [newMessage, setNewMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isSending, setIsSending] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    // UI state
    const [newChatDialog, setNewChatDialog] = useState(false);
    const [settingsDialog, setSettingsDialog] = useState(false);
    const [endChatDialog, setEndChatDialog] = useState(false);
    const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [selectedContext, setSelectedContext] = useState('general_inquiry');
    const [satisfactionRating, setSatisfactionRating] = useState<number | null>(null);
    const [selectedAssessmentId, setSelectedAssessmentId] = useState<string>('');
    const [selectedReportId, setSelectedReportId] = useState<string>('');
    const [availableAssessments, setAvailableAssessments] = useState<any[]>([]);
    const [availableReports, setAvailableReports] = useState<any[]>([]);
    const [loadingReports, setLoadingReports] = useState<boolean>(false);
    
    // Refs
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textFieldRef = useRef<HTMLInputElement>(null);
    
    // Auto-scroll to bottom of messages
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };
    
    useEffect(() => {
        scrollToBottom();
    }, [messages]);
    
    // Load conversations on component mount, but only when authenticated
    useEffect(() => {
        if (isAuthenticated && !authLoading) {
            loadConversations();
            loadAvailableData();
        }
        // Initialize the chat even without authentication for simple chat mode
        console.log('Chat page initialized. isAuthenticated:', isAuthenticated, 'authLoading:', authLoading);
    }, [isAuthenticated, authLoading]);
    
    const loadAvailableData = async () => {
        if (!isAuthenticated) return;
        
        try {
            // Load assessments for context selection
            const assessmentsResponse = await apiClient.getAssessments();
            setAvailableAssessments(assessmentsResponse || []);
            
            // For reports, we'll load them differently since they require assessment_id
            // For now, we'll just set empty reports and load them dynamically when needed
            setAvailableReports([]);
        } catch (error) {
            console.error('Failed to load available data:', error);
            // Set empty arrays as fallback
            setAvailableAssessments([]);
            setAvailableReports([]);
        }
    };
    
    // Load reports for selected assessment
    const loadReportsForAssessment = async (assessmentId: string) => {
        if (!assessmentId || !isAuthenticated) {
            setAvailableReports([]);
            return;
        }
        
        try {
            setLoadingReports(true);
            const reports = await apiClient.getReports(assessmentId);
            setAvailableReports(reports || []);
        } catch (error) {
            console.error('Failed to load reports for assessment:', error);
            setAvailableReports([]);
        } finally {
            setLoadingReports(false);
        }
    };
    
    // Auto-focus message input
    useEffect(() => {
        if (!isSending && textFieldRef.current) {
            textFieldRef.current.focus();
        }
    }, [isSending, currentConversation]);
    
    const loadConversations = async () => {
        if (!isAuthenticated) return;
        
        try {
            setIsLoading(true);
            const response = await apiClient.getConversations({ limit: 50 });
            setConversations(response.conversations);
            
            // Auto-select most recent conversation
            if (response.conversations.length > 0 && !currentConversation) {
                await loadConversation(response.conversations[0].id);
            }
        } catch (error) {
            console.error('Failed to load conversations:', error);
            setError('Failed to load conversations');
        } finally {
            setIsLoading(false);
        }
    };
    
    const loadConversation = async (conversationId: string) => {
        try {
            setIsLoading(true);
            const conversation = await apiClient.getConversation(conversationId);
            setCurrentConversation(conversation);
            setMessages(conversation.messages);
            setError(null);
        } catch (error) {
            console.error('Failed to load conversation:', error);
            setError('Failed to load conversation');
        } finally {
            setIsLoading(false);
        }
    };
    
    const startNewConversation = async (context?: string, title?: string, initialMessage?: string) => {
        try {
            setIsLoading(true);
            setError(null);
            
            // Check if user is authenticated before trying to create a conversation
            if (!isAuthenticated) {
                console.log('🚫 User not authenticated, cannot start conversation');
                setError('Please log in to start a conversation, or use simple chat mode below.');
                setNewChatDialog(false);
                return;
            }
            
            console.log('🚀 Starting new conversation for authenticated user');
            const conversation = await apiClient.startConversation({
                title: title || 'New Chat',
                context: context || selectedContext,
                assessment_id: selectedAssessmentId || undefined,
                report_id: selectedReportId || undefined,
                initial_message: initialMessage
            });
            
            setCurrentConversation(conversation);
            setMessages(conversation.messages);
            setConversations(prev => [
                {
                    id: conversation.id,
                    title: conversation.title,
                    status: conversation.status,
                    context: conversation.context,
                    message_count: conversation.message_count,
                    started_at: conversation.started_at,
                    last_activity: conversation.last_activity,
                    assessment_id: conversation.assessment_id,
                    report_id: conversation.report_id,
                    escalated: conversation.escalated
                },
                ...prev
            ]);
            
            setNewChatDialog(false);
            setError(null);
            console.log('✅ Conversation started successfully:', conversation.id);
        } catch (error) {
            console.error('❌ Failed to start conversation:', error);
            
            // Handle authentication errors gracefully
            if (error instanceof Error && (
                error.message.includes('401') || 
                error.message.includes('unauthorized') || 
                error.message.includes('authentication')
            )) {
                setError('Authentication required. Please log in to start conversations, or use simple chat mode below.');
            } else if (error instanceof Error && error.message.includes('AI Assistant feature is not yet available')) {
                setError('🚧 AI Assistant is currently under development. This feature will be available soon! Please check back later.');
            } else {
                setError('Failed to start new conversation. You can still use simple chat mode below.');
            }
            
            setNewChatDialog(false);
        } finally {
            setIsLoading(false);
        }
    };
    
    const sendMessage = async () => {
        if (!newMessage.trim() || isSending) return;
        
        console.log('🚀 sendMessage started');
        console.log('📊 Current state:', { 
            isAuthenticated, 
            currentConversation: currentConversation?.id || 'none', 
            messageLength: newMessage.trim().length 
        });
        const messageContent = newMessage.trim();
        setNewMessage('');
        setIsSending(true);
        
        // Add user message to UI immediately
        const userMessage: ChatMessage = {
            id: `temp-${Date.now()}`,
            role: 'user',
            content: messageContent,
            timestamp: new Date().toISOString()
        };
        
        setMessages(prev => [...prev, userMessage]);
        
        try {
            let botResponse: ChatMessage;
            
            // If authenticated and has conversation, use conversation mode
            if (isAuthenticated && currentConversation) {
                console.log('🗨️ Using conversation mode');
                try {
                    const response = await apiClient.sendMessage(currentConversation.id, {
                        content: messageContent,
                        context: currentConversation.context,
                        assessment_id: currentConversation.assessment_id,
                        report_id: currentConversation.report_id
                    });
                    
                    botResponse = response;
                    
                    // Update conversation in sidebar
                    setConversations(prev => prev.map(conv => 
                        conv.id === currentConversation.id 
                            ? { ...conv, message_count: conv.message_count + 2, last_activity: new Date().toISOString() }
                            : conv
                    ));
                } catch (conversationError) {
                    console.log('🔄 Conversation mode failed, falling back to simple chat');
                    throw conversationError; // This will trigger the fallback below
                }
            } else {
                // Use simple chat when not authenticated or no conversation
                console.log('🤖 Using simple chat mode (auth:', isAuthenticated, ', conversation:', !!currentConversation, ')');
                const simpleResponse = await apiClient.sendSimpleMessage(messageContent);
                console.log('✅ Simple chat response received:', simpleResponse);
                botResponse = {
                    id: `bot_${Date.now()}`,
                    role: 'assistant' as const,
                    content: simpleResponse.response,
                    timestamp: new Date().toISOString(),
                    metadata: { simple_chat: true }
                };
            }
            
            // Add bot response to messages
            console.log('🔄 Adding bot response to messages:', botResponse);
            setMessages(prev => {
                const newMessages = [...prev, botResponse];
                console.log('✅ Messages state updated:', newMessages);
                return newMessages;
            });
            console.log('🧹 Clearing error state...');
            setError(null); // Clear any previous errors
            console.log('✅ Error state cleared, message should be visible');
            
        } catch (error) {
            console.error('❌ Primary chat failed:', error);
            
            // Fallback to simple chat if conversational chat fails
            try {
                console.log('🔄 Trying simple chat fallback...');
                const simpleResponse = await apiClient.sendSimpleMessage(messageContent);
                console.log('✅ Fallback simple chat worked:', simpleResponse);
                const botResponse = {
                    id: `bot_${Date.now()}`,
                    role: 'assistant' as const,
                    content: simpleResponse.response,
                    timestamp: new Date().toISOString(),
                    metadata: { fallback: true }
                };
                
                setMessages(prev => [...prev, botResponse]);
                setError(null); // Clear error if fallback works
            } catch (fallbackError) {
                console.error('❌ Simple chat fallback also failed:', fallbackError);
                console.error('❌ Full error details:', {
                    error: fallbackError,
                    message: fallbackError?.message,
                    stack: fallbackError?.stack
                });
                setError('I apologize, but I\'m experiencing technical difficulties. Please try again in a moment, or contact our support team if you need immediate assistance.');
                
                // Remove the temporary user message on error
                setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
            }
        } finally {
            setIsSending(false);
        }
    };
    
    const handleKeyPress = (event: React.KeyboardEvent) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    };
    
    const deleteConversation = async (conversationId: string) => {
        try {
            await apiClient.deleteConversation(conversationId);
            
            // Remove from conversations list
            setConversations(prev => prev.filter(conv => conv.id !== conversationId));
            
            // If this was the current conversation, clear it
            if (currentConversation?.id === conversationId) {
                setCurrentConversation(null);
                setMessages([]);
                
                // Load the next conversation if available
                const remainingConversations = conversations.filter(conv => conv.id !== conversationId);
                if (remainingConversations.length > 0) {
                    await loadConversation(remainingConversations[0].id);
                }
            }
        } catch (error) {
            console.error('Failed to delete conversation:', error);
            setError('Failed to delete conversation');
        }
    };
    
    const endConversation = async () => {
        if (!currentConversation) {
            console.log('❌ No current conversation to end');
            setEndChatDialog(false);
            return;
        }

        if (!isAuthenticated) {
            console.log('❌ User not authenticated, cannot end conversation');
            setError('Authentication required to end conversations');
            setEndChatDialog(false);
            return;
        }

        try {
            console.log('🔚 Ending conversation:', currentConversation.id);
            const result = await apiClient.endConversation(currentConversation.id, satisfactionRating || undefined);

            // Update conversation status and title if auto-generated
            setConversations(prev => prev.map(conv =>
                conv.id === currentConversation.id
                    ? {
                        ...conv,
                        status: 'resolved',
                        title: result.title || conv.title // Update with auto-generated title
                    }
                    : conv
            ));

            // Show success message with generated title if available
            if (result.title && result.title !== currentConversation.title) {
                console.log(`✅ Conversation ended and saved with auto-generated title: "${result.title}"`);
                // Show a temporary success message for title generation
                const tempMessage = `Conversation saved as: "${result.title}"`;
                setTimeout(() => {
                    // Could implement a toast notification here
                    console.log('💡 Title auto-generated successfully');
                }, 1000);
            } else {
                console.log('ℹ️ Conversation ended with existing title');
            }

            // Clear current conversation and messages
            setCurrentConversation(null);
            setMessages([]);

            setEndChatDialog(false);
            setSatisfactionRating(null);

            // Force a small delay to ensure UI updates properly
            setTimeout(() => {
                console.log('✅ Conversation ended successfully - UI should now show action buttons');
            }, 100);

            console.log('✅ Conversation ended successfully');
        } catch (error) {
            console.error('❌ Failed to end conversation:', error);

            // Handle authentication errors
            if (error instanceof Error && error.message.includes('401')) {
                setError('Authentication required to end conversations');
            } else {
                setError('Failed to end conversation');
            }

            setEndChatDialog(false);
        }
    };
    
    const formatMessageTime = (timestamp: string) => {
        const date = new Date(timestamp);
        const now = new Date();
        
        // If timestamp is in the future or too far in the past, use "just now"
        const diffMs = now.getTime() - date.getTime();
        if (diffMs < 0 || diffMs > 24 * 60 * 60 * 1000) {
            return 'just now';
        }
        
        return formatDistanceToNow(date, { addSuffix: true });
    };
    
    const getContextIcon = (context: string) => {
        const contextConfig = CONVERSATION_CONTEXTS.find(c => c.value === context);
        return contextConfig?.icon || '💬';
    };
    
    const getContextLabel = (context: string) => {
        const contextConfig = CONVERSATION_CONTEXTS.find(c => c.value === context);
        return contextConfig?.label || context;
    };
    
    const renderMessage = (message: ChatMessage) => {
        const isUser = message.role === 'user';
        const isSystem = message.role === 'system';
        
        return (
            <Box
                key={message.id}
                sx={{
                    display: 'flex',
                    flexDirection: isUser ? 'row-reverse' : 'row',
                    mb: 2,
                    alignItems: 'flex-start'
                }}
            >
                <Avatar
                    sx={{
                        mx: 1,
                        bgcolor: isUser ? 'primary.main' : isSystem ? 'warning.main' : 'secondary.main',
                        width: 32,
                        height: 32
                    }}
                >
                    {isUser ? <UserIcon /> : isSystem ? <SettingsIcon /> : <BotIcon />}
                </Avatar>
                
                <Paper
                    elevation={1}
                    sx={{
                        p: 2,
                        maxWidth: '70%',
                        bgcolor: isUser ? 'primary.light' : isSystem ? 'warning.light' : 'background.paper',
                        color: isUser ? 'primary.contrastText' : 'text.primary'
                    }}
                >
                    <Typography
                        variant="body1"
                        sx={{ 
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word'
                        }}
                    >
                        {message.content}
                    </Typography>
                    
                    <Typography
                        variant="caption"
                        sx={{
                            display: 'block',
                            mt: 1,
                            opacity: 0.7,
                            fontSize: '0.75rem'
                        }}
                    >
                        {formatMessageTime(message.timestamp)}
                    </Typography>
                </Paper>
            </Box>
        );
    };
    
    
    // Show loading state while authentication is being resolved
    if (authLoading) {
        return (
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    minHeight: '100vh',
                    gap: 2,
                }}
            >
                <CircularProgress size={40} />
                <Typography variant="body2" color="text.secondary">
                    Loading AI Assistant...
                </Typography>
            </Box>
        );
    }

    // Sidebar content for conversation history
    const sidebarContent = (
        <Box sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                    Chat History
                </Typography>
                {conversations.length > 0 && (
                    <Chip
                        label={`${conversations.length} chats`}
                        size="small"
                        color="primary"
                        variant="outlined"
                    />
                )}
            </Box>

            {conversations.length === 0 && isAuthenticated && (
                <Alert severity="info" sx={{ mb: 2 }}>
                    No previous conversations yet. Start your first chat!
                </Alert>
            )}

            {!isAuthenticated && (
                <Alert severity="info" sx={{ mb: 2 }}>
                    Log in to save and continue your conversations across sessions.
                </Alert>
            )}
            {conversations.map((conv) => (
                <Box key={conv.id} sx={{ mb: 1 }}>
                    <Button
                        fullWidth
                        variant={currentConversation?.id === conv.id ? "contained" : "outlined"}
                        onClick={() => loadConversation(conv.id)}
                        sx={{
                            justifyContent: "flex-start",
                            textAlign: 'left',
                            flexDirection: 'column',
                            alignItems: 'flex-start',
                            p: 2,
                            height: 'auto',
                            '&:hover': {
                                bgcolor: currentConversation?.id === conv.id ? 'primary.dark' : 'action.hover'
                            }
                        }}
                        startIcon={<HistoryIcon />}
                    >
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, textTransform: 'none' }}>
                            {conv.title}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'none' }}>
                            {conv.message_count} messages • {formatDistanceToNow(new Date(conv.last_activity), { addSuffix: true })}
                        </Typography>
                        {conv.assessment_id && (
                            <Chip
                                label="Assessment"
                                size="small"
                                color="primary"
                                variant="outlined"
                                sx={{ mt: 0.5, fontSize: '0.65rem' }}
                            />
                        )}
                    </Button>
                </Box>
            ))}
        </Box>
    );

    return (
        <ProtectedRoute requireAuth={false}>
            <ResponsiveLayout title="AI Assistant">
                <Box sx={{
                    display: 'flex',
                    height: 'calc(100vh - 140px)',
                    position: 'relative',
                    mt: 1,
                    borderRadius: 2,
                    overflow: 'hidden',
                    bgcolor: 'background.paper',
                    boxShadow: 1,
                    zIndex: 1
                }}>
                    {/* Sidebar Drawer */}
                    <Drawer
                        variant="persistent"
                        open={sidebarOpen}
                        sx={{
                            flexShrink: 0,
                            width: sidebarOpen ? 300 : 0,
                            transition: theme => theme.transitions.create('width', {
                                easing: theme.transitions.easing.sharp,
                                duration: theme.transitions.duration.leavingScreen,
                            }),
                            '& .MuiDrawer-paper': {
                                position: 'relative',
                                whiteSpace: 'nowrap',
                                width: 300,
                                transition: theme => theme.transitions.create('width', {
                                    easing: theme.transitions.easing.sharp,
                                    duration: theme.transitions.duration.enteringScreen,
                                }),
                                border: 'none',
                                borderRight: sidebarOpen ? '1px solid' : 'none',
                                borderColor: 'divider',
                                height: '100%',
                                overflowX: 'hidden'
                            },
                        }}
                    >
                        {sidebarContent}
                    </Drawer>
                    
                    {/* Main Chat Area */}
                    <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
                        {/* Chat Header */}
                        <Paper
                            elevation={1}
                            sx={{
                                p: 2,
                                borderRadius: 0,
                                borderBottom: '1px solid',
                                borderColor: 'divider',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between'
                            }}
                        >
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                <Tooltip title={sidebarOpen ? "Hide Chat History" : "Show Chat History"}>
                                    <IconButton
                                        onClick={() => setSidebarOpen(!sidebarOpen)}
                                        size="small"
                                        sx={{
                                            backgroundColor: sidebarOpen ? 'action.selected' : 'transparent',
                                            '&:hover': {
                                                backgroundColor: sidebarOpen ? 'action.hover' : 'action.hover',
                                            },
                                            transition: 'all 0.2s ease-in-out'
                                        }}
                                    >
                                        <MenuIcon />
                                    </IconButton>
                                </Tooltip>
                                
                                {currentConversation ? (
                                    <>
                                        <Typography variant="h6">
                                            {currentConversation.title}
                                        </Typography>
                                        <Chip
                                            label={getContextIcon(currentConversation.context) + ' ' + getContextLabel(currentConversation.context)}
                                            size="small"
                                            variant="outlined"
                                        />
                                        {currentConversation.escalated && (
                                            <Chip
                                                label="Escalated to Human Support"
                                                size="small"
                                                color="warning"
                                            />
                                        )}
                                    </>
                                ) : (
                                    <>
                                        <Box>
                                            <Typography variant="h6" sx={{ fontWeight: 600 }}>
                                                AI Infrastructure Assistant
                                            </Typography>
                                            <Typography variant="caption" color="text.secondary">
                                                Ask me anything about cloud infrastructure, DevOps, Kubernetes, AWS, Azure, GCP, and more!
                                            </Typography>
                                        </Box>
                                        {!isAuthenticated && (
                                            <Chip
                                                label="Simple Chat Mode"
                                                size="small"
                                                variant="filled"
                                                color="primary"
                                                sx={{ ml: 2 }}
                                            />
                                        )}
                                    </>
                                )}
                            </Box>
                            
                            {currentConversation && (
                                <Box sx={{ display: 'flex', gap: 1 }}>
                                    <TooltipButton
                                        tooltip="Generate a title based on conversation content"
                                        variant="text"
                                        size="small"
                                        onClick={async () => {
                                            try {
                                                const result = await apiClient.generateConversationTitle(currentConversation.id);
                                                // Update the conversation title in state
                                                setConversations(prev => prev.map(conv =>
                                                    conv.id === currentConversation.id
                                                        ? { ...conv, title: result.title }
                                                        : conv
                                                ));
                                                setCurrentConversation(prev =>
                                                    prev ? { ...prev, title: result.title } : prev
                                                );
                                                console.log(`✅ Title generated: "${result.title}"`);
                                            } catch (error) {
                                                console.error('Failed to generate title:', error);
                                                setError('Failed to generate title');
                                            }
                                        }}
                                        disabled={currentConversation.status === 'resolved'}
                                        sx={{ minWidth: 'auto', px: 1 }}
                                    >
                                        ✨
                                    </TooltipButton>
                                    <Button
                                        variant="outlined"
                                        size="small"
                                        onClick={() => setEndChatDialog(true)}
                                        disabled={currentConversation.status === 'resolved'}
                                    >
                                        End Chat
                                    </Button>
                                </Box>
                            )}
                        </Paper>
                        
                        {/* Messages Area */}
                        <Box
                            sx={{
                                flexGrow: 1,
                                overflow: 'auto',
                                p: 2,
                                bgcolor: 'grey.50'
                            }}
                        >
                            {error && (
                                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                                    {console.log('🚨 Displaying error message:', error)}
                                    {error}
                                </Alert>
                            )}
                            
                            {isLoading && messages.length === 0 ? (
                                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                                    <CircularProgress />
                                </Box>
                            ) : (!currentConversation && messages.length === 0) ? (
                                <Box
                                    sx={{
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        height: '100%',
                                        textAlign: 'center',
                                        p: 4,
                                    }}
                                >
                                    {/* Modern Avatar with Gradient */}
                                    <Avatar
                                        sx={{
                                            width: 100,
                                            height: 100,
                                            mb: 3,
                                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                            boxShadow: '0 8px 32px rgba(102, 126, 234, 0.3)',
                                        }}
                                    >
                                        <AIIcon sx={{ fontSize: 48 }} />
                                    </Avatar>

                                    <Typography 
                                        variant="h3" 
                                        gutterBottom 
                                        sx={{ 
                                            fontWeight: 700,
                                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                            backgroundClip: 'text',
                                            WebkitBackgroundClip: 'text',
                                            WebkitTextFillColor: 'transparent',
                                            mb: 2,
                                        }}
                                    >
                                        AI Infrastructure Assistant
                                    </Typography>
                                    
                                    <Typography variant="h6" color="text.secondary" sx={{ mb: 4, maxWidth: 600, fontWeight: 400 }}>
                                        {isAuthenticated 
                                            ? "I'm here to help you with infrastructure planning, assessments, reports, technical questions, and decision-making. Start a conversation to begin!"
                                            : "Ask me anything about cloud infrastructure, DevOps, Kubernetes, AWS, Azure, GCP, Alibaba Cloud, IBM Cloud, and more!"
                                        }
                                    </Typography>
                                    
                                    {/* Quick Action Chips */}
                                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'center', mb: 4 }}>
                                        {['AWS Architecture', 'Kubernetes Deployment', 'Cost Optimization', 'Security Best Practices', 'CI/CD Pipeline'].map((topic) => (
                                            <Chip
                                                key={topic}
                                                label={topic}
                                                variant="outlined"
                                                color="primary"
                                                onClick={() => setNewMessage(`Tell me about ${topic}`)}
                                                sx={{ 
                                                    cursor: 'pointer',
                                                    '&:hover': { bgcolor: 'primary.light' }
                                                }}
                                            />
                                        ))}
                                    </Box>

                                    <Box sx={{ display: 'flex', gap: 2, flexDirection: { xs: 'column', sm: 'row' } }}>
                                        {/* Show Continue Chat button if user has conversations (regardless of isAuthenticated flag) */}
                                        {(isAuthenticated || user) && conversations.length > 0 && (
                                            <Button
                                                variant="outlined"
                                                size="large"
                                                startIcon={<HistoryIcon />}
                                                onClick={() => loadConversation(conversations[0].id)}
                                                sx={{
                                                    borderRadius: 3,
                                                    px: 4,
                                                    py: 1.5,
                                                    fontSize: '1.1rem',
                                                    textTransform: 'none',
                                                    fontWeight: 600,
                                                    borderColor: 'primary.main',
                                                    color: 'primary.main',
                                                    '&:hover': {
                                                        bgcolor: 'primary.light',
                                                        borderColor: 'primary.dark',
                                                    }
                                                }}
                                            >
                                                Continue Last Chat
                                            </Button>
                                        )}

                                        {/* Always show "Start Chat" button - different behavior based on auth */}
                                        <Button
                                            variant="contained"
                                            size="large"
                                            startIcon={<AddIcon />}
                                            onClick={() => {
                                                if (isAuthenticated || user) {
                                                    setNewChatDialog(true);
                                                } else {
                                                    // For non-authenticated users, just start typing
                                                    if (textFieldRef.current) {
                                                        textFieldRef.current.focus();
                                                    }
                                                }
                                            }}
                                            sx={{
                                                borderRadius: 3,
                                                px: 4,
                                                py: 1.5,
                                                fontSize: '1.1rem',
                                                textTransform: 'none',
                                                fontWeight: 600,
                                                boxShadow: '0 4px 20px rgba(102, 126, 234, 0.3)',
                                            }}
                                        >
                                            {(isAuthenticated || user) ? 'Start New Conversation' : 'Start Chatting'}
                                        </Button>
                                    </Box>
                                    
                                    {!isAuthenticated && (
                                        <Typography variant="body2" color="text.secondary" sx={{ mt: 2, opacity: 0.8 }}>
                                            💡 Simple chat mode - just type your question and press Enter!
                                        </Typography>
                                    )}
                                </Box>
                            ) : (
                                <>
                                    {messages.map(renderMessage)}
                                    <div ref={messagesEndRef} />
                                </>
                            )}
                        </Box>
                        {(!currentConversation || currentConversation.status !== 'resolved') && (
                            <Paper
                                elevation={0}
                                sx={{
                                    p: 2,
                                    borderRadius: '0 0 16px 16px',
                                    borderTop: '1px solid',
                                    borderColor: 'divider',
                                    bgcolor: 'background.default'
                                }}
                            >
                                <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
                                    <TextField
                                        ref={textFieldRef}
                                        fullWidth
                                        multiline
                                        maxRows={4}
                                        placeholder={currentConversation ? "Type your message..." : "Ask me anything about cloud infrastructure..."}
                                        value={newMessage}
                                        onChange={(e) => setNewMessage(e.target.value)}
                                        sx={{
                                            '& .MuiOutlinedInput-root': {
                                                borderRadius: 3,
                                                bgcolor: 'background.paper',
                                                '&:hover': {
                                                    '& .MuiOutlinedInput-notchedOutline': {
                                                        borderColor: 'primary.main',
                                                    },
                                                },
                                            },
                                        }}
                                        onKeyPress={handleKeyPress}
                                        disabled={isSending}
                                        variant="outlined"
                                        size="small"
                                    />
                                    <IconButton
                                        color="primary"
                                        onClick={sendMessage}
                                        disabled={!newMessage.trim() || isSending}
                                        size="large"
                                        sx={{
                                            bgcolor: 'primary.main',
                                            color: 'primary.contrastText',
                                            borderRadius: 2,
                                            '&:hover': {
                                                bgcolor: 'primary.dark',
                                            },
                                            '&:disabled': {
                                                bgcolor: 'action.disabled',
                                            },
                                        }}
                                    >
                                        {isSending ? <CircularProgress size={24} color="inherit" /> : <SendIcon />}
                                    </IconButton>
                                </Box>
                                {!currentConversation && (
                                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                                        💡 You can ask general questions directly, or start a new conversation for more advanced features.
                                    </Typography>
                                )}
                            </Paper>
                        )}
                    </Box>
                </Box>
                
                {/* New Chat Dialog */}
                <Dialog open={newChatDialog} onClose={() => setNewChatDialog(false)} maxWidth="md" fullWidth>
                    <DialogTitle>Start New Conversation</DialogTitle>
                    <DialogContent>
                        <FormControl fullWidth sx={{ mt: 2 }}>
                            <InputLabel>Conversation Context</InputLabel>
                            <Select
                                value={selectedContext}
                                onChange={(e) => setSelectedContext(e.target.value)}
                                label="Conversation Context"
                            >
                                {CONVERSATION_CONTEXTS.map((context) => (
                                    <MenuItem key={context.value} value={context.value}>
                                        {context.icon} {context.label}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                        
                        {(selectedContext === 'assessment_help' || selectedContext === 'decision_making') && (
                            <FormControl fullWidth sx={{ mt: 2 }}>
                                <InputLabel>Related Assessment (Optional)</InputLabel>
                                <Select
                                    value={selectedAssessmentId}
                                    onChange={(e) => {
                                        const assessmentId = e.target.value;
                                        setSelectedAssessmentId(assessmentId);
                                        // Load reports for the selected assessment
                                        if (assessmentId) {
                                            loadReportsForAssessment(assessmentId);
                                        } else {
                                            setAvailableReports([]);
                                        }
                                    }}
                                    label="Related Assessment (Optional)"
                                >
                                    <MenuItem value="">
                                        <em>None</em>
                                    </MenuItem>
                                    {availableAssessments.map((assessment) => (
                                        <MenuItem key={assessment.id} value={assessment.id}>
                                            <Box>
                                                <Typography variant="body2">
                                                    {assessment.title}
                                                </Typography>
                                                <Typography variant="caption" color="text.secondary">
                                                    {assessment.status} • {formatDistanceToNow(new Date(assessment.created_at), { addSuffix: true })}
                                                </Typography>
                                            </Box>
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        )}
                        
                        {(selectedContext === 'report_analysis' || selectedContext === 'decision_making') && (
                            <FormControl fullWidth sx={{ mt: 2 }}>
                                <InputLabel>Related Report (Optional)</InputLabel>
                                <Select
                                    value={selectedReportId}
                                    onChange={(e) => setSelectedReportId(e.target.value)}
                                    label="Related Report (Optional)"
                                    disabled={loadingReports}
                                >
                                    <MenuItem value="">
                                        <em>None</em>
                                    </MenuItem>
                                    {loadingReports && (
                                        <MenuItem disabled>
                                            <em>Loading reports...</em>
                                        </MenuItem>
                                    )}
                                    {availableReports.map((report) => (
                                        <MenuItem key={report.id} value={report.id}>
                                            <Box>
                                                <Typography variant="body2">
                                                    {report.title}
                                                </Typography>
                                                <Typography variant="caption" color="text.secondary">
                                                    {report.status} • Compliance: {report.compliance_score}%
                                                </Typography>
                                            </Box>
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        )}
                        
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                            {selectedContext === 'report_analysis' && 
                                "I'll help you analyze your reports and understand the recommendations."
                            }
                            {selectedContext === 'assessment_help' && 
                                "I'll guide you through the assessment process and help with requirements."
                            }
                            {selectedContext === 'decision_making' && 
                                "I'll help you make informed decisions based on your assessments and reports."
                            }
                            {selectedContext === 'technical_support' && 
                                "I'll help you troubleshoot technical issues and problems."
                            }
                            {selectedContext === 'platform_guidance' && 
                                "I'll guide you through platform features and capabilities."
                            }
                            {selectedContext === 'general_inquiry' && 
                                "I'm here to help with any questions about infrastructure and cloud services."
                            }
                        </Typography>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => {
                            setNewChatDialog(false);
                            setSelectedAssessmentId('');
                            setSelectedReportId('');
                        }}>Cancel</Button>
                        <Button onClick={() => startNewConversation()} variant="contained">
                            Start Chat
                        </Button>
                    </DialogActions>
                </Dialog>
                
                {/* End Chat Dialog */}
                <Dialog open={endChatDialog} onClose={() => setEndChatDialog(false)} maxWidth="sm" fullWidth>
                    <DialogTitle>End Conversation</DialogTitle>
                    <DialogContent>
                        <Typography variant="body1" sx={{ mb: 2 }}>
                            This conversation will be saved to your chat history with an automatically generated title based on the discussion content.
                        </Typography>
                        <Typography variant="body1" sx={{ mb: 3 }}>
                            How would you rate your experience with this conversation?
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Typography variant="body2">Rating:</Typography>
                            <Rating
                                value={satisfactionRating}
                                onChange={(_, newValue) => setSatisfactionRating(newValue)}
                            />
                        </Box>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setEndChatDialog(false)}>Cancel</Button>
                        <Button onClick={endConversation} variant="contained">
                            End & Save Conversation
                        </Button>
                    </DialogActions>
                </Dialog>
                
                {/* Chat Settings Dialog */}
                <Dialog open={settingsDialog} onClose={() => setSettingsDialog(false)} maxWidth="sm" fullWidth>
                    <DialogTitle>Chat Settings</DialogTitle>
                    <DialogContent>
                        <Typography variant="body1" sx={{ mb: 3 }}>
                            Configure your chat preferences and settings.
                        </Typography>
                        
                        <Box sx={{ mb: 3 }}>
                            <Typography variant="h6" sx={{ mb: 2 }}>Chat Preferences</Typography>
                            
                            <FormControl fullWidth sx={{ mb: 2 }}>
                                <InputLabel>Default Context</InputLabel>
                                <Select
                                    value={selectedContext}
                                    onChange={(e) => setSelectedContext(e.target.value)}
                                    label="Default Context"
                                >
                                    {CONVERSATION_CONTEXTS.map((context) => (
                                        <MenuItem key={context.value} value={context.value}>
                                            {context.icon} {context.label}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        </Box>
                        
                        <Box sx={{ mb: 3 }}>
                            <Typography variant="h6" sx={{ mb: 2 }}>About</Typography>
                            <Typography variant="body2" color="text.secondary">
                                AI Infrastructure Assistant helps you with cloud architecture, DevOps, 
                                and infrastructure planning. The assistant uses advanced AI to provide 
                                expert guidance and recommendations.
                            </Typography>
                        </Box>
                        
                        <Box sx={{ mb: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                            <Typography variant="body2" color="info.contrastText">
                                💡 <strong>Tip:</strong> For the best experience, provide detailed context 
                                about your infrastructure needs and requirements.
                            </Typography>
                        </Box>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setSettingsDialog(false)}>Close</Button>
                        <Button onClick={() => {
                            setSettingsDialog(false);
                            // You could add logic to save settings here
                        }} variant="contained">
                            Save Settings
                        </Button>
                    </DialogActions>
                </Dialog>
                
                {/* Context Menu */}
                <Menu
                    anchorEl={menuAnchor}
                    open={Boolean(menuAnchor)}
                    onClose={() => setMenuAnchor(null)}
                >
                    <MenuItem onClick={() => {
                        const conversation = conversations.find(c => c.id === currentConversation?.id);
                        if (conversation) {
                            deleteConversation(conversation.id);
                        }
                        setMenuAnchor(null);
                    }}>
                        <DeleteIcon sx={{ mr: 1 }} />
                        Delete
                    </MenuItem>
                </Menu>
            </ResponsiveLayout>
        </ProtectedRoute>
    );
}