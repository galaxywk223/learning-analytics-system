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
