import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../../contexts/AuthContext'
import { getApiErrorMessage } from '../../services/api'


interface LoginLocationState {
  registrationSuccess?: boolean
  registeredEmail?: string
  from?: {
    pathname?: string
  }
}

export default function Login() {
  const { login, isAuthenticated, isLoading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const redirectState = location.state as LoginLocationState | null
  const destination = redirectState?.from?.pathname || '/dashboard'
  const registrationSuccess = redirectState?.registrationSuccess === true
  const registeredEmail = redirectState?.registeredEmail

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-slate-500">Checking your session…</p>
      </main>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      await login({ email: email.trim(), password })
      navigate(destination, { replace: true })
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to sign in. Please try again.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--q-page)] px-4 py-12">
      <section className="q-card w-full max-w-md p-7 sm:p-9">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm font-semibold tracking-wide text-[var(--q-brand)]"
        >
          <span aria-hidden="true">←</span>
          QUANTARA
        </Link>

        <div className="mt-9">
          <p className="q-eyebrow">Welcome back</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-[var(--q-navy)]">
            Sign in to Quantara
          </h1>
          <p className="mt-3 text-sm leading-6 text-[var(--q-muted)]">
            Continue to your financial research workspace.
          </p>
        </div>

        {registrationSuccess && (
            <div
                role="status"
                className="mt-5 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
            >
                <p className="font-semibold">Account created successfully.</p>
                <p className="mt-1">
                    {registeredEmail
                        ? `You can now sign in with ${registeredEmail}.`
                        : `You can now sign in with your new account.`
                    }
                </p>
            </div>
        )}

        <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
          <div>
            <label
              htmlFor="login-email"
              className="mb-2 block text-sm font-medium text-[var(--q-text)]"
            >
              Work email
            </label>
            <input
              id="login-email"
              name="email"
              type="email"
              autoComplete="email"
              required
              maxLength={254}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@company.com"
              className="q-input"
            />
          </div>

          <div>
            <label
              htmlFor="login-password"
              className="mb-2 block text-sm font-medium text-[var(--q-text)]"
            >
              Password
            </label>
            <input
              id="login-password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              className="q-input"
            />
          </div>

          {error && (
            <div
              role="alert"
              className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="q-button q-button-primary w-full"
          >
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-[var(--q-muted)]">
          New to Quantara?{' '}
          <Link
            to="/register"
            className="font-semibold text-[var(--q-brand)] hover:underline"
          >
            Create an account
          </Link>
        </p>
      </section>
    </main>
  )
}