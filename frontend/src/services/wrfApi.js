import api from './api';

const WRF_API_BASE = '/wrf';

export const wrfApi = {
  /**
   * Get recommended WRF configuration for a region
   */
  async getRecommendedConfig(params) {
    const response = await api.get(`${WRF_API_BASE}/recommend-config`, { params });
    return response.data;
  },

  /**
   * Create a new WRF simulation
   */
  async createSimulation(simulationData) {
    const response = await api.post(`${WRF_API_BASE}/simulations`, simulationData);
    return response.data;
  },

  /**
   * List all WRF simulations
   */
  async listSimulations(params = {}) {
    const response = await api.get(`${WRF_API_BASE}/simulations`, { params });
    return response.data;
  },

  /**
   * Get a specific simulation
   */
  async getSimulation(simulationId) {
    const response = await api.get(`${WRF_API_BASE}/simulations/${simulationId}`);
    return response.data;
  },

  /**
   * Get simulation status
   */
  async getSimulationStatus(simulationId) {
    const response = await api.get(`${WRF_API_BASE}/simulations/${simulationId}/status`);
    return response.data;
  },

  /**
   * Start a simulation
   */
  async startSimulation(simulationId) {
    const response = await api.post(`${WRF_API_BASE}/simulations/${simulationId}/start`);
    return response.data;
  },

  /**
   * Cancel a running simulation
   */
  async cancelSimulation(simulationId) {
    const response = await api.post(`${WRF_API_BASE}/simulations/${simulationId}/cancel`);
    return response.data;
  },

  /**
   * Delete a simulation
   */
  async deleteSimulation(simulationId) {
    const response = await api.delete(`${WRF_API_BASE}/simulations/${simulationId}`);
    return response.data;
  },

  /**
   * Get forecast data for a variable
   */
  async getForecastData(simulationId, variable, level = 'surface') {
    const response = await api.get(`${WRF_API_BASE}/simulations/${simulationId}/forecast/${variable}`, {
      params: { level },
    });
    return response.data;
  },
};

export default wrfApi;
