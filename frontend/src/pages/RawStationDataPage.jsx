import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import {
  Database,
  Search,
  RefreshCw,
  Download,
  Filter,
  Calendar,
  MapPin,
  Wind,
  Thermometer,
  Droplets,
  Gauge,
  Compass,
  Activity,
  ChevronDown,
  ChevronUp,
  X,
} from 'lucide-react';
import Header from '../components/layout/Header';
import EmptyState from '../components/common/EmptyState';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { excelFetcherApi } from '../services/excelFetcherApi';
import { formatTimeAgo } from '../utils/format';

// AQI color mapping
const getAqiColor = (aqi) => {
  if (!aqi && aqi !== 0) return 'text-gray-400';
  if (aqi <= 50) return 'text-green-400';
  if (aqi <= 100) return 'text-yellow-400';
  if (aqi <= 150) return 'text-orange-400';
  if (aqi <= 200) return 'text-red-400';
  if (aqi <= 300) return 'text-purple-400';
  return 'text-red-600';
};

const getAqiBadge = (aqi) => {
  if (!aqi && aqi !== 0) return { bg: 'bg-gray-500/20', text: 'text-gray-400', label: 'N/A' };
  if (aqi <= 50) return { bg: 'bg-green-500/20', text: 'text-green-400', label: 'Good' };
  if (aqi <= 100) return { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: 'Moderate' };
  if (aqi <= 150) return { bg: 'bg-orange-500/20', text: 'text-orange-400', label: 'Unhealthy (Sensitive)' };
  if (aqi <= 200) return { bg: 'bg-red-500/20', text: 'text-red-400', label: 'Unhealthy' };
  if (aqi <= 300) return { bg: 'bg-purple-500/20', text: 'text-purple-400', label: 'Very Unhealthy' };
  return { bg: 'bg-red-700/20', text: 'text-red-400', label: 'Hazardous' };
};

function StationSelector({ stations, selectedStation, onSelect }) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');

  const filteredStations = stations.filter(
    (s) =>
      s.name?.toLowerCase().includes(search.toLowerCase()) ||
      s.station_id?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="relative">
      <label className="block text-sm font-medium text-gray-400 mb-1">Select Station</label>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-2.5 bg-[var(--color-bg-card)] border border-white/10 rounded-xl text-left hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-gray-400" />
          <span className={selectedStation ? 'text-white' : 'text-gray-500'}>
            {selectedStation ? selectedStation.name : 'Choose a station...'}
          </span>
        </div>
        {isOpen ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
      </button>

      {isOpen && (
        <div className="absolute z-20 w-full mt-1 bg-[var(--color-bg-card)] border border-white/10 rounded-xl shadow-xl overflow-hidden">
          <div className="p-2 border-b border-white/10">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search stations..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500/50"
              />
            </div>
          </div>
          <div className="max-h-60 overflow-y-auto">
            {filteredStations.length === 0 ? (
              <div className="p-4 text-center text-gray-400 text-sm">No stations found</div>
            ) : (
              filteredStations.map((station) => (
                <button
                  key={station.station_id}
                  onClick={() => {
                    onSelect(station);
                    setIsOpen(false);
                    setSearch('');
                  }}
                  className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-white/5 text-left transition-colors"
                >
                  <MapPin className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-white truncate">{station.name}</div>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

StationSelector.propTypes = {
  stations: PropTypes.array.isRequired,
  selectedStation: PropTypes.object,
  onSelect: PropTypes.func.isRequired,
};

function FetchForm({ selectedStation, onFetch }) {
  const [fromDate, setFromDate] = useState(
    new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [toDate, setToDate] = useState(new Date().toISOString().split('T')[0]);
  const [timeType, setTimeType] = useState('5 phút');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await onFetch({ from_date: fromDate, to_date: toDate, time_type: timeType });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">From Date</label>
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="w-full pl-9 pr-3 py-2.5 bg-[var(--color-bg-card)] border border-white/10 rounded-xl text-white focus:outline-none focus:border-brand-500/50"
            />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">To Date</label>
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="w-full pl-9 pr-3 py-2.5 bg-[var(--color-bg-card)] border border-white/10 rounded-xl text-white focus:outline-none focus:border-brand-500/50"
            />
          </div>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">Time Interval</label>
        <select
          value={timeType}
          onChange={(e) => setTimeType(e.target.value)}
          className="w-full px-4 py-2.5 bg-[var(--color-bg-card)] border border-white/10 rounded-xl text-white focus:outline-none focus:border-brand-500/50"
        >
          <option value="5 phút">5 minutes</option>
          <option value="15 phút">15 minutes</option>
          <option value="30 phút">30 minutes</option>
          <option value="1 giờ">1 hour</option>
        </select>
      </div>

      <button
        type="submit"
        disabled={!selectedStation || isLoading}
        className="w-full btn-primary flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <>
            <RefreshCw className="w-4 h-4 animate-spin" />
            <span>Fetching...</span>
          </>
        ) : (
          <>
            <Database className="w-4 h-4" />
            <span>Fetch Raw Data</span>
          </>
        )}
      </button>
    </form>
  );
}

FetchForm.propTypes = {
  selectedStation: PropTypes.object,
  onFetch: PropTypes.func.isRequired,
};

function DataTable({ data, isLoading }) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        <Database className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>No raw data available. Fetch data first.</p>
      </div>
    );
  }

  // Group data by measured_at for display
  const columns = [
    { key: 'measured_at', label: 'Time', width: 'w-32' },
    { key: 'aqi', label: 'AQI', width: 'w-20' },
    { key: 'pm25', label: 'PM2.5', width: 'w-20' },
    { key: 'pm10', label: 'PM10', width: 'w-20' },
    { key: 'no2', label: 'NO₂', width: 'w-20' },
    { key: 'o3', label: 'O₃', width: 'w-20' },
    { key: 'co', label: 'CO', width: 'w-20' },
    { key: 'so2', label: 'SO₂', width: 'w-20' },
    { key: 'temperature', label: 'Temp', width: 'w-20' },
    { key: 'humidity', label: 'Humidity', width: 'w-20' },
    { key: 'wind_speed', label: 'Wind', width: 'w-20' },
  ];

  const getCellValue = (item, key) => {
    const mapping = {
      measured_at: item.measured_at ? new Date(item.measured_at).toLocaleString() : '-',
      aqi: item.aqi?.toFixed(0) ?? '-',
      pm25: item.pm25?.toFixed(1) ?? '-',
      pm10: item.pm10?.toFixed(1) ?? '-',
      no2: item.no2?.toFixed(1) ?? '-',
      o3: item.o3?.toFixed(1) ?? '-',
      co: item.co?.toFixed(2) ?? '-',
      so2: item.so2?.toFixed(1) ?? '-',
      temperature: item.temperature?.toFixed(1) ?? '-',
      humidity: item.humidity?.toFixed(0) ?? '-',
      wind_speed: item.wind_speed?.toFixed(1) ?? '-',
    };
    return mapping[key] ?? '-';
  };

  const getCellColor = (item, key) => {
    if (key === 'aqi') {
      return getAqiColor(item.aqi);
    }
    return 'text-white';
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/10">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`text-left py-3 px-3 font-medium text-gray-400 ${col.width}`}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.slice(0, 100).map((item, idx) => (
            <tr key={item.id || idx} className="border-b border-white/5 hover:bg-white/5">
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={`py-2 px-3 font-mono text-sm ${getCellColor(item, col.key)}`}
                >
                  {getCellValue(item, col.key)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {data.length > 100 && (
        <div className="text-center py-4 text-gray-400 text-sm">
          Showing 100 of {data.length} records. Export to view all.
        </div>
      )}
    </div>
  );
}

DataTable.propTypes = {
  data: PropTypes.array,
  isLoading: PropTypes.bool,
};

function RawStationDataPage() {
  const [stations, setStations] = useState([]);
  const [selectedStation, setSelectedStation] = useState(null);
  const [rawData, setRawData] = useState([]);
  const [isLoadingStations, setIsLoadingStations] = useState(true);
  const [isLoadingData, setIsLoadingData] = useState(false);
  const [isFetching, setIsFetching] = useState(false);
  const [fetchResult, setFetchResult] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [filterStartTime, setFilterStartTime] = useState('');
  const [filterEndTime, setFilterEndTime] = useState('');

  // Load stations on mount
  useEffect(() => {
    loadStations();
  }, []);

  // Auto-load data when station is selected
  useEffect(() => {
    if (selectedStation) {
      loadRawData();
    }
  }, [selectedStation]);

  async function loadStations() {
    setIsLoadingStations(true);
    try {
      const response = await excelFetcherApi.getStations();
      setStations(response.data?.stations || []);
    } catch (error) {
      console.error('Failed to load stations:', error);
      setStations([]);
    } finally {
      setIsLoadingStations(false);
    }
  }

  async function loadRawData() {
    if (!selectedStation) return;

    setIsLoadingData(true);
    try {
      const params = {
        station_id: selectedStation.station_id,
        from_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        to_date: new Date().toISOString().split('T')[0],
        limit: 1000,
      };
      if (filterStartTime) params.from_date = filterStartTime.split('T')[0];
      if (filterEndTime) params.to_date = filterEndTime.split('T')[0];

      const response = await excelFetcherApi.getRecords(params);
      setRawData(response.data?.records || []);
    } catch (error) {
      console.error('Failed to load raw data:', error);
      setRawData([]);
    } finally {
      setIsLoadingData(false);
    }
  }

  async function handleFetch(fetchParams) {
    // No-op: data is pre-fetched by station-excel-fetcher service
    // Reload data after "fetch"
    await loadRawData();
  }

  function handleExport() {
    if (!rawData || rawData.length === 0) return;

    // Convert to CSV
    const headers = [
      'Time',
      'AQI',
      'PM2.5',
      'PM10',
      'NO2',
      'O3',
      'CO',
      'SO2',
      'Temperature',
      'Humidity',
      'Wind Speed',
    ];

    const rows = rawData.map((item) => [
      item.measured_at ? new Date(item.measured_at).toISOString() : '',
      item.aqi ?? '',
      item.pm25 ?? '',
      item.pm10 ?? '',
      item.no2 ?? '',
      item.o3 ?? '',
      item.co ?? '',
      item.so2 ?? '',
      item.temperature ?? '',
      item.humidity ?? '',
      item.wind_speed ?? '',
    ]);

    const csvContent =
      headers.join(',') + '\n' + rows.map((row) => row.map((cell) => `"${cell}"`).join(',')).join('\n');

    // Download
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `raw_data_${selectedStation?.station_code || 'station'}_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }

  return (
    <div className="min-h-screen">
      <Header title="Raw Station Data" subtitle="5-minute interval air quality data from EnviSoft" />

      <div className="p-6 space-y-6">
        {/* Result Banner */}
        {fetchResult && (
          <div
            className={`flex items-center gap-2 px-4 py-3 rounded-xl text-sm ${
              fetchResult.success
                ? 'bg-green-500/15 text-green-400 border border-green-500/20'
                : 'bg-red-500/15 text-red-400 border border-red-500/20'
            }`}
          >
            {fetchResult.success ? (
              <>
                <Database className="w-4 h-4" />
                <span>
                  {fetchResult.message} ({fetchResult.records_saved} saved)
                </span>
              </>
            ) : (
              <>
                <X className="w-4 h-4" />
                <span>{fetchResult.message}</span>
              </>
            )}
            <button
              onClick={() => setFetchResult(null)}
              className="ml-auto hover:opacity-70"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Station & Fetch Form */}
          <div className="lg:col-span-1 space-y-6">
            <div className="card p-4 space-y-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Database className="w-4 h-4" />
                Fetch Data
              </h3>

              {isLoadingStations ? (
                <LoadingSpinner size="sm" />
              ) : (
                <>
                  <StationSelector
                    stations={stations}
                    selectedStation={selectedStation}
                    onSelect={setSelectedStation}
                  />
                  <FetchForm selectedStation={selectedStation} onFetch={handleFetch} />
                </>
              )}
            </div>

            {/* Station Info */}
            {selectedStation && (
              <div className="card p-4">
                <h3 className="text-sm font-semibold text-white mb-3">Selected Station</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Name</span>
                    <span className="text-white">{selectedStation.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Station ID</span>
                    <span className="text-white font-mono text-xs">{selectedStation.station_id}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Data Display */}
          <div className="lg:col-span-2">
            <div className="card">
              <div className="flex items-center justify-between p-4 border-b border-white/10">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Activity className="w-4 h-4" />
                  Raw Data
                  {rawData.length > 0 && (
                    <span className="text-xs text-gray-400 font-normal">
                      ({rawData.length} records)
                    </span>
                  )}
                </h3>
                <div className="flex items-center gap-2">
                  {/* Filter Toggle */}
                  <button
                    onClick={() => setShowFilters(!showFilters)}
                    className={`p-2 rounded-lg transition-colors ${
                      showFilters
                        ? 'bg-brand-500/20 text-brand-400'
                        : 'text-gray-400 hover:bg-white/10'
                    }`}
                  >
                    <Filter className="w-4 h-4" />
                  </button>

                  {/* Export */}
                  <button
                    onClick={handleExport}
                    disabled={!rawData || rawData.length === 0}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Download className="w-4 h-4" />
                    Export CSV
                  </button>

                  {/* Reload */}
                  <button
                    onClick={loadRawData}
                    disabled={!selectedStation || isLoadingData}
                    className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors disabled:opacity-50"
                  >
                    <RefreshCw className={`w-4 h-4 ${isLoadingData ? 'animate-spin' : ''}`} />
                  </button>
                </div>
              </div>

              {/* Filters */}
              {showFilters && (
                <div className="p-4 border-b border-white/10 bg-white/5">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Start Time (ISO)</label>
                      <input
                        type="datetime-local"
                        value={filterStartTime}
                        onChange={(e) => setFilterStartTime(e.target.value)}
                        className="w-full px-3 py-2 bg-[var(--color-bg-card)] border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-brand-500/50"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">End Time (ISO)</label>
                      <input
                        type="datetime-local"
                        value={filterEndTime}
                        onChange={(e) => setFilterEndTime(e.target.value)}
                        className="w-full px-3 py-2 bg-[var(--color-bg-card)] border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-brand-500/50"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end mt-3">
                    <button
                      onClick={() => {
                        setFilterStartTime('');
                        setFilterEndTime('');
                        loadRawData();
                      }}
                      className="px-3 py-1.5 text-sm text-gray-400 hover:text-white"
                    >
                      Clear Filters
                    </button>
                    <button
                      onClick={loadRawData}
                      className="px-3 py-1.5 text-sm bg-brand-500/20 text-brand-400 rounded-lg hover:bg-brand-500/30"
                    >
                      Apply
                    </button>
                  </div>
                </div>
              )}

              {/* Data Table */}
              <div className="max-h-[600px] overflow-y-auto">
                <DataTable data={rawData} isLoading={isLoadingData} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default RawStationDataPage;
