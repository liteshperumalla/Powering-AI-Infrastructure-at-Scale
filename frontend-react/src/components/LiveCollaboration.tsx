import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
    Box,
    Avatar,
    AvatarGroup,
    Chip,
    Typography,
    Stack,
    Tooltip,
    Badge,
    Paper,
    Popper,
    ClickAwayListener,
    List,
    ListItem,
    ListItemAvatar,
    ListItemText,
    Divider,
    IconButton,
    TextField,
    InputAdornment,
    Fade
} from '@mui/material';
import {
    Person as PersonIcon,
    Edit as EditIcon,
    Visibility as VisibilityIcon,
    Chat as ChatIcon,
    Send as SendIcon,
    Close as CloseIcon
} from '@mui/icons-material';

interface User {
    id: string;
    full_name: string;
    email: string;
    avatar?: string;
    color: string;
}

interface CollaboratorStatus {
    user: User;
    sessionId: string;
    isActive: boolean;
    lastSeen: Date;
    currentField?: string;
    cursorPosition?: {
        x: number;
        y: number;
        fieldId: string;
    };
    isTyping?: boolean;
}

interface FieldUpdate {
    fieldId: string;
    fieldValue: unknown;
    fieldType: string;
    userId: string;
    timestamp: Date;
}

interface ChatMessage {
    id: string;
    userId: string;
    userName: string;
    message: string;
    timestamp: Date;
    type: 'message' | 'system';
}

interface LiveCollaborationProps {
    websocket?: WebSocket | null;
    assessmentId: string;
    currentUser: User;
    onFieldUpdate?: (update: FieldUpdate) => void;
    onCursorUpdate?: (userId: string, position: { x: number; y: number; fieldId: string }) => void;
}

const LiveCollaboration: React.FC<LiveCollaborationProps> = ({
    websocket,
    assessmentId,
    currentUser,
    onFieldUpdate,
    onCursorUpdate
}) => {
    const [collaborators, setCollaborators] = useState<CollaboratorStatus[]>([]);
    const [fieldUpdates, setFieldUpdates] = useState<FieldUpdate[]>([]);
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [showChat, setShowChat] = useState(false);
    const [newMessage, setNewMessage] = useState('');
    const [unreadCount, setUnreadCount] = useState(0);

    const chatAnchorRef = useRef<HTMLButtonElement>(null);
    const chatInputRef = useRef<HTMLInputElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Generate user colors
    const getUserColor = useCallback((userId: string) => {
        const colors = [
            '#1976d2', '#dc004e', '#2e7d32', '#ed6c02', '#9c27b0',
            '#00796b', '#d32f2f', '#7b1fa2', '#388e3c', '#f57c00'
        ];
        const index = userId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
        return colors[index % colors.length];
    }, []);

    // WebSocket message handler
    const handleWebSocketMessage = useCallback((event: MessageEvent) => {
        try {
            const message = JSON.parse(event.data);

            switch (message.type) {
                case 'user_joined':
                    const newUser: User = {
                        id: message.data.user_id,
                        full_name: message.data.user_full_name,
                        email: message.data.user_email || '',
                        color: getUserColor(message.data.user_id)
                    };

                    setCollaborators(prev => {
                        const existing = prev.find(c => c.user.id === newUser.id);
                        if (existing) {
                            return prev.map(c =>
                                c.user.id === newUser.id
                                    ? { ...c, isActive: true, lastSeen: new Date() }
                                    : c
                            );
                        }

                        return [...prev, {
                            user: newUser,
                            sessionId: message.data.session_id,
                            isActive: true,
                            lastSeen: new Date()
                        }];
                    });

                    // Add system message
                    setChatMessages(prev => [...prev, {
                        id: Date.now().toString(),
                        userId: 'system',
                        userName: 'System',
                        message: `${newUser.full_name} joined the assessment`,
                        timestamp: new Date(),
                        type: 'system'
                    }]);
                    break;

                case 'user_left':
                    setCollaborators(prev =>
                        prev.map(c =>
                            c.user.id === message.data.user_id
                                ? { ...c, isActive: false, lastSeen: new Date() }
                                : c
                        )
                    );

                    // Add system message
                    const leavingUser = collaborators.find(c => c.user.id === message.data.user_id);
                    if (leavingUser) {
                        setChatMessages(prev => [...prev, {
                            id: Date.now().toString(),
                            userId: 'system',
                            userName: 'System',
                            message: `${leavingUser.user.full_name} left the assessment`,
                            timestamp: new Date(),
                            type: 'system'
                        }]);
                    }
                    break;

                case 'cursor_update':
                    setCollaborators(prev =>
                        prev.map(c =>
                            c.user.id === message.data.user_id
                                ? {
                                    ...c,
                                    cursorPosition: message.data.cursor_position,
                                    lastSeen: new Date()
                                }
                                : c
                        )
                    );

                    if (onCursorUpdate && message.data.cursor_position) {
                        onCursorUpdate(message.data.user_id, message.data.cursor_position);
                    }
                    break;

                case 'form_update':
                    const update: FieldUpdate = {
                        fieldId: message.data.field_id,
                        fieldValue: message.data.field_value,
                        fieldType: message.data.field_type,
                        userId: message.data.user_id,
                        timestamp: new Date(message.timestamp)
                    };

                    setFieldUpdates(prev => [update, ...(prev || []).slice(0, 49)]); // Keep last 50 updates

                    // Update collaborator status
                    setCollaborators(prev =>
                        prev.map(c =>
                            c.user.id === message.data.user_id
                                ? {
                                    ...c,
                                    currentField: message.data.field_id,
                                    lastSeen: new Date()
                                }
                                : c
                        )
                    );

                    if (onFieldUpdate) {
                        onFieldUpdate(update);
                    }
                    break;

                case 'chat_message':
                    const chatMessage: ChatMessage = {
                        id: message.data.message_id || Date.now().toString(),
                        userId: message.data.user_id,
                        userName: message.data.user_full_name,
                        message: message.data.message,
                        timestamp: new Date(message.timestamp),
                        type: 'message'
                    };

                    setChatMessages(prev => [...prev, chatMessage]);

                    // Increment unread count if chat is not open
                    if (!showChat && chatMessage.userId !== currentUser.id) {
                        setUnreadCount(prev => prev + 1);
                    }
                    break;
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }, [collaborators, getUserColor, onCursorUpdate, onFieldUpdate, showChat, currentUser.id]);

    // Setup WebSocket listener
    useEffect(() => {
        if (websocket) {
            websocket.addEventListener('message', handleWebSocketMessage);

            return () => {
                websocket.removeEventListener('message', handleWebSocketMessage);
            };
        }
    }, [websocket, handleWebSocketMessage]);

    // Auto-scroll chat to bottom
    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [chatMessages]);

    // Clear unread count when chat is opened
    useEffect(() => {
        if (showChat) {
            setUnreadCount(0);
        }
    }, [showChat]);

    // Send cursor position updates
    const sendCursorUpdate = useCallback((position: { x: number; y: number; fieldId: string }) => {
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({
                type: 'cursor_update',
                cursor_position: position,
                field_id: position.fieldId
            }));
        }
    }, [websocket]);

    // Send form field updates
    const sendFormUpdate = useCallback((fieldId: string, fieldValue: unknown, fieldType: string) => {
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({
                type: 'form_update',
                field_id: fieldId,
                field_value: fieldValue,
                field_type: fieldType
            }));
        }
    }, [websocket]);

    // Send chat message
    const sendChatMessage = useCallback(() => {
        if (newMessage.trim() && websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({
                type: 'chat_message',
                message: newMessage.trim(),
                user_full_name: currentUser.full_name
            }));

            setNewMessage('');
        }
    }, [newMessage, websocket, currentUser.full_name]);

    // Handle chat input key press
    const handleChatKeyPress = (event: React.KeyboardEvent) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendChatMessage();
        }
    };

    // Get active collaborators (excluding current user)
    const activeCollaborators = collaborators.filter(c =>
        c.isActive && c.user.id !== currentUser.id
    );

    // Format time for display
    const formatTime = (date: Date) => {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    // Get user initials for avatar
    const getUserInitials = (name: string) => {
        return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    };

    return (
        <Box>
            {/* Collaborators Display */}
            <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                    {activeCollaborators.length > 0
                        ? `${activeCollaborators.length} other${activeCollaborators.length > 1 ? 's' : ''} working on this assessment`
                        : 'You are working alone on this assessment'
                    }
                </Typography>

                {activeCollaborators.length > 0 && (
                    <AvatarGroup max={5} sx={{ '& .MuiAvatar-root': { width: 32, height: 32 } }}>
                        {activeCollaborators.map((collaborator) => (
                            <Tooltip
                                key={collaborator.user.id}
                                title={`${collaborator.user.full_name} ${collaborator.currentField ? `editing ${collaborator.currentField}` : 'online'}`}
                            >
                                <Avatar
                                    sx={{
                                        bgcolor: collaborator.user.color,
                                        fontSize: '0.75rem',
                                        border: collaborator.isTyping ? '2px solid #4caf50' : 'none'
                                    }}
                                >
                                    {collaborator.user.avatar ? (
                                        <img src={collaborator.user.avatar} alt={collaborator.user.full_name} />
                                    ) : (
                                        getUserInitials(collaborator.user.full_name)
                                    )}
                                </Avatar>
                            </Tooltip>
                        ))}
                    </AvatarGroup>
                )}

                {/* Chat Button */}
                <Tooltip title="Open chat">
                    <IconButton
                        ref={chatAnchorRef}
                        onClick={() => setShowChat(!showChat)}
                        size="small"
                    >
                        <Badge badgeContent={unreadCount} color="error">
                            <ChatIcon />
                        </Badge>
                    </IconButton>
                </Tooltip>
            </Stack>

            {/* Recent Field Updates */}
            {fieldUpdates.length > 0 && (
                <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary" gutterBottom>
                        Recent changes:
                    </Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap">
                        {(fieldUpdates || []).slice(0, 3).map((update, index) => {
                            const user = collaborators.find(c => c.user.id === update.userId);
                            return (
                                <Chip
                                    key={index}
                                    size="small"
                                    icon={<EditIcon />}
                                    label={`${user?.user.full_name || 'Someone'} updated ${update.fieldId}`}
                                    variant="outlined"
                                    sx={{ fontSize: '0.7rem' }}
                                />
                            );
                        })}
                    </Stack>
                </Box>
            )}

            {/* Chat Popper */}
            <Popper
                open={showChat}
                anchorEl={chatAnchorRef.current}
                placement="bottom-end"
                transition
                sx={{ zIndex: (theme) => theme.zIndex.modal - 100 }}
            >
                {({ TransitionProps }) => (
                    <Fade {...TransitionProps} timeout={350}>
                        <Paper
                            sx={{
                                width: 350,
                                height: 400,
                                display: 'flex',
                                flexDirection: 'column',
                                border: '1px solid',
                                borderColor: 'divider'
                            }}
                        >
                            {/* Chat Header */}
                            <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
                                <Stack direction="row" justifyContent="space-between" alignItems="center">
                                    <Typography variant="subtitle1">
                                        Team Chat
                                    </Typography>
                                    <IconButton size="small" onClick={() => setShowChat(false)}>
                                        <CloseIcon />
                                    </IconButton>
                                </Stack>
                            </Box>

                            {/* Chat Messages */}
                            <Box sx={{ flexGrow: 1, overflow: 'auto', p: 1 }}>
                                <List dense>
                                    {chatMessages.map((message) => (
                                        <ListItem key={message.id} alignItems="flex-start">
                                            {message.type === 'system' ? (
                                                <ListItemText
                                                    primary={
                                                        <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                                                            {message.message}
                                                        </Typography>
                                                    }
                                                />
                                            ) : (
                                                <>
                                                    <ListItemAvatar>
                                                        <Avatar
                                                            sx={{
                                                                width: 24,
                                                                height: 24,
                                                                bgcolor: getUserColor(message.userId),
                                                                fontSize: '0.7rem'
                                                            }}
                                                        >
                                                            {getUserInitials(message.userName)}
                                                        </Avatar>
                                                    </ListItemAvatar>
                                                    <ListItemText
                                                        primary={
                                                            <Stack direction="row" spacing={1} alignItems="baseline">
                                                                <Typography variant="caption" fontWeight="bold">
                                                                    {message.userName}
                                                                </Typography>
                                                                <Typography variant="caption" color="text.secondary">
                                                                    {formatTime(message.timestamp)}
                                                                </Typography>
                                                            </Stack>
                                                        }
                                                        secondary={
                                                            <Typography variant="body2">
                                                                {message.message}
                                                            </Typography>
                                                        }
                                                    />
                                                </>
                                            )}
                                        </ListItem>
                                    ))}
                                </List>
                                <div ref={messagesEndRef} />
                            </Box>

                            {/* Chat Input */}
                            <Box sx={{ p: 1, borderTop: '1px solid', borderColor: 'divider' }}>
                                <TextField
                                    ref={chatInputRef}
                                    fullWidth
                                    size="small"
                                    placeholder="Type a message..."
                                    value={newMessage}
                                    onChange={(e) => setNewMessage(e.target.value)}
                                    onKeyPress={handleChatKeyPress}
                                    InputProps={{
                                        endAdornment: (
                                            <InputAdornment position="end">
                                                <IconButton
                                                    size="small"
                                                    onClick={sendChatMessage}
                                                    disabled={!newMessage.trim()}
                                                >
                                                    <SendIcon />
                                                </IconButton>
                                            </InputAdornment>
                                        )
                                    }}
                                />
                            </Box>
                        </Paper>
                    </Fade>
                )}
            </Popper>

            {/* Cursor Indicators (would be positioned absolutely over form fields) */}
            {activeCollaborators.map((collaborator) =>
                collaborator.cursorPosition && (
                    <Box
                        key={collaborator.user.id}
                        sx={{
                            position: 'absolute',
                            left: collaborator.cursorPosition.x,
                            top: collaborator.cursorPosition.y,
                            pointerEvents: 'none',
                            zIndex: (theme) => theme.zIndex.drawer - 100
                        }}
                    >
                        <Box
                            sx={{
                                width: 2,
                                height: 20,
                                bgcolor: collaborator.user.color,
                                position: 'relative'
                            }}
                        >
                            <Chip
                                label={collaborator.user.full_name}
                                size="small"
                                sx={{
                                    position: 'absolute',
                                    top: -30,
                                    left: 0,
                                    bgcolor: collaborator.user.color,
                                    color: 'white',
                                    fontSize: '0.6rem',
                                    height: 20
                                }}
                            />
                        </Box>
                    </Box>
                )
            )}
        </Box>
    );
};

export default LiveCollaboration;
