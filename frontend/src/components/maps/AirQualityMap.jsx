import { useState, useCallback } from 'react';
import PropTypes from 'prop-types';
import { GoogleMap, useJsApiLoader } from '@react-google-maps/api';
import { Map as MapIcon, Layers, Locate } from 'lucide-react';
import EmptyState from '../common/EmptyState';
import LoadingSpinner from '../common/LoadingSpinner';
import HeatmapLayer from './HeatmapLayer';

const MAP_LIBRARIES = ['visualization'];

const MAP_STYLES = [
  { elementType: 'geometry', stylers: [{ color: '#0a1018' }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: '#0a1018' }] },
  { elementType: 'labels.text.fill', stylers: [{ color: '#4a5568' }] },
  { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#1a2332' }] },
  { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#0f1720' }] },
  { featureType: 'poi', stylers: [{ visibility: 'off' }] },
];

const DEFAULT_CENTER = { lat: 21.028, lng: 105.854 };
const DEFAULT_ZOOM = 12;

function AirQualityMap({
  markers: _markers = [],
  heatmapData = [],
  center = DEFAULT_CENTER,
  zoom = DEFAULT_ZOOM,
  showHeatmap = true,
  showControls = true,
  height = '100%',
  onMarkerClick: _onMarkerClick,
  children,
  className = '',
}) {
  const [map, setMap] = useState(null);
  const [activeLayer, setActiveLayer] = useState('heatmap');

  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

  const { isLoaded, loadError } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: apiKey || '',
    libraries: MAP_LIBRARIES,
  });

  const onLoad = useCallback((mapInstance) => {
    setMap(mapInstance);
  }, []);

  const onUnmount = useCallback(() => {
    setMap(null);
  }, []);

  if (!apiKey) {
    return (
      <div className={`rounded-xl bg-[var(--color-bg-secondary)] border border-[var(--color-border)] flex items-center justify-center ${className}`} style={{ height }}>
        <EmptyState
          icon={MapIcon}
          title="Map unavailable"
          description="Set VITE_GOOGLE_MAPS_API_KEY in .env to enable the interactive map"
        />
      </div>
    );
  }

  if (loadError) {
    return (
      <div className={`rounded-xl bg-[var(--color-bg-secondary)] border border-[var(--color-border)] flex items-center justify-center ${className}`} style={{ height }}>
        <EmptyState icon={MapIcon} title="Map failed to load" description="Check your API key and network connection" />
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div className={`rounded-xl bg-[var(--color-bg-secondary)] border border-[var(--color-border)] flex items-center justify-center ${className}`} style={{ height }}>
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className={`relative rounded-xl overflow-hidden ${className}`} style={{ height }}>
      {showControls && (
        <div className="absolute top-3 left-3 z-10 flex gap-1.5">
          <button
            onClick={() => setActiveLayer('heatmap')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeLayer === 'heatmap'
                ? 'bg-brand-600/90 text-white shadow-lg'
                : 'bg-[var(--color-bg-card)]/90 text-[var(--color-text-secondary)] border border-[var(--color-border)] hover:bg-[var(--color-bg-card-hover)]'
            } glass`}
          >
            <Layers className="w-3.5 h-3.5" />
            Heatmap
          </button>
          <button
            onClick={() => setActiveLayer('markers')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeLayer === 'markers'
                ? 'bg-brand-600/90 text-white shadow-lg'
                : 'bg-[var(--color-bg-card)]/90 text-[var(--color-text-secondary)] border border-[var(--color-border)] hover:bg-[var(--color-bg-card-hover)]'
            } glass`}
          >
            <Locate className="w-3.5 h-3.5" />
            Markers
          </button>
        </div>
      )}

      <GoogleMap
        mapContainerStyle={{ width: '100%', height: '100%' }}
        center={center}
        zoom={zoom}
        onLoad={onLoad}
        onUnmount={onUnmount}
        options={{
          styles: MAP_STYLES,
          disableDefaultUI: true,
          zoomControl: true,
          mapTypeControl: false,
          streetViewControl: false,
          fullscreenControl: false,
        }}
      >
        {showHeatmap && activeLayer === 'heatmap' && (
          <HeatmapLayer map={map} data={heatmapData} />
        )}
        {children}
      </GoogleMap>
    </div>
  );
}

AirQualityMap.propTypes = {
  markers: PropTypes.array,
  heatmapData: PropTypes.array,
  center: PropTypes.shape({ lat: PropTypes.number, lng: PropTypes.number }),
  zoom: PropTypes.number,
  showHeatmap: PropTypes.bool,
  showControls: PropTypes.bool,
  height: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onMarkerClick: PropTypes.func,
  children: PropTypes.node,
  className: PropTypes.string,
};

export default AirQualityMap;
