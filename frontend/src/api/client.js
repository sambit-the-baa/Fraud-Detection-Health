import axios from 'axios';

const API_BASE_URL = 'https://fraud-detection-health.onrender.com';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

client.interceptors.request.use(
  config => config,
  error => Promise.reject(error)
);

client.interceptors.response.use(
  response => response,
  error => {
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
