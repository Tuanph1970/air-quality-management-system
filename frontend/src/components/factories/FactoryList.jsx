import PropTypes from 'prop-types';
import { Factory } from 'lucide-react';
import FactoryCard from './FactoryCard';
import EmptyState from '../common/EmptyState';
import LoadingSpinner from '../common/LoadingSpinner';

function FactoryList({ factories, isLoading, onFactoryClick, className = '' }) {
  if (isLoading) {
    return <LoadingSpinner className="py-20" size="lg" />;
  }

  if (!factories || factories.length === 0) {
    return (
      <EmptyState
        icon={Factory}
        title="No factories found"
        description="Try adjusting your filters or add a new factory"
      />
    );
  }

  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 ${className}`}>
      {factories.map((factory, index) => (
        <div key={factory.id || index} className={`stagger-${Math.min(index + 1, 6)}`}>
          <FactoryCard factory={factory} onClick={onFactoryClick} />
        </div>
      ))}
    </div>
  );
}

FactoryList.propTypes = {
  factories: PropTypes.array,
  isLoading: PropTypes.bool,
  onFactoryClick: PropTypes.func,
  className: PropTypes.string,
};

export default FactoryList;
