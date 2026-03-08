import { useState } from 'react';
import { Cloud, Settings, MapPin, Clock, Layers, Wind, Thermometer, Droplets, Gauge } from 'lucide-react';
import Button from '../common/Button';
import Card from '../common/Card';
import Input from '../common/Input';
import Select from '../common/Select';

/**
 * WRF Simulation Configuration Form
 * Allows users to configure and create new WRF weather simulations
 */
export default function WRFSimulationForm({ onSubmit, onCancel, isLoading = false }) {
  const [formData, setFormData] = useState({
    name: '',
    // Bounding box
    north: 21.5,
    south: 20.5,
    east: 106.0,
    west: 105.5,
    // Simulation parameters
    horizontal_resolution_km: 9,
    vertical_levels: 30,
    simulation_hours: 48,
    output_interval_hours: 1,
    // Physics options
    microphysics: 'wsmd6',
    longwave_radiation: 'rrtm',
    shortwave_radiation: 'dudhia',
    land_surface: 'noah',
    pbl_scheme: 'ysu',
  });

  const [useRecommended, setUseRecommended] = useState(false);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) : value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const physicsOptions = {
    microphysics: [
      { value: 'wsmd3', label: 'WSM 3-class' },
      { value: 'wsmd5', label: 'WSM 5-class' },
      { value: 'wsmd6', label: 'WSM 6-class (Default)' },
      { value: 'thompson', label: 'Thompson' },
      { value: 'morrison', label: 'Morrison' },
    ],
    longwave_radiation: [
      { value: 'rrtm', label: 'RRTM (Default)' },
      { value: 'cam', label: 'CAM' },
      { value: 'newcam', label: 'New CAM' },
    ],
    shortwave_radiation: [
      { value: 'dudhia', label: 'Dudhia (Default)' },
      { value: 'cam', label: 'CAM' },
      { value: 'rrtmg', label: 'RRTMG' },
    ],
    land_surface: [
      { value: 'noah', label: 'NOAH (Default)' },
      { value: 'ruc', label: 'RUC' },
      { value: 'clm4', label: 'CLM4' },
    ],
    pbl_scheme: [
      { value: 'ysu', label: 'YSU (Default)' },
      { value: 'mynn', label: 'MYNN' },
      { value: 'bouLac', label: 'BouLac' },
    ],
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Cloud className="w-5 h-5 text-blue-600" />
          Basic Information
        </h3>
        
        <Input
          label="Simulation Name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          placeholder="e.g., Hanoi Region Forecast"
          required
        />
      </div>

      {/* Domain Configuration */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <MapPin className="w-5 h-5 text-green-600" />
          Domain Configuration
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Input
            label="North Latitude"
            name="north"
            type="number"
            step="0.01"
            min="-90"
            max="90"
            value={formData.north}
            onChange={handleChange}
            required
          />
          <Input
            label="South Latitude"
            name="south"
            type="number"
            step="0.01"
            min="-90"
            max="90"
            value={formData.south}
            onChange={handleChange}
            required
          />
          <Input
            label="East Longitude"
            name="east"
            type="number"
            step="0.01"
            min="-180"
            max="180"
            value={formData.east}
            onChange={handleChange}
            required
          />
          <Input
            label="West Longitude"
            name="west"
            type="number"
            step="0.01"
            min="-180"
            max="180"
            value={formData.west}
            onChange={handleChange}
            required
          />
        </div>

        <div className="bg-blue-50 p-4 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Domain Center:</strong> {((formData.north + formData.south) / 2).toFixed(4)}°N, {((formData.east + formData.west) / 2).toFixed(4)}°E
            <br />
            <strong>Approximate Size:</strong> {Math.abs(formData.north - formData.south) * 111}km × {Math.abs(formData.east - formData.west) * 111 * Math.abs((formData.north + formData.south) / 2)}km
          </p>
        </div>
      </div>

      {/* Simulation Parameters */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Settings className="w-5 h-5 text-gray-600" />
          Simulation Parameters
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Input
            label="Horizontal Resolution (km)"
            name="horizontal_resolution_km"
            type="number"
            step="1"
            min="1"
            max="50"
            value={formData.horizontal_resolution_km}
            onChange={handleChange}
            required
          />
          <Input
            label="Vertical Levels"
            name="vertical_levels"
            type="number"
            step="1"
            min="10"
            max="100"
            value={formData.vertical_levels}
            onChange={handleChange}
            required
          />
          <Input
            label="Simulation Hours"
            name="simulation_hours"
            type="number"
            step="1"
            min="1"
            max="168"
            value={formData.simulation_hours}
            onChange={handleChange}
            required
          />
          <Input
            label="Output Interval (hours)"
            name="output_interval_hours"
            type="number"
            step="1"
            min="1"
            max="24"
            value={formData.output_interval_hours}
            onChange={handleChange}
            required
          />
        </div>

        <div className="bg-amber-50 p-4 rounded-lg">
          <p className="text-sm text-amber-800">
            <strong>Estimated Grid Points:</strong> ~{Math.ceil(Math.abs(formData.north - formData.south) * 111 / formData.horizontal_resolution_km) * Math.ceil(Math.abs(formData.east - formData.west) * 111 / formData.horizontal_resolution_km) * formData.vertical_levels}
            <br />
            <strong>Estimated Runtime:</strong> {Math.ceil(formData.simulation_hours * formData.horizontal_resolution_km / 10)}-{Math.ceil(formData.simulation_hours * formData.horizontal_resolution_km / 5)} hours
          </p>
        </div>
      </div>

      {/* Physics Options */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Layers className="w-5 h-5 text-purple-600" />
          Physics Parameterization
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Select
            label="Microphysics Scheme"
            name="microphysics"
            value={formData.microphysics}
            onChange={handleChange}
            options={physicsOptions.microphysics}
            icon={<Thermometer className="w-4 h-4" />}
          />
          <Select
            label="Longwave Radiation"
            name="longwave_radiation"
            value={formData.longwave_radiation}
            onChange={handleChange}
            options={physicsOptions.longwave_radiation}
            icon={<Wind className="w-4 h-4" />}
          />
          <Select
            label="Shortwave Radiation"
            name="shortwave_radiation"
            value={formData.shortwave_radiation}
            onChange={handleChange}
            options={physicsOptions.shortwave_radiation}
            icon={<Wind className="w-4 h-4" />}
          />
          <Select
            label="Land Surface Model"
            name="land_surface"
            value={formData.land_surface}
            onChange={handleChange}
            options={physicsOptions.land_surface}
            icon={<MapPin className="w-4 h-4" />}
          />
          <Select
            label="PBL Scheme"
            name="pbl_scheme"
            value={formData.pbl_scheme}
            onChange={handleChange}
            options={physicsOptions.pbl_scheme}
            icon={<Gauge className="w-4 h-4" />}
          />
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end gap-3 pt-4 border-t">
        <Button
          type="button"
          variant="secondary"
          onClick={onCancel}
          disabled={isLoading}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          variant="primary"
          isLoading={isLoading}
        >
          <Cloud className="w-4 h-4 mr-2" />
          Create Simulation
        </Button>
      </div>
    </form>
  );
}
