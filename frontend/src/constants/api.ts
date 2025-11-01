/**
 * API 相关常量
 */

// API 基础路径
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

// API 端点
export const API_ENDPOINTS = {
  // 认证
  AUTH: {
    LOGIN: "/auth/login",
    REGISTER: "/auth/register",
    LOGOUT: "/auth/logout",
    PROFILE: "/auth/profile",
  },

  // 学习记录
  RECORDS: {
    LIST: "/records",
    CREATE: "/records",
    UPDATE: (id) => `/records/${id}`,
    DELETE: (id) => `/records/${id}`,
    DETAIL: (id) => `/records/${id}`,
  },

  // 分类
  CATEGORIES: {
    LIST: "/categories",
    CREATE: "/categories",
    UPDATE: (id) => `/categories/${id}`,
    DELETE: (id) => `/categories/${id}`,
  },

  // 阶段
  STAGES: {
    LIST: "/stages",
    CREATE: "/stages",
    UPDATE: (id) => `/stages/${id}`,
    DELETE: (id) => `/stages/${id}`,
  },

  // 待办
  TODOS: {
    LIST: "/todos",
    CREATE: "/todos",
    UPDATE: (id) => `/todos/${id}`,
    DELETE: (id) => `/todos/${id}`,
    TOGGLE: (id) => `/todos/${id}/toggle`,
  },

  // 倒计时
  COUNTDOWN: {
    LIST: "/countdown",
    CREATE: "/countdown",
    UPDATE: (id) => `/countdown/${id}`,
    DELETE: (id) => `/countdown/${id}`,
  },

  // 里程碑
  MILESTONES: {
    LIST: "/milestones",
    CREATE: "/milestones",
    UPDATE: (id) => `/milestones/${id}`,
    DELETE: (id) => `/milestones/${id}`,
  },

  // 统计图表
  CHARTS: {
    OVERVIEW: "/charts/overview",
    TRENDS: "/charts/trends",
    CATEGORY: "/charts/category",
  },

  // 仪表盘
  DASHBOARD: {
    SUMMARY: "/dashboard/summary",
    RECENT: "/dashboard/recent",
  },
};

// HTTP 状态码
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_ERROR: 500,
};
