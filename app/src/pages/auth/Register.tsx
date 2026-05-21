import { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Factory, Upload, Eye, EyeOff } from 'lucide-react';
import { Button, Input, Card } from '../../components/ui';
import { useAuth } from '../../contexts/AuthContext';

export default function Register() {
  const navigate = useNavigate();
  const { register, isLoading } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [resume, setResume] = useState<File | null>(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isPasswordMatch = password === confirmPassword;
  const canSubmit = name && email && password && confirmPassword && isPasswordMatch;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!isPasswordMatch) {
      setError('Passwords do not match');
      return;
    }

    try {
      await register({
        name,
        email,
        password,
      });
      // Email verification is disabled for now, auto-login and go to portal
      navigate('/portal');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
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
          <h1 className="text-xl font-bold text-on-surface tracking-tight-display text-center mb-1">Create your account</h1>
          <p className="text-sm text-tertiary text-center mb-6">Start your application</p>
          {error && (
            <div className="mb-4 p-3 rounded-md bg-danger/10 text-danger text-xs">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Full Name"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="John Doe"
              required
            />
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
            />
            <div className="relative">
              <Input
                label="Password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Create a password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-8.5 text-tertiary hover:text-on-surface transition-colors"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            <div className="relative">
              <Input
                label="Confirm Password"
                type={showConfirmPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                placeholder="Confirm your password"
                required
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-8.5 text-tertiary hover:text-on-surface transition-colors"
              >
                {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {!isPasswordMatch && confirmPassword && (
              <p className="text-[10px] text-danger mt-1">Passwords do not match</p>
            )}
            <div className="space-y-1.5">
              <label className="block text-sm font-medium text-on-surface-variant">Resume (optional)</label>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={e => setResume(e.target.files?.[0] || null)}
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="w-full flex items-center justify-center gap-2 rounded-md border border-dashed border-[var(--border-ghost)] px-3 py-3 text-sm text-tertiary hover:border-secondary/40 hover:text-secondary transition-colors"
              >
                <Upload size={14} />
                {resume ? resume.name : 'Upload resume (PDF, DOC)'}
              </button>
            </div>
            <Button type="submit" className="w-full" isLoading={isLoading} disabled={!canSubmit}>
              Create Account
            </Button>
          </form>
          <p className="mt-4 text-center text-xs text-tertiary">
            Already have an account?{' '}
            <Link to="/login" className="text-secondary hover:text-secondary/80 transition-colors">
              Sign in
            </Link>
          </p>
        </Card>
      </div>
    </div>
  );
}
