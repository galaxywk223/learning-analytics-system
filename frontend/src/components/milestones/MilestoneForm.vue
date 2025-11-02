<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="720px"
    destroy-on-close
    class="milestone-form-dialog"
  >
    <form @submit.prevent="handleSubmit" autocomplete="off">
      <div class="form-grid">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="事件日期" required>
          <el-date-picker
            v-model="form.event_date"
            type="date"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="分类">
          <el-select
            v-model="form.category_id"
            placeholder="-- 未分类 --"
            clearable
          >
            <el-option :value="null" label="-- 未分类 --" />
            <el-option
              v-for="c in categories"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
      </div>
      <el-form-item label="详细描述 (支持HTML)">
        <el-input
          type="textarea"
          :rows="6"
          v-model="form.description"
          placeholder="可以粘贴部分简单 HTML 标记，如 <p><b><i> 等"
        />
      </el-form-item>
      <el-form-item label="上传附件">
        <input ref="fileInput" type="file" multiple @change="handleFiles" />
        <small class="text-muted">可以按住 Ctrl 或 Shift 选择多个文件。</small>
        <ul v-if="selectedFiles.length" class="selected-files">
          <li v-for="(f, i) in selectedFiles" :key="i">{{ f.name }}</li>
        </ul>
      </el-form-item>
      <div class="dialog-footer" slot="footer">
        <el-button @click="close">取消</el-button>
        <el-button type="primary" :loading="submitting" native-type="submit"
          >保存</el-button
        >
      </div>
    </form>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch, toRaw } from "vue";
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
  selectedFiles.value = Array.from(e.target.files || []);
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
      console.log("[MilestoneForm] 开始更新里程碑:", props.editData.id);
      await milestoneAPI.update(props.editData.id, payload);

      // 上传新增附件
      console.log(
        "[MilestoneForm] 准备上传附件，数量:",
        selectedFiles.value.length
      );
      for (const f of selectedFiles.value) {
        console.log("[MilestoneForm] 上传附件:", f.name);
        const uploadRes = await milestoneAPI.uploadAttachment(
          props.editData.id,
          f
        );
        console.log("[MilestoneForm] 上传结果:", uploadRes);
      }

      // 重新获取完整数据（包含附件）
      console.log("[MilestoneForm] 重新获取完整数据");
      const updatedRes = await milestoneAPI.get(props.editData.id);
      console.log("[MilestoneForm] 获取到的完整数据:", updatedRes);
      emits("saved", { updated: updatedRes.milestone });
    } else {
      const payload = {
        title: form.title,
        event_date: form.event_date,
        description: form.description,
        category_id: form.category_id,
      };
      console.log("[MilestoneForm] 创建新里程碑");
      const res = await milestoneAPI.create(payload);
      console.log("[MilestoneForm] 创建结果:", res);

      // 上传附件
      if (selectedFiles.value.length) {
        console.log(
          "[MilestoneForm] 准备上传附件，数量:",
          selectedFiles.value.length
        );
        for (const f of selectedFiles.value) {
          console.log("[MilestoneForm] 上传附件:", f.name);
          const uploadRes = await milestoneAPI.uploadAttachment(
            res.milestone.id,
            f
          );
          console.log("[MilestoneForm] 上传结果:", uploadRes);
        }
      }

      // 重新获取完整数据（包含附件）
      console.log("[MilestoneForm] 重新获取完整数据");
      const createdRes = await milestoneAPI.get(res.milestone.id);
      console.log("[MilestoneForm] 获取到的完整数据:", createdRes);
      emits("saved", { created: createdRes.milestone });
    }
    close();
  } catch (e) {
    console.error("[MilestoneForm] 保存里程碑失败:", e);
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.milestone-form-dialog :deep(.el-dialog__body) {
  padding-top: 4px;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-gap: 12px;
  margin-bottom: 8px;
}
.selected-files {
  margin: 6px 0 0;
  padding: 0;
  list-style: none;
  font-size: 12px;
  color: var(--color-text-medium);
}
.selected-files li {
  margin: 2px 0;
}
</style>
