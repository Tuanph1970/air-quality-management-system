
import PropTypes from 'prop-types';
import { getAqiLevel, formatAqi } from '../../utils/aqi';

function AqiBadge({ value, showLabel = false, size = 'sm' }) {
  const level = getAqiLevel(value);

  const sizeClasses = {
    sm: 'aqi-badge text-xs',
    md: 'aqi-badge text-sm px-4 py-1.5',
    lg: 'aqi-badge text-base px-5 py-2',
  };

  return (
    <span className={`${sizeClasses[size]} ${level.bgClass}`}>
      <span className="status-dot status-dot-active" style={{ backgroundColor: level.color, boxShadow: `0 0 6px ${level.color}60` }} />
      <span className="font-mono">{formatAqi(value)}</span>
      {showLabel && <span className="font-sans">{level.label}</span>}
    </span>
  );
}

AqiBadge.propTypes = {
  value: PropTypes.number,
  showLabel: PropTypes.bool,
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
};

export default AqiBadge;
