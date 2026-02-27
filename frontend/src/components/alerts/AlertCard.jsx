import PropTypes from 'prop-types';
import { AlertTriangle, AlertCircle, Info, Clock, Factory, ArrowRight } from 'lucide-react';
import Badge from '../common/Badge';
import { formatTimeAgo } from '../../utils/format';

const SEVERITY_CONFIG = {
  high: { icon: AlertTriangle, badge: 'danger', label: 'High' },
  medium: { icon: AlertCircle, badge: 'warning', label: 'Medium' },
  low: { icon: Info, badge: 'info', label: 'Low' },
};

function AlertCard({ violation, onClick, className = '' }) {
  const severity = SEVERITY_CONFIG[violation.severity] || SEVERITY_CONFIG.medium;
  const SeverityIcon = severity.icon;
  const isActive = violation.status === 'active';

  return (
    <button
      onClick={() => onClick?.(violation)}
      className={`card group text-left w-full transition-all duration-300 hover:border-[var(--color-border-light)] hover:shadow-card-hover ${
        isActive ? 'border-l-2 border-l-aqi-unhealthy/60' : ''
      } ${className}`}
    >
      <div className="flex items-start gap-3">
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
          severity.badge === 'danger' ? 'bg-aqi-unhealthy/10 border border-aqi-unhealthy/20' :
          severity.badge === 'warning' ? 'bg-aqi-unhealthy-sensitive/10 border border-aqi-unhealthy-sensitive/20' :
          'bg-blue-500/10 border border-blue-500/20'
        }`}>
          <SeverityIcon className={`w-4 h-4 ${
            severity.badge === 'danger' ? 'text-aqi-unhealthy' :
            severity.badge === 'warning' ? 'text-aqi-unhealthy-sensitive' :
            'text-blue-400'
          }`} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5">
            <Badge variant={severity.badge} dot>
              {severity.label}
            </Badge>
            <Badge variant={isActive ? 'danger' : 'success'} dot>
              {isActive ? 'Active' : 'Resolved'}
            </Badge>
          </div>

          <p className="text-sm text-[var(--color-text-primary)] font-medium mb-1">
            {violation.pollutant ? (
              <>
                <span className="font-mono uppercase">{violation.pollutant}</span> exceeded threshold
              </>
            ) : (
              'Violation detected'
            )}
          </p>

          {violation.measured_value != null && violation.threshold != null && (
            <p className="text-xs text-[var(--color-text-muted)] mb-2">
              Measured{' '}
              <span className="font-mono text-aqi-unhealthy">{violation.measured_value}</span>{' '}
              / Limit{' '}
              <span className="font-mono text-[var(--color-text-secondary)]">{violation.threshold}</span>{' '}
              µg/m³
            </p>
          )}

          <div className="flex items-center gap-3 text-[10px] text-[var(--color-text-muted)]">
            {violation.factory_name && (
              <span className="flex items-center gap-1">
                <Factory className="w-3 h-3" />
                {violation.factory_name}
              </span>
            )}
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatTimeAgo(violation.detected_at || violation.created_at)}
            </span>
          </div>
        </div>

        <ArrowRight className="w-4 h-4 text-[var(--color-text-muted)] opacity-0 group-hover:opacity-100 transition-all duration-200 transform group-hover:translate-x-0.5 flex-shrink-0 mt-2" />
      </div>
    </button>
  );
}

AlertCard.propTypes = {
  violation: PropTypes.shape({
    id: PropTypes.string,
    severity: PropTypes.string,
    status: PropTypes.string,
    pollutant: PropTypes.string,
    measured_value: PropTypes.number,
    threshold: PropTypes.number,
    factory_name: PropTypes.string,
    detected_at: PropTypes.string,
    created_at: PropTypes.string,
  }).isRequired,
  onClick: PropTypes.func,
  className: PropTypes.string,
};

export default AlertCard;
