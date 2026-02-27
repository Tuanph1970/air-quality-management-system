import { create } from 'zustand';
import { airQualityApi } from '../services/airQualityApi';
import { sensorApi } from '../services/sensorApi';
import { alertApi } from '../services/alertApi';
import { factoryApi } from '../services/factoryApi';

const useDashboardStore = create((set) => ({
  currentAqi: null,
  recentReadings: [],
  activeViolations: [],
  factories: [],
  isLoading: false,
  error: null,

  fetchDashboardData: async () => {
    set({ isLoading: true, error: null });
    try {
      const [aqiRes, violationsRes, factoriesRes] = await Promise.allSettled([
        airQualityApi.getCurrentAqi(),
        alertApi.getViolations({ status: 'active', limit: 5 }),
        factoryApi.list({ limit: 10 }),
      ]);

      set({
        currentAqi: aqiRes.status === 'fulfilled' ? aqiRes.value.data : null,
        activeViolations: violationsRes.status === 'fulfilled' ? violationsRes.value.data?.data || [] : [],
        factories: factoriesRes.status === 'fulfilled' ? factoriesRes.value.data?.data || [] : [],
        isLoading: false,
      });
    } catch (err) {
      set({ error: 'Failed to fetch dashboard data', isLoading: false });
    }
  },

  fetchSensorReadings: async (sensorId, params) => {
    try {
      const response = await sensorApi.getReadings(sensorId, params);
      set({ recentReadings: response.data?.data || [] });
    } catch (_err) {
      // Silently handle - readings are non-critical
    }
  },
}));

export default useDashboardStore;
