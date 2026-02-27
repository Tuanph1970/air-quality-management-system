
import PropTypes from 'prop-types';

function StatCard({ label, value, icon: Icon, trend, trendLabel, variant = 'default', className = '' }) {
  const variantStyles = {
    default: 'border-[var(--color-border)]',
    good: 'border-aqi-good/20 shadow-aqi',
    warning: 'border-aqi-unhealthy-sensitive/20 shadow-aqi-warn',
    danger: 'border-aqi-unhealthy/20 shadow-aqi-danger',
  };

  return (
    <div className={`card ${variantStyles[variant]} ${className}`}>
      <div className="flex items-start justify-between mb-3">
        <span className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">
          {label}
        </span>
        {Icon && (
          <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center">
            <Icon className="w-4 h-4 text-[var(--color-text-muted)]" />
          </div>
        )}
      </div>

      <div className="flex items-end gap-3">
        <span className="text-display-sm font-display font-bold text-[var(--color-text-primary)]">
          {value}
        </span>

        {trend != null && (
          <span
            className={`text-xs font-mono font-medium mb-1 ${
              trend > 0 ? 'text-red-400' : trend < 0 ? 'text-aqi-good' : 'text-[var(--color-text-muted)]'
            }`}
          >
            {trend > 0 ? '+' : ''}{trend}%
          </span>
        )}
      </div>

      {trendLabel && (
        <p className="text-xs text-[var(--color-text-muted)] mt-1">{trendLabel}</p>
      )}
    </div>
  );
}

StatCard.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  icon: PropTypes.elementType,
  trend: PropTypes.number,
  trendLabel: PropTypes.string,
  variant: PropTypes.oneOf(['default', 'good', 'warning', 'danger']),
  className: PropTypes.string,
};

export default StatCard;
