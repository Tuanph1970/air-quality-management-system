import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { 
  MapPin, 
  Search, 
  RefreshCw, 
  TrendingUp, 
  Wind, 
  Droplets, 
  Thermometer,
  Activity,
  Clock,
  ChevronRight,
  X
} from 'lucide-react';
import Header from '../components/layout/Header';
import EmptyState from '../components/common/EmptyState';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { stationIngestionApi } from '../services/stationIngestionApi';
import { formatTimeAgo } from '../utils/format';
import TimeSeriesChart from '../components/charts/TimeSeriesChart';

// AQI color mapping
const getAqiColor = (aqi) => {
  if (!aqi) return 'text-gray-400';
  if (aqi <= 50) return 'text-green-500';
  if (aqi <= 100) return 'text-yellow-500';
  if (aqi <= 150) return 'text-orange-500';
  if (aqi <= 200) return 'text-red-500';
  if (aqi <= 300) return 'text-purple-500';
  return 'text-red-700';
};

const getAqiBadge = (aqi) => {
  if (!aqi) return { bg: 'bg-gray-500/20', text: 'text-gray-400', label: 'N/A' };
  if (aqi <= 50) return { bg: 'bg-green-500/20', text: 'text-green-400', label: 'Good' };
  if (aqi <= 100) return { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: 'Moderate' };
  if (aqi <= 150) return { bg: 'bg-orange-500/20', text: 'text-orange-400', label: 'Unhealthy (Sensitive)' };
  if (aqi <= 200) return { bg: 'bg-red-500/20', text: 'text-red-400', label: 'Unhealthy' };
  if (aqi <= 300) return { bg: 'bg-purple-500/20', text: 'text-purple-400', label: 'Very Unhealthy' };
  return { bg: 'bg-red-700/20', text: 'text-red-400', label: 'Hazardous' };
};

function StationCard({ station, onClick }) {
  const latestReading = station.latest_reading;
  const aqi = latestReading?.aqi;
  const aqiBadge = getAqiBadge(aqi);

  return (
    <div 
      onClick={() => onClick(station)}
      className="card p-4 cursor-pointer hover:bg-white/10 transition-all duration-200 border border-white/5 hover:border-white/20"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center">
            <Activity className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h3 className="font-semibold text-white text-sm line-clamp-1">{station.station_name}</h3>
            <p className="text-xs text-gray-400 flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              {station.station_code}
            </p>
          </div>
        </div>
        <ChevronRight className="w-4 h-4 text-gray-500" />
      </div>

      {latestReading ? (
        <>
          <div className="flex items-center gap-3 mb-3">
            <div className={`px-3 py-1 rounded-full text-sm font-semibold ${aqiBadge.bg} ${aqiBadge.text}`}>
              AQI: {aqi?.toFixed(0) || '--'}
            </div>
            <span className="text-xs text-gray-400 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatTimeAgo(latestReading.reading_time)}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <div className="bg-white/5 rounded-lg p-2 text-center">
              <Wind className="w-3 h-3 text-gray-400 mx-auto mb-1" />
              <div className="text-xs text-gray-400">PM2.5</div>
              <div className="text-sm font-mono text-white">{latestReading.pm25?.toFixed(1) || '--'}</div>
            </div>
            <div className="bg-white/5 rounded-lg p-2 text-center">
              <Wind className="w-3 h-3 text-gray-400 mx-auto mb-1" />
              <div className="text-xs text-gray-400">PM10</div>
              <div className="text-sm font-mono text-white">{latestReading.pm10?.toFixed(1) || '--'}</div>
            </div>
            <div className="bg-white/5 rounded-lg p-2 text-center">
              <Activity className="w-3 h-3 text-gray-400 mx-auto mb-1" />
              <div className="text-xs text-gray-400">O3</div>
              <div className="text-sm font-mono text-white">{latestReading.o3?.toFixed(1) || '--'}</div>
            </div>
          </div>
        </>
      ) : (
        <div className="text-center py-4 text-gray-400 text-sm">
          No recent data
        </div>
      )}
    </div>
  );
}

StationCard.propTypes = {
  station: PropTypes.shape({
    id: PropTypes.string.isRequired,
    station_code: PropTypes.string.isRequired,
    station_name: PropTypes.string.isRequired,
    latest_reading: PropTypes.shape({
      aqi: PropTypes.number,
      pm25: PropTypes.number,
      pm10: PropTypes.number,
      o3: PropTypes.number,
      reading_time: PropTypes.string,
    }),
  }).isRequired,
  onClick: PropTypes.func.isRequired,
};

function StationDetailPanel({ station, onClose, timeRange }) {
  const [readings, setReadings] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (station) {
      loadReadings();
    }
  }, [station, timeRange]);

  async function loadReadings() {
    setIsLoading(true);
    try {
      const params = {
        from_time: timeRange.from,
        to_time: timeRange.to,
      };
      const response = await stationIngestionApi.getStationReadings(station.station_code, params);
      setReadings(response.data || []);
    } catch (error) {
      console.error('Failed to load readings:', error);
      setReadings([]);
    } finally {
      setIsLoading(false);
    }
  }

  const latestReading = readings[readings.length - 1];

  return (
    <div className="fixed inset-y-0 right-0 w-full md:w-[600px] bg-[var(--color-bg-card)] shadow-2xl z-50 overflow-hidden flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <div>
          <h2 className="text-lg font-semibold text-white">{station.station_name}</h2>
          <p className="text-sm text-gray-400 flex items-center gap-1">
            <MapPin className="w-3 h-3" />
            {station.station_code}
          </p>
        </div>
        <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg transition-colors">
          <X className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Latest Reading Summary */}
        {latestReading && (
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-xl p-4">
              <div className="text-sm text-gray-400 mb-1">AQI</div>
              <div className={`text-3xl font-bold ${getAqiColor(latestReading.aqi)}`}>
                {latestReading.aqi?.toFixed(0) || '--'}
              </div>
              <div className="text-xs text-gray-400 mt-1">
                {getAqiBadge(latestReading.aqi).label}
              </div>
            </div>
            <div className="bg-white/5 rounded-xl p-4">
              <div className="text-sm text-gray-400 mb-1">Updated</div>
              <div className="text-sm text-white font-mono">
                {formatTimeAgo(latestReading.reading_time)}
              </div>
              <div className="text-xs text-gray-400 mt-1">
                {new Date(latestReading.reading_time).toLocaleString()}
              </div>
            </div>
          </div>
        )}

        {/* Pollutant Cards */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-white/5 rounded-xl p-3 text-center">
            <Wind className="w-4 h-4 text-gray-400 mx-auto mb-2" />
            <div className="text-xs text-gray-400">PM2.5</div>
            <div className="text-lg font-mono text-white">
              {latestReading?.pm25?.toFixed(1) || '--'}
            </div>
            <div className="text-xs text-gray-500">µg/m³</div>
          </div>
          <div className="bg-white/5 rounded-xl p-3 text-center">
            <Wind className="w-4 h-4 text-gray-400 mx-auto mb-2" />
            <div className="text-xs text-gray-400">PM10</div>
            <div className="text-lg font-mono text-white">
              {latestReading?.pm10?.toFixed(1) || '--'}
            </div>
            <div className="text-xs text-gray-500">µg/m³</div>
          </div>
          <div className="bg-white/5 rounded-xl p-3 text-center">
            <Activity className="w-4 h-4 text-gray-400 mx-auto mb-2" />
            <div className="text-xs text-gray-400">O3</div>
            <div className="text-lg font-mono text-white">
              {latestReading?.o3?.toFixed(1) || '--'}
            </div>
            <div className="text-xs text-gray-500">µg/m³</div>
          </div>
          <div className="bg-white/5 rounded-xl p-3 text-center">
            <TrendingUp className="w-4 h-4 text-gray-400 mx-auto mb-2" />
            <div className="text-xs text-gray-400">CO</div>
            <div className="text-lg font-mono text-white">
              {latestReading?.co?.toFixed(2) || '--'}
            </div>
            <div className="text-xs text-gray-500">µg/m³</div>
          </div>
          <div className="bg-white/5 rounded-xl p-3 text-center">
            <TrendingUp className="w-4 h-4 text-gray-400 mx-auto mb-2" />
            <div className="text-xs text-gray-400">SO2</div>
            <div className="text-lg font-mono text-white">
              {latestReading?.so2?.toFixed(2) || '--'}
            </div>
            <div className="text-xs text-gray-500">µg/m³</div>
          </div>
          <div className="bg-white/5 rounded-xl p-3 text-center">
            <TrendingUp className="w-4 h-4 text-gray-400 mx-auto mb-2" />
            <div className="text-xs text-gray-400">NO2</div>
            <div className="text-lg font-mono text-white">
              {latestReading?.no2?.toFixed(2) || '--'}
            </div>
            <div className="text-xs text-gray-500">µg/m³</div>
          </div>
        </div>

        {/* Environmental Data */}
        {(latestReading?.temperature || latestReading?.humidity) && (
          <div className="bg-white/5 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Thermometer className="w-4 h-4 text-gray-400" />
              Environmental
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-gray-400">Temperature</div>
                <div className="text-lg font-mono text-white">
                  {latestReading?.temperature?.toFixed(1) || '--'} °C
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400">Humidity</div>
                <div className="text-lg font-mono text-white">
                  {latestReading?.humidity?.toFixed(1) || '--'} %
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Time Series Chart */}
        <div className="bg-white/5 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-gray-400" />
            Time Series (24h)
          </h3>
          {isLoading ? (
            <LoadingSpinner size="sm" />
          ) : readings.length > 0 ? (
            <TimeSeriesChart data={readings} height={200} />
          ) : (
            <div className="text-center text-gray-400 text-sm py-8">
              No data available for this period
            </div>
          )}
        </div>

        {/* Data Table */}
        <div className="bg-white/5 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Recent Readings</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 border-b border-white/10">
                  <th className="text-left py-2">Time</th>
                  <th className="text-right">AQI</th>
                  <th className="text-right">PM2.5</th>
                  <th className="text-right">PM10</th>
                </tr>
              </thead>
              <tbody>
                {readings.slice(-10).reverse().map((reading, idx) => (
                  <tr key={reading.id || idx} className="border-b border-white/5">
                    <td className="py-2 text-gray-300">
                      {new Date(reading.reading_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className={`text-right font-mono ${getAqiColor(reading.aqi)}`}>
                      {reading.aqi?.toFixed(0) || '--'}
                    </td>
                    <td className="text-right font-mono text-gray-300">
                      {reading.pm25?.toFixed(1) || '--'}
                    </td>
                    <td className="text-right font-mono text-gray-300">
                      {reading.pm10?.toFixed(1) || '--'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

StationDetailPanel.propTypes = {
  station: PropTypes.shape({
    station_code: PropTypes.string.isRequired,
    station_name: PropTypes.string.isRequired,
  }),
  onClose: PropTypes.func.isRequired,
  timeRange: PropTypes.shape({
    from: PropTypes.string,
    to: PropTypes.string,
  }).isRequired,
};

function StationsPage() {
  const [stations, setStations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState(null); // { success, message }
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStation, setSelectedStation] = useState(null);
  const [timeRange, setTimeRange] = useState({
    from: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    to: new Date().toISOString(),
  });

  useEffect(() => {
    loadStations();
  }, []);

  async function loadStations() {
    setIsLoading(true);
    try {
      const response = await stationIngestionApi.getStations();
      setStations(response.data || []);
    } catch (error) {
      console.error('Failed to load stations:', error);
      setStations([]);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSync() {
    setIsSyncing(true);
    setSyncResult(null);
    try {
      const [stationsRes, aqiRes] = await Promise.all([
        stationIngestionApi.syncStations(),
        stationIngestionApi.syncAqiData(24),
      ]);
      const newStations = stationsRes.data?.new_stations ?? 0;
      const readingsSynced = aqiRes.data?.readings_synced ?? 0;
      setSyncResult({ success: true, message: `Synced ${newStations} new stations, ${readingsSynced} readings` });
      await loadStations();
    } catch (error) {
      console.error('Sync failed:', error);
      setSyncResult({ success: false, message: error?.response?.data?.detail || error.message || 'Sync failed' });
    } finally {
      setIsSyncing(false);
      setTimeout(() => setSyncResult(null), 5000);
    }
  }

  const filteredStations = stations.filter(
    (s) =>
      s.station_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.station_code?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const avgAqi = stations.reduce((acc, s) => {
    const aqi = s.latest_reading?.aqi;
    return aqi ? acc + aqi : acc;
  }, 0);
  const displayedAvgAqi = stations.filter(s => s.latest_reading?.aqi).length > 0 
    ? (avgAqi / stations.filter(s => s.latest_reading?.aqi).length).toFixed(0) 
    : '--';

  return (
    <div className="min-h-screen">
      <Header 
        title="Monitoring Stations" 
        subtitle={`${filteredStations.length} stations | Avg AQI: ${displayedAvgAqi}`} 
      />

      <div className="p-6 space-y-5">
        {/* Sync result banner */}
        {syncResult && (
          <div className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm ${
            syncResult.success
              ? 'bg-green-500/15 text-green-400 border border-green-500/20'
              : 'bg-red-500/15 text-red-400 border border-red-500/20'
          }`}>
            <span>{syncResult.success ? '✓' : '✗'}</span>
            <span>{syncResult.message}</span>
          </div>
        )}

        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search stations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input pl-9"
            />
          </div>
          <button
            onClick={handleSync}
            disabled={isSyncing}
            className="btn-primary flex items-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} />
            <span>{isSyncing ? 'Syncing…' : 'Sync Data'}</span>
          </button>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card p-4">
            <div className="text-sm text-gray-400">Total Stations</div>
            <div className="text-2xl font-bold text-white">{stations.length}</div>
          </div>
          <div className="card p-4">
            <div className="text-sm text-gray-400">Active Stations</div>
            <div className="text-2xl font-bold text-green-400">
              {stations.filter(s => s.is_active !== false).length}
            </div>
          </div>
          <div className="card p-4">
            <div className="text-sm text-gray-400">Avg AQI</div>
            <div className={`text-2xl font-bold ${getAqiColor(displayedAvgAqi)}`}>
              {displayedAvgAqi}
            </div>
          </div>
          <div className="card p-4">
            <div className="text-sm text-gray-400">Last Sync</div>
            <div className="text-sm font-mono text-white">
              {new Date().toLocaleTimeString()}
            </div>
          </div>
        </div>

        {/* Station Grid */}
        {isLoading ? (
          <LoadingSpinner className="py-20" size="lg" />
        ) : filteredStations.length === 0 ? (
          <EmptyState
            icon={MapPin}
            title="No stations found"
            description="Sync data from the external API to load stations"
            action={
              <button onClick={handleSync} disabled={isSyncing} className="btn-primary flex items-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed">
                <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} />
                {isSyncing ? 'Syncing…' : 'Sync Stations'}
              </button>
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredStations.map((station) => (
              <StationCard 
                key={station.id} 
                station={station} 
                onClick={setSelectedStation}
              />
            ))}
          </div>
        )}
      </div>

      {/* Detail Panel */}
      {selectedStation && (
        <>
          <div 
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setSelectedStation(null)}
          />
          <StationDetailPanel 
            station={selectedStation} 
            onClose={() => setSelectedStation(null)}
            timeRange={timeRange}
          />
        </>
      )}
    </div>
  );
}

export default StationsPage;
