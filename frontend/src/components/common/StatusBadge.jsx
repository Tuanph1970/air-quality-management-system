
import PropTypes from 'prop-types';

const STATUS_CONFIG = {
  active: { dot: 'status-dot-active', label: 'Active', text: 'text-aqi-good' },
  warning: { dot: 'status-dot-warning', label: 'Warning', text: 'text-aqi-unhealthy-sensitive' },
  critical: { dot: 'status-dot-critical', label: 'Critical', text: 'text-aqi-unhealthy' },
  suspended: { dot: 'status-dot-offline', label: 'Suspended', text: 'text-gray-400' },
  offline: { dot: 'status-dot-offline', label: 'Offline', text: 'text-gray-500' },
  resolved: { dot: 'status-dot-active', label: 'Resolved', text: 'text-aqi-good' },
};

function StatusBadge({ status }) {
  const config = STATUS_CONFIG[status?.toLowerCase()] || STATUS_CONFIG.offline;

  return (
    <span className="inline-flex items-center gap-2 text-xs font-medium">
      <span className={`status-dot ${config.dot}`} />
      <span className={config.text}>{config.label}</span>
    </span>
  );
}

StatusBadge.propTypes = {
  status: PropTypes.string.isRequired,
};

export default StatusBadge;
