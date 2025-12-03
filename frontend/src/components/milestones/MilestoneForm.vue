<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="680px"
    destroy-on-close
    class="milestone-form-dialog"
    :show-close="true"
    top="8vh"
  >
    <form @submit.prevent="handleSubmit" autocomplete="off" class="milestone-form">
      <div class="form-body">
        <!-- Top Row: Title & Date -->
        <div class="form-row split-row">
          <div class="form-group flex-grow">
            <label class="form-label">标题 <span class="required">*</span></label>
            <el-input 
              v-model="form.title" 
              maxlength="200" 
              show-word-limit 
              placeholder="给这个成就起个名字"
              class="record-input tall-input"
            />
          </div>
          <div class="form-group w-date">
            <label class="form-label">日期 <span class="required">*</span></label>
            <el-date-picker
              v-model="form.event_date"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="选择日期"
              class="record-input tall-input"
              :clearable="false"
              style="width: 100%"
            />
          </div>
        </div>
        
        <!-- Category -->
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">分类</label>
            <el-select
              v-model="form.category_id"
              placeholder="选择分类"
              clearable
              class="record-select"
              popper-class="record-dropdown"
              style="width: 100%"
            >
              <el-option
                v-for="c in categories"
                :key="c.id"
                :label="c.name"
                :value="c.id"
              />
            </el-select>
          </div>
        </div>

        <!-- Description -->
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">详细描述</label>
            <el-input
              type="textarea"
              :rows="6"
              v-model="form.description"
              placeholder="记录这次成就的细节与感受..."
              resize="none"
              class="record-textarea"
            />
          </div>
        </div>

        <!-- Attachments -->
        <div class="form-row">
          <label class="form-label">附件</label>
          <div 
            class="upload-area" 
            @click="fileInput?.click()"
            :class="{ 'has-files': selectedFiles.length > 0 }"
          >
            <input
              ref="fileInput"
              type="file"
              multiple
              @change="handleFiles"
              class="hidden-input"
            />
            
            <div class="upload-placeholder" v-if="selectedFiles.length === 0">
              <div class="icon-circle">
                <span class="icon">📎</span>
              </div>
              <div class="text-content">
                <span class="primary-text">点击或拖拽上传文件</span>
                <span class="secondary-text">支持图片、文档等，最大 20MB</span>
              </div>
            </div>

            <div class="file-list" v-else>
              <div class="add-more-btn">
                <span class="icon">＋</span>
                <span>添加更多</span>
              </div>
              <div v-for="(f, i) in selectedFiles" :key="i" class="file-item" @click.stop>
                <span class="file-icon">📄</span>
                <span class="file-name">{{ f.name }}</span>
                <button type="button" class="remove-btn" @click="removeFile(i)">
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 3L3 9M3 3L9 9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="dialog-footer">
        <button type="button" class="btn-cancel" @click="close">取消</button>
        <button type="submit" class="btn-submit" :disabled="submitting">
          {{ submitting ? "保存中..." : "保存成就" }}
        </button>
      </div>
    </form>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from "vue";
import { milestoneAPI } from "@/api/modules/milestone";

const props = defineProps({
  modelValue: Boolean,
  editData: { type: Object, default: null },
  categories: { type: Array, default: () => [] },
});
const emits = defineEmits(["update:modelValue", "saved"]);

const visible = ref(false);
watch(
  () => props.modelValue,
  (v) => (visible.value = v)
);
const dialogTitle = computed(() =>
  props.editData ? "编辑成就" : "记录新成就"
);

const form = reactive({
  title: "",
  event_date: "",
  description: "",
  category_id: null,
});
const fileInput = ref(null);
const selectedFiles = ref([]);
const submitting = ref(false);

watch(
  () => props.editData,
  (data) => {
    if (data) {
      form.title = data.title || "";
      form.event_date = data.event_date || "";
      form.description = data.description || "";
      form.category_id = data.category_id ?? null;
    } else {
      reset();
    }
  }
);

function reset() {
  form.title = "";
  form.event_date = new Date().toISOString().slice(0, 10);
  form.description = "";
  form.category_id = null;
  selectedFiles.value = [];
  if (fileInput.value) fileInput.value.value = "";
}

function close() {
  emits("update:modelValue", false);
}

function handleFiles(e) {
  const newFiles = Array.from(e.target.files || []);
  selectedFiles.value = [...selectedFiles.value, ...newFiles];
  if (fileInput.value) fileInput.value.value = ""; 
}

function removeFile(idx) {
  selectedFiles.value.splice(idx, 1);
}

async function handleSubmit() {
  if (!form.title || !form.event_date) return;
  submitting.value = true;
  try {
    if (props.editData) {
      const payload = {
        title: form.title,
        event_date: form.event_date,
        description: form.description,
        category_id: form.category_id,
      };
      await milestoneAPI.update(props.editData.id, payload);

      for (const f of selectedFiles.value) {
        await milestoneAPI.uploadAttachment(props.editData.id, f);
      }

      const updatedRes = await milestoneAPI.get(props.editData.id);
      emits("saved", { updated: updatedRes.milestone });
    } else {
      const payload = {
        title: form.title,
        event_date: form.event_date,
        description: form.description,
        category_id: form.category_id,
      };
      const res = await milestoneAPI.create(payload);

      if (selectedFiles.value.length) {
        for (const f of selectedFiles.value) {
          await milestoneAPI.uploadAttachment(res.milestone.id, f);
        }
      }

      const createdRes = await milestoneAPI.get(res.milestone.id);
      emits("saved", { created: createdRes.milestone });
    }
    close();
  } catch (e) {
    console.error("[MilestoneForm] Failed to save:", e);
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
/* Dialog & Overlay */
.milestone-form-dialog :deep(.el-overlay) {
  background-color: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(4px);
}

.milestone-form-dialog :deep(.el-dialog) {
  border-radius: 20px;
  box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.15);
  padding: 0;
  overflow: hidden;
  background: #ffffff;
}

.milestone-form-dialog :deep(.el-dialog__header) {
  margin: 0;
  padding: 24px 32px 12px;
  border-bottom: none;
}

.milestone-form-dialog :deep(.el-dialog__title) {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a1a;
}

.milestone-form-dialog :deep(.el-dialog__headerbtn) {
  top: 24px;
  right: 24px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  transition: background 0.2s;
}

.milestone-form-dialog :deep(.el-dialog__headerbtn:hover) {
  background: #f5f5f5;
}

.milestone-form-dialog :deep(.el-dialog__body) {
  padding: 12px 32px 32px;
}

/* Form Layout */
.milestone-form {
  display: flex;
  flex-direction: column;
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.split-row {
  flex-direction: row;
  gap: 20px;
}

.flex-grow {
  flex: 1;
}

.w-date {
  width: 180px;
  flex-shrink: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-left: 2px;
}

.required {
  color: #ef4444;
  margin-left: 2px;
}

/* Record Form Style Inputs */
.record-input :deep(.el-input__wrapper),
.record-select :deep(.el-input__wrapper) {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  box-shadow: none !important;
  padding: 0 14px;
  height: 52px !important;
  line-height: 52px;
  box-sizing: border-box;
  transition: all 0.15s ease;
}

.tall-input :deep(.el-input__wrapper),
.tall-input :deep(.el-date-editor .el-input__wrapper) {
  height: 52px !important;
  line-height: 52px;
}

.tall-input :deep(.el-input__inner),
.tall-input :deep(.el-date-editor .el-input__inner) {
  height: 52px !important;
  line-height: 52px;
  display: flex;
  align-items: center;
}

.tall-input :deep(.el-input__prefix) {
  display: flex;
  align-items: center;
}

.record-input :deep(.el-input__wrapper:hover),
.record-select :deep(.el-input__wrapper:hover) {
  background: #f1f5f9;
}

.record-input :deep(.el-input__wrapper.is-focus),
.record-select :deep(.el-input__wrapper.is-focus) {
  background: #ffffff;
  border-color: #c4c8d2;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.15) !important;
}

.record-input :deep(.el-input__inner) {
  font-size: 15px;
  color: #111827;
  height: 100%;
  line-height: normal;
  display: flex;
  align-items: center;
}

/* Textarea */
.record-textarea :deep(.el-textarea__inner) {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 14px;
  font-size: 15px;
  color: #111827;
  box-shadow: none;
  transition: all 0.15s ease;
}

.record-textarea :deep(.el-textarea__inner:focus) {
  background: #ffffff;
  border-color: #c4c8d2;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.15);
}

/* Upload Area */
.upload-area {
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 14px;
  min-height: 80px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-area:hover {
  background: #ffffff;
  border-color: #94a3b8;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.upload-area.has-files {
  background: #ffffff;
  border-style: solid;
  border-color: #e2e8f0;
  justify-content: flex-start;
  align-items: flex-start;
}

.upload-placeholder {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e0e7ff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-circle .icon {
  font-size: 18px;
}

.text-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.primary-text {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}

.secondary-text {
  font-size: 12px;
  color: #94a3b8;
}

.hidden-input {
  display: none;
}

/* File List */
.file-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  width: 100%;
}

.add-more-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #f1f5f9;
  border-radius: 10px;
  color: #64748b;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s;
}

.add-more-btn:hover {
  background: #e2e8f0;
  color: #475569;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  transition: all 0.2s;
}

.file-item:hover {
  border-color: #cbd5e1;
  background: #ffffff;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

.file-name {
  font-size: 13px;
  color: #334155;
  font-weight: 500;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  background: transparent;
  color: #94a3b8;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: #fee2e2;
  color: #ef4444;
}

/* Footer */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 14px;
  margin-top: 12px;
  padding-top: 20px;
  border-top: 1px solid #f1f5f9;
}

.btn-cancel {
  min-width: 100px;
  height: 48px;
  border-radius: 14px;
  border: none;
  background: #f8fafc;
  color: #4b5563;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: #f1f5f9;
  color: #374151;
}

.btn-submit {
  min-width: 120px;
  height: 48px;
  border-radius: 14px;
  border: none;
  background: #6366f1;
  color: #ffffff;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 10px 20px rgba(99, 102, 241, 0.2);
}

.btn-submit:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}
</style>
