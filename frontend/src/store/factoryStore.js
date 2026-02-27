import { create } from 'zustand';
import { factoryApi } from '../services/factoryApi';

const useFactoryStore = create((set, get) => ({
  factories: [],
  selectedFactory: null,
  pagination: { total: 0, skip: 0, limit: 20 },
  filters: { status: '', search: '' },
  isLoading: false,
  error: null,

  fetchFactories: async (params = {}) => {
    set({ isLoading: true, error: null });
    try {
      const { filters, pagination } = get();
      const response = await factoryApi.list({
        status: filters.status || undefined,
        search: filters.search || undefined,
        skip: pagination.skip,
        limit: pagination.limit,
        ...params,
      });
      const data = response.data;
      set({
        factories: data.data || data || [],
        pagination: { ...get().pagination, total: data.total || 0 },
        isLoading: false,
      });
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed to load factories', isLoading: false });
    }
  },

  fetchFactoryById: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const response = await factoryApi.getById(id);
      set({ selectedFactory: response.data, isLoading: false });
      return response.data;
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Factory not found', isLoading: false });
      return null;
    }
  },

  createFactory: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await factoryApi.create(data);
      const newFactory = response.data;
      set((state) => ({
        factories: [newFactory, ...state.factories],
        isLoading: false,
      }));
      return newFactory;
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed to create factory', isLoading: false });
      throw err;
    }
  },

  suspendFactory: async (id, reason) => {
    set({ isLoading: true, error: null });
    try {
      const response = await factoryApi.suspend(id, { reason });
      const updated = response.data;
      set((state) => ({
        factories: state.factories.map((f) => (f.id === id ? updated : f)),
        selectedFactory: state.selectedFactory?.id === id ? updated : state.selectedFactory,
        isLoading: false,
      }));
      return updated;
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed to suspend factory', isLoading: false });
      throw err;
    }
  },

  resumeFactory: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const response = await factoryApi.resume(id);
      const updated = response.data;
      set((state) => ({
        factories: state.factories.map((f) => (f.id === id ? updated : f)),
        selectedFactory: state.selectedFactory?.id === id ? updated : state.selectedFactory,
        isLoading: false,
      }));
      return updated;
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Failed to resume factory', isLoading: false });
      throw err;
    }
  },

  setFilters: (filters) => set((state) => ({ filters: { ...state.filters, ...filters } })),
  setPage: (skip) => set((state) => ({ pagination: { ...state.pagination, skip } })),
  clearSelected: () => set({ selectedFactory: null }),
  clearError: () => set({ error: null }),
}));

export default useFactoryStore;
