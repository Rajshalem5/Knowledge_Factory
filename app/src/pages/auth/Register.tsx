import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Factory } from 'lucide-react';
import { Button, Input, Card } from '../../components/ui';
import { useAuth } from '../../contexts/AuthContext';

export default function Register() {
  const navigate = useNavigate();
  const { register, isLoading } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [college, setCollege] = useState('');
  const [branch, setBranch] = useState('');
  const [cgpa, setCgpa] = useState('');
  const [passedOutYear, setPassedOutYear] = useState('');
  const [languageChoice, setLanguageChoice] = useState('Python');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    // Validate CGPA
    const cgpaValue = parseFloat(cgpa);
    if (isNaN(cgpaValue) || cgpaValue < 0 || cgpaValue > 10) {
      setError('CGPA must be between 0 and 10');
      return;
    }

    // Validate year
    const yearValue = parseInt(passedOutYear);
    if (isNaN(yearValue) || yearValue < 2000 || yearValue > 2030) {
      setError('Please enter a valid year');
      return;
    }

    const registerData = {
      name,
      email,
      password,
      college,
      branch,
      cgpa: cgpaValue,
      passed_out_year: yearValue,
      language_choice: languageChoice,
    };

    try {
      await register(registerData);
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
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Create a password (min 8 characters)"
              required
            />
            <Input
              label="College"
              value={college}
              onChange={e => setCollege(e.target.value)}
              placeholder="Your college name"
              required
            />
            <Input
              label="Branch"
              value={branch}
              onChange={e => setBranch(e.target.value)}
              placeholder="e.g., Computer Science"
              required
            />
            <Input
              label="CGPA"
              type="number"
              step="0.01"
              min="0"
              max="10"
              value={cgpa}
              onChange={e => setCgpa(e.target.value)}
              placeholder="e.g., 8.5"
              required
            />
            <Input
              label="Passed Out Year"
              type="number"
              min="2000"
              max="2030"
              value={passedOutYear}
              onChange={e => setPassedOutYear(e.target.value)}
              placeholder="e.g., 2024"
              required
            />
            <div className="space-y-1.5">
              <label className="block text-sm font-medium text-on-surface-variant">Preferred Language</label>
              <select
                value={languageChoice}
                onChange={e => setLanguageChoice(e.target.value)}
                className="w-full rounded-md border border-[var(--border-ghost)] bg-[var(--bg-surface)] px-3 py-2 text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/40"
                required
              >
                <option value="Python">Python</option>
                <option value="JavaScript">JavaScript</option>
                <option value="Java">Java</option>
                <option value="C++">C++</option>
                <option value="C">C</option>
              </select>
            </div>
            <Button type="submit" className="w-full" isLoading={isLoading}>
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
