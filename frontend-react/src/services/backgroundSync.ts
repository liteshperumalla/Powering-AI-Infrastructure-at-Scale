'use client';

import React from 'react';

interface SyncData {
    id: string;
    type: 'assessment' | 'report' | 'preference' | 'notification';
    action: 'create' | 'update' | 'delete';
    data: any;
    timestamp: number;
    retryCount: number;
    maxRetries: number;
}

interface SyncQueue {
    items: SyncData[];
    lastSync: number;
}

class BackgroundSyncService {
    private readonly STORAGE_KEY = 'background-sync-queue';
    private readonly MAX_RETRIES = 3;
    private readonly RETRY_DELAY = 2000;
    private readonly SYNC_INTERVAL = 30000; // 30 seconds
    
    private syncQueue: SyncQueue = { items: [], lastSync: 0 };
    private isOnline = typeof window !== 'undefined' ? navigator.onLine : true;
    private isSyncing = false;
    private syncInterval: NodeJS.Timeout | null = null;
    private retryTimeouts: Map<string, NodeJS.Timeout> = new Map();

    constructor() {
        this.loadQueueFromStorage();
        if (typeof window !== 'undefined') {
            this.setupEventListeners();
            this.startPeriodicSync();
        }
    }

    private setupEventListeners(): void {
        // Online/offline detection
        window.addEventListener('online', this.handleOnline.bind(this));
        window.addEventListener('offline', this.handleOffline.bind(this));

        // Page visibility for sync on focus
        document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));

        // Beforeunload to save queue
        window.addEventListener('beforeunload', this.saveQueueToStorage.bind(this));
    }

    private handleOnline(): void {
        console.log('🌐 Back online - starting background sync');
        this.isOnline = true;
        this.triggerSync();
        
        // Dispatch custom event for UI updates
        window.dispatchEvent(new CustomEvent('backgroundSyncOnline'));
    }

    private handleOffline(): void {
        console.log('📴 Gone offline - background sync paused');
        this.isOnline = false;
        
        // Dispatch custom event for UI updates
        window.dispatchEvent(new CustomEvent('backgroundSyncOffline'));
    }

    private handleVisibilityChange(): void {
        if (!document.hidden && this.isOnline) {
            this.triggerSync();
        }
    }

    private loadQueueFromStorage(): void {
        if (typeof window === 'undefined') return;
        
        try {
            const stored = localStorage.getItem(this.STORAGE_KEY);
            if (stored) {
                this.syncQueue = JSON.parse(stored);
            }
        } catch (error) {
            console.error('Failed to load sync queue from storage:', error);
            this.syncQueue = { items: [], lastSync: 0 };
        }
    }

    private saveQueueToStorage(): void {
        if (typeof window === 'undefined') return;
        
        try {
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.syncQueue));
        } catch (error) {
            console.error('Failed to save sync queue to storage:', error);
        }
    }

    private startPeriodicSync(): void {
        this.syncInterval = setInterval(() => {
            if (this.isOnline && this.syncQueue.items.length > 0) {
                this.triggerSync();
            }
        }, this.SYNC_INTERVAL);
    }

    public addToQueue(item: Omit<SyncData, 'id' | 'timestamp' | 'retryCount' | 'maxRetries'>): string {
        const syncData: SyncData = {
            id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            timestamp: Date.now(),
            retryCount: 0,
            maxRetries: this.MAX_RETRIES,
            ...item,
        };

        this.syncQueue.items.push(syncData);
        this.saveQueueToStorage();

        console.log(`📦 Added to sync queue: ${syncData.type} ${syncData.action}`, syncData);

        // Try immediate sync if online
        if (this.isOnline) {
            this.triggerSync();
        }

        return syncData.id;
    }

    public async triggerSync(): Promise<void> {
        if (!this.isOnline || this.isSyncing || this.syncQueue.items.length === 0) {
            return;
        }

        this.isSyncing = true;
        console.log(`🔄 Starting background sync (${this.syncQueue.items.length} items)`);

        // Dispatch sync start event
        window.dispatchEvent(new CustomEvent('backgroundSyncStart', {
            detail: { queueLength: this.syncQueue.items.length }
        }));

        const startTime = Date.now();
        let successCount = 0;
        let errorCount = 0;

        // Process items in batches to avoid overwhelming the server
        const batchSize = 5;
        const items = [...this.syncQueue.items];

        for (let i = 0; i < items.length; i += batchSize) {
            const batch = items.slice(i, i + batchSize);
            const batchPromises = batch.map(item => this.processSyncItem(item));
            
            const results = await Promise.allSettled(batchPromises);
            
            results.forEach((result, index) => {
                const item = batch[index];
                if (result.status === 'fulfilled' && result.value) {
                    successCount++;
                    this.removeFromQueue(item.id);
                } else {
                    errorCount++;
                    this.handleSyncError(item, result.status === 'rejected' ? result.reason : null);
                }
            });
        }

        this.syncQueue.lastSync = Date.now();
        this.saveQueueToStorage();
        this.isSyncing = false;

        const duration = Date.now() - startTime;
        console.log(`✅ Background sync completed in ${duration}ms: ${successCount} success, ${errorCount} errors`);

        // Dispatch sync complete event
        window.dispatchEvent(new CustomEvent('backgroundSyncComplete', {
            detail: { 
                duration, 
                successCount, 
                errorCount, 
                remainingItems: this.syncQueue.items.length 
            }
        }));
    }

    private async processSyncItem(item: SyncData): Promise<boolean> {
        try {
            const endpoint = this.getEndpointForItem(item);
            const method = this.getMethodForAction(item.action);
            
            const response = await fetch(endpoint, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`,
                },
                body: ['GET', 'DELETE'].includes(method) ? undefined : JSON.stringify(item.data),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Handle response if needed
            const result = await response.json();
            console.log(`✅ Synced ${item.type} ${item.action}:`, result);
            
            return true;
        } catch (error) {
            console.error(`❌ Failed to sync ${item.type} ${item.action}:`, error);
            throw error;
        }
    }

    private handleSyncError(item: SyncData, error: any): void {
        item.retryCount++;

        if (item.retryCount >= item.maxRetries) {
            console.error(`🚫 Max retries exceeded for ${item.type} ${item.action}, removing from queue`);
            this.removeFromQueue(item.id);
            
            // Dispatch error event for UI handling
            window.dispatchEvent(new CustomEvent('backgroundSyncError', {
                detail: { item, error: 'Max retries exceeded' }
            }));
        } else {
            console.warn(`🔄 Scheduling retry ${item.retryCount}/${item.maxRetries} for ${item.type} ${item.action}`);
            
            // Schedule retry with exponential backoff
            const delay = this.RETRY_DELAY * Math.pow(2, item.retryCount - 1);
            const timeoutId = setTimeout(() => {
                this.retryTimeouts.delete(item.id);
                if (this.isOnline) {
                    this.processSyncItem(item).then(success => {
                        if (success) {
                            this.removeFromQueue(item.id);
                        } else {
                            this.handleSyncError(item, 'Retry failed');
                        }
                    });
                }
            }, delay);
            
            this.retryTimeouts.set(item.id, timeoutId);
        }
    }

    private removeFromQueue(itemId: string): void {
        this.syncQueue.items = this.syncQueue.items.filter(item => item.id !== itemId);
        
        // Clear any pending retry timeout
        const timeoutId = this.retryTimeouts.get(itemId);
        if (timeoutId) {
            clearTimeout(timeoutId);
            this.retryTimeouts.delete(itemId);
        }
    }

    private getEndpointForItem(item: SyncData): string {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        
        switch (item.type) {
            case 'assessment':
                return item.action === 'create' 
                    ? `${baseUrl}/api/assessments`
                    : `${baseUrl}/api/assessments/${item.data.id}`;
            case 'report':
                return item.action === 'create'
                    ? `${baseUrl}/api/reports`
                    : `${baseUrl}/api/reports/${item.data.id}`;
            case 'preference':
                return `${baseUrl}/api/user/preferences`;
            case 'notification':
                return `${baseUrl}/api/notifications/${item.data.id}/read`;
            default:
                throw new Error(`Unknown sync item type: ${item.type}`);
        }
    }

    private getMethodForAction(action: SyncData['action']): string {
        switch (action) {
            case 'create': return 'POST';
            case 'update': return 'PUT';
            case 'delete': return 'DELETE';
            default: return 'POST';
        }
    }

    private getAuthToken(): string {
        // Get token from localStorage or Redux store
        return (typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null) || '';
    }

    // Public API methods
    public getQueueStatus() {
        return {
            isOnline: this.isOnline,
            isSyncing: this.isSyncing,
            queueLength: this.syncQueue.items.length,
            lastSync: this.syncQueue.lastSync,
            pendingRetries: this.retryTimeouts.size,
        };
    }

    public clearQueue(): void {
        this.syncQueue.items = [];
        this.retryTimeouts.forEach(timeout => clearTimeout(timeout));
        this.retryTimeouts.clear();
        this.saveQueueToStorage();
        console.log('🧹 Sync queue cleared');
    }

    public forceSync(): Promise<void> {
        return this.triggerSync();
    }

    public destroy(): void {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
        }
        this.retryTimeouts.forEach(timeout => clearTimeout(timeout));
        this.retryTimeouts.clear();
        this.saveQueueToStorage();
        
        // Remove event listeners
        window.removeEventListener('online', this.handleOnline.bind(this));
        window.removeEventListener('offline', this.handleOffline.bind(this));
        document.removeEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
        window.removeEventListener('beforeunload', this.saveQueueToStorage.bind(this));
    }

    // Convenience methods for common operations
    public syncAssessmentCreate(assessmentData: any): string {
        return this.addToQueue({
            type: 'assessment',
            action: 'create',
            data: assessmentData,
        });
    }

    public syncAssessmentUpdate(assessmentId: string, assessmentData: any): string {
        return this.addToQueue({
            type: 'assessment',
            action: 'update',
            data: { id: assessmentId, ...assessmentData },
        });
    }

    public syncNotificationRead(notificationId: string): string {
        return this.addToQueue({
            type: 'notification',
            action: 'update',
            data: { id: notificationId, read: true },
        });
    }

    public syncUserPreferences(preferences: any): string {
        return this.addToQueue({
            type: 'preference',
            action: 'update',
            data: preferences,
        });
    }
}

// Create a singleton instance
let backgroundSyncService: BackgroundSyncService | null = null;

export const getBackgroundSyncService = (): BackgroundSyncService => {
    if (!backgroundSyncService) {
        backgroundSyncService = new BackgroundSyncService();
    }
    return backgroundSyncService;
};

// React hook for using background sync
export const useBackgroundSync = () => {
    const [status, setStatus] = React.useState(getBackgroundSyncService().getQueueStatus());
    
    React.useEffect(() => {
        const service = getBackgroundSyncService();
        
        const updateStatus = () => setStatus(service.getQueueStatus());
        
        // Listen for sync events
        const handleSyncStart = () => updateStatus();
        const handleSyncComplete = () => updateStatus();
        const handleOnline = () => updateStatus();
        const handleOffline = () => updateStatus();
        
        window.addEventListener('backgroundSyncStart', handleSyncStart);
        window.addEventListener('backgroundSyncComplete', handleSyncComplete);
        window.addEventListener('backgroundSyncOnline', handleOnline);
        window.addEventListener('backgroundSyncOffline', handleOffline);
        
        // Update status periodically
        const interval = setInterval(updateStatus, 5000);
        
        return () => {
            window.removeEventListener('backgroundSyncStart', handleSyncStart);
            window.removeEventListener('backgroundSyncComplete', handleSyncComplete);
            window.removeEventListener('backgroundSyncOnline', handleOnline);
            window.removeEventListener('backgroundSyncOffline', handleOffline);
            clearInterval(interval);
        };
    }, []);
    
    return {
        ...status,
        sync: getBackgroundSyncService(),
    };
};

export default BackgroundSyncService;