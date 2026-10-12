import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { getApiErrorMessage } from '../../services/api'
import { register } from '../../services/authService'

export default function Register() {
  const navigate = useNavigate()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Your passwords do not match.')
      return
    }

    setIsSubmitting(true)

    try {
      await register({
        name: name.trim(),
        email: email.trim(),
        password,
      })

      navigate('/login', {
        replace: true,
        state: {
          registrationSuccess: true,
          registeredEmail: email.trim(),
        },
      })
    } catch (err) {
      setError(
        getApiErrorMessage(err, 'Unable to create your account. Please try again.'),
      )
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
          <p className="q-eyebrow">Get started</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-[var(--q-navy)]">
            Create your account
          </h1>
          <p className="mt-3 text-sm leading-6 text-[var(--q-muted)]">
            Create your account to access Quantara's financial research workspace.
          </p>
        </div>

        <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
          <div>
            <label
              htmlFor="register-name"
              className="mb-2 block text-sm font-medium text-[var(--q-text)]"
            >
              Full name
            </label>
            <input
              id="register-name"
              name="name"
              type="text"
              autoComplete="name"
              required
              minLength={2}
              maxLength={120}
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Your full name"
              className="q-input"
            />
          </div>

          <div>
            <label
              htmlFor="register-email"
              className="mb-2 block text-sm font-medium text-[var(--q-text)]"
            >
              Work email
            </label>
            <input
              id="register-email"
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
              htmlFor="register-password"
              className="mb-2 block text-sm font-medium text-[var(--q-text)]"
            >
              Password
            </label>
            <input
              id="register-password"
              name="password"
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Create a password"
              className="q-input"
            />
            <p className="mt-2 text-xs text-[var(--q-muted)]">
              Use at least 8 characters.
            </p>
          </div>

          <div>
            <label
              htmlFor="register-confirm-password"
              className="mb-2 block text-sm font-medium text-[var(--q-text)]"
            >
              Confirm password
            </label>
            <input
              id="register-confirm-password"
              name="confirmPassword"
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              placeholder="Re-enter your password"
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
            {isSubmitting ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-[var(--q-muted)]">
          Already have an account?{' '}
          <Link
            to="/login"
            className="font-semibold text-[var(--q-brand)] hover:underline"
          >
            Sign in
          </Link>
        </p>
      </section>
    </main>
  )
}