import axios, {
    type InternalAxiosRequestConfig,
} from 'axios'

const api = axios.create({
    baseURL: '/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
})

const ACCESS_TOKEN_KEY = 'quantara_access_token'
const REFRESH_TOKEN_KEY = 'quantara_refresh_token'

interface TokenResponse {
    access_token: string
    refresh_token: string
    token_type: string
}

interface RetryableRequestConfig extends InternalAxiosRequestConfig {
    _retry?: boolean
}

let refreshPromise: Promise<string> | null = null

function clearSession() {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY)
    sessionStorage.removeItem(REFRESH_TOKEN_KEY)

    window.dispatchEvent(new Event('quantara:session-expired'))
}

async function refreshAccessToken(): Promise<string> {
    const refreshToken = sessionStorage.getItem(REFRESH_TOKEN_KEY)

    if (!refreshToken) {
        throw new Error('No refresh token available')
    }

    const response = await axios.post<TokenResponse>(
        '/api/v1/auth/refresh',
        { refresh_token: refreshToken },
        {
            headers: {
                'Content-Type': 'application/json',
            },
        },
    )

    const tokens = response.data

    //Save both tokens together because the backend rotates refresh tokens.
    sessionStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token)
    sessionStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)

    return tokens.access_token
}

api.interceptors.request.use((config) => {
    const accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY)

    if (accessToken) {
        config.headers.set('Authorization', `Bearer ${accessToken}`)
    }

    return config
})

api.interceptors.response.use(
    (response) => response,
    async (error: unknown) => {
        if (!axios.isAxiosError(error) || !error.config) {
            return Promise.reject(error)
        }

        const config = error.config as RetryableRequestConfig
        const status = error.response?.status
        const url = config.url ?? ''

        const isAuthenticationRequest = 
            url.includes('/auth/login') ||
            url.includes('/auth/register') ||
            url.includes('/auth/refresh') ||
            url.includes('/auth/logout')

        if (
            status !== 401 ||
            config._retry ||
            isAuthenticationRequest
        ) {
            return Promise.reject(error)
        }

        config._retry = true

        try {
            if (!refreshPromise) {
                refreshPromise = refreshAccessToken().finally(() => {
                    refreshPromise = null
                })
            }

            const newAccessToken = await refreshPromise

            config.headers.set(
                'Authorization',
                `Bearer ${newAccessToken}`,
            )

            return api(config)
        } catch (refreshError) {
            clearSession()
            return Promise.reject(refreshError)
        }
    },
)

export function getApiErrorMessage(
    error: unknown,
    fallback = 'Something went wrong. Please try again.',
): string {
    if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail

        if (typeof detail === 'string') {
            return detail
        }

        if (Array.isArray(detail)) {
            return detail
                .map((item: { msg?: string }) => item.msg ?? '')
                .filter(Boolean)
                .join(', ')
        }

        if (!error.response) {
            return 'Unable to connect to Quantara. Please check that the API is running.'
        }
    }

    return fallback
}

export default api