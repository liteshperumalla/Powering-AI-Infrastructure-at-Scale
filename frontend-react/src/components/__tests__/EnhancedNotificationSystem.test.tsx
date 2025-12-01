import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import EnhancedNotificationSystem from '../EnhancedNotificationSystem';

// Mock fetch
global.fetch = jest.fn();

describe('EnhancedNotificationSystem', () => {
    beforeEach(() => {
        (global.fetch as jest.Mock).mockReset();
        (global.fetch as jest.Mock).mockResolvedValue({
            ok: true,
            json: () => Promise.resolve([]),
        });
    });

    test('renders notification bell icon', () => {
        render(<EnhancedNotificationSystem />);
        expect(screen.getByLabelText(/notifications/i)).toBeInTheDocument();
    });

    test('opens notification menu on click', async () => {
        const user = userEvent.setup();
        render(<EnhancedNotificationSystem />);
        
        const notificationButton = screen.getByLabelText(/notifications/i);
        await user.click(notificationButton);
        
        expect(screen.getByText('Notifications')).toBeInTheDocument();
    });

    test('displays loading state while fetching notifications', async () => {
        (global.fetch as jest.Mock).mockImplementation(() => 
            new Promise(resolve => setTimeout(() => resolve({
                ok: true,
                json: () => Promise.resolve([]),
                headers: { get: () => null }
            }), 100))
        );

        const user = userEvent.setup();
        render(<EnhancedNotificationSystem />);
        
        const notificationButton = screen.getByLabelText(/notifications/i);
        await user.click(notificationButton);
        
        expect(screen.getByText('Loading notifications...')).toBeInTheDocument();
    });

    test('displays empty state when no notifications', async () => {
        const user = userEvent.setup();
        render(<EnhancedNotificationSystem />);
        
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith('/api/api/v1/performance/alerts');
        });

        const notificationButton = screen.getByLabelText(/notifications/i);
        await user.click(notificationButton);
        
        expect(screen.getByText('No notifications')).toBeInTheDocument();
        expect(screen.getByText("You're all caught up!")).toBeInTheDocument();
    });

    test('handles fetch errors gracefully', async () => {
        (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

        const user = userEvent.setup();
        render(<EnhancedNotificationSystem />);
        
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalled();
        });

        const notificationButton = screen.getByLabelText(/notifications/i);
        await user.click(notificationButton);
        
        await waitFor(() => {
            expect(screen.getByText('No notifications')).toBeInTheDocument();
        });
    });

    test('updates badge count based on unread notifications', async () => {
        const mockNotifications = [
            { 
                id: '1', 
                title: 'Test Alert', 
                message: 'Something happened', 
                severity: 'warning', 
                acknowledged: false,
                timestamp: new Date().toISOString()
            },
            { 
                id: '2', 
                title: 'Test Alert 2', 
                message: 'All good', 
                severity: 'info', 
                acknowledged: true,
                timestamp: new Date().toISOString()
            }
        ];

        (global.fetch as jest.Mock)
            .mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockNotifications),
            })
            .mockResolvedValue({
                ok: true,
                json: () => Promise.resolve([]),
            });

        render(<EnhancedNotificationSystem />);
        
        await waitFor(() => {
            expect(screen.getAllByText('1').length).toBeGreaterThan(0); // Badge count for unread
        });
    });
});
