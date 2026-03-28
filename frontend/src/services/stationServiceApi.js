import axios from 'axios';

const STATION_SERVICE_API_URL = import.meta.env.VITE_STATION_SERVICE_API_URL || 'http://localhost:8007';

// Create axios instance for station service API
const apiClient = axios.create({
  baseURL: `${STATION_SERVICE_API_URL}/api/v1`,
  timeout: 120000, // 2 minutes for data fetch operations
});

// Add auth token if available
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const stationServiceApi = {
  // ==========================================================================
  // Station CRUD
  // ==========================================================================

  // Get all stations
  getStations: (params = {}) => apiClient.get('/stations', { params }),

  // Get station by ID
  getStation: (stationId) => apiClient.get(`/stations/${stationId}`),

  // Get station by code
  getStationByCode: (stationCode) => apiClient.get(`/stations/code/${stationCode}`),

  // Create station
  createStation: (data) => apiClient.post('/stations', data),

  // Update station
  updateStation: (stationId, data) => apiClient.put(`/stations/${stationId}`, data),

  // Delete station
  deleteStation: (stationId) => apiClient.delete(`/stations/${stationId}`),

  // ==========================================================================
  // Station API Configuration
  // ==========================================================================

  // Configure station API
  configureStationApi: (stationId, data) =>
    apiClient.post(`/stations/${stationId}/configure-api`, data),

  // Activate station
  activateStation: (stationId) => apiClient.post(`/stations/${stationId}/activate`),

  // Deactivate station
  deactivateStation: (stationId, reason = '') =>
    apiClient.post(`/stations/${stationId}/deactivate`, null, { params: { reason } }),

  // ==========================================================================
  // Station Readings
  // ==========================================================================

  // Get readings for a station
  getReadings: (stationId, params = {}) =>
    apiClient.get(`/stations/${stationId}/readings`, { params }),

  // Get latest readings
  getLatestReadings: (stationId) =>
    apiClient.get(`/stations/${stationId}/readings/latest`),

  // Record readings
  recordReadings: (stationId, data) =>
    apiClient.post(`/stations/${stationId}/record-readings`, data),

  // ==========================================================================
  // Raw Station Data (5-minute interval)
  // ==========================================================================

  // Fetch raw 5-minute data from EnviSoft
  fetchRawData: (stationId, data) =>
    apiClient.post(`/stations/${stationId}/fetch-raw-data`, data),

  // Get raw 5-minute data
  getRawData: (stationId, params = {}) =>
    apiClient.get(`/stations/${stationId}/raw-data`, { params }),

  // ==========================================================================
  // Utility
  // ==========================================================================

  // Find nearby stations
  getNearbyStations: (params) => apiClient.get('/stations/nearby', { params }),

  // Health check
  health: () => apiClient.get('/health'),
};

