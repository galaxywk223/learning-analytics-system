/**
 * 全局类型定义
 */

// API 响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  data?: T;
  error?: string;
}

// 分页参数
export interface PaginationParams {
  page?: number;
  per_page?: number;
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// 用户类型
export interface User {
  id: number;
  username: string;
  email: string;
  created_at: string;
}

// 分类类型
export interface Category {
  id: number;
  name: string;
  color?: string;
  icon?: string;
  user_id: number;
  subcategories?: SubCategory[];
  children?: SubCategory[];
}

// 子分类类型
export interface SubCategory {
  id: number;
  name: string;
  category_id: number;
  category?: Category;
}

// 学习记录类型
export interface LogEntry {
  id: number;
  user_id: number;
  subcategory_id: number;
  content: string;
  duration_minutes: number;
  log_date: string;
  created_at: string;
  updated_at?: string;
  subcategory?: SubCategory;
}

// 阶段类型
export interface Stage {
  id: number;
  name: string;
  start_date: string;
  end_date?: string;
  description?: string;
  user_id: number;
}

// 倒计时类型
export interface Countdown {
  id: number;
  title: string;
  target_date: string;
  description?: string;
  icon?: string;
  color?: string;
  user_id: number;
  created_at: string;
  is_expired?: boolean;
  days_remaining?: number;
  progress_percentage?: number;
}

// 里程碑类型
export interface Milestone {
  id: number;
  title: string;
  description?: string;
  target_date?: string;
  achieved_date?: string;
  category_id?: number;
  user_id: number;
  is_achieved: boolean;
  created_at: string;
}

// 里程碑分类类型
export interface MilestoneCategory {
  id: number;
  name: string;
  color?: string;
  icon?: string;
  user_id: number;
}

// 座右铭类型
export interface Motto {
  id: number;
  content: string;
  author?: string;
  is_favorite: boolean;
  user_id: number;
  created_at: string;
}

// 待办事项类型
export interface TodoItem {
  id: number;
  content: string;
  is_completed: boolean;
  priority?: "low" | "medium" | "high";
  due_date?: string;
  user_id: number;
  created_at: string;
  updated_at?: string;
}

// 每日计划类型
export interface DailyPlan {
  id: number;
  plan_date: string;
  content: string;
  is_completed: boolean;
  user_id: number;
  created_at: string;
}

// 图表数据类型
export interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

export interface ChartDataset {
  label: string;
  data: number[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
}

// KPI 数据类型
export interface KPIData {
  total_duration_minutes: number;
  total_records: number;
  avg_daily_minutes: number;
  active_days: number;
}

// 设置类型
export interface Settings {
  id: number;
  user_id: number;
  theme?: "light" | "dark" | "auto";
  language?: string;
  timezone?: string;
  [key: string]: any;
}
