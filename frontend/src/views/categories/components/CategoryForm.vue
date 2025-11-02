<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑分类' : '新增分类'"
    @close="handleClose"
    width="500px"
    :close-on-click-modal="false"
    class="category-dialog"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
      label-position="top"
    >
      <el-form-item label="分类名称" prop="name">
        <el-input
          v-model="form.name"
          placeholder="请输入分类名称"
          clearable
          maxlength="50"
          show-word-limit
        />
      </el-form-item>

      <el-form-item v-if="parentCategory" label="父分类">
        <el-input :value="parentCategory.name" disabled readonly>
          <template #prefix>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              style="width: 16px; height: 16px"
            >
              <path
                d="M10 4H4c-1.11 0-2 .89-2 2v12c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2h-8l-2-2z"
              />
            </svg>
          </template>
        </el-input>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          {{ isEdit ? "更新" : "创建" }}
        </el-button>
      </div>
    </template>
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

const formRef = ref(null);
const form = ref({
  name: "",
});

const isEdit = computed(() => {
  return props.categoryData && props.categoryData.id;
});

const rules = {
  name: [
    { required: true, message: "请输入分类名称", trigger: "blur" },
    {
      min: 2,
      max: 50,
      message: "分类名称长度在 2 到 50 个字符",
      trigger: "blur",
    },
  ],
};

// 初始化表单数据
function initForm() {
  if (props.categoryData) {
    form.value = {
      name: props.categoryData.name || "",
    };
  } else {
    form.value = {
      name: "",
    };
  }
}

// 处理提交
async function handleSubmit() {
  if (!formRef.value) return;

  try {
    const valid = await formRef.value.validate();
    if (!valid) return;

    // 构建提交数据 - 只提取 name 字段
    const submitData = {
      name: form.value.name,
    };

    // 如果是子分类，添加父分类信息
    if (props.parentCategory) {
      submitData.parent_id = props.parentCategory.id;
    }

    // 如果是编辑模式，添加ID
    if (isEdit.value) {
      submitData.id = props.categoryData.id;
    }

    console.log("Submitting category data:", submitData);
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
  if (formRef.value) {
    formRef.value.resetFields();
  }
  initForm();
}

// 监听器
watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      nextTick(() => {
        initForm();
      });
    } else {
      resetForm();
    }
  }
);

watch(() => props.categoryData, initForm, { deep: true });
</script>

<style scoped>
.category-dialog {
  border-radius: 12px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-dialog__header) {
  background: #fafbfc;
  padding: 20px 24px;
  border-bottom: 1px solid #e8eaf6;
  border-radius: 12px 12px 0 0;
}

:deep(.el-dialog__title) {
  font-weight: 600;
  color: #1e293b;
  font-size: 18px;
}

:deep(.el-dialog__body) {
  padding: 24px;
}

:deep(.el-input__inner) {
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: border-color 0.2s ease;
}

:deep(.el-input__inner:focus) {
  border-color: #667eea;
}

:deep(.el-textarea__inner) {
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: border-color 0.2s ease;
}

:deep(.el-textarea__inner:focus) {
  border-color: #667eea;
}
</style>
