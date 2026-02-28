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
      // Backend returns access_token (not token)
      const { access_token, user } = response.data;
      localStorage.setItem('token', access_token);
      set({ user, token: access_token, isAuthenticated: true, isLoading: false });
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

  forgotPassword: async (email) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authApi.forgotPassword(email);
      set({ isLoading: false });
      return response.data;
    } catch (err) {
      const message = err.response?.data?.detail || 'Request failed';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  resetPassword: async (token, newPassword) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authApi.resetPassword(token, newPassword);
      set({ isLoading: false });
      return response.data;
    } catch (err) {
      const message = err.response?.data?.detail || 'Password reset failed';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  fetchProfile: async () => {
    try {
      const response = await authApi.getProfile();
      set({ user: response.data });
    } catch (_err) {
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
