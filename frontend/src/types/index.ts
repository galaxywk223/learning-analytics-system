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
  target_datetime_utc: string; // 后端返回的字段
  created_at_utc?: string; // 后端返回的字段
  user_id: number;
  // 后端计算的增强字段
  remaining_days?: number;
  is_expired?: boolean;
  progress_percentage?: number;
  card_status?: "normal" | "warning" | "urgent" | "expired";
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

// 专注表单数据类型
export interface FocusFormData {
  name: string;
  categoryId: number | null;
  subcategoryId: number | null;
  notes: string;
}

// 认证相关API响应类型
export interface LoginResponse extends ApiResponse {
  success: boolean;
  access_token: string;
  refresh_token: string;
  user: User;
  message?: string;
}

export interface RegisterResponse extends ApiResponse {
  success: boolean;
  message?: string;
}

export interface UserProfileResponse extends ApiResponse {
  success: boolean;
  user: User;
}

export interface RefreshTokenResponse extends ApiResponse {
  success: boolean;
  access_token: string;
}

// 分类相关API响应类型
export interface CategoriesResponse extends ApiResponse {
  success: boolean;
  categories: Category[];
  items?: Category[];
}

// 座右铭相关API响应类型
export interface MottosResponse extends ApiResponse {
  mottos: Motto[];
}

export interface MottoResponse extends ApiResponse {
  success: boolean;
  motto: Motto;
}

// 阶段相关API响应类型
export interface StagesResponse extends ApiResponse {
  success: boolean;
  stages: Stage[];
  message?: string;
}

export interface StageResponse extends ApiResponse {
  success: boolean;
  stage: Stage;
  message?: string;
}

// 记录相关API响应类型
export interface RecordsResponse extends ApiResponse {
  weeks: any[];
}

// 设置相关API响应类型
export interface SettingsResponse extends ApiResponse {
  theme?: string;
  background_image?: string;
  active_stage_id?: number;
}
