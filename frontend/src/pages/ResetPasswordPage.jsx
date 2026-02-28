import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Activity, Eye, EyeOff, ArrowLeft, ShieldCheck } from 'lucide-react';
import useAuthStore from '../store/authStore';

function ResetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { resetPassword, isLoading, error, clearError } = useAuthStore();

  const [form, setForm] = useState({
    token: searchParams.get('token') || '',
    newPassword: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [localError, setLocalError] = useState('');
  const [success, setSuccess] = useState('');

  function handleChange(e) {
    clearError();
    setLocalError('');
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLocalError('');

    if (!form.token.trim()) {
      setLocalError('Please enter the reset token.');
      return;
    }
    if (form.newPassword !== form.confirmPassword) {
      setLocalError('Passwords do not match.');
      return;
    }

    try {
      const data = await resetPassword(form.token.trim(), form.newPassword);
      setSuccess(data.message || 'Password reset successfully!');
      setTimeout(() => navigate('/login'), 2500);
    } catch (_err) {
      // Error handled in store
    }
  }

  const displayError = localError || error;

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
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
            Reset Password
          </h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            Enter your reset token and choose a new password
          </p>
        </div>

        {success ? (
          <div className="card !p-6">
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 mb-4">
              {success}
            </div>
            <p className="text-xs text-[var(--color-text-muted)] text-center">
              Redirecting to sign in...
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="card !p-6 space-y-4">
            {displayError && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-400">
                {displayError}
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">
                Reset Token
              </label>
              <input
                type="text"
                name="token"
                value={form.token}
                onChange={handleChange}
                className="input font-mono text-xs"
                placeholder="Paste your reset token here"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">
                New Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="newPassword"
                  value={form.newPassword}
                  onChange={handleChange}
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
                Confirm New Password
              </label>
              <div className="relative">
                <input
                  type={showConfirm ? 'text' : 'password'}
                  name="confirmPassword"
                  value={form.confirmPassword}
                  onChange={handleChange}
                  className="input pr-10"
                  placeholder="Re-enter your new password"
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

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full"
            >
              {isLoading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  Reset Password
                </>
              )}
            </button>
          </form>
        )}

        <div className="text-center mt-4">
          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to sign in
          </Link>
        </div>
      </div>
    </div>
  );
}

export default ResetPasswordPage;
