import { apiClient } from '../api';

// Mock fetch
global.fetch = jest.fn();

describe('API Client', () => {
    beforeEach(() => {
        (global.fetch as jest.Mock).mockClear();
    });

    describe('getCloudServices', () => {
        test('fetches cloud services successfully', async () => {
            const mockServices = [
                { id: '1', name: 'EC2', provider: 'aws', category: 'compute' },
                { id: '2', name: 'S3', provider: 'aws', category: 'storage' }
            ];

            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ services: mockServices })
            });

            const result = await apiClient.getCloudServices();
            
            expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/cloud-services/', {
                headers: { 'Content-Type': 'application/json' },
                signal: expect.any(AbortSignal)
            });
            expect(result.services).toEqual(mockServices);
        });

        test('handles API errors gracefully', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: false,
                status: 500,
                statusText: 'Internal Server Error'
            });

            await expect(apiClient.getCloudServices()).rejects.toThrow('Failed to fetch cloud services');
        });

        test('handles network errors', async () => {
            (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

            await expect(apiClient.getCloudServices()).rejects.toThrow('Network error');
        });
    });

    describe('getAssessments', () => {
        test('fetches assessments successfully', async () => {
            const mockAssessments = [
                { id: '1', name: 'Test Assessment', status: 'completed' }
            ];

            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ assessments: mockAssessments })
            });

            const result = await apiClient.getAssessments();
            
            expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/assessments/', {
                headers: { 'Content-Type': 'application/json' }
            });
            expect(result.assessments).toEqual(mockAssessments);
        });

        test('handles unauthorized access', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: false,
                status: 401,
                statusText: 'Unauthorized'
            });

            await expect(apiClient.getAssessments()).rejects.toThrow('Failed to fetch assessments');
        });
    });

    describe('timeout handling', () => {
        test('applies correct timeout for cloud services', async () => {
            (global.fetch as jest.Mock).mockImplementationOnce((url, options) => {
                expect(options.signal).toBeInstanceOf(AbortSignal);
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve({ services: [] })
                });
            });

            await apiClient.getCloudServices();
            
            expect(global.fetch).toHaveBeenCalledWith(
                'http://localhost:8000/api/cloud-services/',
                expect.objectContaining({
                    signal: expect.any(AbortSignal)
                })
            );
        });
    });

    describe('request headers', () => {
        test('includes correct content-type header', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve({ services: [] })
            });

            await apiClient.getCloudServices();
            
            expect(global.fetch).toHaveBeenCalledWith(
                'http://localhost:8000/api/cloud-services/',
                expect.objectContaining({
                    headers: expect.objectContaining({
                        'Content-Type': 'application/json'
                    })
                })
            );
        });
    });
});