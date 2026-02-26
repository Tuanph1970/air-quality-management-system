import api from './api';

export const sensorApi = {
  list: (params) => api.get('/sensors', { params }),
  getById: (id) => api.get(`/sensors/${id}`),
  register: (data) => api.post('/sensors', data),
  getReadings: (sensorId, params) => api.get(`/sensors/${sensorId}/readings`, { params }),
  submitReading: (data) => api.post('/readings', data),
};
