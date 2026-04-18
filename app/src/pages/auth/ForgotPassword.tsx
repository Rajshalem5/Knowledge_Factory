import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Factory, ArrowLeft } from 'lucide-react';
import { Button, Input, Card } from '../../components/ui';
import { authApi } from '../../api/auth';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await authApi.forgotPassword({ email });
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send reset email');
    } finally {
      setIsLoading(false);
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
          {sent ? (
            <div className="text-center">
              <h1 className="text-xl font-bold text-on-surface tracking-tight-display mb-2">Check your email</h1>
              <p className="text-sm text-tertiary mb-4">
                We sent a password reset link to <span className="text-on-surface">{email}</span>
              </p>
              <Link to="/login" className="text-sm text-secondary hover:text-secondary/80 transition-colors">
                Back to sign in
              </Link>
            </div>
          ) : (
            <>
              <h1 className="text-xl font-bold text-on-surface tracking-tight-display text-center mb-1">Reset password</h1>
              <p className="text-sm text-tertiary text-center mb-6">
                Enter your email and we'll send you a reset link.
              </p>
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
                <Button type="submit" className="w-full" isLoading={isLoading}>
                  Send Reset Link
                </Button>
              </form>
              <Link
                to="/login"
                className="mt-4 flex items-center justify-center gap-1 text-xs text-tertiary hover:text-on-surface-variant transition-colors"
              >
                <ArrowLeft size={12} />
                Back to sign in
              </Link>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
