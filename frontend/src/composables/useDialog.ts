/**
 * 通用对话框组合式函数
 * 用于管理对话框的显示、隐藏和表单数据
 */
import { ref, computed } from "vue";

export function useDialog(initialFormData = {}) {
  const dialogVisible = ref(false);
  const formData = ref({ ...initialFormData });
  const isEditMode = computed(() => !!formData.value.id);

  const openDialog = (data = null) => {
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
