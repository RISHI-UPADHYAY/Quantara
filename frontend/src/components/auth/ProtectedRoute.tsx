import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'

export default function ProtectedRoute() {
    const { isAuthenticated, isLoading } = useAuth()
    const location = useLocation()

    if (isLoading) {
        return (
            <main
                aria-busy="true"
                className="flex min-h-screen items-center justify-center"
            >
                <p className="text-sm text-slate-500">
                    Restoring your Quantara session...
                </p>
            </main>
        )
    }

    if (!isAuthenticated) {
        return (
            <Navigate
                to="/login"
                replace
                state={{ from: location }}
            />
        )
    }

    return <Outlet />
}