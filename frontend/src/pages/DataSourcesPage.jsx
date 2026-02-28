import { useState, useEffect, useCallback } from 'react';
import { Database, Satellite, Upload, RefreshCw, Clock, Calendar, Settings, Play, FileSpreadsheet, Download } from 'lucide-react';
import Header from '../components/layout/Header';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import EmptyState from '../components/common/EmptyState';
import ExcelImportModal from '../components/satellite/ExcelImportModal';
import { satelliteApi } from '../services/satelliteApi';

// Satellite source configuration
const SATELLITE_SOURCES = [
  {
    id: 'cams_pm25',
    name: 'CAMS PM2.5',
    description: 'Copernicus Atmosphere Monitoring Service - Particulate Matter 2.5μm',
    type: 'satellite',
    resolution: '40km',
    frequency: 'Hourly',
    color: 'blue',
  },
  {
    id: 'cams_pm10',
    name: 'CAMS PM10',
    description: 'Copernicus Atmosphere Monitoring Service - Particulate Matter 10μm',
    type: 'satellite',
    resolution: '40km',
    frequency: 'Hourly',
    color: 'cyan',
  },
  {
    id: 'modis_terra',
    name: 'MODIS Terra AOD',
    description: 'NASA Terra Satellite - Aerosol Optical Depth',
    type: 'satellite',
    resolution: '10km',
    frequency: 'Daily',
    color: 'orange',
  },
  {
    id: 'modis_aqua',
    name: 'MODIS Aqua AOD',
    description: 'NASA Aqua Satellite - Aerosol Optical Depth',
    type: 'satellite',
    resolution: '10km',
    frequency: 'Daily',
    color: 'purple',
  },
  {
    id: 'tropomi_no2',
    name: 'TROPOMI NO₂',
    description: 'Sentinel-5P - Nitrogen Dioxide',
    type: 'satellite',
    resolution: '7×3.5km',
    frequency: 'Daily',
    color: 'red',
  },
  {
    id: 'tropomi_so2',
    name: 'TROPOMI SO₂',
    description: 'Sentinel-5P - Sulfur Dioxide',
    type: 'satellite',
    resolution: '7×3.5km',
    frequency: 'Daily',
    color: 'yellow',
  },
];

const EXCEL_TEMPLATES = [
  {
    id: 'historical_readings',
    name: 'Historical Air Quality Readings',
    description: 'Import historical sensor data with timestamps and pollutant measurements',
    columns: ['timestamp', 'location_id', 'latitude', 'longitude', 'pm25', 'pm10', 'co2', 'no2', 'temperature', 'humidity'],
    icon: FileSpreadsheet,
  },
  {
    id: 'factory_records',
    name: 'Factory Emission Records',
    description: 'Import factory emission data and permit information',
    columns: ['factory_name', 'registration_number', 'latitude', 'longitude', 'industry_type', 'pm25_limit', 'pm10_limit', 'status'],
    icon: FileSpreadsheet,
  },
];

function DataSourceCard({ source, latestData, onRefresh, loading }) {
  const getStatusBadge = () => {
    if (loading) return { label: 'Fetching...', variant: 'secondary' };
    if (latestData) {
      const hoursSince = Math.floor((Date.now() - new Date(latestData.observation_time).getTime()) / 3600000);
      if (hoursSince < 6) return { label: 'Recent', variant: 'success' };
      if (hoursSince < 24) return { label: 'Stale', variant: 'warning' };
      return { label: 'Old', variant: 'danger' };
    }
    return { label: 'No Data', variant: 'secondary' };
  };

  const status = getStatusBadge();
  const lastUpdate = latestData?.observation_time
    ? new Date(latestData.observation_time)
    : null;

  return (
    <div className="card p-4 hover:border-brand-600/50 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg bg-${source.color}-600/20 text-${source.color}-400`}>
            <Satellite size={20} />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">{source.name}</h3>
            <p className="text-xs text-slate-400">{source.resolution} • {source.frequency}</p>
          </div>
        </div>
        <Badge variant={status.variant}>{status.label}</Badge>
      </div>

      <p className="text-xs text-slate-400 mb-4 line-clamp-2">{source.description}</p>

      {lastUpdate && (
        <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-3">
          <Clock size={12} />
          Last update: {lastUpdate.toLocaleString()}
        </div>
      )}

      <div className="flex gap-2">
        <Button
          size="sm"
          variant="ghost"
          onClick={() => onRefresh(source.id)}
          disabled={loading}
          className="flex-1"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Fetch Now
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="flex-1"
        >
          <Settings size={14} />
          Configure
        </Button>
      </div>
    </div>
  );
}

function ImportHistoryCard({ imports }) {
  if (!imports || imports.length === 0) {
    return (
      <EmptyState
        icon={FileSpreadsheet}
        title="No imports yet"
        description="Upload Excel files to import historical data"
        size="sm"
      />
    );
  }

  return (
    <div className="space-y-2">
      {imports.map((imp) => (
        <div
          key={imp.id}
          className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-[var(--color-border)]/50"
        >
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${imp.status === 'completed' ? 'bg-green-600/20 text-green-400' : 'bg-red-600/20 text-red-400'}`}>
              {imp.status === 'completed' ? <CheckCircle size={16} /> : <XCircle size={16} />}
            </div>
            <div>
              <p className="text-sm font-medium text-white">{imp.filename}</p>
              <p className="text-xs text-slate-400">
                {imp.data_type} • {imp.record_count} records
              </p>
            </div>
          </div>
          <div className="text-xs text-slate-500">
            {new Date(imp.import_time).toLocaleString()}
          </div>
        </div>
      ))}
    </div>
  );
}

function ScheduleCard({ schedule, onUpdate }) {
  const [editing, setEditing] = useState(false);
  const [localSchedule, setLocalSchedule] = useState(schedule);

  const handleSave = () => {
    onUpdate(localSchedule);
    setEditing(false);
  };

  return (
    <Card title="Fetch Schedule" icon={<Calendar size={20} />}>
      {editing ? (
        <div className="space-y-4">
          {Object.entries(localSchedule).map(([key, value]) => (
            <div key={key} className="flex items-center gap-3">
              <label className="text-xs text-slate-400 w-32 capitalize">
                {key.replace('_', ' ')}
              </label>
              <input
                type="text"
                value={value}
                onChange={(e) => setLocalSchedule({ ...localSchedule, [key]: e.target.value })}
                className="flex-1 bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white"
                placeholder="Cron expression"
              />
            </div>
          ))}
          <div className="flex gap-2 pt-2">
            <Button size="sm" onClick={handleSave}>Save</Button>
            <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>Cancel</Button>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {schedule && Object.entries(schedule).map(([key, value]) => (
            <div key={key} className="flex justify-between items-center">
              <span className="text-sm text-slate-400 capitalize">{key.replace('_', ' ')}</span>
              <code className="text-xs bg-slate-700 px-2 py-1 rounded text-white font-mono">{value}</code>
            </div>
          ))}
          <Button size="sm" variant="outline" onClick={() => setEditing(true)} className="w-full mt-2">
            <Settings size={14} /> Edit Schedule
          </Button>
        </div>
      )}
    </Card>
  );
}

function DataSourcesPage() {
  const [sources, setSources] = useState([]);
  const [loadingSources, setLoadingSources] = useState(new Set());
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [importHistory, setImportHistory] = useState([]);
  const [schedule, setSchedule] = useState(null);
  const [activeTab, setActiveTab] = useState('satellite');

  // Load initial data
  useEffect(() => {
    fetchAllSources();
    fetchImportHistory();
    fetchSchedule();
  }, []);

  const fetchAllSources = async () => {
    try {
      const promises = SATELLITE_SOURCES.map(async (source) => {
        try {
          const response = await satelliteApi.getLatest(source.id);
          return { ...source, latestData: response };
        } catch {
          return { ...source, latestData: null };
        }
      });
      const results = await Promise.all(promises);
      setSources(results);
    } catch (error) {
      console.error('Failed to fetch sources:', error);
    }
  };

  const fetchImportHistory = async () => {
    // Placeholder - would call API to get import history
    setImportHistory([
      { id: 1, filename: 'readings_2024.xlsx', data_type: 'historical_readings', record_count: 1250, status: 'completed', import_time: new Date(Date.now() - 3600000).toISOString() },
      { id: 2, filename: 'factories_q1.xlsx', data_type: 'factory_records', record_count: 45, status: 'completed', import_time: new Date(Date.now() - 86400000).toISOString() },
    ]);
  };

  const fetchSchedule = async () => {
    try {
      // Placeholder - would call GET /satellite/schedule
      setSchedule({
        modis_fetch: '0 2 * * *',
        tropomi_fetch: '0 3 * * *',
        cams_fetch: '0 */6 * * *',
      });
    } catch (error) {
      console.error('Failed to fetch schedule:', error);
    }
  };

  const handleRefresh = useCallback(async (sourceId) => {
    setLoadingSources((prev) => new Set(prev).add(sourceId));
    try {
      await satelliteApi.triggerFetch({ source: sourceId, date: new Date().toISOString().split('T')[0] });
      await fetchAllSources();
    } catch (error) {
      console.error('Failed to refresh:', error);
    } finally {
      setLoadingSources((prev) => {
        const next = new Set(prev);
        next.delete(sourceId);
        return next;
      });
    }
  }, []);

  const handleUpdateSchedule = async (newSchedule) => {
    try {
      // Placeholder - would call PUT /satellite/schedule
      setSchedule(newSchedule);
    } catch (error) {
      console.error('Failed to update schedule:', error);
    }
  };

  const handleDownloadTemplate = (templateId) => {
    // Placeholder - would call GET /excel/templates/{templateId}
    alert(`Downloading template: ${templateId}`);
  };

  return (
    <div className="min-h-screen">
      <Header
        title="Data Sources"
        subtitle="Manage satellite data sources and Excel imports"
      />

      <div className="p-6 space-y-6">
        {/* Tab Navigation */}
        <div className="flex gap-2 border-b border-slate-700">
          <button
            onClick={() => setActiveTab('satellite')}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'satellite'
                ? 'text-brand-400 border-b-2 border-brand-400'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Satellite size={16} className="inline mr-2" />
            Satellite Sources
          </button>
          <button
            onClick={() => setActiveTab('excel')}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'excel'
                ? 'text-brand-400 border-b-2 border-brand-400'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <FileSpreadsheet size={16} className="inline mr-2" />
            Excel Imports
          </button>
          <button
            onClick={() => setActiveTab('schedule')}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'schedule'
                ? 'text-brand-400 border-b-2 border-brand-400'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Calendar size={16} className="inline mr-2" />
            Schedule
          </button>
        </div>

        {/* Satellite Sources Tab */}
        {activeTab === 'satellite' && (
          <>
            <div className="flex justify-between items-center">
              <p className="text-sm text-slate-400">
                Configure and monitor satellite data sources for your city
              </p>
              <Button onClick={fetchAllSources} variant="outline">
                <RefreshCw size={16} className="mr-2" />
                Refresh All
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {sources.map((source) => (
                <DataSourceCard
                  key={source.id}
                  source={source}
                  latestData={source.latestData}
                  onRefresh={handleRefresh}
                  loading={loadingSources.has(source.id)}
                />
              ))}
            </div>

            <ScheduleCard schedule={schedule} onUpdate={handleUpdateSchedule} />
          </>
        )}

        {/* Excel Imports Tab */}
        {activeTab === 'excel' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <p className="text-sm text-slate-400">
                Import historical air quality data and factory records from Excel files
              </p>
              <Button onClick={() => setImportModalOpen(true)}>
                <Upload size={16} className="mr-2" />
                Import Excel
              </Button>
            </div>

            {/* Templates */}
            <Card title="Excel Templates" icon={<FileSpreadsheet size={20} />}>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {EXCEL_TEMPLATES.map((template) => (
                  <div
                    key={template.id}
                    className="p-4 rounded-lg bg-white/[0.02] border border-slate-700"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-green-600/20 text-green-400">
                          <template.icon size={20} />
                        </div>
                        <div>
                          <h4 className="text-sm font-semibold text-white">{template.name}</h4>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDownloadTemplate(template.id)}
                      >
                        <Download size={14} />
                        Download
                      </Button>
                    </div>
                    <p className="text-xs text-slate-400 mb-3">{template.description}</p>
                    <div>
                      <p className="text-xs text-slate-500 mb-1">Required columns:</p>
                      <div className="flex flex-wrap gap-1">
                        {template.columns.map((col) => (
                          <span
                            key={col}
                            className="text-[10px] bg-slate-700 px-2 py-0.5 rounded text-slate-300 font-mono"
                          >
                            {col}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Import History */}
            <Card title="Import History" icon={<Clock size={20} />}>
              <ImportHistoryCard imports={importHistory} />
            </Card>
          </div>
        )}

        {/* Schedule Tab */}
        {activeTab === 'schedule' && (
          <div className="max-w-2xl">
            <ScheduleCard schedule={schedule} onUpdate={handleUpdateSchedule} />

            <Card title="Manual Fetch" icon={<Play size={20} />} className="mt-6">
              <p className="text-sm text-slate-400 mb-4">
                Trigger an immediate data fetch from any satellite source
              </p>
              <div className="grid grid-cols-2 gap-3">
                {SATELLITE_SOURCES.slice(0, 4).map((source) => (
                  <Button
                    key={source.id}
                    size="sm"
                    variant="outline"
                    onClick={() => handleRefresh(source.id)}
                    disabled={loadingSources.has(source.id)}
                    className="justify-start"
                  >
                    <Satellite size={14} className="mr-2" />
                    {source.name.split(' ')[0]}
                  </Button>
                ))}
              </div>
            </Card>
          </div>
        )}
      </div>

      {/* Excel Import Modal */}
      <ExcelImportModal
        isOpen={importModalOpen}
        onClose={() => setImportModalOpen(false)}
        onImportComplete={() => {
          fetchImportHistory();
          setImportModalOpen(false);
        }}
      />
    </div>
  );
}

export default DataSourcesPage;
