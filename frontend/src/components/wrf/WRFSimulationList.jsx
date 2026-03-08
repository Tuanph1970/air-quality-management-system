import { useState, useEffect } from 'react';
import { Cloud, Play, Pause, Trash2, Clock, CheckCircle, XCircle, AlertCircle, RefreshCw, FileText } from 'lucide-react';
import Badge from '../common/Badge';
import Button from '../common/Button';
import ProgressBar from '../common/ProgressBar';
import { wrfApi } from '../../services/wrfApi';

/**
 * WRF Simulation List Component
 * Displays list of WRF simulations with status and controls
 */
export default function WRFSimulationList({ onSimulationSelect, onRefresh }) {
  const [simulations, setSimulations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadSimulations = async () => {
    try {
      setLoading(true);
      const data = await wrfApi.listSimulations({ limit: 20 });
      setSimulations(data.simulations || []);
      setError(null);
    } catch (err) {
      setError('Failed to load simulations');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSimulations();
  }, []);

  const handleStart = async (id) => {
    try {
      await wrfApi.startSimulation(id);
      loadSimulations();
      onRefresh?.();
    } catch (err) {
      console.error('Failed to start simulation:', err);
    }
  };

  const handleCancel = async (id) => {
    try {
      await wrfApi.cancelSimulation(id);
      loadSimulations();
    } catch (err) {
      console.error('Failed to cancel simulation:', err);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this simulation?')) {
      try {
        await wrfApi.deleteSimulation(id);
        loadSimulations();
      } catch (err) {
        console.error('Failed to delete simulation:', err);
      }
    }
  };

  const getStatusIcon = (status) => {
    const icons = {
      pending: <Clock className="w-4 h-4" />,
      downloading_data: <RefreshCw className="w-4 h-4 animate-spin" />,
      preprocessing: <RefreshCw className="w-4 h-4 animate-spin" />,
      running: <RefreshCw className="w-4 h-4 animate-spin" />,
      post_processing: <RefreshCw className="w-4 h-4 animate-spin" />,
      completed: <CheckCircle className="w-4 h-4" />,
      failed: <XCircle className="w-4 h-4" />,
      cancelled: <AlertCircle className="w-4 h-4" />,
    };
    return icons[status] || <Clock className="w-4 h-4" />;
  };

  const getStatusBadgeVariant = (status) => {
    const variants = {
      pending: 'gray',
      downloading_data: 'blue',
      preprocessing: 'blue',
      running: 'blue',
      post_processing: 'blue',
      completed: 'green',
      failed: 'red',
      cancelled: 'gray',
    };
    return variants[status] || 'gray';
  };

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
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Loading simulations...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
        <p className="text-red-600">{error}</p>
        <Button onClick={loadSimulations} variant="secondary" className="mt-4">
          Retry
        </Button>
      </div>
    );
  }

  if (simulations.length === 0) {
    return (
      <div className="text-center py-12">
        <Cloud className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No simulations yet</h3>
        <p className="text-gray-500 mb-4">Create your first WRF weather simulation</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {simulations.map((sim) => (
        <Card key={sim.id} className="hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="text-lg font-semibold text-gray-900">{sim.name}</h3>
                <Badge variant={getStatusBadgeVariant(sim.status)}>
                  <span className="flex items-center gap-1">
                    {getStatusIcon(sim.status)}
                    {sim.status.replace('_', ' ')}
                  </span>
                </Badge>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600 mb-3">
                <div>
                  <span className="font-medium">Created:</span>
                  <br />
                  {new Date(sim.created_at).toLocaleDateString()}
                </div>
                <div>
                  <span className="font-medium">Elapsed:</span>
                  <br />
                  {formatDuration(sim.elapsed_seconds)}
                </div>
                <div>
                  <span className="font-medium">Remaining:</span>
                  <br />
                  {formatDuration(sim.estimated_remaining_seconds)}
                </div>
                <div>
                  <span className="font-medium">Progress:</span>
                  <br />
                  {sim.progress_percent}%
                </div>
              </div>

              {sim.status !== 'completed' && sim.status !== 'failed' && sim.status !== 'cancelled' && (
                <div className="mb-3">
                  <ProgressBar
                    progress={sim.progress_percent}
                    className="h-2"
                    showLabel={false}
                  />
                </div>
              )}

              {sim.error_message && (
                <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-800">
                  <strong>Error:</strong> {sim.error_message}
                </div>
              )}
            </div>

            <div className="flex flex-col gap-2 ml-4">
              {sim.status === 'pending' && (
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => handleStart(sim.id)}
                  icon={<Play className="w-4 h-4" />}
                >
                  Start
                </Button>
              )}
              {(sim.status === 'running' || sim.status === 'preprocessing' || sim.status === 'downloading_data') && (
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => handleCancel(sim.id)}
                  icon={<Pause className="w-4 h-4" />}
                >
                  Cancel
                </Button>
              )}
              {(sim.status === 'completed' || sim.status === 'failed' || sim.status === 'cancelled') && (
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => onSimulationSelect?.(sim)}
                  icon={<FileText className="w-4 h-4" />}
                >
                  View
                </Button>
              )}
              <Button
                size="sm"
                variant="danger"
                onClick={() => handleDelete(sim.id)}
                icon={<Trash2 className="w-4 h-4" />}
              >
                Delete
              </Button>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
