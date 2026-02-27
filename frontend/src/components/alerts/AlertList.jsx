import PropTypes from 'prop-types';
import { AlertTriangle } from 'lucide-react';
import AlertCard from './AlertCard';
import EmptyState from '../common/EmptyState';
import LoadingSpinner from '../common/LoadingSpinner';

function AlertList({ violations, isLoading, onViolationClick, className = '' }) {
  if (isLoading) {
    return <LoadingSpinner className="py-20" size="lg" />;
  }

  if (!violations || violations.length === 0) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="No violations found"
        description="No active or matching violations at this time"
      />
    );
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {violations.map((violation, index) => (
        <div key={violation.id || index} className={`stagger-${Math.min(index + 1, 6)}`}>
          <AlertCard violation={violation} onClick={onViolationClick} />
        </div>
      ))}
    </div>
  );
}

AlertList.propTypes = {
  violations: PropTypes.array,
  isLoading: PropTypes.bool,
  onViolationClick: PropTypes.func,
  className: PropTypes.string,
};

export default AlertList;
