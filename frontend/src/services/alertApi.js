import api from './api';

export const alertApi = {
  getViolations: (params) => api.get('/violations', { params }),
  getViolationById: (id) => api.get(`/violations/${id}`),
  resolveViolation: (id, data) => api.post(`/violations/${id}/resolve`, data),
};
