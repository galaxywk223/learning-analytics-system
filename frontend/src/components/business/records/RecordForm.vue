<template>
  <el-form
    ref="formRef"
    :model="form"
    :rules="rules"
    label-position="top"
    @submit.prevent="submitForm"
    class="record-form"
  >
    <!-- 任务名称 -->
    <el-form-item label="📝 任务" prop="task">
      <el-input
        v-model="form.task"
        placeholder="例如：学习 Vue Router"
        size="large"
        clearable
      />
    </el-form-item>

    <!-- 日期、时间段、时长 -->
    <el-row :gutter="16">
      <el-col :span="8">
        <el-form-item label="📅 日期" prop="log_date">
          <el-date-picker
            v-model="form.log_date"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
            size="large"
          />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="⏰ 时间段" prop="time_slot">
          <el-input
            v-model="form.time_slot"
            placeholder="例如：9:00-11:00"
            size="large"
            clearable
          />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="⏱️ 实际时长">
          <div class="duration-inputs">
            <div class="duration-item">
              <el-input-number
                v-model="form.duration_hours"
                :min="0"
                :max="24"
                controls-position="right"
                size="large"
              />
              <span class="duration-unit">小时</span>
            </div>
            <div class="duration-item">
              <el-input-number
                v-model="form.duration_minutes"
                :min="0"
                :max="59"
                controls-position="right"
                size="large"
              />
              <span class="duration-unit">分钟</span>
            </div>
          </div>
        </el-form-item>
      </el-col>
    </el-row>

    <!-- 分类和标签 -->
    <el-row :gutter="16">
      <el-col :span="12">
        <el-form-item label="📁 分类" prop="category_id">
          <el-select
            v-model="form.category_id"
            placeholder="请选择分类"
            style="width: 100%"
            size="large"
            @change="onCategoryChange"
          >
            <el-option
              v-for="item in categoryStore.categoryOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="🏷️ 标签" prop="subcategory_id">
          <el-select
            v-model="form.subcategory_id"
            placeholder="请先选择分类"
            style="width: 100%"
            size="large"
            :disabled="!subCategoryOptions.length"
            clearable
          >
            <el-option
              v-for="item in subCategoryOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
      </el-col>
    </el-row>

    <el-divider />

    <!-- 笔记 -->
    <el-form-item label="💭 笔记" prop="notes">
      <el-input
        v-model="form.notes"
        type="textarea"
        :rows="4"
        placeholder="记录一些想法或遇到的问题..."
        maxlength="500"
        show-word-limit
      />
    </el-form-item>

    <!-- 心情 - 5个表情 😃 😊 😐 😟 😠 -->
    <el-form-item label="😊 心情" prop="mood">
      <el-radio-group v-model="form.mood" size="large" class="mood-radios">
        <el-radio :label="5" border>😃</el-radio>
        <el-radio :label="4" border>😊</el-radio>
        <el-radio :label="3" border>😐</el-radio>
        <el-radio :label="2" border>😟</el-radio>
        <el-radio :label="1" border>😠</el-radio>
      </el-radio-group>
    </el-form-item>

    <!-- 按钮 -->
    <div class="dialog-footer">
      <el-button size="large" @click="$emit('cancel')">取消</el-button>
      <el-button
        size="large"
        type="primary"
        @click="submitForm"
        :loading="loading"
      >
        {{ isEditing ? "💾 更新记录" : "✨ 添加记录" }}
      </el-button>
    </div>
  </el-form>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from "vue";
import { useCategoryStore } from "@/stores/modules/category";
import { ElMessage } from "element-plus";

const props = defineProps({
  record: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  defaultDate: {
    type: String,
    default: null,
  },
});

const emit = defineEmits(["submit", "cancel"]);

const categoryStore = useCategoryStore();
const formRef = ref(null);

const isEditing = computed(() => !!props.record?.id);

const form = reactive({
  id: null,
  log_date: "",
  time_slot: "",
  task: "",
  duration_hours: 0,
  duration_minutes: 0,
  category_id: null,
  subcategory_id: null,
  mood: 3,
  notes: "",
});

const rules = {
  task: [{ required: true, message: "请输入任务名称", trigger: "blur" }],
  log_date: [{ required: true, message: "请选择日期", trigger: "change" }],
};

const subCategoryOptions = computed(() => {
  if (!form.category_id) return [];
  return categoryStore.getSubCategoryOptions(form.category_id);
});

function onCategoryChange() {
  console.log("Category changed to:", form.category_id);
  const options = categoryStore.getSubCategoryOptions(form.category_id);
  console.log("Available subcategories:", options);
  form.subcategory_id = null;
}

function setFormValues(record) {
  if (!record) {
    formRef.value?.resetFields();
    form.id = null;
    form.log_date = props.defaultDate || new Date().toISOString().split("T")[0];
    form.time_slot = "";
    form.task = "";
    form.duration_hours = 0;
    form.duration_minutes = 0;
    form.category_id = null;
    form.subcategory_id = null;
    form.mood = 3;
    form.notes = "";
  } else {
    form.id = record.id;
    form.log_date = record.log_date;
    form.time_slot = record.time_slot || "";
    form.task = record.task;

    // 将 actual_duration (分钟) 转换为小时和分钟
    const totalMinutes = record.actual_duration || 0;
    form.duration_hours = Math.floor(totalMinutes / 60);
    form.duration_minutes = totalMinutes % 60;

    // 从 subcategory 获取 category_id
    if (record.subcategory) {
      form.category_id = record.subcategory.category_id;
      setTimeout(() => {
        form.subcategory_id = record.subcategory_id;
      }, 50);
    } else {
      form.category_id = null;
      form.subcategory_id = null;
    }

    form.mood = record.mood || 3;
    form.notes = record.notes || "";
  }
}

watch(
  () => props.record,
  (newRecord) => {
    setFormValues(newRecord);
  },
  { immediate: true }
);

watch(
  () => props.defaultDate,
  (newDate) => {
    if (newDate && !isEditing.value) {
      form.log_date = newDate;
    }
  }
);

onMounted(() => {
  console.log("RecordForm mounted, fetching categories...");
  categoryStore.fetchCategories().then(() => {
    console.log("Categories loaded:", categoryStore.categoryOptions);
    console.log("Full tree:", categoryStore.tree);
  });
  if (!isEditing.value) {
    form.log_date = props.defaultDate || new Date().toISOString().split("T")[0];
  }
});

const submitForm = async () => {
  if (!formRef.value) return;
  try {
    await formRef.value.validate();
    
    // 构建提交数据，只包含有效字段
    const submitData = {
      task: form.task,
      log_date: form.log_date,
      time_slot: form.time_slot || null,
      duration_hours: form.duration_hours || 0,
      duration_minutes: form.duration_minutes || 0,
      subcategory_id: form.subcategory_id || null,
      mood: form.mood || 3,
      notes: form.notes || null,
    };
    
    // 如果是编辑模式，添加ID
    if (isEditing.value) {
      submitData.id = form.id;
    }
    
    console.log("Submitting form data:", submitData);
    emit("submit", submitData);
  } catch (error) {
    console.error("Form validation error:", error);
    ElMessage.error("请检查表单输入");
  }
};
</script>

<style scoped>
.record-form {
  padding: 0;
}

.duration-inputs {
  display: flex;
  gap: 12px;
  width: 100%;
}

.duration-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.duration-unit {
  color: #64748b;
  font-weight: 500;
  font-size: 0.875rem;
  white-space: nowrap;
}

.dialog-footer {
  text-align: right;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 2px solid rgba(226, 232, 240, 0.6);
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.dialog-footer :deep(.el-button) {
  padding: 12px 32px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.95rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 120px;
}

.dialog-footer :deep(.el-button--default) {
  border: 2px solid rgba(226, 232, 240, 0.8);
  background: white;
  color: #64748b;
}

.dialog-footer :deep(.el-button--default):hover {
  background: #f8fafc;
  border-color: #cbd5e1;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.dialog-footer :deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
}

.dialog-footer :deep(.el-button--primary):hover {
  background: linear-gradient(135deg, #5568d3 0%, #63398e 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

:deep(.el-form) {
  padding: 0.5rem;
}

:deep(.el-form-item__label) {
  font-weight: 600;
  color: #1e293b;
  font-size: 0.95rem;
  margin-bottom: 0.5rem;
}

:deep(.el-input__wrapper) {
  border-radius: 10px;
  padding: 8px 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

:deep(.el-input__wrapper):hover {
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #667eea;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.25);
}

:deep(.el-input--large .el-input__wrapper) {
  padding: 12px 16px;
  font-size: 1rem;
}

:deep(.el-select) {
  width: 100%;
}

:deep(.el-select .el-input__wrapper) {
  border-radius: 10px;
}

:deep(.el-textarea__inner) {
  border-radius: 10px;
  padding: 12px 16px;
  border: 2px solid transparent;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  font-size: 0.95rem;
}

:deep(.el-textarea__inner):hover {
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

:deep(.el-textarea__inner):focus {
  border-color: #667eea;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.25);
}

:deep(.el-date-editor) {
  width: 100%;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-input-number .el-input__wrapper) {
  border-radius: 10px;
}

:deep(.el-radio-group) {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

:deep(.el-radio.is-bordered) {
  border-radius: 12px;
  padding: 14px 24px;
  border: 2px solid rgba(226, 232, 240, 0.8);
  background: white;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 1.75rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

:deep(.el-radio.is-bordered):hover {
  border-color: #667eea;
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.25);
}

:deep(.el-radio.is-bordered.is-checked) {
  border-color: #667eea;
  background: linear-gradient(
    135deg,
    rgba(102, 126, 234, 0.1) 0%,
    rgba(118, 75, 162, 0.1) 100%
  );
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.35);
  transform: translateY(-3px) scale(1.08);
}

:deep(.el-divider) {
  margin: 2rem 0;
  border-color: rgba(226, 232, 240, 0.6);
}

:deep(.el-form-item) {
  margin-bottom: 1.75rem;
}

:deep(.el-col) {
  margin-bottom: 0;
}

/* 美化数字输入框旁边的文字 */
:deep(.el-form-item__content > span) {
  color: #64748b;
  font-weight: 500;
  font-size: 0.9rem;
}
</style>
