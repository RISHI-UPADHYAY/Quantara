
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './ProtectedRoute'

const authState = vi.hoisted(() => ({
    isAuthenticated: false,
    isLoading: false,
}))

vi.mock('../../contexts/AuthContext', () => ({
    useAuth: () => authState,
}))

afterEach(() => {
    cleanup()
    authState.isAuthenticated = false
    authState.isLoading = false
})

function renderProtectedRoute() {
    return render(
        <MemoryRouter initialEntries={['/dashboard']}>
            <Routes>
                <Route path="/login" element={<h1>Login Page</h1>} />
                <Route element={<ProtectedRoute />}>
                    <Route
                        path="/dashboard"
                        element={<h1>Protected Dashboard</h1>}
                    />
                </Route>
            </Routes>
        </MemoryRouter>,
    )
}

describe('ProtectedRoute', () => {
    it('redirects unauthenticated users to login', () => {
        authState.isAuthenticated = false
        authState.isLoading = false

        renderProtectedRoute()

        expect(
            screen.getByRole('heading', { name: 'Login Page' }),
        ).toBeTruthy()
    })

    it('renders the dashboard for authenticated users', () => {
        authState.isAuthenticated = true
        authState.isLoading = false

        renderProtectedRoute()

        expect(
            screen.getByRole('heading', { name: 'Protected Dashboard' }),
        ).toBeTruthy()
    })

    it('shows a loading message while restoring the session', () => {
        authState.isAuthenticated = false
        authState.isLoading = true

        renderProtectedRoute()

        expect(
            screen.getByText('Restoring your Quantara session...'),
        ).toBeTruthy()
    })
})
