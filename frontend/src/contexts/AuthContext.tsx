import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useState,
    type ReactNode,
} from 'react'

import {
    getCurrentUser,
    login as loginRequest,
    logout as logoutRequest,
    refreshTokens,
    type LoginCredentials,
    type User,
} from '../services/authService'

import type { AuthTokens } from '../services/authService'


interface AuthContextValue {
    user: User | null
    isAuthenticated: boolean
    isLoading: boolean
    login: (credentials: LoginCredentials) => Promise<void>
    logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

const ACCESS_TOKEN_KEY = 'quantara_access_token'
const REFRESH_TOKEN_KEY = 'quantara_refresh_token'

function saveTokens(
    tokens: AuthTokens,
) {
    sessionStorage.setItem(
        ACCESS_TOKEN_KEY,
        tokens.access_token,
    )

    sessionStorage.setItem(
        REFRESH_TOKEN_KEY,
        tokens.refresh_token,
    )
}

function clearTokens() {
    sessionStorage.removeItem(
        ACCESS_TOKEN_KEY,
    )

    sessionStorage.removeItem(
        REFRESH_TOKEN_KEY,
    )
}

export function AuthProvider(
    { children }: { children: ReactNode },
) {
    const [user, setUser] = useState<User | null>(null)
    const [isLoading, setIsLoading] = useState(true)

    const login = useCallback(
        async (credentials: LoginCredentials) => {
            const tokens = await loginRequest(credentials)
            saveTokens(tokens)

            try {
                const currentUser = await getCurrentUser(tokens.access_token)
                setUser(currentUser)
            } catch (error) {
                clearTokens()
                setUser(null)
                throw error
            }
        }
    , [])


    const logout = useCallback(async () => {
        const refreshToken = sessionStorage.getItem(REFRESH_TOKEN_KEY)

        clearTokens()
        setUser(null)

        if (refreshToken) {
            await logoutRequest(refreshToken)
        }
    }, [])

    useEffect(() => {
        let cancelled = false

        const handleSessionExpired = () => {
            clearTokens()
            setUser(null)
        }

        window.addEventListener(
            'quantara:session-expired',
            handleSessionExpired,
        )

        async function restoreSession() {
            const accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY)
            const refreshToken = sessionStorage.getItem(REFRESH_TOKEN_KEY)

            if (!accessToken || !refreshToken) {
                clearTokens()
                if (!cancelled) setIsLoading(false)
                
                return
            }

            try {
                let currentUser: User

                try {
                    currentUser = await getCurrentUser(accessToken)
                } catch {
                    const refreshedTokens = await refreshTokens(refreshToken)
                    saveTokens(refreshedTokens)
                    currentUser = await getCurrentUser(refreshedTokens.access_token)
                }

                if (!cancelled) setUser(currentUser)
                
            } catch {
                clearTokens()
                if (!cancelled) 
                    setUser(null)
            } finally {
                if (!cancelled)
                    setIsLoading(false)
            }
        }

        void restoreSession()

        return () => {
            cancelled = true
            window.removeEventListener(
                'quantara:session-expired',
                handleSessionExpired,
            )
        }
    }, [])

    return (
        <AuthContext.Provider
            value={{
                user,
                isAuthenticated: user !== null,
                isLoading,
                login,
                logout,
            }}
        >
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const context = useContext(AuthContext)

    if (!context) {
        throw new Error(
            'useAuth must be used within an AuthProvider'
        )
    }

    return context
}