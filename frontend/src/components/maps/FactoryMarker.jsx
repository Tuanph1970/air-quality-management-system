import PropTypes from 'prop-types';
import { Factory } from 'lucide-react';
import { getAqiColor } from '../../utils/aqi';

function FactoryMarker({ factory, onClick, isSelected = false }) {
  const color = getAqiColor(factory.current_aqi);
  const statusColor =
    factory.operational_status === 'active' ? '#00e400' :
    factory.operational_status === 'warning' ? '#ff7e00' :
    factory.operational_status === 'critical' ? '#ff0000' :
    '#64748b';

  return (
    <button
      onClick={() => onClick?.(factory)}
      className={`group relative flex items-center justify-center w-10 h-10 rounded-xl transition-all duration-200 hover:scale-110 ${
        isSelected
          ? 'bg-brand-600/30 border-2 border-brand-400 shadow-aqi'
          : 'bg-[var(--color-bg-card)] border border-[var(--color-border)] hover:border-[var(--color-border-light)]'
      }`}
      title={factory.name}
    >
      <Factory className="w-4 h-4" style={{ color: statusColor }} />

      {/* Status dot */}
      <span
        className="absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-[var(--color-bg-primary)]"
        style={{ backgroundColor: statusColor }}
      />

      {/* Tooltip */}
      <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-10">
        <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-xs whitespace-nowrap shadow-lg">
          <p className="font-medium text-[var(--color-text-primary)]">{factory.name}</p>
          <p className="text-[var(--color-text-muted)]">
            AQI: <span className="font-mono" style={{ color }}>{factory.current_aqi || '--'}</span>
          </p>
        </div>
      </div>
    </button>
  );
}

FactoryMarker.propTypes = {
  factory: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string.isRequired,
    operational_status: PropTypes.string,
    current_aqi: PropTypes.number,
    latitude: PropTypes.number,
    longitude: PropTypes.number,
  }).isRequired,
  onClick: PropTypes.func,
  isSelected: PropTypes.bool,
};

export default FactoryMarker;
