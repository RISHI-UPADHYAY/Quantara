import api from './api'

export interface User {
    id: string
    name: string
    email: string
}

export interface AuthTokens {
    access_token: string
    refresh_token: string
    token_type: string
}

export interface LoginCredentials {
    email: string
    password: string
}

export interface RegisterPayload {
    name: string
    email: string
    password: string
}

export async function login(
    credentials: LoginCredentials,
): Promise<AuthTokens> {
    const response = await api.post<AuthTokens>(
        '/auth/login',
        credentials,
    )

    return response.data
}

export async function register(
    payload: RegisterPayload,
) : Promise<User> {
    const response = await api.post<User>(
        '/auth/register',
        payload,
    )

    return response.data
}

export async function refreshTokens(
    refreshToken: string,
): Promise<AuthTokens> {
    const response = await api.post<AuthTokens>(
        '/auth/refresh',
        { refresh_token: refreshToken },
    )

    return response.data
}

export async function getCurrentUser(
    accessToken: string,
): Promise<User> {
    const response = await api.get<User>(
        '/users/me',
        {
            headers: {
                Authorization: `Bearer ${accessToken}`,
            },
        },
    )

    return response.data
}

export async function logout(
    refreshToken: string,
): Promise<void> {
    await api.post(
        '/auth/logout',
        {
            refresh_token: refreshToken,
        }
    )
}