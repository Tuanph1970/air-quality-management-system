import PropTypes from 'prop-types';

const VARIANT_STYLES = {
  default: 'bg-white/5 text-[var(--color-text-secondary)] border-[var(--color-border)]',
  success: 'bg-aqi-good/10 text-aqi-good border-aqi-good/20',
  warning: 'bg-aqi-unhealthy-sensitive/10 text-aqi-unhealthy-sensitive border-aqi-unhealthy-sensitive/20',
  danger: 'bg-aqi-unhealthy/10 text-aqi-unhealthy border-aqi-unhealthy/20',
  info: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  purple: 'bg-aqi-very-unhealthy/10 text-aqi-very-unhealthy border-aqi-very-unhealthy/20',
};

function Badge({ children, variant = 'default', dot = false, className = '' }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${VARIANT_STYLES[variant]} ${className}`}
    >
      {dot && (
        <span className={`w-1.5 h-1.5 rounded-full ${
          variant === 'success' ? 'bg-aqi-good' :
          variant === 'warning' ? 'bg-aqi-unhealthy-sensitive' :
          variant === 'danger' ? 'bg-aqi-unhealthy' :
          variant === 'info' ? 'bg-blue-400' :
          'bg-[var(--color-text-muted)]'
        }`} />
      )}
      {children}
    </span>
  );
}

Badge.propTypes = {
  children: PropTypes.node.isRequired,
  variant: PropTypes.oneOf(['default', 'success', 'warning', 'danger', 'info', 'purple']),
  dot: PropTypes.bool,
  className: PropTypes.string,
};

export default Badge;
