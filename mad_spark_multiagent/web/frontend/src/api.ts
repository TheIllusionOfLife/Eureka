import axios from 'axios';

// Configure axios with the backend URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 12 * 60 * 1000, // 12 minutes timeout for idea generation
});

// Add retry logic for failed requests
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Retry on network errors or 5xx server errors (excluding timeout)
    if (
      (error.code === 'NETWORK_ERROR' || 
       (error.response && error.response.status >= 500 && error.response.status < 600)) &&
      !originalRequest._retry &&
      originalRequest.url !== '/ws/progress' // Don't retry WebSocket endpoints
    ) {
      originalRequest._retry = true;
      
      // Wait 2 seconds before retry
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      console.log('Retrying request to:', originalRequest.url);
      return api(originalRequest);
    }
    
    return Promise.reject(error);
  }
);

export default api;