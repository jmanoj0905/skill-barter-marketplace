import { create } from 'zustand';
import api from '../lib/api';

// Auto-login as User A for demo
const autoLoginUserA = async () => {
  try {
    const response = await api.post('/auth/login', {
      email: 'usera@test.com',
      password: 'password'
    });
    const { access_token } = response.data;
    localStorage.setItem('token', access_token);

    const userResponse = await api.get('/auth/me');
    const user = userResponse.data;
    localStorage.setItem('user', JSON.stringify(user));

    return { user, token: access_token };
  } catch (error) {
    console.error('Auto-login failed:', error);
    return { user: null, token: null };
  }
};

// Initialize auth state with User A
const initAuth = async () => {
  const storedUser = localStorage.getItem('user');
  const storedToken = localStorage.getItem('token');

  if (storedUser && storedToken) {
    return {
      user: JSON.parse(storedUser),
      token: storedToken,
      isAuthenticated: true
    };
  }

  // Auto-login as User A
  const { user, token } = await autoLoginUserA();
  return {
    user,
    token,
    isAuthenticated: !!token
  };
};

const useAuthStore = create((set, get) => ({
  user: JSON.parse(localStorage.getItem('user')) || null,
  token: localStorage.getItem('token') || null,
  isAuthenticated: !!localStorage.getItem('token'),
  isLoading: false,
  error: null,

  // Initialize auth on app load
  initializeAuth: async () => {
    const auth = await initAuth();
    set(auth);
  },

  login: async (credentials) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post('/auth/login', credentials);
      const { access_token } = response.data;

      localStorage.setItem('token', access_token);

      // Fetch user info
      const userResponse = await api.get('/auth/me');
      const user = userResponse.data;

      localStorage.setItem('user', JSON.stringify(user));

      set({
        token: access_token,
        user,
        isAuthenticated: true,
        isLoading: false,
      });

      return user;
    } catch (error) {
      const message = error.response?.data?.detail || 'Login failed';
      set({ error: message, isLoading: false });
      throw new Error(message);
    }
  },

  register: async (userData) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post('/auth/register', userData);
      const { access_token } = response.data;

      localStorage.setItem('token', access_token);

      // Fetch user info
      const userResponse = await api.get('/auth/me');
      const user = userResponse.data;

      localStorage.setItem('user', JSON.stringify(user));

      set({
        token: access_token,
        user,
        isAuthenticated: true,
        isLoading: false,
      });

      return user;
    } catch (error) {
      const message = error.response?.data?.detail || 'Registration failed';
      set({ error: message, isLoading: false });
      throw new Error(message);
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    });
  },

  clearError: () => set({ error: null }),

  refreshUser: async () => {
    try {
      const userResponse = await api.get('/auth/me');
      const user = userResponse.data;
      localStorage.setItem('user', JSON.stringify(user));
      set({ user });
    } catch (error) {
      // Silently fail
    }
  },
}));

export default useAuthStore;
