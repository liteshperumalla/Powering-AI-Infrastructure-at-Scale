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
    List,
    ListItem,
    ListItemText,
    ListItemSecondaryAction,
    Divider,
    Menu,
    MenuItem,
    Alert,
    Tooltip,
    FormControl,
    InputLabel,
    Select,
    Rating,
    Drawer,
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
import Navigation from '@/components/Navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
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
    
    // State management
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [currentConversation, setCurrentConversation] = useState<ConversationDetail | null>(null);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [newMessage, setNewMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isSending, setIsSending] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    // UI state
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [newChatDialog, setNewChatDialog] = useState(false);
    const [settingsDialog, setSettingsDialog] = useState(false);
    const [endChatDialog, setEndChatDialog] = useState(false);
    const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
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
        } catch (error) {
            console.error('Failed to start conversation:', error);
            setError('Failed to start new conversation');
        } finally {
            setIsLoading(false);
        }
    };
    
    const sendMessage = async () => {
        if (!newMessage.trim() || isSending || !currentConversation) return;
        
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
            // Send message to API
            const botResponse = await apiClient.sendMessage(currentConversation.id, {
                content: messageContent,
                context: currentConversation.context,
                assessment_id: currentConversation.assessment_id,
                report_id: currentConversation.report_id
            });
            
            // Add bot response to messages
            setMessages(prev => [...prev, botResponse]);
            
            // Update conversation in sidebar
            setConversations(prev => prev.map(conv => 
                conv.id === currentConversation.id 
                    ? { ...conv, message_count: conv.message_count + 2, last_activity: new Date().toISOString() }
                    : conv
            ));
            
        } catch (error) {
            console.error('Failed to send message:', error);
            setError('Failed to send message');
            
            // Remove the temporary user message on error
            setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
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
        if (!currentConversation) return;
        
        try {
            await apiClient.endConversation(currentConversation.id, satisfactionRating || undefined);
            
            // Update conversation status
            setConversations(prev => prev.map(conv => 
                conv.id === currentConversation.id 
                    ? { ...conv, status: 'resolved' }
                    : conv
            ));
            
            setEndChatDialog(false);
            setSatisfactionRating(null);
        } catch (error) {
            console.error('Failed to end conversation:', error);
            setError('Failed to end conversation');
        }
    };
    
    const formatMessageTime = (timestamp: string) => {
        return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
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
                        {message.metadata?.confidence && (
                            <span> • Confidence: {(message.metadata.confidence * 100).toFixed(0)}%</span>
                        )}
                    </Typography>
                </Paper>
            </Box>
        );
    };
    
    const sidebarContent = (
        <Box sx={{ width: 300, height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Header */}
            <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="h6">Chat History</Typography>
                    <IconButton
                        size="small"
                        onClick={() => setNewChatDialog(true)}
                        color="primary"
                    >
                        <AddIcon />
                    </IconButton>
                </Box>
            </Box>
            
            {/* Conversations List */}
            <List sx={{ flexGrow: 1, overflow: 'auto' }}>
                {conversations.map((conversation) => (
                    <ListItem
                        key={conversation.id}
                        button
                        selected={currentConversation?.id === conversation.id}
                        onClick={() => loadConversation(conversation.id)}
                        sx={{
                            flexDirection: 'column',
                            alignItems: 'stretch',
                            py: 1.5
                        }}
                    >
                        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                            <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                                <Typography
                                    variant="subtitle2"
                                    noWrap
                                    sx={{ fontWeight: conversation.escalated ? 'bold' : 'normal' }}
                                >
                                    {conversation.title}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                    {formatMessageTime(conversation.last_activity)} • {conversation.message_count} messages
                                </Typography>
                            </Box>
                            <IconButton
                                size="small"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setMenuAnchor(e.currentTarget);
                                }}
                            >
                                <MoreVertIcon fontSize="small" />
                            </IconButton>
                        </Box>
                        
                        <Box sx={{ display: 'flex', alignItems: 'center', mt: 1, gap: 1 }}>
                            <Chip
                                label={getContextLabel(conversation.context)}
                                size="small"
                                variant="outlined"
                                sx={{ fontSize: '0.7rem' }}
                            />
                            {conversation.escalated && (
                                <Chip
                                    label="Escalated"
                                    size="small"
                                    color="warning"
                                    sx={{ fontSize: '0.7rem' }}
                                />
                            )}
                        </Box>
                    </ListItem>
                ))}
                
                {conversations.length === 0 && !isLoading && (
                    <ListItem>
                        <ListItemText
                            primary="No conversations yet"
                            secondary="Start a new chat to begin"
                        />
                    </ListItem>
                )}
            </List>
            
            {/* Footer */}
            <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
                <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<SettingsIcon />}
                    onClick={() => setSettingsDialog(true)}
                >
                    Chat Settings
                </Button>
            </Box>
        </Box>
    );
    
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

    return (
        <ProtectedRoute>
            <Navigation title="AI Assistant">
                <Box sx={{ display: 'flex', height: 'calc(100vh - 128px)', position: 'relative' }}>
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
                                
                                {currentConversation && (
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
                                )}
                            </Box>
                            
                            {currentConversation && (
                                <Box>
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
                                    {error}
                                </Alert>
                            )}
                            
                            {isLoading && messages.length === 0 ? (
                                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                                    <CircularProgress />
                                </Box>
                            ) : !currentConversation ? (
                                <Box
                                    sx={{
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        height: '100%',
                                        textAlign: 'center'
                                    }}
                                >
                                    <AIIcon sx={{ fontSize: 80, color: 'primary.main', mb: 2 }} />
                                    <Typography variant="h4" gutterBottom>
                                        Welcome to AI Assistant
                                    </Typography>
                                    <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 600 }}>
                                        I'm here to help you with infrastructure planning, assessments, reports, 
                                        technical questions, and decision-making. Start a conversation to begin!
                                    </Typography>
                                    <Button
                                        variant="contained"
                                        size="large"
                                        startIcon={<AddIcon />}
                                        onClick={() => setNewChatDialog(true)}
                                    >
                                        Start New Conversation
                                    </Button>
                                </Box>
                            ) : (
                                <>
                                    {messages.map(renderMessage)}
                                    <div ref={messagesEndRef} />
                                </>
                            )}
                        </Box>
                        
                        {/* Message Input */}
                        {currentConversation && currentConversation.status !== 'resolved' && (
                            <Paper
                                elevation={3}
                                sx={{
                                    p: 2,
                                    borderRadius: 0,
                                    borderTop: '1px solid',
                                    borderColor: 'divider'
                                }}
                            >
                                <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
                                    <TextField
                                        ref={textFieldRef}
                                        fullWidth
                                        multiline
                                        maxRows={4}
                                        placeholder="Type your message..."
                                        value={newMessage}
                                        onChange={(e) => setNewMessage(e.target.value)}
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
                                    >
                                        {isSending ? <CircularProgress size={24} /> : <SendIcon />}
                                    </IconButton>
                                </Box>
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
                            End Conversation
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
            </Navigation>
        </ProtectedRoute>
    );
}