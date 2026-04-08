<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑分类' : '新增分类'"
    width="520px"
    :close-on-click-modal="false"
    class="ios-dialog category-dialog"
    align-center
    destroy-on-close
    @close="handleClose"
  >
    <form class="dialog-form category-dialog-form" @submit.prevent="handleSubmit">
      <div class="dialog-intro">
        <p class="dialog-kicker">
          {{ isEdit ? "调整分类信息" : "创建新的分类节点" }}
        </p>
        <p class="dialog-subtitle">
          {{ dialogSubtitle }}
        </p>
      </div>

      <div class="field-grid">
        <label class="field-card">
          <span class="field-label">名称</span>
          <span class="field-hint">给这个分类起一个清晰、好找的名字。</span>
          <el-input
            v-model="form.name"
            placeholder="例如：面试、保研、课程复盘"
            maxlength="50"
            clearable
          />
        </label>

        <label class="field-card">
          <span class="field-label">父分类</span>
          <span class="field-hint">{{ parentHint }}</span>
          <el-select
            v-model="form.parent_id"
            class="field-select"
            placeholder="不选择则作为根分类"
          >
            <el-option
              :label="isSubCategory || parentCategory ? '无，设为根分类' : '无，作为根分类'"
              :value="null"
            />
            <el-option
              v-for="p in availableParents"
              :key="p.id"
              :label="p.name"
              :value="p.id"
              :disabled="p.id === form.id"
            />
          </el-select>
        </label>
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

const dialogSubtitle = computed(() => {
  if (isEdit.value) {
    return "可以在这里修改分类名称，或者重新整理它所在的层级。";
  }

  if (props.parentCategory?.name) {
    return `当前会默认创建在“${props.parentCategory.name}”下，你也可以在下方调整。`;
  }

  return "为学习内容建立更清晰的分组，后续记录和统计都会更直观。";
});

const parentHint = computed(() => {
  if (props.parentCategory?.name) {
    return `默认归属到“${props.parentCategory.name}”，如有需要可改成其他根分类。`;
  }

  if (isEdit.value && props.categoryData?.category_id) {
    return "可以重新挂到其他根分类下，也可以直接设为根分类。";
  }

  return "留空时会直接作为一级分类显示。";
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
.category-dialog-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.dialog-intro {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dialog-kicker {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--brand-primary-strong);
}

.dialog-subtitle {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--color-text-secondary);
}

.field-grid {
  display: grid;
  gap: 14px;
}

.field-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 18px;
  border-radius: 22px;
  border: 1px solid var(--stroke-soft);
  background:
    linear-gradient(
      180deg,
      color-mix(in srgb, var(--surface-soft) 68%, white) 0%,
      var(--surface-card) 100%
    );
  box-shadow:
    inset 0 1px 0 color-mix(in srgb, var(--glass-line) 60%, transparent),
    0 12px 28px -24px color-mix(in srgb, var(--brand-primary) 36%, transparent);
}

.field-label {
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text-heading);
}

.field-hint {
  font-size: 12px;
  line-height: 1.6;
  color: var(--color-text-muted);
}

.field-select {
  width: 100%;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 4px;
}

.dialog-footer .pill-btn {
  min-width: 108px;
}

:deep(.category-dialog) {
  overflow: hidden;
}

:deep(.category-dialog .el-dialog__header) {
  padding: 28px 28px 0;
  border-bottom: none;
}

:deep(.category-dialog .el-dialog__body) {
  padding: 18px 28px 28px;
}

:deep(.category-dialog .el-dialog__title) {
  font-size: clamp(1.45rem, 1.8vw, 1.8rem);
  font-weight: 800;
  letter-spacing: -0.02em;
}

:deep(.category-dialog .el-dialog__headerbtn) {
  top: 22px;
  right: 22px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--surface-soft) 80%, white);
  transition:
    background-color var(--motion-fast) var(--motion-ease),
    transform var(--motion-fast) var(--motion-ease);
}

:deep(.category-dialog .el-dialog__headerbtn:hover) {
  background: var(--brand-primary-soft);
  transform: rotate(90deg);
}

:deep(.category-dialog .el-dialog__close) {
  color: var(--color-text-secondary);
  font-size: 18px;
}

:deep(.category-dialog .el-input__wrapper),
:deep(.category-dialog .el-select__wrapper) {
  border-radius: 16px !important;
  min-height: 48px;
  background: color-mix(in srgb, var(--bg-elevated) 92%, white) !important;
}

@media (max-width: 640px) {
  .dialog-footer {
    flex-direction: column-reverse;
  }

  .dialog-footer .pill-btn {
    width: 100%;
  }

  :deep(.category-dialog) {
    width: min(92vw, 520px) !important;
  }

  :deep(.category-dialog .el-dialog__header) {
    padding: 24px 20px 0;
  }

  :deep(.category-dialog .el-dialog__body) {
    padding: 16px 20px 22px;
  }
}
</style>
