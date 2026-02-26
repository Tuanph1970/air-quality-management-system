import api from './api';

export const factoryApi = {
  list: (params) => api.get('/factories', { params }),
  getById: (id) => api.get(`/factories/${id}`),
  create: (data) => api.post('/factories', data),
  update: (id, data) => api.put(`/factories/${id}`, data),
  suspend: (id, data) => api.post(`/factories/${id}/suspend`, data),
  resume: (id) => api.post(`/factories/${id}/resume`),
};
