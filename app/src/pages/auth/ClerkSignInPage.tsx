import { SignIn } from '@clerk/react'
import { Link } from 'react-router-dom'

export default function ClerkSignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--bg-base)]">
      <div className="w-full max-w-md px-4">
        <SignIn />
        <p className="mt-4 text-center text-xs text-[var(--text-tertiary)]">
          New here?{' '}
          <Link to="/register" className="text-[var(--color-secondary)] hover:text-[var(--color-secondary)]/80 transition-colors">
            Create an account
          </Link>
          {' '}(collects college, branch, CGPA, etc.)
        </p>
      </div>
    </div>
  )
}
