import axios from 'axios';

// ─── Base Axios Instance ───────────────────────────────────────────────────────
const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 60000, // 60s for ML inference
  headers: { 'Content-Type': 'application/json' },
});

// ─── Attach JWT token to every request ────────────────────────────────────────
API.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('agrismart_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Global response error handler ────────────────────────────────────────────
API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired – clear storage and redirect to login
      localStorage.removeItem('agrismart_token');
      localStorage.removeItem('agrismart_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ─── Auth API ─────────────────────────────────────────────────────────────────
export const authAPI = {
  register: (data) => API.post('/api/auth/register', data),
  login: (data) => API.post('/api/auth/login', data),
  getMe: () => API.get('/api/auth/me'),
};

// ─── Disease Detection API ────────────────────────────────────────────────────
export const diseaseAPI = {
  /**
   * Send full data URL (e.g. "data:image/jpeg;base64,/9j/...")
   * Backend strips the prefix — do NOT strip it here
   */
  predict: (dataURL, filename) =>
    API.post('/api/disease/predict', {
      image_base64: dataURL,   // full data URL — backend handles stripping
      filename: filename || 'leaf.jpg',
    }),

  getHistory: (page = 1, limit = 10) =>
    API.get(`/api/disease/history?page=${page}&limit=${limit}`),

  getById: (id) => API.get(`/api/disease/${id}`),
};

// ─── Fertilizer API ───────────────────────────────────────────────────────────
export const fertilizerAPI = {
  recommend: (data) => API.post('/api/fertilizer/recommend', data),
};

// ─── Market Price API ─────────────────────────────────────────────────────────
export const priceAPI = {
  predict: (data) => API.post('/api/price/predict', data),
};

// ─── Voice API ──────────────────────────────────────────────────────────────
export const voiceAPI = {
  process: (transcript, language) => API.post('/api/voice/process', { transcript, language }),
};

// ─── Dashboard API ────────────────────────────────────────────────────────────
export const dashboardAPI = {
  getStats: () => API.get('/api/dashboard/stats'),
  getHistory: (module, page = 1, perPage = 10) =>
    API.get(`/api/dashboard/history/${module}?page=${page}&per_page=${perPage}`),
  getRecentActivity: (limit = 10) => API.get(`/api/dashboard/recent-activity?limit=${limit}`),
};

export default API;