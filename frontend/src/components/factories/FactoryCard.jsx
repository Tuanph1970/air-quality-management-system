import PropTypes from 'prop-types';
import { Factory, MapPin, Calendar, ArrowRight } from 'lucide-react';
import StatusBadge from '../common/StatusBadge';
import AqiBadge from '../common/AqiBadge';
import { formatDate } from '../../utils/format';

function FactoryCard({ factory, onClick, className = '' }) {
  const statusMap = {
    active: 'active',
    warning: 'warning',
    critical: 'critical',
    suspended: 'suspended',
  };

  return (
    <button
      onClick={() => onClick?.(factory)}
      className={`card group text-left w-full transition-all duration-300 hover:border-[var(--color-border-light)] hover:shadow-card-hover ${className}`}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-600/10 border border-brand-600/20 flex items-center justify-center flex-shrink-0">
            <Factory className="w-5 h-5 text-brand-400" />
          </div>
          <div className="min-w-0">
            <h3 className="text-sm font-display font-semibold text-[var(--color-text-primary)] truncate">
              {factory.name}
            </h3>
            <p className="text-xs text-[var(--color-text-muted)] font-mono">
              {factory.registration_number}
            </p>
          </div>
        </div>
        <AqiBadge value={factory.current_aqi} />
      </div>

      <div className="space-y-2.5">
        <div className="flex items-center justify-between">
          <StatusBadge status={statusMap[factory.operational_status] || 'offline'} />
          <span className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">
            {factory.industry_type}
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
          <MapPin className="w-3 h-3 flex-shrink-0" />
          <span className="truncate">
            {factory.latitude?.toFixed(4)}, {factory.longitude?.toFixed(4)}
          </span>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-[var(--color-border)]">
          <div className="flex items-center gap-1.5 text-[10px] text-[var(--color-text-muted)]">
            <Calendar className="w-3 h-3" />
            {formatDate(factory.created_at)}
          </div>
          <ArrowRight className="w-3.5 h-3.5 text-[var(--color-text-muted)] opacity-0 group-hover:opacity-100 transition-all duration-200 transform group-hover:translate-x-0.5" />
        </div>
      </div>
    </button>
  );
}

FactoryCard.propTypes = {
  factory: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string.isRequired,
    registration_number: PropTypes.string,
    industry_type: PropTypes.string,
    operational_status: PropTypes.string,
    current_aqi: PropTypes.number,
    latitude: PropTypes.number,
    longitude: PropTypes.number,
    created_at: PropTypes.string,
  }).isRequired,
  onClick: PropTypes.func,
  className: PropTypes.string,
};

export default FactoryCard;
