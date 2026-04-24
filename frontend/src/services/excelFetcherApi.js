import axios from 'axios';

// Excel fetcher runs on port 8011 (dev) or proxied via nginx /api/v1/excel-fetcher/ (prod)
const rawUrl = import.meta.env.VITE_EXCEL_FETCHER_URL || '/api/v1/excel-fetcher';
const EXCEL_FETCHER_URL = rawUrl.endsWith('/api/v1') ? `${rawUrl}/excel-fetcher` : rawUrl;

const excelApi = axios.create({
  baseURL: EXCEL_FETCHER_URL,
  timeout: 120000,
});

export const excelFetcherApi = {
  getStations: () => excelApi.get('/stations'),

  getRecords: (params = {}) => excelApi.get('/records', { params }),

  health: () => excelApi.get('/health'),
};
