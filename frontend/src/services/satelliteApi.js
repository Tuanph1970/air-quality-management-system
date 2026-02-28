import api from './api';

export const satelliteApi = {
  getLatestAll: async () => {
    const sources = ['cams_pm25', 'cams_pm10', 'modis_terra', 'tropomi_no2'];
    const results = await Promise.all(
      sources.map(async (source) => {
        try {
          const response = await api.get(`/satellite/data/latest/${source}`);
          return response.data;
        } catch {
          return null;
        }
      })
    );
    return results.filter(Boolean);
  },

  getLatest: async (source) => {
    const response = await api.get(`/satellite/data/latest/${source}`);
    return response.data;
  },

  getDataForLocation: async (lat, lon, date) => {
    const response = await api.post('/satellite/data/location', {
      latitude: lat,
      longitude: lon,
      date
    });
    return response.data;
  },

  triggerFetch: async (params) => {
    const response = await api.post('/satellite/fetch', params);
    return response.data;
  },

  validateExcel: async (file, dataType) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('data_type', dataType);
    const response = await api.post('/satellite/excel/validate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  importExcel: async (file, dataType) => {
    const formData = new FormData();
    formData.append('file', file);
    const endpoint = dataType === 'historical_readings' 
      ? '/satellite/excel/import/readings'
      : '/satellite/excel/import/factories';
    const response = await api.post(endpoint, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  getImportStatus: async (importId) => {
    const response = await api.get(`/satellite/excel/import/${importId}`);
    return response.data;
  }
};
