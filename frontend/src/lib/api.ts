import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const API_URL = import.meta.env.VITE_API_URL ?? "/api/v1";

export const api = axios.create({ baseURL: API_URL });

const ACCESS_KEY = "ce_access_token";
const REFRESH_KEY = "ce_refresh_token";

export const tokenStorage = {
  getAccess: () => localStorage.getItem(ACCESS_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set: (access: string, refresh: string) => {
    localStorage.setItem(ACCESS_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

// Anexa o Bearer token em toda requisição.
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStorage.getAccess();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Em 401, tenta renovar o access token via refresh token uma única vez.
let refreshing = false;
api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && !original._retry && !refreshing) {
      const refresh = tokenStorage.getRefresh();
      if (refresh) {
        original._retry = true;
        refreshing = true;
        try {
          const resp = await axios.post(`${API_URL}/auth/refresh`, { refresh_token: refresh });
          tokenStorage.set(resp.data.access_token, resp.data.refresh_token);
          refreshing = false;
          original.headers.Authorization = `Bearer ${resp.data.access_token}`;
          return api(original);
        } catch {
          refreshing = false;
          tokenStorage.clear();
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);
