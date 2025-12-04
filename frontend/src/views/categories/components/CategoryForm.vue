<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑分类' : '新增分类'"
    @close="handleClose"
    width="420px"
    :close-on-click-modal="false"
    class="ios-dialog"
    align-center
  >
    <form @submit.prevent="handleSubmit" class="dialog-form">
      <div class="ios-input-group">
        <div class="input-row">
          <label>名称</label>
          <input
            v-model="form.name"
            type="text"
            placeholder="请输入分类名称"
            required
            maxlength="50"
          />
        </div>
        
        <div v-if="parentCategory" class="input-row">
          <label>父分类</label>
          <div class="static-value">
            <span class="icon">📂</span>
            {{ parentCategory.name }}
          </div>
        </div>
      </div>

      <div class="dialog-footer">
        <button type="button" class="btn ghost" @click="handleClose">取消</button>
        <button type="submit" class="btn primary" :disabled="loading">
          {{ loading ? (isEdit ? "更新中..." : "创建中...") : (isEdit ? "更新" : "创建") }}
        </button>
      </div>
    </form>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from "vue";
import { ElMessage } from "element-plus";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  categoryData: {
    type: Object,
    default: null,
  },
  parentCategory: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["close", "submit"]);

const defaultFormState = {
  name: "",
};
const form = ref({ ...defaultFormState });

const isEdit = computed(() => {
  return props.categoryData && props.categoryData.id;
});

// 初始化或填充表单数据
function syncFormFromProps() {
  const name = props.categoryData?.name || "";
  Object.assign(form.value, { name });
}

// 处理提交
async function handleSubmit() {
  if (!form.value.name.trim()) {
    ElMessage.warning("请输入分类名称");
    return;
  }

  try {
    // 构建提交数据 - 只提取 name 字段
    const submitData = {
      name: form.value.name.trim(),
    };

    // 如果是子分类，添加父分类信息
    if (props.parentCategory) {
      submitData.parent_id = props.parentCategory.id;
    }

    // 如果是编辑模式，添加ID
    if (isEdit.value) {
      submitData.id = props.categoryData.id;
    }

    emit("submit", submitData);
  } catch (error) {
    console.error("表单验证失败:", error);
    ElMessage.error("请检查表单数据");
  }
}

// 处理关闭
function handleClose() {
  emit("close");
}

// 重置表单
function resetForm() {
  Object.assign(form.value, { ...defaultFormState });
}

// 监听器
watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      nextTick(() => {
        syncFormFromProps();
      });
    } else {
      resetForm();
    }
  }
);

watch(() => props.categoryData, () => syncFormFromProps(), { deep: true });
</script>

<style scoped>
/* Reuse iOS Dialog Styles */
.ios-input-group {
  background: #f9fafb;
  border-radius: 12px;
  padding: 0 16px;
  border: 1px solid #e5e7eb;
  margin-bottom: 24px;
}

.input-row {
  display: flex;
  align-items: center;
  padding: 14px 0;
  border-bottom: 1px solid #e5e7eb;
}

.input-row:last-child {
  border-bottom: none;
}

.input-row label {
  width: 70px;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
}

.input-row input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 14px;
  color: #111827;
  padding: 0;
}

.static-value {
  flex: 1;
  font-size: 14px;
  color: #374151;
  display: flex;
  align-items: center;
  gap: 6px;
}

.static-value .icon {
  font-size: 16px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn {
  border: none;
  border-radius: 8px;
  padding: 8px 20px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn.primary {
  background: #111827;
  color: white;
}

.btn.primary:hover {
  background: #374151;
}

.btn.ghost {
  background: transparent;
  color: #6b7280;
}

.btn.ghost:hover {
  background: #f3f4f6;
  color: #111827;
}

/* Override Element Dialog Styles locally if needed, 
   but ideally these should be global or scoped to the dialog class */
:deep(.el-dialog__header) {
  margin-right: 0;
  padding: 20px 24px;
  border-bottom: 1px solid #f3f4f6;
}

:deep(.el-dialog__title) {
  font-weight: 700;
  font-size: 16px;
  color: #111827;
}

:deep(.el-dialog__body) {
  padding: 24px;
}

:deep(.el-dialog__footer) {
  padding: 0; /* Custom footer used */
}
</style>
