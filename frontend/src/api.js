import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Catch 401 globally → redirect to login with "expired" flag
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && window.location.pathname !== "/login") {
      localStorage.removeItem("token");
      const returnTo = window.location.pathname;
      window.location.href = `/login?expired=1&return=${encodeURIComponent(returnTo)}`;
    }
    return Promise.reject(err);
  }
);

export default api;
