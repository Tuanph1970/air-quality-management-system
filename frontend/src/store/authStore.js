import { create } from 'zustand';
import { authApi } from '../services/authApi';

const useAuthStore = create((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  isLoading: false,
  error: null,

  login: async (credentials) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authApi.login(credentials);
      const { token, user } = response.data;
      localStorage.setItem('token', token);
      set({ user, token, isAuthenticated: true, isLoading: false });
      return response.data;
    } catch (err) {
      const message = err.response?.data?.detail || 'Login failed';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  register: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authApi.register(data);
      set({ isLoading: false });
      return response.data;
    } catch (err) {
      const message = err.response?.data?.detail || 'Registration failed';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  fetchProfile: async () => {
    try {
      const response = await authApi.getProfile();
      set({ user: response.data });
    } catch (_err) {
      // Token may be invalid
      set({ user: null, token: null, isAuthenticated: false });
      localStorage.removeItem('token');
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    set({ user: null, token: null, isAuthenticated: false, error: null });
  },

  clearError: () => set({ error: null }),
}));

export default useAuthStore;
