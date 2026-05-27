import { useNavigate } from 'react-router-dom';
import { Factory, Brain, Shield, BarChart3, ArrowRight, Zap, Eye, Moon, Sun } from 'lucide-react';
import { Button } from '../components/ui';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

const FEATURES = [
  {
    icon: Brain,
    title: 'AI-Powered Assessments',
    description: 'Automatically generated coding challenges tailored to each role, evaluated by intelligent scoring.',
  },
  {
    icon: Eye,
    title: 'Proctored Evaluations',
    description: 'Real-time proctoring detects tab switches, face anomalies, and copy-paste attempts.',
  },
  {
    icon: Shield,
    title: 'Bias-Free Selection',
    description: 'AI evaluation removes human bias — every candidate is scored on merit alone.',
  },
  {
    icon: BarChart3,
    title: 'End-to-End Pipeline',
    description: 'From application to selection, track every candidate through a clear, visual funnel.',
  },
];

export default function Landing() {
  console.log('[Landing] === RENDERING ===');
  console.log('[Landing] Path:', window.location.pathname);
  const navigate = useNavigate();
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      {/* Nav */}
      <nav className="flex items-center justify-between px-6 h-14 bg-[var(--bg-layer1)]">
        <div className="flex items-center gap-2">
          <Factory size={22} className="text-secondary" />
          <span className="font-bold text-sm">Knowledge Factory</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-md text-tertiary hover:text-on-surface hover:bg-surface-container-low transition-colors"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          {user ? (
            <Button size="sm" onClick={() => navigate('/portal')}>
              Dashboard
            </Button>
          ) : (
            <>
              <Button variant="ghost" size="sm" onClick={() => navigate('/login')}>
                Login
              </Button>
              <Button size="sm" onClick={() => navigate('/register')}>
                Apply Now
              </Button>
            </>
          )}
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-secondary/5 to-transparent pointer-events-none" />
        <div className="max-w-5xl mx-auto px-6 pt-24 pb-20 text-center relative">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-secondary/10 text-secondary text-xs font-medium mb-6">
            <Zap size={12} />
            AI-Powered Hiring Pipeline
          </div>
          <h1 className="text-5xl font-bold tracking-tight-display text-on-surface mb-6 text-balance">
            Hire smarter.
            <br />
            <span className="text-secondary">Evaluate faster.</span>
          </h1>
          <p className="text-lg text-on-surface-variant max-w-2xl mx-auto mb-8 text-balance">
            Knowledge Factory automates the entire intern hiring pipeline — from registration
            to AI-driven assessment and final selection — with fairness at every step.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Button size="lg" onClick={() => navigate('/register')}>
              Start Application
              <ArrowRight size={16} />
            </Button>
            <Button variant="secondary" size="lg" onClick={() => navigate('/login')}>
              Sign In
            </Button>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h2 className="text-2xl font-bold tracking-tight-display text-on-surface mb-3">Built for precision hiring</h2>
          <p className="text-sm text-tertiary">
            Every feature designed to remove friction and bias from the hiring process.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {FEATURES.map(feature => (
            <div
              key={feature.title}
              className="group p-6 rounded-md bg-[var(--bg-layer2)] ghost-shadow transition-colors"
            >
              <feature.icon size={24} className="text-secondary mb-4" />
              <h3 className="font-semibold text-on-surface tracking-tight-display mb-2">{feature.title}</h3>
              <p className="text-sm text-on-surface-variant">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pipeline visualization */}
      <section className="max-w-5xl mx-auto px-6 py-16">
        <div className="rounded-md bg-[var(--bg-layer2)] ghost-shadow p-8">
          <h2 className="text-xl font-bold text-on-surface tracking-tight-display mb-6 text-center">The Hiring Pipeline</h2>
          <div className="flex items-center justify-center gap-2 flex-wrap">
            {['Applied', 'Eligible', 'Round 1', 'Round 2', 'Round 3', 'Interview', 'Selected'].map((step, i, arr) => (
              <div key={step} className="flex items-center">
                <div className="flex flex-col items-center">
                  <div className="w-10 h-10 rounded-full bg-secondary/10 flex items-center justify-center text-xs font-bold text-secondary">
                    {i + 1}
                  </div>
                  <span className="mt-1.5 text-[10px] text-tertiary uppercase tracking-architectural">{step}</span>
                </div>
                {i < arr.length - 1 && (
                  <div className="w-8 h-px bg-[var(--border-ghost)] mb-5" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[var(--bg-layer1)] py-6 text-center text-xs text-tertiary">
        Knowledge Factory — Precision hiring, powered by AI.
      </footer>
    </div>
  );
}
