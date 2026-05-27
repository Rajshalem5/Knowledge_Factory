import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Factory } from 'lucide-react';
import { Button, Input, Card } from '../../components/ui';
import { useAuth } from '../../contexts/AuthContext';
import { getSafeHomeRoute } from '../../utils/roles';

export default function Login() {
  const navigate = useNavigate();
  const { login, isLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const userData = await login(email, password);
      const rawRole = userData.role || 'candidate';
      const normalizedRole = rawRole.toLowerCase().replace(/_/g, '');
      const target = getSafeHomeRoute(normalizedRole);
      console.log(`[Login] Success. User: ${userData.email}, RawRole: ${rawRole}, NormalizedRole: ${normalizedRole}, Redirecting to: ${target}`);
      navigate(target);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  const handleOAuth = async (provider: 'google' | 'github') => {
    try {
      await clerk.client.signIn.authenticateWithRedirect({
        strategy: provider === 'google' ? 'oauth_google' : 'oauth_github',
        redirectUrl: '/redirect',
        redirectUrlComplete: '/redirect',
      });
    } catch {
      // Fallback: navigate to sign-in page
      navigate('/sign-in');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-base)] px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center justify-center gap-2 mb-8">
          <Factory size={24} className="text-secondary" />
          <span className="font-bold">Knowledge Factory</span>
        </div>
        <Card padding="lg">
          <h1 className="text-xl font-bold text-on-surface tracking-tight-display text-center mb-1">Welcome back</h1>
          <p className="text-sm text-tertiary text-center mb-6">Sign in to your account</p>

          {/* Clerk social login buttons — redirect directly to OAuth provider */}
          <div className="space-y-2 mb-4">
            <button
              onClick={() => handleOAuth('google')}
              className="w-full flex items-center justify-center gap-3 px-4 py-2.5 rounded-md border border-[var(--border-ghost)] bg-white dark:bg-[var(--color-surface-container-low)] hover:bg-gray-50 dark:hover:bg-[var(--color-surface-container-lowest)] transition-colors text-sm font-medium"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" xmlns="http://www.w3.org/2000/svg">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              Continue with Google
            </button>
            <button
              onClick={() => handleOAuth('github')}
              className="w-full flex items-center justify-center gap-3 px-4 py-2.5 rounded-md border border-[var(--border-ghost)] bg-white dark:bg-[var(--color-surface-container-low)] hover:bg-gray-50 dark:hover:bg-[var(--color-surface-container-lowest)] transition-colors text-sm font-medium"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              Continue with GitHub
            </button>
          </div>

          <div className="flex items-center gap-3 mb-4">
            <div className="flex-1 h-px bg-[var(--border-ghost)]" />
            <span className="text-xs text-tertiary">or sign in with password</span>
            <div className="flex-1 h-px bg-[var(--border-ghost)]" />
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-md bg-danger/10 text-danger text-xs">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
            />
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
            <div className="flex justify-end">
              <Link to="/forgot-password" className="text-xs text-secondary hover:text-secondary/80 transition-colors">
                Forgot password?
              </Link>
            </div>
            <Button type="submit" className="w-full" isLoading={isLoading}>
              Sign In
            </Button>
          </form>
          <p className="mt-4 text-center text-xs text-tertiary">
            Don't have an account?{' '}
            <Link to="/register" className="text-secondary hover:text-secondary/80 transition-colors">
              Apply now
            </Link>
          </p>
        </Card>
      </div>
    </div>
  );
}
