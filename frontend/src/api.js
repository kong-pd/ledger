/**
 * Axios instance — 所有 API 请求都走这里
 *
 * 做了两件事：
 *  1. baseURL 指向后端
 *  2. 请求拦截器自动从 localStorage 读 token 加到 Header
 *     这样每个页面不用自己管 token
 */
import axios from "axios";

const api = axios.create({ baseURL: "http://localhost:8000" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
