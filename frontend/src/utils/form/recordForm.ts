import type { FormRules } from "element-plus";
import dayjs from "dayjs";

/**
 * 表单数据接口
 */
export interface FormData {
  task: string;
  log_date: string;
  time_slot: string;
  actual_duration: number;
  duration_hours?: number;
  duration_minutes?: number;
  category_id: number | null;
  subcategory_id: number | null;
  mood: number;
  notes: string;
}

/**
 * 服务器数据接口
 */
export interface ServerData {
  [key: string]: any;
  method?: string | string[];
}

/**
 * 表单验证规则
 */
export const formRules: FormRules = {
  task: [
    { required: true, message: "请输入任务名称", trigger: "blur" },
    {
      min: 2,
      max: 100,
      message: "任务名称长度在 2 到 100 个字符",
      trigger: "blur",
    },
  ],
  log_date: [{ required: true, message: "请选择日期", trigger: "change" }],
  actual_duration: [
    { required: true, message: "请输入时长", trigger: "blur" },
    {
      type: "number",
      min: 1,
      message: "时长必须大于0",
      trigger: "blur",
    },
  ],
  category_id: [{ required: true, message: "请选择分类", trigger: "change" }],
  subcategory_id: [
    { required: true, message: "请选择标签", trigger: "change" },
  ],
};

/**
 * 默认表单数据
 */
export function getDefaultFormData(defaultDate?: string | null): FormData {
  const baseDate = defaultDate ? dayjs(defaultDate) : dayjs();
  const effectiveDate = baseDate.isValid() ? baseDate : dayjs();

  return {
    task: "",
    log_date: effectiveDate.format("YYYY-MM-DD"),
    time_slot: "",
    actual_duration: 0,
    duration_hours: 0,
    duration_minutes: 0,
    category_id: null,
    subcategory_id: null,
    mood: 3,
    notes: "",
  };
}

/**
 * 表单数据验证
 */
export function validateFormData(formData: FormData): string[] {
  const errors: string[] = [];

  if (!formData.task?.trim()) {
    errors.push("任务名称不能为空");
  }

  if (!formData.log_date) {
    errors.push("请选择日期");
  }

  if (!formData.actual_duration || formData.actual_duration <= 0) {
    errors.push("请输入正确的时长");
  }

  if (!formData.category_id) {
    errors.push("请选择分类");
  }

  if (!formData.subcategory_id) {
    errors.push("请选择标签");
  }

  return errors;
}

/**
 * 格式化表单数据用于提交
 */
export function formatFormDataForSubmit(
  formData: FormData
): Record<string, any> {
  // 只发送后端需要的字段
  return {
    task: formData.task?.trim(),
    log_date: formData.log_date,
    time_slot: formData.time_slot?.trim() || null,
    actual_duration: formData.actual_duration,
    category_id: formData.category_id,
    subcategory_id: formData.subcategory_id,
    mood: formData.mood,
    notes: formData.notes?.trim() || null,
  };
}

/**
 * 从服务器数据格式化到表单数据
 */
export function formatServerDataToForm(
  serverData: ServerData,
  defaultDate?: string | null
): FormData {
  const base = getDefaultFormData(defaultDate ?? serverData?.log_date);
  const actualDurationRaw = Number(serverData.actual_duration ?? base.actual_duration ?? 0);
  const durationHours = Math.floor(actualDurationRaw / 60);
  const durationMinutes = actualDurationRaw % 60;

  const subcategoryId =
    serverData.subcategory_id ?? serverData.subcategory?.id ?? null;
  const categoryId =
    serverData.category_id ?? serverData.subcategory?.category_id ?? null;

  return {
    ...base,
    ...serverData,
    actual_duration: actualDurationRaw,
    duration_hours: durationHours,
    duration_minutes: durationMinutes,
    subcategory_id: subcategoryId,
    category_id: categoryId,
    mood: serverData.mood ?? base.mood,
    notes: serverData.notes ?? base.notes,
  } as FormData;
}
