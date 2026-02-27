
import PropTypes from 'prop-types';
import { Bell, Search, User, LogOut } from 'lucide-react';
import useAuthStore from '../../store/authStore';

function Header({ title, subtitle }) {
  const { user, logout, isAuthenticated } = useAuthStore();

  return (
    <header className="sticky top-0 z-30 h-16 bg-[var(--color-bg-primary)]/80 glass border-b border-[var(--color-border)] px-6 flex items-center justify-between">
      {/* Title */}
      <div>
        <h1 className="text-lg font-display font-semibold text-[var(--color-text-primary)]">
          {title}
        </h1>
        {subtitle && (
          <p className="text-xs text-[var(--color-text-muted)]">{subtitle}</p>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        {/* Search */}
        <div className="relative hidden md:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
          <input
            type="text"
            placeholder="Search..."
            className="input pl-9 w-64 bg-[var(--color-bg-card)] text-sm"
          />
        </div>

        {/* Notifications */}
        <button className="btn-ghost relative p-2.5 rounded-xl">
          <Bell className="w-[18px] h-[18px]" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-aqi-unhealthy rounded-full" />
        </button>

        {/* User */}
        {isAuthenticated && (
          <div className="flex items-center gap-3 ml-2 pl-3 border-l border-[var(--color-border)]">
            <div className="w-8 h-8 rounded-xl bg-brand-600/20 flex items-center justify-center">
              <User className="w-4 h-4 text-brand-400" />
            </div>
            <div className="hidden lg:block">
              <p className="text-sm font-medium text-[var(--color-text-primary)] leading-tight">
                {user?.full_name || 'User'}
              </p>
              <p className="text-[11px] text-[var(--color-text-muted)]">
                {user?.role || 'Operator'}
              </p>
            </div>
            <button
              onClick={logout}
              className="btn-ghost p-2 rounded-xl text-[var(--color-text-muted)] hover:text-red-400"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

Header.propTypes = {
  title: PropTypes.string.isRequired,
  subtitle: PropTypes.string,
};

export default Header;
