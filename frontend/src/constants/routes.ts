/**
 * 路由相关常量
 */

// 路由名称
export const ROUTE_NAMES = {
  // 认证
  LOGIN: "Login",
  REGISTER: "Register",

  // 主要功能
  DASHBOARD: "Dashboard",
  RECORDS: "Records",
  CATEGORIES: "Categories",
  STAGES: "Stages",
  TODOS: "Todos",
  MILESTONES: "Milestones",
  COUNTDOWN: "Countdown",
  CHARTS: "Charts",
  DAILY_PLAN: "DailyPlan",

  // 设置
  SETTINGS: "Settings",
  SETTINGS_APPEARANCE: "SettingsAppearance",
  SETTINGS_ACCOUNT: "SettingsAccount",
  SETTINGS_DATA: "SettingsData",

  // 错误
  NOT_FOUND: "NotFound",
};

// 路由路径
export const ROUTE_PATHS = {
  LOGIN: "/login",
  REGISTER: "/register",
  DASHBOARD: "/dashboard",
  RECORDS: "/records",
  CATEGORIES: "/categories",
  STAGES: "/stages",
  TODOS: "/todos",
  MILESTONES: "/milestones",
  COUNTDOWN: "/countdown",
  CHARTS: "/charts",
  DAILY_PLAN: "/dailyplan",
  SETTINGS: "/settings",
};

// 路由元信息
export const ROUTE_META = {
  REQUIRES_AUTH: "requiresAuth",
  TITLE: "title",
};
