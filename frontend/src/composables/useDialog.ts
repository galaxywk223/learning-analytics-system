/**
 * 通用对话框组合式函数
 * 用于管理对话框的显示、隐藏和表单数据
 */
import { ref, computed, type Ref } from "vue";

interface DialogFormData {
  id?: number | string;
  [key: string]: any;
}

export function useDialog<T extends DialogFormData>(initialFormData: T) {
  const dialogVisible = ref(false);
  const formData = ref({ ...initialFormData });
  const isEditMode = computed(() => !!(formData.value as T).id);

  const openDialog = (data: T | null = null) => {
    if (data) {
      formData.value = { ...data };
    } else {
      formData.value = { ...initialFormData };
    }
    dialogVisible.value = true;
  };

  const closeDialog = () => {
    dialogVisible.value = false;
    formData.value = { ...initialFormData };
  };

  const resetForm = () => {
    formData.value = { ...initialFormData };
  };

  return {
    dialogVisible,
    formData,
    isEditMode,
    openDialog,
    closeDialog,
    resetForm,
  };
}
