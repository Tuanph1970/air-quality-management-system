
import { Link } from 'react-router-dom';
import { Home, AlertCircle } from 'lucide-react';

function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center">
        <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-6">
          <AlertCircle className="w-8 h-8 text-[var(--color-text-muted)]" />
        </div>
        <h1 className="text-display-lg font-display font-bold text-[var(--color-text-primary)] mb-2">
          404
        </h1>
        <p className="text-sm text-[var(--color-text-muted)] mb-6">
          Page not found
        </p>
        <Link to="/" className="btn-primary">
          <Home className="w-4 h-4" />
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}

export default NotFoundPage;
