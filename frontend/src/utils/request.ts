/**
 * Axios HTTP客户端封装
 */
import axios, { type AxiosInstance, type AxiosRequestConfig } from "axios";
import { ElMessage } from "element-plus";
import router from "@/router";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

const request: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
});

const refreshClient = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
});

type PendingRequest = {
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
};

let isRefreshing = false;
let pendingQueue: PendingRequest[] = [];

const processQueue = (error: unknown | null, token: string | null) => {
  pendingQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else if (token) {
      resolve(token);
    }
  });
  pendingQueue = [];
};

const handleUnauthorized = (message?: string) => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  if (message) {
    ElMessage.error(message);
  }
  if (router.currentRoute.value.path !== "/login") {
    router.push("/login");
  }
};

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 从localStorage获取token
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error("请求拦截异常:", error);
    return Promise.reject(error);
  }
);

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    // 针对 blob 响应需要保留完整 response 以获取 headers/status
    if (response.config && response.config.responseType === "blob") {
      return response;
    }
    return response.data;
  },
  (error) => {
    console.error("响应拦截异常:", error);

    const { response } = error;
    const originalRequest = (error.config || {}) as AxiosRequestConfig & {
      _retry?: boolean;
    };

    if (response?.status === 401) {
      const isAuthRequest =
        originalRequest.url?.includes("/api/auth/login") ||
        originalRequest.url?.includes("/api/auth/refresh");

      const message = response.data?.message || "登录已过期，请重新登录";

      if (originalRequest._retry || isAuthRequest) {
        handleUnauthorized(message);
        return Promise.reject(error);
      }

      const refreshToken = localStorage.getItem("refresh_token");
      if (!refreshToken) {
        handleUnauthorized(message);
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          pendingQueue.push({
            resolve: (token) => {
              originalRequest.headers = originalRequest.headers || {};
              (originalRequest.headers as Record<string, string>).Authorization =
                token;
              resolve(request(originalRequest));
            },
            reject,
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      return new Promise((resolve, reject) => {
        refreshClient
          .post(
            "/api/auth/refresh",
            {},
            {
              headers: {
                Authorization: `Bearer ${refreshToken}`,
              },
            }
          )
          .then((res) => {
            const newAccessToken = res.data?.access_token;
            if (!newAccessToken) {
              throw new Error("Missing access token in refresh response");
            }

            const bearerToken = `Bearer ${newAccessToken}`;
            localStorage.setItem("access_token", newAccessToken);
            request.defaults.headers.common.Authorization = bearerToken;
            processQueue(null, bearerToken);

            originalRequest.headers = originalRequest.headers || {};
            (originalRequest.headers as Record<string, string>).Authorization =
              bearerToken;
            resolve(request(originalRequest));
          })
          .catch((refreshError: any) => {
            processQueue(refreshError, null);
            const refreshMessage =
              refreshError?.response?.data?.message || message;
            handleUnauthorized(refreshMessage);
            reject(refreshError);
          })
          .finally(() => {
            isRefreshing = false;
          });
      });
    }

    if (response) {
      const { status, data } = response;

      switch (status) {
        case 403:
          ElMessage.error(data.message || "无权访问");
          break;
        case 404:
          ElMessage.error(data.message || "请求的资源不存在");
          break;
        case 500:
          ElMessage.error(data.message || "服务器内部错误");
          break;
        default:
          ElMessage.error(data.message || "请求失败");
      }
    } else if (error.code === "ECONNABORTED") {
      ElMessage.error("请求超时，请稍后重试");
    } else if (error.request) {
      ElMessage.error("网络异常，请检查连接");
    } else {
      ElMessage.error("请求发生未知错误");
    }

    return Promise.reject(error);
  }
);

export default request;
