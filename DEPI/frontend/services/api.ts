import axios, { AxiosError } from "axios";

const API_BASE_URL = "/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor - add auth token if available
api.interceptors.request.use(
  (config) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle common errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      
      if (status === 401) {
        // Unauthorized - clear token and redirect to login
        if (typeof window !== "undefined") {
          localStorage.removeItem("token");
          window.location.href = "/login";
        }
      } else if (status === 403) {
        // Forbidden
        console.error("Access forbidden:", error.response.data);
      } else if (status >= 500) {
        // Server error
        console.error("Server error:", error.response.data);
      }
    } else if (error.request) {
      // Request made but no response received
      console.error("Network error - no response received:", error.message);
    } else {
      // Error in request setup
      console.error("Request setup error:", error.message);
    }
    
    return Promise.reject(error);
  }
);

export default api;
export { API_BASE_URL };
