<template>
  <el-dialog
    :title="editMode ? '编辑待办' : '新增待办'"
    v-model="visible"
    width="480px"
    @close="onClose"
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
      <el-form-item label="标题" prop="title">
        <el-input
          v-model="form.title"
          maxlength="100"
          show-word-limit
          placeholder="请输入标题"
        />
      </el-form-item>
      <el-form-item label="描述" prop="description">
        <el-input
          type="textarea"
          v-model="form.description"
          :rows="3"
          placeholder="可填写描述"
        />
      </el-form-item>
      <el-form-item label="优先级" prop="priority">
        <el-select v-model="form.priority" placeholder="选择">
          <el-option label="低" value="low" />
          <el-option label="中" value="medium" />
          <el-option label="高" value="high" />
        </el-select>
      </el-form-item>
      <el-form-item label="截止日期" prop="due_date">
        <el-date-picker
          v-model="form.due_date"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="选择日期"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">{{
        editMode ? "保存" : "创建"
      }}</el-button>
    </template>
  </el-dialog>
</template>
<script setup>
import { ref, reactive, watch, nextTick } from "vue";

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  data: { type: Object, default: () => ({}) },
});
const emit = defineEmits(["update:modelValue", "submit"]);

const visible = ref(false);
const editMode = ref(false);
const submitting = ref(false);
const formRef = ref();
const form = reactive({
  id: null,
  title: "",
  description: "",
  priority: "medium",
  due_date: "",
});

const rules = {
  title: [{ required: true, message: "请输入标题", trigger: "blur" }],
  priority: [{ required: true, message: "请选择优先级", trigger: "change" }],
};

watch(
  () => props.modelValue,
  (val) => {
    visible.value = val;
    if (val) initForm();
  }
);

function initForm() {
  editMode.value = !!props.data?.id;
  form.id = props.data.id || null;
  form.title = props.data.title || "";
  form.description = props.data.description || "";
  form.priority = props.data.priority || "medium";
  form.due_date = props.data.due_date || "";
  nextTick(() => formRef.value?.clearValidate());
}

function onClose() {
  emit("update:modelValue", false);
}

function handleSubmit() {
  formRef.value.validate(async (ok) => {
    if (!ok) return;
    submitting.value = true;
    try {
      const payload = { ...form };
      emit("submit", payload);
    } finally {
      submitting.value = false;
    }
  });
}

// 对外提供 open(data?) 方法
defineExpose({
  open(data) {
    emit("update:modelValue", true);
  },
});
</script>

<style scoped></style>
