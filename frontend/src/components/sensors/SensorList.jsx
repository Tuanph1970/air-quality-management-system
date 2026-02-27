import PropTypes from 'prop-types';
import { Radio } from 'lucide-react';
import SensorCard from './SensorCard';
import EmptyState from '../common/EmptyState';
import LoadingSpinner from '../common/LoadingSpinner';

function SensorList({ sensors, isLoading, onSensorClick, className = '' }) {
  if (isLoading) {
    return <LoadingSpinner className="py-20" size="lg" />;
  }

  if (!sensors || sensors.length === 0) {
    return (
      <EmptyState
        icon={Radio}
        title="No sensors found"
        description="Try adjusting your filters or register a new sensor"
      />
    );
  }

  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 ${className}`}>
      {sensors.map((sensor, index) => (
        <div key={sensor.id || index} className={`stagger-${Math.min(index + 1, 6)}`}>
          <SensorCard sensor={sensor} onClick={onSensorClick} />
        </div>
      ))}
    </div>
  );
}

SensorList.propTypes = {
  sensors: PropTypes.array,
  isLoading: PropTypes.bool,
  onSensorClick: PropTypes.func,
  className: PropTypes.string,
};

export default SensorList;
