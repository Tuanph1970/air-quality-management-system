import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, ArrowLeft, Mail, Copy, Check } from 'lucide-react';
import useAuthStore from '../store/authStore';

function ForgotPasswordPage() {
  const { forgotPassword, isLoading, error, clearError } = useAuthStore();
  const [email, setEmail] = useState('');
  const [result, setResult] = useState(null); // { message, reset_token }
  const [copied, setCopied] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    clearError();
    try {
      const data = await forgotPassword(email);
      setResult(data);
    } catch (_err) {
      // Error handled in store
    }
  }

  function copyToken() {
    if (result?.reset_token) {
      navigator.clipboard.writeText(result.reset_token);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

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
            Forgot Password
          </h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            Enter your email to receive a reset link
          </p>
        </div>

        {!result ? (
          <form onSubmit={handleSubmit} className="card !p-6 space-y-4">
            {error && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-400">
                {error}
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => { clearError(); setEmail(e.target.value); }}
                className="input"
                placeholder="you@example.com"
                required
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
                  <Mail className="w-4 h-4" />
                  Send Reset Link
                </>
              )}
            </button>
          </form>
        ) : (
          <div className="card !p-6 space-y-4">
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400">
              {result.message}
            </div>

            {result.reset_token && (
              <div className="space-y-2">
                <p className="text-xs font-medium text-[var(--color-text-secondary)]">
                  Development Mode — Reset Token:
                </p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 p-2 rounded-lg bg-[var(--color-surface-alt)] text-xs text-[var(--color-text-primary)] break-all font-mono border border-[var(--color-border)]">
                    {result.reset_token}
                  </code>
                  <button
                    type="button"
                    onClick={copyToken}
                    className="shrink-0 p-2 rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
                    title="Copy token"
                  >
                    {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
                <p className="text-xs text-[var(--color-text-muted)]">
                  Use this token on the{' '}
                  <Link to={`/reset-password?token=${result.reset_token}`} className="text-brand-400 hover:text-brand-300">
                    reset password page
                  </Link>
                  . Token expires in 30 minutes.
                </p>
              </div>
            )}
          </div>
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

export default ForgotPasswordPage;
