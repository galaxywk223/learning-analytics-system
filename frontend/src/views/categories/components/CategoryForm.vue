<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑分类' : '新增分类'"
    width="420px"
    :close-on-click-modal="false"
    class="ios-dialog"
    align-center
    @close="handleClose"
  >
    <form class="dialog-form" @submit.prevent="handleSubmit">
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

        <!-- Parent Category Selection -->
        <div class="input-row">
          <label>父分类</label>

          <!-- Case 1: Creating subcategory (parent pre-determined but changeable) or Editing subcategory -->
          <div v-if="isSubCategory || parentCategory" class="select-wrapper">
            <select v-model="form.parent_id" class="custom-select">
              <option :value="null">无 (设为根分类)</option>
              <option
                v-for="p in availableParents"
                :key="p.id"
                :value="p.id"
                :disabled="p.id === form.id"
              >
                {{ p.name }}
              </option>
            </select>
          </div>
          <!-- Case 2: Creating root category or Editing root -->
          <div v-else class="select-wrapper">
            <select v-model="form.parent_id" class="custom-select">
              <option :value="null">无 (根分类)</option>
              <option
                v-for="p in availableParents"
                :key="p.id"
                :value="p.id"
                :disabled="p.id === form.id"
              >
                {{ p.name }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <div class="dialog-footer">
        <button type="button" class="pill-btn secondary" @click="handleClose">
          取消
        </button>
        <button type="submit" class="pill-btn primary" :disabled="loading">
          {{
            loading
              ? isEdit
                ? "更新中..."
                : "创建中..."
              : isEdit
                ? "更新"
                : "创建"
          }}
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
  availableParents: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["close", "submit"]);

const defaultFormState = {
  id: null,
  name: "",
  parent_id: null,
};
const form = ref({ ...defaultFormState });

const isEdit = computed(() => {
  return props.categoryData && props.categoryData.id;
});

const isSubCategory = computed(() => {
  // If editing, check if it has a category_id (parent id)
  if (isEdit.value) return !!props.categoryData.category_id;
  // If creating, check if parentCategory prop is passed
  return !!props.parentCategory;
});

// 初始化或填充表单数据
function syncFormFromProps() {
  const name = props.categoryData?.name || "";
  const id = props.categoryData?.id || null;
  // Determine parent_id
  let pid = null;
  if (props.categoryData && props.categoryData.category_id) {
    pid = props.categoryData.category_id;
  } else if (props.parentCategory) {
    pid = props.parentCategory.id;
  }

  Object.assign(form.value, { id, name, parent_id: pid });
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
      parent_id: form.value.parent_id,
      category_id: form.value.parent_id,
    };

    // 如果没有选择父分类，且原本有(或props传递了)，说明可能意图是设为根
    // 但后端通常需要明确的 parent_id (or null/0)

    // 注意：如果是创建模式，CategoriesView 依赖 parentCategory prop 来决定调用 createCategory 还是 createSubCategory
    // 如果在这个表单里改变了层级，view层的逻辑可能需要适配。
    // 为了简单，我们传递 parent_id 给 view，让 view 处理。

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
  },
);

watch(
  () => props.categoryData,
  () => syncFormFromProps(),
  { deep: true },
);
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

.select-wrapper {
  flex: 1;
}

.custom-select {
  width: 100%;
  background: transparent;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 14px;
  color: #111827;
  outline: none;
  appearance: none; /* Remove default arrow */
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236b7280'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 16px;
}

.custom-select:focus {
  border-color: #4f46e5;
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1);
}
</style>
