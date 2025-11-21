import axios from 'axios';

// Set base URL from .env for production OR fallback to localhost for dev
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create Axios client with config
const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Request interceptor (optional: add auth headers here)
client.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
);

// Response interceptor with robust error logging
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const message =
        error.response.data?.message ||
        error.response.data?.detail ||
        error.response.data?.error ||
        'An error occurred';
      console.error('API Error:', message);
    } else if (error.request) {
      console.error('Network Error: No response from server');
    } else {
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default client;
