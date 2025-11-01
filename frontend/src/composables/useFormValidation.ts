/**
 * 表单验证组合式函数
 * 提供常用的表单验证规则
 */
import { ref } from "vue";

export function useFormValidation() {
  const formRef = ref(null);

  /**
   * 必填验证
   */
  const required = (message = "此项为必填项") => ({
    required: true,
    message,
    trigger: "blur",
  });

  /**
   * 邮箱验证
   */
  const email = (message = "请输入有效的邮箱地址") => ({
    type: "email",
    message,
    trigger: "blur",
  });

  /**
   * 长度验证
   */
  const length = (min, max, message) => ({
    min,
    max,
    message: message || `长度应在 ${min} 到 ${max} 个字符之间`,
    trigger: "blur",
  });

  /**
   * 数字验证
   */
  const number = (message = "请输入数字") => ({
    type: "number",
    message,
    trigger: "blur",
  });

  /**
   * 自定义验证
   */
  const custom = (validator, message, trigger = "blur") => ({
    validator: (rule, value, callback) => {
      if (validator(value)) {
        callback();
      } else {
        callback(new Error(message));
      }
    },
    trigger,
  });

  /**
   * 验证表单
   */
  const validateForm = async () => {
    if (!formRef.value) return false;
    try {
      await formRef.value.validate();
      return true;
    } catch (error) {
      return false;
    }
  };

  /**
   * 重置表单
   */
  const resetForm = () => {
    if (formRef.value) {
      formRef.value.resetFields();
    }
  };

  /**
   * 清空验证
   */
  const clearValidate = () => {
    if (formRef.value) {
      formRef.value.clearValidate();
    }
  };

  return {
    formRef,
    required,
    email,
    length,
    number,
    custom,
    validateForm,
    resetForm,
    clearValidate,
  };
}
