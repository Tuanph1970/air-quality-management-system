import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { Radio, Plus, Search, Signal, SignalLow, SignalZero } from 'lucide-react';
import Header from '../components/layout/Header';
import StatusBadge from '../components/common/StatusBadge';
import EmptyState from '../components/common/EmptyState';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { sensorApi } from '../services/sensorApi';
import { formatTimeAgo } from '../utils/format';

function BatteryIndicator({ level }) {
  const color = level > 50 ? 'text-aqi-good' : level > 20 ? 'text-aqi-unhealthy-sensitive' : 'text-aqi-unhealthy';
  const Icon = level > 50 ? Signal : level > 20 ? SignalLow : SignalZero;

  return (
    <span className={`flex items-center gap-1 text-xs font-mono ${color}`}>
      <Icon className="w-3.5 h-3.5" />
      {level}%
    </span>
  );
}

BatteryIndicator.propTypes = {
  level: PropTypes.number.isRequired,
};

function SensorsPage() {
  const [sensors, setSensors] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadSensors();
  }, []);

  async function loadSensors() {
    setIsLoading(true);
    setError(null);
    try {
      const response = await sensorApi.list();
      // Handle different response formats
      const data = response.data;
      if (data?.items) {
        // sensor-service returns { items: [], total: number }
        setSensors(data.items);
      } else if (data?.data) {
        setSensors(data.data);
      } else if (Array.isArray(data)) {
        setSensors(data);
      } else {
        setSensors([]);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load sensors');
      setSensors([]);
    } finally {
      setIsLoading(false);
    }
  }

  const filtered = sensors.filter((s) =>
    s.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.serial_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.model?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Map sensor-service format to frontend display format
  const displaySensors = filtered.map((sensor) => ({
    id: sensor.id,
    name: sensor.serial_number || sensor.model || 'Unknown Sensor',
    type: sensor.sensor_type,
    status: sensor.status?.toLowerCase() || 'offline',
    factory_name: sensor.factory_id ? `Factory ${sensor.factory_id.toString().slice(0, 8)}...` : 'N/A',
    last_reading: { value: '--', timestamp: null },
    battery_level: 100, // PurpleAir devices are powered, not battery
  }));

  return (
    <div className="min-h-screen">
      <Header title="Sensors" subtitle={`${sensors.length} monitoring stations`} />

      <div className="p-6 space-y-5">
        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
            <input
              type="text"
              placeholder="Search sensors..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input pl-9"
            />
          </div>
          <button className="btn-primary">
            <Plus className="w-4 h-4" />
            <span className="hidden sm:inline">Register Sensor</span>
          </button>
        </div>

        {/* Sensor Table */}
        {isLoading ? (
          <LoadingSpinner className="py-20" size="lg" />
        ) : error ? (
          <EmptyState
            icon={Radio}
            title="Error loading sensors"
            description={error}
          />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={Radio}
            title="No sensors found"
            description="Register a new sensor to start monitoring"
          />
        ) : (
          <div className="card !p-0 overflow-hidden">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Sensor</th>
                  <th>Type</th>
                  <th>Factory</th>
                  <th>Status</th>
                  <th>Last Reading</th>
                  <th>Battery</th>
                  <th>Updated</th>
                </tr>
              </thead>
              <tbody>
                {displaySensors.map((sensor) => (
                  <tr key={sensor.id} className="cursor-pointer">
                    <td>
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center">
                          <Radio className="w-4 h-4 text-[var(--color-text-muted)]" />
                        </div>
                        <span className="font-medium text-[var(--color-text-primary)]">
                          {sensor.name}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className="font-mono text-xs bg-white/5 px-2 py-0.5 rounded">
                        {sensor.type}
                      </span>
                    </td>
                    <td className="text-[var(--color-text-secondary)]">{sensor.factory_name}</td>
                    <td><StatusBadge status={sensor.status} /></td>
                    <td>
                      <span className="font-mono text-[var(--color-text-primary)]">
                        {sensor.last_reading?.value ?? '--'}
                      </span>
                    </td>
                    <td><BatteryIndicator level={sensor.battery_level} /></td>
                    <td className="text-[var(--color-text-muted)]">
                      {sensor.last_reading?.timestamp ? formatTimeAgo(sensor.last_reading.timestamp) : '--'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default SensorsPage;
