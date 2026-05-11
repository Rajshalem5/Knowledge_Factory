import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Factory } from 'lucide-react';
import { Button, Input, Card } from '../../components/ui';
import { useAuth } from '../../contexts/AuthContext';
import { ROLE_HOME_ROUTES } from '../../utils/roles';

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
      const role = (userData.role || 'candidate') as keyof typeof ROLE_HOME_ROUTES;
      navigate(ROLE_HOME_ROUTES[role] || '/portal');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
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
