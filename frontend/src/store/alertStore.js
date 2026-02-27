import { create } from 'zustand';
import { alertApi } from '../services/alertApi';

const useAlertStore = create((set, get) => ({
  violations: [],
  selectedViolation: null,
  stats: { active: 0, high: 0, resolved: 0 },
  filters: { status: 'all', severity: '' },
  isLoading: false,
  error: null,

  fetchViolations: async (params = {}) => {
    set({ isLoading: true, error: null });
    try {
      const { filters } = get();
      const response = await alertApi.getViolations({
        status: filters.status !== 'all' ? filters.status : undefined,
        severity: filters.severity || undefined,
        ...params,
      });
      const data = response.data;
      const violations = data.data || data || [];
      set({
        violations,
        stats: {
          active: violations.filter((v) => v.status === 'active').length,
          high: violations.filter((v) => v.severity === 'high' && v.status === 'active').length,
          resolved: violations.filter((v) => v.status === 'resolved').length,
        },
        isLoading: false,
      });
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed to load violations', isLoading: false });
    }
  },

  fetchViolationById: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const response = await alertApi.getViolationById(id);
      set({ selectedViolation: response.data, isLoading: false });
      return response.data;
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Violation not found', isLoading: false });
      return null;
    }
  },

  resolveViolation: async (id, data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await alertApi.resolveViolation(id, data);
      const updated = response.data;
      set((state) => ({
        violations: state.violations.map((v) => (v.id === id ? updated : v)),
        selectedViolation: state.selectedViolation?.id === id ? updated : state.selectedViolation,
        isLoading: false,
      }));
      return updated;
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed to resolve violation', isLoading: false });
      throw err;
    }
  },

  setFilters: (filters) => set((state) => ({ filters: { ...state.filters, ...filters } })),
  clearSelected: () => set({ selectedViolation: null }),
  clearError: () => set({ error: null }),
}));

export default useAlertStore;
