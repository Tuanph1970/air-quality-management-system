import PropTypes from 'prop-types';

function Card({ children, title, subtitle, action, variant = 'default', padding = true, className = '', ...props }) {
  const variantStyles = {
    default: '',
    good: 'border-aqi-good/20 shadow-aqi',
    warning: 'border-aqi-unhealthy-sensitive/20 shadow-aqi-warn',
    danger: 'border-aqi-unhealthy/20 shadow-aqi-danger',
    flat: '!border-transparent !shadow-none',
  };

  return (
    <div className={`card ${variantStyles[variant]} ${padding ? '' : '!p-0'} ${className}`} {...props}>
      {(title || action) && (
        <div className="flex items-center justify-between mb-4">
          <div>
            {title && (
              <h3 className="text-sm font-display font-semibold text-[var(--color-text-primary)]">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-xs text-[var(--color-text-muted)]">{subtitle}</p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
}

Card.propTypes = {
  children: PropTypes.node,
  title: PropTypes.string,
  subtitle: PropTypes.string,
  action: PropTypes.node,
  variant: PropTypes.oneOf(['default', 'good', 'warning', 'danger', 'flat']),
  padding: PropTypes.bool,
  className: PropTypes.string,
};

export default Card;
