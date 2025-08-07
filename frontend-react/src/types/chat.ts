/**
 * Chat-related types and interfaces for the full-page chatbot interface
 */

// Core chat types
export interface Message {
    id: string;
    conversationId: string;
    type: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: Date;
    metadata: MessageMetadata;
    status: 'sending' | 'sent' | 'delivered' | 'failed';
    reactions?: MessageReaction[];
}

export interface MessageMetadata {
    intent?: string;
    confidence?: number;
    knowledgeSource?: 'llm' | 'faq' | 'report' | 'assessment';
    processingTime?: number;
    suggestions?: string[];
    requiresEscalation?: boolean;
    contextUsed?: string[];
}

export interface MessageReaction {
    type: 'like' | 'dislike' | 'helpful' | 'not_helpful';
    timestamp: Date;
}

export interface Conversation {
    id: string;
    title: string;
    status: 'active' | 'paused' | 'completed' | 'escalated';
    createdAt: Date;
    updatedAt: Date;
    messageCount: number;
    summary?: string;
    context: ConversationContext;
    metadata: ConversationMetadata;
}

export interface ConversationSummary {
    id: string;
    title: string;
    status: 'active' | 'paused' | 'completed' | 'escalated';
    lastMessage?: string;
    lastMessageAt?: Date;
    messageCount: number;
    createdAt: Date;
    updatedAt: Date;
}

export interface ConversationContext {
    userId: string;
    userContext?: UserContext;
    sessionId?: string;
    referrer?: string;
    initialIntent?: string;
}

export interface ConversationMetadata {
    tags?: string[];
    priority?: 'low' | 'medium' | 'high';
    category?: string;
    escalationReason?: string;
    satisfactionRating?: number;
}

export interface UserContext {
    profile: UserProfile;
    assessments: AssessmentSummary[];
    reports: ReportSummary[];
    preferences: UserPreferences;
    conversationHistory: ConversationSummary[];
}

export interface UserProfile {
    name: string;
    company: string;
    role: string;
    experienceLevel: 'beginner' | 'intermediate' | 'advanced';
    industry: string;
}

export interface AssessmentSummary {
    id: string;
    title: string;
    status: 'draft' | 'in_progress' | 'completed' | 'failed';
    businessRequirements: Record<string, any>;
    technicalRequirements: Record<string, any>;
    createdAt: Date;
}

export interface ReportSummary {
    id: string;
    title: string;
    type: string;
    keyFindings: string[];
    recommendations: string[];
    createdAt: Date;
}

export interface UserPreferences {
    technicalDepth: 'basic' | 'intermediate' | 'advanced';
    preferredProviders: string[];
    focusAreas: string[];
    communicationStyle: 'concise' | 'detailed';
}

// API request/response types
export interface CreateConversationRequest {
    title?: string;
    initialMessage?: string;
    context?: Partial<ConversationContext>;
}

export interface CreateConversationResponse {
    conversation: Conversation;
    message?: Message;
}

export interface SendMessageRequest {
    content: string;
    type?: 'user';
    metadata?: Partial<MessageMetadata>;
}

export interface SendMessageResponse {
    message: Message;
    response: Message;
}

export interface ConversationsResponse {
    conversations: ConversationSummary[];
    total: number;
    page: number;
    limit: number;
    hasMore: boolean;
}

export interface ConversationDetailResponse {
    conversation: Conversation;
    messages: Message[];
    hasMore: boolean;
    nextCursor?: string;
}

export interface UserContextResponse {
    context: UserContext;
    lastUpdated: Date;
}

export interface SearchRequest {
    query: string;
    conversationId?: string;
    messageType?: 'user' | 'assistant' | 'system';
    dateRange?: {
        start: Date;
        end: Date;
    };
    limit?: number;
    offset?: number;
}

export interface SearchResult {
    messageId: string;
    conversationId: string;
    conversationTitle: string;
    content: string;
    snippet: string;
    timestamp: Date;
    relevanceScore: number;
    highlights: string[];
}

export interface SearchResponse {
    results: SearchResult[];
    total: number;
    query: string;
    processingTime: number;
}

// WebSocket message types
export interface WebSocketMessage {
    type: 'chat_message' | 'typing_indicator' | 'message_stream' | 'connection_status' | 'error';
    data: any;
    timestamp: Date;
    messageId?: string;
}

export interface TypingIndicatorData {
    conversationId: string;
    isTyping: boolean;
    userId?: string;
}

export interface MessageStreamData {
    messageId: string;
    conversationId: string;
    token: string;
    isComplete: boolean;
}

export interface ConnectionStatusData {
    status: 'connected' | 'disconnected' | 'reconnecting';
    lastSeen?: Date;
}

// Chat state types
export type ConnectionStatus = 'connected' | 'disconnected' | 'reconnecting';

export interface ChatError {
    type: 'connection' | 'message_send' | 'load_conversation' | 'context_load';
    message: string;
    retryable: boolean;
    timestamp: Date;
    details?: any;
}

// Message actions
export type MessageAction =
    | { type: 'copy'; messageId: string }
    | { type: 'share'; messageId: string }
    | { type: 'react'; messageId: string; reaction: MessageReaction['type'] }
    | { type: 'feedback'; messageId: string; rating: number; comment?: string }
    | { type: 'edit'; messageId: string; newContent: string }
    | { type: 'delete'; messageId: string };

// Export utility types
export type MessageStatus = Message['status'];
export type ConversationStatus = Conversation['status'];
export type MessageType = Message['type'];