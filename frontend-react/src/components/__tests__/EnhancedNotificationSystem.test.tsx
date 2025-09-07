import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import EnhancedNotificationSystem from '../EnhancedNotificationSystem';

// Mock fetch
global.fetch = jest.fn();

describe('EnhancedNotificationSystem', () => {
    beforeEach(() => {
        (global.fetch as jest.Mock).mockClear();
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
                json: () => Promise.resolve([])
            }), 100))
        );

        const user = userEvent.setup();
        render(<EnhancedNotificationSystem />);
        
        const notificationButton = screen.getByLabelText(/notifications/i);
        await user.click(notificationButton);
        
        expect(screen.getByText('Loading notifications...')).toBeInTheDocument();
    });

    test('displays empty state when no notifications', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: () => Promise.resolve([])
        });

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
        
        expect(screen.getByText('No notifications')).toBeInTheDocument();
    });

    test('updates badge count based on unread notifications', async () => {
        const mockNotifications = [
            { id: '1', title: 'Test Alert', severity: 'warning', acknowledged: false },
            { id: '2', title: 'Test Alert 2', severity: 'info', acknowledged: true }
        ];

        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: () => Promise.resolve(mockNotifications)
        });

        render(<EnhancedNotificationSystem />);
        
        await waitFor(() => {
            expect(screen.getByText('1')).toBeInTheDocument(); // Badge count for unread
        });
    });
});