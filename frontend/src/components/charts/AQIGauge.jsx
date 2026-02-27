import PropTypes from 'prop-types';
import { getAqiLevel, formatAqi } from '../../utils/aqi';

function AQIGauge({ value, size = 160, showLabel = true, className = '' }) {
  const level = getAqiLevel(value);
  const percentage = Math.min((value || 0) / 500, 1);
  const circumference = 2 * Math.PI * 60;
  const strokeDashoffset = circumference * (1 - percentage * 0.75);
  const rotation = -225;

  return (
    <div className={`flex flex-col items-center ${className}`}>
      <div className="relative" style={{ width: size, height: size * 0.7 }}>
        <svg
          width={size}
          height={size * 0.7}
          viewBox="0 0 160 112"
          className="overflow-visible"
        >
          {/* Background arc */}
          <circle
            cx="80"
            cy="80"
            r="60"
            fill="none"
            stroke="var(--color-border)"
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * 0.25}
            transform={`rotate(${rotation} 80 80)`}
          />
          {/* Value arc */}
          <circle
            cx="80"
            cy="80"
            r="60"
            fill="none"
            stroke={level.color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            transform={`rotate(${rotation} 80 80)`}
            style={{
              filter: `drop-shadow(0 0 6px ${level.color}60)`,
              transition: 'stroke-dashoffset 1s ease-out, stroke 0.5s ease',
            }}
          />
        </svg>

        {/* Center value */}
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-1">
          <span
            className="text-3xl font-display font-bold font-mono tabular-nums leading-none"
            style={{ color: level.color }}
          >
            {formatAqi(value)}
          </span>
          {showLabel && (
            <span className="text-[10px] text-[var(--color-text-muted)] mt-1 uppercase tracking-wider font-medium">
              {level.label}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

AQIGauge.propTypes = {
  value: PropTypes.number,
  size: PropTypes.number,
  showLabel: PropTypes.bool,
  className: PropTypes.string,
};

export default AQIGauge;
