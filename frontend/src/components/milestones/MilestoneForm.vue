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
/* Dialog & Overlay - iOS Premium */
.milestone-form-dialog :deep(.el-overlay) {
  background-color: rgba(0, 0, 0, 0.2);
}

.milestone-form-dialog :deep(.el-dialog) {
  border-radius: 24px;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.2);
  padding: 0;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.98);
}

.milestone-form-dialog :deep(.el-dialog__header) {
  margin: 0;
  padding: 24px 32px 16px;
  border-bottom: none;
}

.milestone-form-dialog :deep(.el-dialog__title) {
  font-size: 22px;
  font-weight: 700;
  color: #1c1c1e;
  letter-spacing: -0.5px;
}

.milestone-form-dialog :deep(.el-dialog__headerbtn) {
  top: 24px;
  right: 24px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f2f2f7;
  transition: all 0.2s ease;
}

.milestone-form-dialog :deep(.el-dialog__headerbtn:hover) {
  background: #e5e5ea;
  transform: scale(1.05);
}

.milestone-form-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #8e8e93;
  font-weight: 700;
}

.milestone-form-dialog :deep(.el-dialog__body) {
  padding: 8px 32px 32px;
}

/* Form Layout */
.milestone-form {
  display: flex;
  flex-direction: column;
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.split-row {
  flex-direction: row;
  gap: 20px;
}

.flex-grow {
  flex: 1;
}

.w-date {
  width: 200px;
  flex-shrink: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 15px;
  font-weight: 600;
  color: #1c1c1e;
  margin-left: 4px;
}

.required {
  color: #ff3b30;
  margin-left: 2px;
}

/* Record Form Style Inputs - iOS Style */
.record-input :deep(.el-input__wrapper),
.record-select :deep(.el-input__wrapper) {
  background: #f2f2f7;
  border: none;
  border-radius: 12px;
  box-shadow: none !important;
  padding: 0 16px;
  height: 52px !important;
  line-height: 52px;
  box-sizing: border-box;
  transition: all 0.2s ease;
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
  background: #e5e5ea;
}

.record-input :deep(.el-input__wrapper.is-focus),
.record-select :deep(.el-input__wrapper.is-focus) {
  background: #ffffff;
  box-shadow: 0 0 0 2px #007AFF !important;
}

.record-input :deep(.el-input__inner) {
  font-size: 17px;
  color: #1c1c1e;
  height: 100%;
  line-height: normal;
  display: flex;
  align-items: center;
  font-weight: 500;
}

/* Textarea */
.record-textarea :deep(.el-textarea__inner) {
  background: #f2f2f7;
  border: none;
  border-radius: 16px;
  padding: 16px;
  font-size: 17px;
  color: #1c1c1e;
  box-shadow: none;
  transition: all 0.2s ease;
  font-family: inherit;
}

.record-textarea :deep(.el-textarea__inner:focus) {
  background: #ffffff;
  box-shadow: 0 0 0 2px #007AFF;
}

/* Upload Area */
.upload-area {
  background: #f9f9f9;
  border: 2px dashed #e5e5ea;
  border-radius: 16px;
  min-height: 100px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-area:hover {
  background: #f2f2f7;
  border-color: #007AFF;
}

.upload-area.has-files {
  background: #ffffff;
  border-style: solid;
  border-color: #e5e5ea;
  justify-content: flex-start;
  align-items: flex-start;
}

.upload-placeholder {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-circle {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #e5e5ea;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #007AFF;
}

.icon-circle .icon {
  font-size: 24px;
}

.text-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.primary-text {
  font-size: 16px;
  font-weight: 600;
  color: #1c1c1e;
}

.secondary-text {
  font-size: 13px;
  color: #8e8e93;
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
  padding: 10px 16px;
  background: #f2f2f7;
  border-radius: 12px;
  color: #007AFF;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.add-more-btn:hover {
  background: #e5e5ea;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #f9f9f9;
  border: 1px solid #e5e5ea;
  border-radius: 12px;
  transition: all 0.2s;
}

.file-item:hover {
  border-color: #007AFF;
  background: #ffffff;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.file-name {
  font-size: 14px;
  color: #1c1c1e;
  font-weight: 500;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: #8e8e93;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: #e5e5ea;
  color: #ff3b30;
}

/* Footer */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  margin-top: 16px;
  padding-top: 24px;
  border-top: 1px solid #f2f2f7;
}

.btn-cancel {
  min-width: 100px;
  height: 48px;
  border-radius: 999px;
  border: none;
  background: #f2f2f7;
  color: #1c1c1e;
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: #e5e5ea;
}

.btn-submit {
  min-width: 140px;
  height: 48px;
  border-radius: 999px;
  border: none;
  background: #007AFF;
  color: #ffffff;
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-1px);
  background: #0062cc;
  box-shadow: 0 6px 16px rgba(0, 122, 255, 0.4);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
</style>
