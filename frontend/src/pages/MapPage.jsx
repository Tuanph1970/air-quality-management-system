import { useState } from 'react';
import { Map, Layers, Locate, Factory } from 'lucide-react';
import Header from '../components/layout/Header';
import EmptyState from '../components/common/EmptyState';
import SatelliteDataPanel from '../components/satellite/SatelliteDataPanel';

function MapPage() {
  const [dataSource, setDataSource] = useState('fused'); // 'sensor', 'satellite', 'fused'
  const [activeLayers, setActiveLayers] = useState({
    heatmap: true,
    sensors: false,
    factories: false
  });

  const toggleLayer = (layer) => {
    setActiveLayers(prev => ({ ...prev, [layer]: !prev[layer] }));
  };

  const getHeatmapData = () => {
    // Placeholder - will be replaced with actual data based on dataSource
    switch (dataSource) {
      case 'sensor':
        return []; // Sensor readings data
      case 'satellite':
        return []; // Satellite data
      case 'fused':
      default:
        return []; // Fused data from both sources
    }
  };

  return (
    <div className="min-h-screen">
      <Header title="Map View" subtitle="Geographic air quality visualization" />

      <div className="p-6">
        <div className="card h-[calc(100vh-180px)] flex flex-col">
          {/* Map container */}
          <div className="flex-1 rounded-xl bg-[var(--color-bg-secondary)] border border-[var(--color-border)] overflow-hidden relative">
            
            {/* Data Source Toggle */}
            <div className="absolute top-4 right-4 z-10 bg-slate-800/90 rounded-lg p-3 backdrop-blur-sm">
              <div className="text-xs text-slate-400 mb-2">Data Source</div>
              <div className="flex gap-1">
                {['sensor', 'satellite', 'fused'].map((source) => (
                  <button
                    key={source}
                    onClick={() => setDataSource(source)}
                    className={`px-3 py-1 rounded text-sm capitalize transition-colors ${
                      dataSource === source
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    {source}
                  </button>
                ))}
              </div>
            </div>

            {/* Map Toolbar */}
            <div className="absolute bottom-4 right-4 z-10 bg-slate-800/90 rounded-lg p-2 backdrop-blur-sm">
              <div className="flex gap-1">
                <button
                  onClick={() => toggleLayer('heatmap')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs transition-colors ${
                    activeLayers.heatmap
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  <Layers className="w-3.5 h-3.5" /> Heatmap
                </button>
                <button
                  onClick={() => toggleLayer('sensors')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs transition-colors ${
                    activeLayers.sensors
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  <Locate className="w-3.5 h-3.5" /> Sensors
                </button>
                <button
                  onClick={() => toggleLayer('factories')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs transition-colors ${
                    activeLayers.factories
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  <Factory className="w-3.5 h-3.5" /> Factories
                </button>
              </div>
            </div>

            {/* Satellite Data Panel */}
            <div className="absolute top-4 left-4 z-10 w-72">
              <SatelliteDataPanel onDataSelect={(data) => console.log('Selected:', data)} />
            </div>

            {/* Map placeholder - will integrate @react-google-maps/api */}
            <div className="absolute inset-0 flex items-center justify-center">
              <EmptyState
                icon={Map}
                title="Map view"
                description={`Showing ${dataSource} data source`}
              />
            </div>

            {/* Grid overlay to simulate map texture */}
            <div
              className="absolute inset-0 opacity-5 pointer-events-none"
              style={{
                backgroundImage: `
                  linear-gradient(var(--color-border) 1px, transparent 1px),
                  linear-gradient(90deg, var(--color-border) 1px, transparent 1px)
                `,
                backgroundSize: '40px 40px',
              }}
            />

            {/* Heatmap layer placeholder */}
            {activeLayers.heatmap && (
              <div className="absolute inset-0 pointer-events-none opacity-30">
                {/* Heatmap visualization will be rendered here based on getHeatmapData() */}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default MapPage;
