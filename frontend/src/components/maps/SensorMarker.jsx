import PropTypes from 'prop-types';
import { Radio } from 'lucide-react';

function SensorMarker({ sensor, onClick, isSelected = false }) {
  const statusColor =
    sensor.status === 'active' ? '#00e400' :
    sensor.status === 'warning' ? '#ff7e00' :
    '#64748b';

  return (
    <button
      onClick={() => onClick?.(sensor)}
      className={`group relative flex items-center justify-center w-8 h-8 rounded-lg transition-all duration-200 hover:scale-110 ${
        isSelected
          ? 'bg-blue-600/30 border-2 border-blue-400'
          : 'bg-[var(--color-bg-card)] border border-[var(--color-border)] hover:border-[var(--color-border-light)]'
      }`}
      title={sensor.name}
    >
      <Radio className="w-3.5 h-3.5" style={{ color: statusColor }} />

      {/* Pulse ring for active sensors */}
      {sensor.status === 'active' && (
        <span className="absolute inset-0 rounded-lg border border-aqi-good/30 animate-ping" />
      )}

      {/* Tooltip */}
      <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-10">
        <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-xs whitespace-nowrap shadow-lg">
          <p className="font-medium text-[var(--color-text-primary)]">{sensor.name}</p>
          <p className="text-[var(--color-text-muted)]">{sensor.type}</p>
        </div>
      </div>
    </button>
  );
}

SensorMarker.propTypes = {
  sensor: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string.isRequired,
    type: PropTypes.string,
    status: PropTypes.string,
    latitude: PropTypes.number,
    longitude: PropTypes.number,
  }).isRequired,
  onClick: PropTypes.func,
  isSelected: PropTypes.bool,
};

export default SensorMarker;
