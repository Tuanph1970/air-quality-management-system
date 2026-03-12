import api from './api';
import axios from 'axios';

const STATION_INGESTION_API_URL = import.meta.env.VITE_STATION_INGESTION_API_URL || 'http://localhost:8010/api/v1';

// Create a separate axios instance for station ingestion API
const stationApi = axios.create({
  baseURL: STATION_INGESTION_API_URL,
  timeout: 30000,
});

export const stationIngestionApi = {
  // Get all stations
  getStations: () => stationApi.get('/stations'),
  
  // Get a specific station by code
  getStationByCode: (stationCode) => stationApi.get(`/stations/${stationCode}`),
  
  // Get readings for a specific station
  getStationReadings: (stationCode, params) => 
    stationApi.get(`/stations/${stationCode}/readings`, { params }),
  
  // Get time series readings for all stations
  getTimeSeriesReadings: (params) => 
    stationApi.get('/readings/timeseries', { params }),
  
  // Trigger manual sync
  syncStations: () => stationApi.post('/sync/stations'),
  syncAqiData: (hours = 24) => stationApi.post('/sync/aqi', { params: { hours } }),
  
  // Health check
  health: () => stationApi.get('/health'),
};

export default stationIngestionApi;
