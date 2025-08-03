import { useEffect, useRef, useState, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../store';

interface WebSocketConfig {
    url: string;
    protocols?: string | string[];
    reconnectInterval?: number;
    maxReconnectAttempts?: number;
    heartbeatInterval?: number;
    onOpen?: (event: Event) => void;
    onClose?: (event: CloseEvent) => void;
    onError?: (event: Event) => void;
    onMessage?: (event: MessageEvent) => void;
}

interface WebSocketState {
    socket: WebSocket | null;
    isConnected: boolean;
    isConnecting: boolean;
    error: string | null;
    reconnectAttempts: number;
    lastMessage: MessageEvent | null;
}

export const useWebSocket = (config: WebSocketConfig) => {
    const [state, setState] = useState<WebSocketState>({
        socket: null,
        isConnected: false,
        isConnecting: false,
        error: null,
        reconnectAttempts: 0,
        lastMessage: null
    });

    const {
        url,
        protocols,
        reconnectInterval = 3000,
        maxReconnectAttempts = 5,
        heartbeatInterval = 30000,
        onOpen,
        onClose,
        onError,
        onMessage
    } = config;

    const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
    const heartbeatTimeoutRef = useRef<NodeJS.Timeout>();
    const shouldReconnectRef = useRef(true);

    // Get auth token from Redux store
    const authToken = useSelector((state: RootState) => state.auth.token);

    const connect = useCallback(() => {
        if (state.isConnecting || state.isConnected) {
            return;
        }

        setState(prev => ({ ...prev, isConnecting: true, error: null }));

        try {
            // Add auth token to WebSocket URL
            const wsUrl = authToken
                ? `${url}${url.includes('?') ? '&' : '?'}token=${authToken}`
                : url;

            const socket = new WebSocket(wsUrl, protocols);

            socket.onopen = (event) => {
                setState(prev => ({
                    ...prev,
                    socket,
                    isConnected: true,
                    isConnecting: false,
                    error: null,
                    reconnectAttempts: 0
                }));

                // Start heartbeat
                startHeartbeat(socket);

                onOpen?.(event);
            };

            socket.onclose = (event) => {
                setState(prev => ({
                    ...prev,
                    socket: null,
                    isConnected: false,
                    isConnecting: false
                }));

                // Clear heartbeat
                if (heartbeatTimeoutRef.current) {
                    clearTimeout(heartbeatTimeoutRef.current);
                }

                onClose?.(event);

                // Attempt reconnection if not manually closed
                if (shouldReconnectRef.current && event.code !== 1000) {
                    scheduleReconnect();
                }
            };

            socket.onerror = (event) => {
                setState(prev => ({
                    ...prev,
                    error: 'WebSocket connection error',
                    isConnecting: false
                }));

                onError?.(event);
            };

            socket.onmessage = (event) => {
                setState(prev => ({ ...prev, lastMessage: event }));
                onMessage?.(event);
            };

        } catch (error) {
            setState(prev => ({
                ...prev,
                error: error instanceof Error ? error.message : 'Connection failed',
                isConnecting: false
            }));
        }
    }, [url, protocols, authToken, onOpen, onClose, onError, onMessage]);

    const disconnect = useCallback(() => {
        shouldReconnectRef.current = false;

        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }

        if (heartbeatTimeoutRef.current) {
            clearTimeout(heartbeatTimeoutRef.current);
        }

        if (state.socket) {
            state.socket.close(1000, 'Manual disconnect');
        }

        setState(prev => ({
            ...prev,
            socket: null,
            isConnected: false,
            isConnecting: false,
            error: null,
            reconnectAttempts: 0
        }));
    }, [state.socket]);

    const scheduleReconnect = useCallback(() => {
        if (state.reconnectAttempts >= maxReconnectAttempts) {
            setState(prev => ({
                ...prev,
                error: `Max reconnection attempts (${maxReconnectAttempts}) reached`
            }));
            return;
        }

        setState(prev => ({
            ...prev,
            reconnectAttempts: prev.reconnectAttempts + 1
        }));

        reconnectTimeoutRef.current = setTimeout(() => {
            connect();
        }, reconnectInterval * Math.pow(2, state.reconnectAttempts)); // Exponential backoff
    }, [state.reconnectAttempts, maxReconnectAttempts, reconnectInterval, connect]);

    const startHeartbeat = useCallback((socket: WebSocket) => {
        const sendHeartbeat = () => {
            if (socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({
                    type: 'heartbeat',
                    timestamp: new Date().toISOString()
                }));

                heartbeatTimeoutRef.current = setTimeout(sendHeartbeat, heartbeatInterval);
            }
        };

        heartbeatTimeoutRef.current = setTimeout(sendHeartbeat, heartbeatInterval);
    }, [heartbeatInterval]);

    const sendMessage = useCallback((message: string | object) => {
        if (state.socket && state.isConnected) {
            const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
            state.socket.send(messageStr);
            return true;
        }
        return false;
    }, [state.socket, state.isConnected]);

    const sendTypedMessage = useCallback((type: string, data: unknown) => {
        return sendMessage({
            type,
            data,
            timestamp: new Date().toISOString()
        });
    }, [sendMessage]);

    // Auto-connect when component mounts and auth token is available
    useEffect(() => {
        if (authToken) {
            shouldReconnectRef.current = true;
            connect();
        }

        return () => {
            disconnect();
        };
    }, [authToken, connect, disconnect]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            shouldReconnectRef.current = false;
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (heartbeatTimeoutRef.current) {
                clearTimeout(heartbeatTimeoutRef.current);
            }
        };
    }, []);

    return {
        ...state,
        connect,
        disconnect,
        sendMessage,
        sendTypedMessage,
        reconnect: () => {
            disconnect();
            setTimeout(connect, 100);
        }
    };
};

// Specialized hook for assessment-specific WebSocket connections
export const useAssessmentWebSocket = (assessmentId: string) => {
    const baseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const url = `${baseUrl}/ws/${assessmentId}`;

    return useWebSocket({ url });
};

// Specialized hook for general system WebSocket connections
export const useSystemWebSocket = () => {
    const baseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const url = `${baseUrl}/ws`;

    return useWebSocket({ url });
};

export default useWebSocket;