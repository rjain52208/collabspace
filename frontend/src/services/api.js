import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${API_URL}/api/token/refresh/`, {
          refresh: refreshToken,
        });

        const { access } = response.data;
        localStorage.setItem('access_token', access);

        originalRequest.headers.Authorization = `Bearer ${access}`;
        return api(originalRequest);
      } catch (err) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(err);
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (userData) => api.post('/register/', userData),
  login: (credentials) => axios.post(`${API_URL}/api/token/`, credentials),
  getCurrentUser: () => api.get('/me/'),
};

// Documents API
export const documentsAPI = {
  getAll: () => api.get('/documents/'),
  getById: (id) => api.get(`/documents/${id}/`),
  create: (data) => api.post('/documents/', data),
  update: (id, data) => api.patch(`/documents/${id}/`, data),
  delete: (id) => api.delete(`/documents/${id}/`),
  share: (id, userIds) => api.post(`/documents/${id}/share/`, { user_ids: userIds }),
  getVersions: (id) => api.get(`/documents/${id}/versions/`),
  uploadFile: (id, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/documents/${id}/upload_file/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// Activities API
export const activitiesAPI = {
  getAll: () => api.get('/activities/'),
};

export default api;
