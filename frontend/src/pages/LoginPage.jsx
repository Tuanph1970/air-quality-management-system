import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Activity, Eye, EyeOff, ArrowRight, UserPlus, LogIn } from 'lucide-react';
import useAuthStore from '../store/authStore';

const ROLES = [
  { value: 'PUBLIC', label: 'Public (Read-only)' },
  { value: 'FACTORY_OWNER', label: 'Factory Owner' },
  { value: 'INSPECTOR', label: 'Inspector' },
  { value: 'CITY_MANAGER', label: 'City Manager' },
  { value: 'ADMIN', label: 'Administrator' },
];

function LoginPage() {
  const navigate = useNavigate();
  const { login, register, isLoading, error, clearError } = useAuthStore();

  const [tab, setTab] = useState('login'); // 'login' | 'register'
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [success, setSuccess] = useState('');

  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [registerForm, setRegisterForm] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    role: 'PUBLIC',
    organization: '',
  });

  function handleTabChange(newTab) {
    clearError();
    setSuccess('');
    setTab(newTab);
  }

  function handleLoginChange(e) {
    clearError();
    setLoginForm({ ...loginForm, [e.target.name]: e.target.value });
  }

  function handleRegisterChange(e) {
    clearError();
    setRegisterForm({ ...registerForm, [e.target.name]: e.target.value });
  }

  async function handleLogin(e) {
    e.preventDefault();
    try {
      await login(loginForm);
      navigate('/');
    } catch (_err) {
      // Error handled in store
    }
  }

  async function handleRegister(e) {
    e.preventDefault();
    if (registerForm.password !== registerForm.confirmPassword) {
      useAuthStore.setState({ error: 'Passwords do not match' });
      return;
    }
    try {
      const payload = {
        email: registerForm.email,
        password: registerForm.password,
        full_name: registerForm.full_name,
        role: registerForm.role,
        organization: registerForm.organization || undefined,
      };
      await register(payload);
      setSuccess('Account created successfully! You can now sign in.');
      setRegisterForm({ email: '', password: '', confirmPassword: '', full_name: '', role: 'PUBLIC', organization: '' });
      setTab('login');
    } catch (_err) {
      // Error handled in store
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 noise-bg" />
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-600/5 rounded-full blur-[120px]" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-600/5 rounded-full blur-[120px]" />

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-500 to-emerald-400 flex items-center justify-center mx-auto mb-4 shadow-aqi">
            <Activity className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-display-sm font-display font-bold text-[var(--color-text-primary)]">
            AQMS Dashboard
          </h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            Air Quality Management System
          </p>
        </div>

        {/* Tab switcher */}
        <div className="flex rounded-xl overflow-hidden border border-[var(--color-border)] mb-4 bg-[var(--color-surface)]">
          <button
            type="button"
            onClick={() => handleTabChange('login')}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium transition-colors ${
              tab === 'login'
                ? 'bg-brand-500 text-white'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
            }`}
          >
            <LogIn className="w-4 h-4" />
            Sign In
          </button>
          <button
            type="button"
            onClick={() => handleTabChange('register')}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium transition-colors ${
              tab === 'register'
                ? 'bg-brand-500 text-white'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
            }`}
          >
            <UserPlus className="w-4 h-4" />
            Register
          </button>
        </div>

        {/* Success message */}
        {success && (
          <div className="mb-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400">
            {success}
          </div>
        )}

        {/* ── LOGIN FORM ── */}
        {tab === 'login' && (
          <form onSubmit={handleLogin} className="card !p-6 space-y-4">
            {error && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-400">
                {error}
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">
                Email
              </label>
              <input
                type="email"
                name="email"
                value={loginForm.email}
                onChange={handleLoginChange}
                className="input"
                placeholder="you@example.com"
                required
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-medium text-[var(--color-text-secondary)]">
                  Password
                </label>
                <Link
                  to="/forgot-password"
                  className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={loginForm.password}
                  onChange={handleLoginChange}
                  className="input pr-10"
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full"
            >
              {isLoading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  Sign in
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        )}

        {/* ── REGISTER FORM ── */}
        {tab === 'register' && (
          <form onSubmit={handleRegister} className="card !p-6 space-y-4">
            {error && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-400">
                {error}
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">
                Full Name
              </label>
              <input
                type="text"
                name="full_name"
                value={registerForm.full_name}
                onChange={handleRegisterChange}
                className="input"
                placeholder="John Doe"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">
                Email
              </label>
              <input
                type="email"
                name="email"
                value={registerForm.email}
                onChange={handleRegisterChange}
                className="input"
                placeholder="you@example.com"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={registerForm.password}
                  onChange={handleRegisterChange}
                  className="input pr-10"
                  placeholder="Min 8 chars, upper+lower+digit+symbol"
                  required
                  minLength={8}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">
                Confirm Password
              </label>
              <div className="relative">
                <input
                  type={showConfirm ? 'text' : 'password'}
                  name="confirmPassword"
                  value={registerForm.confirmPassword}
                  onChange={handleRegisterChange}
                  className="input pr-10"
                  placeholder="Re-enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]"
                >
                  {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">
                Role
              </label>
              <select
                name="role"
                value={registerForm.role}
                onChange={handleRegisterChange}
                className="input"
              >
                {ROLES.map((r) => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">
                Organization <span className="text-[var(--color-text-muted)]">(optional)</span>
              </label>
              <input
                type="text"
                name="organization"
                value={registerForm.organization}
                onChange={handleRegisterChange}
                className="input"
                placeholder="Your company or agency"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full"
            >
              {isLoading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  Create Account
                  <UserPlus className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        )}

        <p className="text-center text-xs text-[var(--color-text-muted)] mt-6">
          Air Quality Management System v1.0
        </p>
      </div>
    </div>
  );
}

export default LoginPage;
