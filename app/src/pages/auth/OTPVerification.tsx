import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Factory } from 'lucide-react';
import { Button, Input, Card } from '../../components/ui';
import { authApi } from '../../api/auth';

export default function OTPVerification() {
  const navigate = useNavigate();
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const email = localStorage.getItem('kf_user') ? JSON.parse(localStorage.getItem('kf_user')!).email : '';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await authApi.verifyOtp({ email, otp });
      navigate('/portal');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed');
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
          <h1 className="text-xl font-bold text-on-surface tracking-tight-display text-center mb-1">Verify your email</h1>
          <p className="text-sm text-tertiary text-center mb-6">
            We sent a code to <span className="text-on-surface">{email}</span>
          </p>
          {error && (
            <div className="mb-4 p-3 rounded-md bg-danger/10 text-danger text-xs">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Verification Code"
              value={otp}
              onChange={e => setOtp(e.target.value)}
              placeholder="Enter 6-digit code"
              required
              maxLength={6}
            />
            <Button type="submit" className="w-full" isLoading={isLoading}>
              Verify
            </Button>
          </form>
          <button className="mt-4 w-full text-center text-xs text-secondary hover:text-secondary/80 transition-colors">
            Resend code
          </button>
        </Card>
      </div>
    </div>
  );
}
