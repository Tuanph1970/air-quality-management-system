import api from './api';

export const airQualityApi = {
  getCurrentAqi: (params) => api.get('/air-quality/current', { params }),
  getForecast: (params) => api.get('/air-quality/forecast', { params }),
  getMapData: (params) => api.get('/air-quality/map', { params }),
  getHistory: (params) => api.get('/air-quality/history', { params }),
};
