
import { NavLink, useLocation } from 'react-router-dom';
import PropTypes from 'prop-types';
import {
  LayoutDashboard,
  Factory,
  Radio,
  AlertTriangle,
  Wind,
  Map,
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
  Activity,
} from 'lucide-react';

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/air-quality', label: 'Air Quality', icon: Wind },
  { path: '/factories', label: 'Factories', icon: Factory },
  { path: '/sensors', label: 'Sensors', icon: Radio },
  { path: '/alerts', label: 'Alerts', icon: AlertTriangle },
  { path: '/map', label: 'Map View', icon: Map },
  { path: '/reports', label: 'Reports', icon: FileText },
];

const BOTTOM_ITEMS = [
  { path: '/settings', label: 'Settings', icon: Settings },
];

function Sidebar({ collapsed, onToggle }) {
  const location = useLocation();

  return (
    <aside
      className={`fixed top-0 left-0 z-40 h-screen flex flex-col bg-[var(--color-bg-secondary)] border-r border-[var(--color-border)] transition-all duration-300 ${
        collapsed ? 'w-[68px]' : 'w-[240px]'
      }`}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 h-16 border-b border-[var(--color-border)]">
        <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-emerald-400 flex items-center justify-center">
          <Activity className="w-5 h-5 text-white" />
        </div>
        {!collapsed && (
          <div className="animate-fade-in">
            <span className="text-sm font-display font-bold text-[var(--color-text-primary)] tracking-tight">
              AQMS
            </span>
            <span className="block text-[10px] text-[var(--color-text-muted)] uppercase tracking-widest">
              Air Quality
            </span>
          </div>
        )}
      </div>

      {/* Nav Items */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-brand-600/10 text-brand-400 border border-brand-600/20'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-white/[0.03] border border-transparent'
              }`}
              title={collapsed ? item.label : undefined}
            >
              <Icon
                className={`flex-shrink-0 w-[18px] h-[18px] transition-colors ${
                  isActive ? 'text-brand-400' : 'text-[var(--color-text-muted)] group-hover:text-[var(--color-text-secondary)]'
                }`}
              />
              {!collapsed && (
                <span className="animate-fade-in truncate">{item.label}</span>
              )}
              {isActive && !collapsed && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-brand-400" />
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="px-2 py-3 border-t border-[var(--color-border)] space-y-1">
        {BOTTOM_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-brand-600/10 text-brand-400'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-white/[0.03]'
              }`}
              title={collapsed ? item.label : undefined}
            >
              <Icon className="flex-shrink-0 w-[18px] h-[18px] text-[var(--color-text-muted)]" />
              {!collapsed && <span className="animate-fade-in">{item.label}</span>}
            </NavLink>
          );
        })}

        {/* Collapse toggle */}
        <button
          onClick={onToggle}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] hover:bg-white/[0.03] transition-all duration-200"
        >
          {collapsed ? (
            <ChevronRight className="w-[18px] h-[18px]" />
          ) : (
            <>
              <ChevronLeft className="w-[18px] h-[18px]" />
              <span className="animate-fade-in">Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}

Sidebar.propTypes = {
  collapsed: PropTypes.bool.isRequired,
  onToggle: PropTypes.func.isRequired,
};

export default Sidebar;
