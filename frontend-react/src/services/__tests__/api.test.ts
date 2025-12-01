import { apiClient } from '../api';

const createMockHeaders = (overrides: Record<string, string> = {}) => ({
    get: jest.fn((key: string) => {
        if (overrides[key]) return overrides[key];
        if (key.toLowerCase() === 'content-type') return 'application/json';
        if (key.toLowerCase() === 'content-length') return '1';
        return null;
    }),
});

const createMockResponse = (overrides: Partial<Response> & { body?: any } = {}) => {
    const { body, headers, ...rest } = overrides;
    return {
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: headers ?? createMockHeaders(),
        json: jest.fn().mockResolvedValue(body ?? {}),
        text: jest.fn().mockResolvedValue(''),
        ...rest,
    } as unknown as Response;
};

// Mock fetch
global.fetch = jest.fn();

describe('API Client', () => {
    beforeEach(() => {
        (global.fetch as jest.Mock).mockReset();
        (global.fetch as jest.Mock).mockResolvedValue(createMockResponse({ body: {} }));
    });

    describe('getCloudServices', () => {
        test('fetches cloud services successfully', async () => {
            const mockServices = [
                { id: '1', name: 'EC2', provider: 'aws', category: 'compute' },
                { id: '2', name: 'S3', provider: 'aws', category: 'storage' }
            ];

            (global.fetch as jest.Mock).mockResolvedValueOnce(
                createMockResponse({ body: { services: mockServices } })
            );

            const result = await apiClient.getCloudServices();
            
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('http://localhost:8000/api/cloud-services?'),
                expect.objectContaining({
                    headers: expect.objectContaining({
                        'Content-Type': 'application/json',
                        'Cache-Control': expect.any(String),
                    }),
                    signal: expect.any(AbortSignal)
                })
            );
            expect(result.services).toEqual(mockServices);
        });

        test('handles API errors gracefully', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce(createMockResponse({
                ok: false,
                status: 500,
                statusText: 'Internal Server Error',
                json: jest.fn().mockResolvedValue({ message: 'Internal Server Error' })
            }));

            await expect(apiClient.getCloudServices()).rejects.toThrow('Server error. Please try again later.');
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

            (global.fetch as jest.Mock).mockResolvedValueOnce(
                createMockResponse({ body: { assessments: mockAssessments } })
            );

            const result = await apiClient.getAssessments();
            
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('http://localhost:8000/api/v1/assessments'),
                expect.objectContaining({
                    headers: expect.objectContaining({
                        'Content-Type': 'application/json'
                    })
                })
            );
            expect(result.assessments).toEqual(mockAssessments);
        });

        test('handles unauthorized access', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce(createMockResponse({
                ok: false,
                status: 401,
                statusText: 'Unauthorized',
                json: jest.fn().mockResolvedValue({ message: 'Unauthorized' })
            }));

            await expect(apiClient.getAssessments()).rejects.toThrow('Unauthorized');
        });
    });

    describe('timeout handling', () => {
        test('applies correct timeout for cloud services', async () => {
            (global.fetch as jest.Mock).mockImplementationOnce((url, options) => {
                expect(options.signal).toBeInstanceOf(AbortSignal);
                return Promise.resolve(createMockResponse({ body: { services: [] } }));
            });

            await apiClient.getCloudServices();
            
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('http://localhost:8000/api/cloud-services?'),
                expect.objectContaining({
                    signal: expect.any(Object)
                })
            );
        });
    });

    describe('request headers', () => {
        test('includes correct content-type header', async () => {
            (global.fetch as jest.Mock).mockResolvedValueOnce(
                createMockResponse({ body: { services: [] } })
            );

            await apiClient.getCloudServices();
            
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('http://localhost:8000/api/cloud-services?'),
                expect.objectContaining({
                    headers: expect.objectContaining({
                        'Content-Type': 'application/json'
                    })
                })
            );
        });
    });
});
