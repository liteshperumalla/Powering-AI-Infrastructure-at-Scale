'use client';

import React, { useState } from 'react';
import { Button, TextField, Paper, Typography, Box } from '@mui/material';

export default function TestChatPage() {
    const [message, setMessage] = useState('');
    const [response, setResponse] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const testSimpleChat = async () => {
        setIsLoading(true);
        setError('');
        setResponse('');

        try {
            console.log('Testing simple chat with message:', message);
            
            const url = 'http://localhost:8000/api/chat/simple';
            const payload = {
                message: message || 'Hello, can you help me?',
                session_id: `test_${Date.now()}`
            };

            console.log('Making request to:', url);
            console.log('Payload:', payload);

            const res = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });

            console.log('Response status:', res.status, res.statusText);

            if (!res.ok) {
                const errorText = await res.text();
                console.error('API Error:', errorText);
                setError(`HTTP ${res.status}: ${res.statusText}\n\n${errorText}`);
                return;
            }

            const result = await res.json();
            console.log('API Response:', result);
            setResponse(result.response || 'No response content');
            
        } catch (err) {
            console.error('Network Error:', err);
            setError(`Network Error: ${err.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Box sx={{ p: 4, maxWidth: 800, margin: '0 auto' }}>
            <Typography variant="h4" gutterBottom>
                🧪 Direct Chat API Test
            </Typography>
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                This page tests the chat API directly without any complex frontend logic.
            </Typography>

            <Paper sx={{ p: 3, mb: 3 }}>
                <TextField
                    fullWidth
                    label="Test Message"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Enter a message to test the AI assistant"
                    sx={{ mb: 2 }}
                />
                
                <Button 
                    variant="contained" 
                    onClick={testSimpleChat}
                    disabled={isLoading}
                    sx={{ mr: 2 }}
                >
                    {isLoading ? 'Testing...' : 'Test Chat API'}
                </Button>

                <Button 
                    variant="outlined" 
                    onClick={() => {
                        setMessage('');
                        setResponse('');
                        setError('');
                    }}
                >
                    Clear
                </Button>
            </Paper>

            {error && (
                <Paper sx={{ p: 2, mb: 2, bgcolor: '#ffebee' }}>
                    <Typography variant="h6" color="error">
                        ❌ Error:
                    </Typography>
                    <Typography variant="body2" component="pre" sx={{ mt: 1, whiteSpace: 'pre-wrap' }}>
                        {error}
                    </Typography>
                </Paper>
            )}

            {response && (
                <Paper sx={{ p: 2, bgcolor: '#e8f5e8' }}>
                    <Typography variant="h6" color="success.main">
                        ✅ AI Response:
                    </Typography>
                    <Typography variant="body1" sx={{ mt: 1, whiteSpace: 'pre-wrap' }}>
                        {response}
                    </Typography>
                </Paper>
            )}

            <Paper sx={{ p: 2, mt: 3, bgcolor: '#f5f5f5' }}>
                <Typography variant="h6">🔧 Debug Info:</Typography>
                <Typography variant="body2" component="div">
                    <strong>API URL:</strong> http://localhost:8000/api/chat/simple<br/>
                    <strong>Current Time:</strong> {new Date().toLocaleString()}<br/>
                    <strong>User Agent:</strong> {typeof window !== 'undefined' ? navigator.userAgent.substring(0, 100) + '...' : 'N/A (Server-side)'}
                </Typography>
            </Paper>
        </Box>
    );
}