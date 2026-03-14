import { useState } from 'react';
import { Cloud, Plus, MapPin, Settings, RefreshCw } from 'lucide-react';
import Header from '../components/layout/Header';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import WRFSimulationForm from '../components/wrf/WRFSimulationForm';
import WRFSimulationList from '../components/wrf/WRFSimulationList';
import WRFSimulationDetail from '../components/wrf/WRFSimulationDetail';
import { wrfApi } from '../services/wrfApi';

/**
 * WRF Weather Forecasting Page
 * Main page for configuring and managing WRF simulations
 */
export default function WRFPage() {
  const [view, setView] = useState('list'); // 'list', 'create', 'detail'
  const [selectedSimulation, setSelectedSimulation] = useState(null);
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateSimulation = async (formData) => {
    try {
      setIsCreating(true);
      await wrfApi.createSimulation(formData);
      setView('list');
    } catch (err) {
      console.error('Failed to create simulation:', err);
      alert('Failed to create simulation: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsCreating(false);
    }
  };

  const handleSimulationSelect = (simulation) => {
    setSelectedSimulation(simulation);
    setView('detail');
  };

  const handleBackToList = () => {
    setView('list');
    setSelectedSimulation(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <Cloud className="w-8 h-8 text-blue-600" />
                WRF Weather Forecasting
              </h1>
              <p className="mt-2 text-gray-600">
                Configure and run Weather Research and Forecasting (WRF) model simulations for air quality modeling
              </p>
            </div>
            {view === 'list' && (
              <Button
                variant="primary"
                onClick={() => setView('create')}
                icon={Plus}
              >
                New Simulation
              </Button>
            )}
          </div>
        </div>

        {/* Info Banner */}
        <Card className="mb-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Cloud className="w-6 h-6 text-blue-600" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 mb-1">WRF Model Integration</h3>
              <p className="text-sm text-gray-700 mb-2">
                The Weather Research and Forecasting (WRF) model provides high-resolution meteorological data 
                for air quality simulations. This includes temperature, humidity, wind speed/direction, 
                pressure, and precipitation forecasts.
              </p>
              <div className="flex flex-wrap gap-4 text-xs text-gray-600">
                <span className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  Regional Downscaling
                </span>
                <span className="flex items-center gap-1">
                  <Settings className="w-3 h-3" />
                  Configurable Physics
                </span>
                <span className="flex items-center gap-1">
                  <RefreshCw className="w-3 h-3" />
                  GFS Boundary Data
                </span>
              </div>
            </div>
          </div>
        </Card>

        {/* Content */}
        {view === 'create' && (
          <Card>
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Create New Simulation</h2>
              <p className="text-gray-600 text-sm mt-1">
                Configure the WRF model parameters for your weather simulation
              </p>
            </div>
            <WRFSimulationForm
              onSubmit={handleCreateSimulation}
              onCancel={handleBackToList}
              isLoading={isCreating}
            />
          </Card>
        )}

        {view === 'list' && (
          <WRFSimulationList
            onSimulationSelect={handleSimulationSelect}
            onRefresh={() => {}}
          />
        )}

        {view === 'detail' && selectedSimulation && (
          <WRFSimulationDetail
            simulation={selectedSimulation}
            onBack={handleBackToList}
          />
        )}
      </main>
    </div>
  );
}
