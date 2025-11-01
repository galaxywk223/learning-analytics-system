/**
 * Axios HTTP客户端配置
 */
import axios, { type AxiosInstance } from "axios";
import { ElMessage } from "element-plus";
import router from "@/router";

// 创建axios实例
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:5000",
  timeout: 15000,
});

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
    console.error("请求错误:", error);
    return Promise.reject(error);
  }
);

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    // 保留 blob 响应的完整对象以访问 headers/status (用于导出等场景)
    if (response.config && response.config.responseType === "blob") {
      return response;
    }
    return response.data;
  },
  (error) => {
    console.error("响应错误:", error);

    if (error.response) {
      const { status, data } = error.response;

      switch (status) {
        case 401:
          // 未授权,清除token并跳转登录
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          ElMessage.error(data.message || "登录已过期,请重新登录");
          router.push("/login");
          break;
        case 403:
          ElMessage.error(data.message || "没有权限访问");
          break;
        case 404:
          ElMessage.error(data.message || "请求的资源不存在");
          break;
        case 500:
          ElMessage.error(data.message || "服务器错误");
          break;
        default:
          ElMessage.error(data.message || "请求失败");
      }
    } else if (error.request) {
      ElMessage.error("网络错误,请检查您的网络连接");
    } else {
      ElMessage.error("请求配置错误");
    }

    return Promise.reject(error);
  }
);

export default request;
