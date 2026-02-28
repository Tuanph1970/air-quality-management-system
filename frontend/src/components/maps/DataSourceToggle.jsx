import PropTypes from 'prop-types';
import { Layers, Satellite, Radio, Merge } from 'lucide-react';

/**
 * DataSourceToggle - Toggle between different data sources for map visualization
 * 
 * @param {string} value - Current selected source ('sensor', 'satellite', 'fused')
 * @param {function} onChange - Callback when source changes
 * @param {boolean} disabled - Disable the toggle
 * @param {object} stats - Optional statistics for each source
 */
function DataSourceToggle({ value, onChange, disabled = false, stats = {} }) {
  const sources = [
    {
      id: 'sensor',
      label: 'Sensors',
      icon: Radio,
      description: 'Ground-level IoT sensor readings',
      color: 'blue',
      count: stats.sensor?.count || 0,
    },
    {
      id: 'satellite',
      label: 'Satellite',
      icon: Satellite,
      description: 'Satellite observations (CAMS, MODIS, TROPOMI)',
      color: 'purple',
      count: stats.satellite?.count || 0,
    },
    {
      id: 'fused',
      label: 'Fused',
      icon: Merge,
      description: 'Calibrated combination of both sources',
      color: 'green',
      count: stats.fused?.count || 0,
    },
  ];

  return (
    <div className="inline-flex items-center gap-1 p-1 bg-slate-800/90 rounded-lg backdrop-blur-sm border border-slate-700">
      <div className="flex items-center gap-1 px-2 py-1 text-xs text-slate-400">
        <Layers size={14} />
        <span className="font-medium">Data Source:</span>
      </div>
      
      {sources.map((source) => {
        const Icon = source.icon;
        const isActive = value === source.id;
        
        return (
          <button
            key={source.id}
            onClick={() => !disabled && onChange(source.id)}
            disabled={disabled}
            className={`
              relative flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium
              transition-all duration-200
              ${isActive 
                ? `bg-${source.color}-600 text-white shadow-lg shadow-${source.color}-600/20` 
                : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
            style={{
              backgroundColor: isActive 
                ? getSourceColor(source.color) 
                : undefined,
            }}
          >
            <Icon size={14} />
            <span>{source.label}</span>
            {source.count > 0 && (
              <span className={`
                text-[10px] px-1.5 py-0.5 rounded-full
                ${isActive ? 'bg-white/20' : 'bg-slate-600'}
              `}>
                {source.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

// Helper to get color value (since Tailwind can't process dynamic classes)
function getSourceColor(color) {
  const colors = {
    blue: 'rgb(37, 99, 235)',
    purple: 'rgb(147, 51, 234)',
    green: 'rgb(34, 197, 94)',
  };
  return colors[color] || colors.blue;
}

DataSourceToggle.propTypes = {
  value: PropTypes.oneOf(['sensor', 'satellite', 'fused']).isRequired,
  onChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
  stats: PropTypes.shape({
    sensor: PropTypes.shape({ count: PropTypes.number }),
    satellite: PropTypes.shape({ count: PropTypes.number }),
    fused: PropTypes.shape({ count: PropTypes.number }),
  }),
};

export default DataSourceToggle;
