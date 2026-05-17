import { useUser, useAuth } from '@clerk/react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import { tokenStore } from '../../api/token'
import { ROLE_HOME_ROUTES } from '../../utils/roles'

/**
 * Post-sign-in redirect page.
 * Syncs Clerk user with KF backend:
 *   1. Calls /api/auth/clerk-sync to link Clerk ↔ KF user by email
 *   2. If linked → redirect to role-based dashboard
 *   3. If 404 → redirect to register (no KF account for this email)
 */
export default function AuthRedirect() {
  const { isSignedIn, isLoaded } = useAuth()
  const { user: clerkUser } = useUser()
  const navigate = useNavigate()
  const [status, setStatus] = useState<'syncing' | 'redirecting' | 'error'>('syncing')
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    if (!isLoaded) return

    const activeUser = clerkUser // captured at effect time
    if (!isSignedIn || !activeUser) {
      navigate('/login', { replace: true })
      return
    }

    async function sync() {
      try {
        const user = activeUser
        if (!user) {
          navigate('/login', { replace: true })
          return
        }
        const email = user.primaryEmailAddress?.emailAddress
        if (!email) {
          setStatus('error')
          setErrorMsg('No email found on Clerk account.')
          return
        }

        // Call backend to link Clerk user ↔ KF user
        const data = await api.post<{
          access_token: string
          refresh_token: string
          user: { id: string; email: string; name: string; role: string }
        }>('/api/auth/clerk-sync', {
          clerk_id: user.id,
          email,
          name: user.fullName || '',
        })

        // Store token + user
        tokenStore.setAccessToken(data.access_token)
        const role = data.user.role.toLowerCase() as keyof typeof ROLE_HOME_ROUTES

        if (role in ROLE_HOME_ROUTES) {
          navigate(ROLE_HOME_ROUTES[role], { replace: true })
        } else {
          navigate('/', { replace: true })
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        // 404 means no KF account — redirect to register
        if (msg.includes('404') || msg.toLowerCase().includes('no existing account')) {
          navigate('/register', { replace: true })
        } else {
          setStatus('error')
          setErrorMsg(msg)
        }
      }
    }

    sync()
  }, [isLoaded, isSignedIn, clerkUser, navigate])

  if (status === 'error') {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <p className="text-[var(--color-danger)]">Sync failed: {errorMsg}</p>
        <button
          onClick={() => navigate('/login', { replace: true })}
          className="text-sm text-[var(--color-secondary)] hover:underline"
        >
          Back to sign in
        </button>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <p className="text-[var(--text-secondary)]">
        {status === 'syncing' ? 'Signing in...' : 'Redirecting...'}
      </p>
    </div>
  )
}
