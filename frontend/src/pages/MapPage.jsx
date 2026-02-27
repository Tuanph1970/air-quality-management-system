
import { Map, Layers, Locate } from 'lucide-react';
import Header from '../components/layout/Header';
import EmptyState from '../components/common/EmptyState';

function MapPage() {
  return (
    <div className="min-h-screen">
      <Header title="Map View" subtitle="Geographic air quality visualization" />

      <div className="p-6">
        <div className="card h-[calc(100vh-180px)] flex flex-col">
          {/* Map toolbar */}
          <div className="flex items-center justify-between pb-4 border-b border-[var(--color-border)] mb-4">
            <div className="flex gap-2">
              <button className="btn-secondary text-xs">
                <Layers className="w-3.5 h-3.5" /> AQI Heatmap
              </button>
              <button className="btn-ghost text-xs">
                <Locate className="w-3.5 h-3.5" /> Sensors
              </button>
              <button className="btn-ghost text-xs">
                <Map className="w-3.5 h-3.5" /> Factories
              </button>
            </div>
          </div>

          {/* Map placeholder - will integrate @react-google-maps/api */}
          <div className="flex-1 rounded-xl bg-[var(--color-bg-secondary)] border border-[var(--color-border)] overflow-hidden relative">
            <div className="absolute inset-0 flex items-center justify-center">
              <EmptyState
                icon={Map}
                title="Map view"
                description="Configure VITE_GOOGLE_MAPS_API_KEY in .env to enable the interactive map"
              />
            </div>
            {/* Grid overlay to simulate map texture */}
            <div
              className="absolute inset-0 opacity-5"
              style={{
                backgroundImage: `
                  linear-gradient(var(--color-border) 1px, transparent 1px),
                  linear-gradient(90deg, var(--color-border) 1px, transparent 1px)
                `,
                backgroundSize: '40px 40px',
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default MapPage;
