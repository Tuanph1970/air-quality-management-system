import api from './api';

export const airQualityApi = {
  getCurrentAqi: (params) => api.get('/air-quality/current', { params }),
  getForecast: (params) => api.get('/air-quality/forecast', { params }),
  getMapData: (params) => api.get('/air-quality/map', { params }),
  getHistory: (params) => api.get('/air-quality/history', { params }),
  
  // Fused Data endpoints
  getFusedData: (params) => api.get('/air-quality/fused', { params }),
  getFusedMapData: (params) => api.get('/air-quality/fused/map', { params }),
  triggerFusion: () => api.post('/air-quality/fuse'),
  
  // Validation endpoints
  getValidationReport: () => api.get('/air-quality/validation/report'),
  getSensorValidation: (sensorId) => api.get(`/air-quality/validation/sensors/${sensorId}`),
  runValidation: () => api.post('/air-quality/validation/run'),
  
  // Calibration endpoints
  getCalibrationStatus: () => api.get('/air-quality/calibration/status'),
  getCalibrationMetrics: () => api.get('/air-quality/calibration/metrics'),
  trainCalibration: (params) => api.post('/air-quality/calibration/train', params),
};

