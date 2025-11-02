/**
 * 加载状态管理组合式函数
 * 用于管理异步操作的加载状态
 */
import { ref } from "vue";
import { ElMessage } from "element-plus";

interface LoadingOptions {
  successMessage?: string;
  errorMessage?: string;
  showSuccess?: boolean;
  showError?: boolean;
}

export function useLoading() {
  const loading = ref(false);
  const error = ref<any>(null);

  /**
   * 执行异步操作
   * @param asyncFn - 异步函数
   * @param options - 配置选项
   */
  const execute = async <T>(
    asyncFn: () => Promise<T>,
    options: LoadingOptions = {}
  ) => {
    const {
      successMessage = "",
      errorMessage = "操作失败",
      showSuccess = false,
      showError = true,
    } = options;

    loading.value = true;
    error.value = null;

    try {
      const result = await asyncFn();

      if (showSuccess && successMessage) {
        ElMessage.success(successMessage);
      }

      return result;
    } catch (err: any) {
      error.value = err;

      if (showError) {
        const msg =
          err?.response?.data?.message || err?.message || errorMessage;
        ElMessage.error(msg);
      }

      throw err;
    } finally {
      loading.value = false;
    }
  };

  return {
    loading,
    error,
    execute,
  };
}
