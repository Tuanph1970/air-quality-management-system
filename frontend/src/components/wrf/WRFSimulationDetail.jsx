import { useState, useEffect } from 'react';
import { 
  Cloud, Thermometer, Droplets, Wind, Gauge, 
  MapPin, Calendar, Clock, CheckCircle, ArrowLeft, Download
} from 'lucide-react';
import Card from '../common/Card';
import Button from '../common/Button';
import Badge from '../common/Badge';
import { wrfApi } from '../../services/wrfApi';

/**
 * WRF Simulation Detail View
 * Shows detailed information and results of a completed simulation
 */
export default function WRFSimulationDetail({ simulation, onBack }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedVariable, setSelectedVariable] = useState('temperature');

  useEffect(() => {
    if (simulation?.id) {
      loadDetail();
    }
  }, [simulation]);

  const loadDetail = async () => {
    try {
      setLoading(true);
      const data = await wrfApi.getSimulation(simulation.id);
      setDetail(data);
    } catch (err) {
      console.error('Failed to load simulation detail:', err);
    } finally {
      setLoading(false);
    }
  };

  const variables = [
    { id: 'temperature', name: 'Temperature', icon: Thermometer, unit: '°C' },
    { id: 'humidity', name: 'Humidity', icon: Droplets, unit: '%' },
    { id: 'wind_speed', name: 'Wind Speed', icon: Wind, unit: 'm/s' },
    { id: 'wind_direction', name: 'Wind Direction', icon: Wind, unit: '°' },
    { id: 'pressure', name: 'Pressure', icon: Gauge, unit: 'hPa' },
    { id: 'precipitation', name: 'Precipitation', icon: Cloud, unit: 'mm' },
  ];

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Cloud className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Simulation not found</p>
        <Button onClick={onBack} className="mt-4">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to List
        </Button>
      </div>
    );
  }

  const SelectedIcon = variables.find(v => v.id === selectedVariable)?.icon || Thermometer;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button onClick={onBack} variant="secondary" size="sm">
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{detail.name}</h2>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant={detail.status === 'completed' ? 'green' : 'gray'}>
                {detail.status}
              </Badge>
              <span className="text-sm text-gray-500">
                {new Date(detail.created_at).toLocaleString()}
              </span>
            </div>
          </div>
        </div>
        {detail.status === 'completed' && (
          <Button variant="primary" icon={Download}>
            Export Data
          </Button>
        )}
      </div>

      {/* Configuration Summary */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Configuration</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-1">
            <p className="text-sm text-gray-500">Domain</p>
            <p className="font-medium">
              {detail.config?.bounding_box?.north?.toFixed(2)}°N to {detail.config?.bounding_box?.south?.toFixed(2)}°N
            </p>
            <p className="font-medium">
              {detail.config?.bounding_box?.west?.toFixed(2)}°E to {detail.config?.bounding_box?.east?.toFixed(2)}°E
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-gray-500">Resolution</p>
            <p className="font-medium">{detail.config?.horizontal_resolution_km} km horizontal</p>
            <p className="font-medium">{detail.config?.vertical_levels} vertical levels</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-gray-500">Duration</p>
            <p className="font-medium">{detail.config?.simulation_hours} hours</p>
            <p className="font-medium">Output every {detail.config?.output_interval_hours}h</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-gray-500">Runtime</p>
            <p className="font-medium">Elapsed: {formatDuration(detail.elapsed_seconds)}</p>
            <p className="font-medium">Total: {formatDuration(detail.elapsed_seconds)}</p>
          </div>
        </div>
      </Card>

      {/* Variable Selection */}
      {detail.status === 'completed' && (
        <>
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Weather Variables</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {variables.map((variable) => {
                const Icon = variable.icon;
                return (
                  <button
                    key={variable.id}
                    onClick={() => setSelectedVariable(variable.id)}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      selectedVariable === variable.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <Icon className={`w-6 h-6 mx-auto mb-2 ${
                      selectedVariable === variable.id ? 'text-blue-600' : 'text-gray-600'
                    }`} />
                    <p className="text-sm font-medium text-center">{variable.name}</p>
                    <p className="text-xs text-gray-500 text-center">{variable.unit}</p>
                  </button>
                );
              })}
            </div>
          </Card>

          {/* Forecast Visualization Placeholder */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <SelectedIcon className="w-5 h-5 text-blue-600" />
                {variables.find(v => v.id === selectedVariable)?.name} Forecast
              </h3>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Calendar className="w-4 h-4" />
                <span>Time series available</span>
              </div>
            </div>

            {/* Placeholder for forecast chart/map */}
            <div className="bg-gray-100 rounded-lg h-64 flex items-center justify-center">
              <div className="text-center text-gray-500">
                <MapPin className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>Forecast visualization would appear here</p>
                <p className="text-sm">Variable: {selectedVariable}</p>
                <p className="text-sm">Domain: {detail.config?.bounding_box?.center_lat?.toFixed(2)}°N, {detail.config?.bounding_box?.center_lon?.toFixed(2)}°E</p>
              </div>
            </div>

            {/* Output Files */}
            {detail.wrf_output_files?.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Output Files</h4>
                <div className="space-y-1">
                  {detail.wrf_output_files.slice(0, 5).map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
                      <code className="text-gray-700 truncate flex-1">{file}</code>
                      <Button size="sm" variant="secondary">
                        <Download className="w-3 h-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </>
      )}

      {/* Physics Options */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Physics Parameterization</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Microphysics:</span>
            <p className="font-medium">{detail.config?.physics_options?.microphysics || 'N/A'}</p>
          </div>
          <div>
            <span className="text-gray-500">Longwave Radiation:</span>
            <p className="font-medium">{detail.config?.physics_options?.longwave_radiation || 'N/A'}</p>
          </div>
          <div>
            <span className="text-gray-500">Shortwave Radiation:</span>
            <p className="font-medium">{detail.config?.physics_options?.shortwave_radiation || 'N/A'}</p>
          </div>
          <div>
            <span className="text-gray-500">Land Surface:</span>
            <p className="font-medium">{detail.config?.physics_options?.land_surface || 'N/A'}</p>
          </div>
          <div>
            <span className="text-gray-500">PBL Scheme:</span>
            <p className="font-medium">{detail.config?.physics_options?.pbl_scheme || 'N/A'}</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
