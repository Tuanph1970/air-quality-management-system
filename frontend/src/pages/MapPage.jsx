import { useState, useEffect, useCallback, useMemo } from 'react';
import { Map, Layers, Locate, Factory, Radio, Merge, RefreshCw } from 'lucide-react';
import { GoogleMap, useJsApiLoader, Circle } from '@react-google-maps/api';
import Header from '../components/layout/Header';
import EmptyState from '../components/common/EmptyState';
import LoadingSpinner from '../components/common/LoadingSpinner';
import DataSourceToggle from '../components/maps/DataSourceToggle';
import AirQualityMap from '../components/maps/AirQualityMap';
import DataSourceStatus from '../components/satellite/DataSourceStatus';
import { airQualityApi } from '../services/airQualityApi';
import { sensorApi } from '../services/sensorApi';
import { satelliteApi } from '../services/satelliteApi';
import { getAqiLevel } from '../utils/aqi';

const MAP_LIBRARIES = ['visualization'];
const DEFAULT_CENTER = { lat: 10.7769, lng: 106.7009 }; // Ho Chi Minh City
const DEFAULT_ZOOM = 11;

function MapPage() {
  const [dataSource, setDataSource] = useState('fused'); // 'sensor', 'satellite', 'fused'
  const [heatmapData, setHeatmapData] = useState([]);
  const [sensorMarkers, setSensorMarkers] = useState([]);
  const [factoryMarkers, setFactoryMarkers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [mapBounds, setMapBounds] = useState(null);
  const [selectedSensor, setSelectedSensor] = useState(null);
  const [validationData, setValidationData] = useState(null);

  // Load initial data
  useEffect(() => {
    fetchData();
  }, [dataSource]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch data based on selected source
      await Promise.all([
        fetchHeatmapData(),
        fetchSensorMarkers(),
        fetchFactoryMarkers(),
      ]);
    } catch (error) {
      console.error('Failed to fetch map data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchHeatmapData = async () => {
    try {
      let data = [];
      
      if (dataSource === 'sensor') {
        // Get sensor readings for heatmap
        const response = await airQualityApi.getMapData({
          minLat: DEFAULT_CENTER.lat - 0.5,
          minLng: DEFAULT_CENTER.lng - 0.5,
          maxLat: DEFAULT_CENTER.lat + 0.5,
          maxLng: DEFAULT_CENTER.lng + 0.5,
          zoomLevel: DEFAULT_ZOOM,
        });
        data = response.grid_cells || [];
      } else if (dataSource === 'satellite') {
        // Get satellite data for heatmap
        const fusedData = await airQualityApi.getFusedData({
          lat_min: DEFAULT_CENTER.lat - 0.5,
          lat_max: DEFAULT_CENTER.lat + 0.5,
          lon_min: DEFAULT_CENTER.lng - 0.5,
          lon_max: DEFAULT_CENTER.lng + 0.5,
        });
        data = fusedData.data?.map((point) => ({
          lat: point.latitude,
          lng: point.longitude,
          aqi_value: point.fused_aqi || 0,
          level: getAqiLevel(point.fused_aqi || 0).level,
          color: getAqiLevel(point.fused_aqi || 0).color,
          confidence: point.confidence,
        })) || [];
      } else {
        // Fused data (default)
        const response = await airQualityApi.getFusedMapData({
          north: DEFAULT_CENTER.lat + 0.5,
          south: DEFAULT_CENTER.lat - 0.5,
          east: DEFAULT_CENTER.lng + 0.5,
          west: DEFAULT_CENTER.lng - 0.5,
        });
        data = response.grid_cells || [];
      }

      // Convert to heatmap format
      const heatmapPoints = data.map((cell) => ({
        location: new google.maps.LatLng(cell.lat || cell.latitude, cell.lng || cell.longitude),
        weight: cell.aqi_value / 500, // Normalize to 0-1
        aqi: cell.aqi_value,
        level: cell.level,
        color: cell.color,
      }));

      setHeatmapData(heatmapPoints);
    } catch (error) {
      console.error('Failed to fetch heatmap data:', error);
      setHeatmapData([]);
    }
  };

  const fetchSensorMarkers = async () => {
    try {
      const sensors = await sensorApi.getAll();
      const markers = sensors.map((sensor) => ({
        id: sensor.id,
        position: { lat: sensor.latitude, lng: sensor.longitude },
        name: sensor.name || `Sensor ${sensor.serial_number}`,
        status: sensor.status,
        lastReading: sensor.last_reading,
        aqi: sensor.last_reading?.aqi || 0,
      }));
      setSensorMarkers(markers);
    } catch (error) {
      console.error('Failed to fetch sensors:', error);
      setSensorMarkers([]);
    }
  };

  const fetchFactoryMarkers = async () => {
    try {
      // Would call factory API here
      setFactoryMarkers([]);
    } catch (error) {
      console.error('Failed to fetch factories:', error);
      setFactoryMarkers([]);
    }
  };

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  }, [dataSource]);

  const handleDataSourceChange = (newSource) => {
    setDataSource(newSource);
  };

  const handleSensorClick = async (sensor) => {
    setSelectedSensor(sensor);
    // Fetch validation data for this sensor
    try {
      const validation = await airQualityApi.getSensorValidation(sensor.id);
      setValidationData(validation);
    } catch (error) {
      console.error('Failed to fetch validation data:', error);
    }
  };

  // Calculate data source statistics
  const dataSourceStats = useMemo(() => ({
    sensor: { count: sensorMarkers.length },
    satellite: { count: heatmapData.filter((h) => h.color).length },
    fused: { count: heatmapData.length },
  }), [sensorMarkers, heatmapData]);

  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

  const { isLoaded, loadError } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: apiKey || '',
    libraries: MAP_LIBRARIES,
  });

  if (!apiKey) {
    return (
      <div className="min-h-screen">
        <Header title="Map View" subtitle="Geographic air quality visualization" />
        <div className="p-6">
          <EmptyState
            icon={Map}
            title="Map unavailable"
            description="Set VITE_GOOGLE_MAPS_API_KEY in .env to enable the interactive map"
          />
        </div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="min-h-screen">
        <Header title="Map View" subtitle="Geographic air quality visualization" />
        <div className="p-6">
          <EmptyState
            icon={Map}
            title="Map failed to load"
            description="Check your API key and network connection"
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Header 
        title="Map View" 
        subtitle="Geographic air quality visualization"
        action={
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="btn-primary flex items-center gap-2"
          >
            <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
            Refresh
          </button>
        }
      />

      <div className="p-6 h-[calc(100vh-140px)]">
        <div className="grid grid-cols-12 gap-4 h-full">
          {/* Main Map Area */}
          <div className="col-span-9 flex flex-col gap-4 h-full">
            {/* Data Source Toggle */}
            <div className="card p-3 flex items-center justify-between">
              <DataSourceToggle
                value={dataSource}
                onChange={handleDataSourceChange}
                stats={dataSourceStats}
              />
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span>Showing:</span>
                <span className="text-white font-medium capitalize">{dataSource} data</span>
              </div>
            </div>

            {/* Map Container */}
            <div className="card flex-1 relative overflow-hidden">
              {loading ? (
                <div className="absolute inset-0 flex items-center justify-center">
                  <LoadingSpinner size="lg" />
                </div>
              ) : (
                <AirQualityMap
                  center={DEFAULT_CENTER}
                  zoom={DEFAULT_ZOOM}
                  heatmapData={heatmapData.map((h) => ({
                    location: { lat: h.location.lat(), lng: h.location.lng() },
                    weight: h.weight,
                    aqi: h.aqi,
                  }))}
                  showHeatmap={true}
                  showControls={true}
                >
                  {/* Sensor Markers */}
                  {sensorMarkers.map((sensor) => (
                    <Circle
                      key={sensor.id}
                      center={sensor.position}
                      radius={500}
                      options={{
                        fillColor: getAqiLevel(sensor.aqi).color,
                        fillOpacity: 0.3,
                        strokeColor: getAqiLevel(sensor.aqi).color,
                        strokeWeight: 2,
                        clickable: true,
                      }}
                      onClick={() => handleSensorClick(sensor)}
                    />
                  ))}
                </AirQualityMap>
              )}
            </div>
          </div>

          {/* Right Sidebar */}
          <div className="col-span-3 flex flex-col gap-4 h-full overflow-y-auto">
            {/* Data Source Status */}
            <DataSourceStatus compact onRefresh={handleRefresh} />

            {/* Selected Sensor Details */}
            {selectedSensor && (
              <div className="card">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Radio size={16} className="text-blue-400" />
                    <h3 className="text-sm font-semibold text-white">{selectedSensor.name}</h3>
                  </div>
                  <button
                    onClick={() => setSelectedSensor(null)}
                    className="text-slate-400 hover:text-white"
                  >
                    ×
                  </button>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Status:</span>
                    <span className={selectedSensor.status === 'online' ? 'text-green-400' : 'text-red-400'}>
                      {selectedSensor.status}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Last Reading:</span>
                    <span className="text-white">{selectedSensor.aqi} AQI</span>
                  </div>
                  {validationData && (
                    <div className="pt-2 border-t border-slate-700">
                      <div className="text-xs text-slate-400 mb-1">Validation</div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Correlation:</span>
                        <span className="text-white font-mono">{validationData.correlation?.toFixed(3)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Deviation:</span>
                        <span className={validationData.is_valid ? 'text-green-400' : 'text-red-400'}>
                          {validationData.is_valid ? 'Within tolerance' : 'Anomaly detected'}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Legend */}
            <div className="card">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Layers size={16} />
                AQI Legend
              </h3>
              <div className="space-y-2">
                {[
                  { level: 'Good', range: '0-50', color: '#22c55e' },
                  { level: 'Moderate', range: '51-100', color: '#eab308' },
                  { level: 'Unhealthy (SG)', range: '101-150', color: '#f97316' },
                  { level: 'Unhealthy', range: '151-200', color: '#ef4444' },
                  { level: 'Very Unhealthy', range: '201-300', color: '#a855f7' },
                  { level: 'Hazardous', range: '301+', color: '#7f1d1d' },
                ].map((item) => (
                  <div key={item.level} className="flex items-center gap-2">
                    <div
                      className="w-4 h-4 rounded"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-xs text-slate-300 flex-1">{item.level}</span>
                    <span className="text-xs text-slate-500 font-mono">{item.range}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Data Source Info */}
            <div className="card">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Merge size={16} />
                Data Sources
              </h3>
              <div className="space-y-3 text-xs">
                <div className="flex items-start gap-2">
                  <Radio size={14} className="text-blue-400 mt-0.5" />
                  <div>
                    <div className="text-white font-medium">Ground Sensors</div>
                    <div className="text-slate-400">
                      Real-time IoT sensor readings from {sensorMarkers.length} active stations
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <Map size={14} className="text-purple-400 mt-0.5" />
                  <div>
                    <div className="text-white font-medium">Satellite Data</div>
                    <div className="text-slate-400">
                      CAMS, MODIS, and TROPOMI atmospheric observations
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <Merge size={14} className="text-green-400 mt-0.5" />
                  <div>
                    <div className="text-white font-medium">Fused Data</div>
                    <div className="text-slate-400">
                      ML-calibrated combination with cross-validation
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default MapPage;
