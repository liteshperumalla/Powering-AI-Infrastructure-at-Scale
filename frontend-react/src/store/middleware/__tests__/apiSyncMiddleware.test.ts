import { apiSyncMiddleware } from '../apiSyncMiddleware';
import { apiClient } from '../../../services/api';

jest.mock('../../../services/api', () => ({
    apiClient: { setStoredToken: jest.fn(), removeStoredToken: jest.fn() },
}));

const run = (token: string | null, action: { type: string; payload?: unknown }) => {
    const store = { getState: () => ({ auth: { token } }), dispatch: jest.fn() };
    const next = jest.fn((a) => a);
    apiSyncMiddleware(store as any)(next)(action);
    expect(next).toHaveBeenCalledWith(action);
};

describe('apiSyncMiddleware', () => {
    beforeEach(() => jest.clearAllMocks());

    test('keeps the stored token while auth is still initializing', () => {
        // Regression: auth/initialize/pending runs before the token is read from
        // storage; clearing here logged users out on every page reload.
        run(null, { type: 'auth/initialize/pending' });
        run(null, { type: 'auth/login/pending' });
        run(null, { type: 'auth/login/rejected' });
        expect(apiClient.removeStoredToken).not.toHaveBeenCalled();
    });

    test('syncs a token into the API client', () => {
        run('abc', { type: 'auth/setToken', payload: 'abc' });
        expect(apiClient.setStoredToken).toHaveBeenCalledWith('abc');
    });

    test.each([
        { type: 'auth/clearAuth' },
        { type: 'auth/logout/fulfilled' },
        { type: 'auth/setToken', payload: null },
    ])('removes the stored token on explicit sign-out: $type', (action) => {
        run(null, action);
        expect(apiClient.removeStoredToken).toHaveBeenCalledTimes(1);
    });

    test('ignores non-auth actions', () => {
        run(null, { type: 'ui/toggleTheme' });
        expect(apiClient.removeStoredToken).not.toHaveBeenCalled();
        expect(apiClient.setStoredToken).not.toHaveBeenCalled();
    });
});
