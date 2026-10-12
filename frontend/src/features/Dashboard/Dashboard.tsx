import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";


export default function Dashboard() {
    const { user, logout } = useAuth()
    const navigate = useNavigate()
    const [isLoggingOut, setIsLoggingOut] = useState(false)

    const handleLogout = async () => {
        setIsLoggingOut(true)

        try {
            await logout()
        } catch (error) {
            // The local session is already cleared by AuthContext.
            // The backend may still need to revoke the refresh token.
            console.error('Backend logout request failed: ', error)
        } finally {
            navigate('/login', { replace: true })
        }
    }

    return (
        <main className="q-page">
            <header>
                <h1>Quantara Dashboard</h1>
                <p>
                    Welcome{user?.name ? `, ${user.name}` : ''}.
                </p>
                {user?.email && <p>{user.email}</p>}
            </header>

            <section className="q-card">
                <h2>Overview</h2>
                <p>
                    Your authenticated Quantara workspace is ready.
                </p>
            </section>

            <button
                type="button"
                className="q-button"
                onClick={handleLogout}
                disabled={isLoggingOut}
            >
                {isLoggingOut ? 'Signing out...' : 'Logout'}
            </button>
        </main>
    )
}