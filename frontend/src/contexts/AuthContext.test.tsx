
import { useAuth, AuthProvider } from './AuthContext'
import {
    afterEach,
    beforeEach,
    describe,
    expect,
    it,
    vi,
} from 'vitest'
import {
    cleanup,
    render,
    screen,
    waitFor,
} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode } from 'react'

import {
    getCurrentUser,
    login as loginRequest,
    logout as logoutRequest,
} from '../services/authService'

vi.mock('../services/authService', () => ({
    getCurrentUser: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    refreshTokens: vi.fn(),
}))

const mockUser = {
    id: 'user-123',
    name: 'Test User',
    email: 'test@example.com',
}

const mockTokens = {
    access_token: 'test-access-token',
    refresh_token: 'test-refresh-token',
    token_type: 'bearer',
}

function TestConsumer() {
    const { user, isAuthenticated, isLoading, login, logout } = useAuth()

    return (
        <div>
            <p>Loading: {String(isLoading)}</p>
            <p>Authenticated: {String(isAuthenticated)}</p>
            <p>User: {user?.email ?? 'none'}</p>

            <button
                onClick={() =>
                    void login({
                        email: 'test@example.com',
                        password: 'password123',
                    }).catch(() => undefined)
                }
            >
                Test login
            </button>

            <button onClick={() => void logout().catch(() => undefined)}>
                Test logout
            </button>
        </div>
    )
}

function renderAuthProvider(children: ReactNode = <TestConsumer />) {
    return render(
        <AuthProvider>{children}</AuthProvider>,
    )
}

beforeEach(() => {
    sessionStorage.clear()
    vi.clearAllMocks()
})

afterEach(() => {
    cleanup()
})

describe('AuthContext', () => {
    it('logs in and stores tokens and the current user', async () => {
        vi.mocked(loginRequest).mockResolvedValue(mockTokens)
        vi.mocked(getCurrentUser).mockResolvedValue(mockUser)

        const user = userEvent.setup()
        renderAuthProvider()

        await waitFor(() => {
            expect(screen.getByText('Loading: false')).toBeTruthy()
        })

        await user.click(screen.getByRole('button', { name: 'Test login' }))

        await waitFor(() => {
            expect(screen.getByText('Authenticated: true')).toBeTruthy()
            expect(screen.getByText('User: test@example.com')).toBeTruthy()
        })

        expect(sessionStorage.getItem('quantara_access_token')).toBe(
            mockTokens.access_token,
        )
        expect(sessionStorage.getItem('quantara_refresh_token')).toBe(
            mockTokens.refresh_token,
        )
    })

    it('clears local session when logout request fails', async () => {
        vi.mocked(logoutRequest).mockRejectedValue(
            new Error('Backend unavailable'),
        )

        sessionStorage.setItem(
            'quantara_access_token',
            mockTokens.access_token,
        )
        sessionStorage.setItem(
            'quantara_refresh_token',
            mockTokens.refresh_token,
        )

        vi.mocked(getCurrentUser).mockResolvedValue(mockUser)

        const user = userEvent.setup()
        renderAuthProvider()

        await waitFor(() => {
            expect(screen.getByText('Loading: false')).toBeTruthy()
        })

        await user.click(screen.getByRole('button', { name: 'Test logout' }))

        await waitFor(() => {
            expect(screen.getByText('Authenticated: false')).toBeTruthy()
            expect(screen.getByText('User: none')).toBeTruthy()
        })

        expect(sessionStorage.getItem('quantara_access_token')).toBeNull()
        expect(sessionStorage.getItem('quantara_refresh_token')).toBeNull()
    })

    
    it('clears tokens when loading the user fails after login', async () => {
        vi.mocked(loginRequest).mockResolvedValue(mockTokens)
        vi.mocked(getCurrentUser).mockRejectedValue(
            new Error('Unable to load user'),
        )

        const user = userEvent.setup()
        renderAuthProvider()

        await waitFor(() => {
            expect(screen.getByText('Loading: false')).toBeTruthy()
        })

        await user.click(screen.getByRole('button', { name: 'Test login' }))

        await waitFor(() => {
            expect(sessionStorage.getItem('quantara_access_token')).toBeNull()
            expect(sessionStorage.getItem('quantara_refresh_token')).toBeNull()
            expect(screen.getByText('Authenticated: false')).toBeTruthy()
            expect(screen.getByText('User: none')).toBeTruthy()
        })
    })

})
