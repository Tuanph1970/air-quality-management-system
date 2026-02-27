import PropTypes from 'prop-types';
import { Radio, Signal, SignalLow, SignalMedium, MapPin, Clock } from 'lucide-react';
import StatusBadge from '../common/StatusBadge';
import { formatTimeAgo } from '../../utils/format';

function SensorCard({ sensor, onClick, className = '' }) {
  const BatteryIcon =
    sensor.battery_level > 70 ? Signal :
    sensor.battery_level > 30 ? SignalMedium :
    SignalLow;

  const batteryColor =
    sensor.battery_level > 70 ? 'text-aqi-good' :
    sensor.battery_level > 30 ? 'text-aqi-unhealthy-sensitive' :
    'text-aqi-unhealthy';

  return (
    <button
      onClick={() => onClick?.(sensor)}
      className={`card group text-left w-full transition-all duration-300 hover:border-[var(--color-border-light)] hover:shadow-card-hover ${className}`}
    >
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center flex-shrink-0">
          <Radio className="w-5 h-5 text-blue-400" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-sm font-display font-semibold text-[var(--color-text-primary)] truncate">
              {sensor.name}
            </h3>
            <StatusBadge status={sensor.status || 'offline'} />
          </div>

          <p className="text-xs text-[var(--color-text-muted)] mb-3 capitalize">
            {sensor.type || 'Unknown type'}
          </p>

          <div className="grid grid-cols-2 gap-2 mb-3">
            {sensor.last_reading?.pm25 != null && (
              <div className="p-2 rounded-lg bg-white/[0.02] border border-[var(--color-border)]">
                <p className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">PM2.5</p>
                <p className="text-sm font-mono font-semibold text-[var(--color-text-primary)] tabular-nums">
                  {sensor.last_reading.pm25}
                </p>
              </div>
            )}
            {sensor.last_reading?.pm10 != null && (
              <div className="p-2 rounded-lg bg-white/[0.02] border border-[var(--color-border)]">
                <p className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">PM10</p>
                <p className="text-sm font-mono font-semibold text-[var(--color-text-primary)] tabular-nums">
                  {sensor.last_reading.pm10}
                </p>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between text-[10px] text-[var(--color-text-muted)] pt-2 border-t border-[var(--color-border)]">
            <div className="flex items-center gap-3">
              {sensor.latitude != null && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {sensor.latitude.toFixed(3)}, {sensor.longitude?.toFixed(3)}
                </span>
              )}
            </div>
            <div className="flex items-center gap-3">
              {sensor.battery_level != null && (
                <span className={`flex items-center gap-1 ${batteryColor}`}>
                  <BatteryIcon className="w-3 h-3" />
                  {sensor.battery_level}%
                </span>
              )}
              {sensor.last_reading_at && (
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatTimeAgo(sensor.last_reading_at)}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </button>
  );
}

SensorCard.propTypes = {
  sensor: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string.isRequired,
    type: PropTypes.string,
    status: PropTypes.string,
    latitude: PropTypes.number,
    longitude: PropTypes.number,
    battery_level: PropTypes.number,
    last_reading_at: PropTypes.string,
    last_reading: PropTypes.shape({
      pm25: PropTypes.number,
      pm10: PropTypes.number,
    }),
  }).isRequired,
  onClick: PropTypes.func,
  className: PropTypes.string,
};

export default SensorCard;
