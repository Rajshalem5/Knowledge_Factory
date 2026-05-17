import { SignUp } from '@clerk/react'

export default function ClerkSignUpPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--bg-base)]">
      <div className="w-full max-w-md px-4">
        <SignUp />
      </div>
    </div>
  )
}
