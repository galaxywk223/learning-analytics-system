/**
 * 应用状态常量
 */

// 数据加载状态
export const LOADING_STATUS = {
  IDLE: "idle",
  LOADING: "loading",
  SUCCESS: "success",
  ERROR: "error",
};

// 待办状态
export const TODO_STATUS = {
  PENDING: "pending",
  IN_PROGRESS: "in_progress",
  COMPLETED: "completed",
  CANCELLED: "cancelled",
};

// 待办优先级
export const TODO_PRIORITY = {
  LOW: "low",
  MEDIUM: "medium",
  HIGH: "high",
  URGENT: "urgent",
};

// 待办优先级文本
export const TODO_PRIORITY_TEXT = {
  [TODO_PRIORITY.LOW]: "低",
  [TODO_PRIORITY.MEDIUM]: "中",
  [TODO_PRIORITY.HIGH]: "高",
  [TODO_PRIORITY.URGENT]: "紧急",
};

// 待办优先级颜色
export const TODO_PRIORITY_COLORS = {
  [TODO_PRIORITY.LOW]: "#909399",
  [TODO_PRIORITY.MEDIUM]: "#409EFF",
  [TODO_PRIORITY.HIGH]: "#E6A23C",
  [TODO_PRIORITY.URGENT]: "#F56C6C",
};

// 主题模式
export const THEME_MODE = {
  LIGHT: "light",
  DARK: "dark",
  AUTO: "auto",
};

// 日期格式
export const DATE_FORMATS = {
  DATE: "YYYY-MM-DD",
  DATETIME: "YYYY-MM-DD HH:mm:ss",
  TIME: "HH:mm:ss",
  MONTH: "YYYY-MM",
  YEAR: "YYYY",
};

// 分页默认值
export const PAGINATION = {
  PAGE: 1,
  PAGE_SIZE: 10,
  PAGE_SIZES: [10, 20, 50, 100],
};

// 存储键名
export const STORAGE_KEYS = {
  TOKEN: "auth_token",
  USER: "user_info",
  THEME: "theme_mode",
  SETTINGS: "app_settings",
};
