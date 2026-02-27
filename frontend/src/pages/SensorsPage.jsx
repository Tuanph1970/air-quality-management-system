import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { Radio, Plus, Search, Signal, SignalLow, SignalZero } from 'lucide-react';
import Header from '../components/layout/Header';
import StatusBadge from '../components/common/StatusBadge';
import EmptyState from '../components/common/EmptyState';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { sensorApi } from '../services/sensorApi';
import { formatTimeAgo } from '../utils/format';

const MOCK_SENSORS = [
  { id: '1', name: 'Station A-01', type: 'PM2.5', status: 'active', factory_name: 'Steel Plant Alpha', last_reading: { value: 12.8, timestamp: new Date().toISOString() }, battery_level: 92 },
  { id: '2', name: 'Station A-02', type: 'Multi-Gas', status: 'active', factory_name: 'Steel Plant Alpha', last_reading: { value: 0.035, timestamp: new Date(Date.now() - 300000).toISOString() }, battery_level: 78 },
  { id: '3', name: 'Station B-01', type: 'PM10', status: 'warning', factory_name: 'Chemical Works Beta', last_reading: { value: 88.5, timestamp: new Date(Date.now() - 600000).toISOString() }, battery_level: 25 },
  { id: '4', name: 'Station C-01', type: 'SO2', status: 'active', factory_name: 'Cement Factory Gamma', last_reading: { value: 0.12, timestamp: new Date(Date.now() - 120000).toISOString() }, battery_level: 95 },
  { id: '5', name: 'Station D-01', type: 'NO2', status: 'offline', factory_name: 'Textile Mill Delta', last_reading: { value: null, timestamp: null }, battery_level: 0 },
  { id: '6', name: 'Station E-01', type: 'CO', status: 'active', factory_name: 'Power Plant Epsilon', last_reading: { value: 1.2, timestamp: new Date(Date.now() - 180000).toISOString() }, battery_level: 67 },
];

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
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadSensors();
  }, []);

  async function loadSensors() {
    setIsLoading(true);
    try {
      const response = await sensorApi.list();
      setSensors(response.data?.data || MOCK_SENSORS);
    } catch (_err) {
      setSensors(MOCK_SENSORS);
    } finally {
      setIsLoading(false);
    }
  }

  const filtered = sensors.filter((s) =>
    s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.factory_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
                {filtered.map((sensor) => (
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
