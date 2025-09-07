/**
 * Unit tests for utility helper functions
 */

describe('Utility Helper Functions', () => {
    describe('formatCurrency', () => {
        test('formats currency correctly', () => {
            const formatCurrency = (amount: number): string => {
                return new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD',
                }).format(amount);
            };

            expect(formatCurrency(1000)).toBe('$1,000.00');
            expect(formatCurrency(1234.56)).toBe('$1,234.56');
            expect(formatCurrency(0)).toBe('$0.00');
            expect(formatCurrency(-500)).toBe('-$500.00');
        });
    });

    describe('calculatePercentage', () => {
        test('calculates percentage correctly', () => {
            const calculatePercentage = (value: number, total: number): number => {
                if (total === 0) return 0;
                return Math.round((value / total) * 100);
            };

            expect(calculatePercentage(25, 100)).toBe(25);
            expect(calculatePercentage(33, 100)).toBe(33);
            expect(calculatePercentage(1, 3)).toBe(33); // 33.33... rounded to 33
            expect(calculatePercentage(0, 100)).toBe(0);
            expect(calculatePercentage(50, 0)).toBe(0); // Division by zero handling
        });
    });

    describe('formatDate', () => {
        test('formats dates correctly', () => {
            const formatDate = (dateString: string): string => {
                const date = new Date(dateString);
                return date.toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                });
            };

            expect(formatDate('2024-01-15T10:30:00Z')).toBe('Jan 15, 2024');
            expect(formatDate('2023-12-31T23:59:59Z')).toBe('Dec 31, 2023');
        });

        test('handles invalid dates', () => {
            const formatDate = (dateString: string): string => {
                const date = new Date(dateString);
                if (isNaN(date.getTime())) {
                    return 'Invalid Date';
                }
                return date.toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                });
            };

            expect(formatDate('invalid-date')).toBe('Invalid Date');
            expect(formatDate('')).toBe('Invalid Date');
        });
    });

    describe('debounce', () => {
        test('debounces function calls', (done) => {
            let callCount = 0;
            const debouncedFn = debounce(() => {
                callCount++;
            }, 100);

            // Call multiple times rapidly
            debouncedFn();
            debouncedFn();
            debouncedFn();

            // Should not be called immediately
            expect(callCount).toBe(0);

            // Should be called once after delay
            setTimeout(() => {
                expect(callCount).toBe(1);
                done();
            }, 150);
        });

        function debounce<T extends (...args: any[]) => any>(
            func: T,
            wait: number
        ): (...args: Parameters<T>) => void {
            let timeout: NodeJS.Timeout;
            return (...args: Parameters<T>) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => func.apply(this, args), wait);
            };
        }
    });

    describe('validateEmail', () => {
        test('validates email addresses correctly', () => {
            const validateEmail = (email: string): boolean => {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                return emailRegex.test(email);
            };

            expect(validateEmail('test@example.com')).toBe(true);
            expect(validateEmail('user.name@domain.co.uk')).toBe(true);
            expect(validateEmail('invalid-email')).toBe(false);
            expect(validateEmail('test@')).toBe(false);
            expect(validateEmail('@domain.com')).toBe(false);
            expect(validateEmail('')).toBe(false);
        });
    });

    describe('generateId', () => {
        test('generates unique IDs', () => {
            const generateId = (): string => {
                return Math.random().toString(36).substr(2, 9);
            };

            const id1 = generateId();
            const id2 = generateId();
            
            expect(typeof id1).toBe('string');
            expect(typeof id2).toBe('string');
            expect(id1).not.toBe(id2);
            expect(id1.length).toBeGreaterThan(0);
            expect(id2.length).toBeGreaterThan(0);
        });
    });

    describe('deepClone', () => {
        test('creates deep copies of objects', () => {
            const deepClone = <T>(obj: T): T => {
                return JSON.parse(JSON.stringify(obj));
            };

            const original = {
                name: 'test',
                nested: { value: 42 },
                array: [1, 2, 3]
            };

            const cloned = deepClone(original);
            
            expect(cloned).toEqual(original);
            expect(cloned).not.toBe(original);
            expect(cloned.nested).not.toBe(original.nested);
            expect(cloned.array).not.toBe(original.array);

            // Modify cloned object
            cloned.nested.value = 100;
            expect(original.nested.value).toBe(42); // Original unchanged
        });
    });

    describe('arrayToMap', () => {
        test('converts array to map by key', () => {
            const arrayToMap = <T, K extends keyof T>(
                array: T[],
                key: K
            ): Map<T[K], T> => {
                return new Map(array.map(item => [item[key], item]));
            };

            const services = [
                { id: '1', name: 'EC2' },
                { id: '2', name: 'S3' },
            ];

            const serviceMap = arrayToMap(services, 'id');
            
            expect(serviceMap.get('1')).toEqual({ id: '1', name: 'EC2' });
            expect(serviceMap.get('2')).toEqual({ id: '2', name: 'S3' });
            expect(serviceMap.size).toBe(2);
        });
    });
});