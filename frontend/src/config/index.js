/**
 * 应用配置文件
 */

export default {
  // 应用信息
  app: {
    name: "学习记录器",
    version: "2.0.0",
    description: "个人学习时间跟踪和分析工具",
  },

  // API 配置
  api: {
    baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api",
    timeout: 10000, // 请求超时时间（毫秒）
    withCredentials: true, // 跨域请求是否携带凭证
  },

  // 认证配置
  auth: {
    tokenKey: "auth_token",
    tokenExpiry: 7 * 24 * 60 * 60 * 1000, // 7天（毫秒）
    loginRoute: "/login",
    homeRoute: "/dashboard",
  },

  // 分页配置
  pagination: {
    pageSize: 10,
    pageSizes: [10, 20, 50, 100],
  },

  // 日期配置
  date: {
    format: "YYYY-MM-DD",
    datetimeFormat: "YYYY-MM-DD HH:mm:ss",
    timeFormat: "HH:mm:ss",
  },

  // 图表配置
  charts: {
    colors: [
      "#5470c6",
      "#91cc75",
      "#fac858",
      "#ee6666",
      "#73c0de",
      "#3ba272",
      "#fc8452",
      "#9a60b4",
      "#ea7ccc",
    ],
    animation: true,
    animationDuration: 1000,
  },

  // 主题配置
  theme: {
    default: "light",
    primary: "#409EFF",
    success: "#67C23A",
    warning: "#E6A23C",
    danger: "#F56C6C",
    info: "#909399",
  },

  // 功能开关
  features: {
    enableDarkMode: true,
    enableExport: true,
    enableImport: true,
    enableNotifications: true,
  },
};
