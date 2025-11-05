<template>
  <div class="motto-management settings-subview">
    <!-- 添加格言 -->
    <div class="card mb-4 add-card">
      <div class="card-header">
        <div class="header-title">
          <Icon icon="lucide:quote" class="title-icon" />
          <div class="title-text">
            <h5 class="card-title">添加新格言</h5>
            <p class="subtitle">写下一句激励你的话语，启发每一天。</p>
          </div>
        </div>
      </div>
      <div class="card-body">
        <el-form
          :model="form"
          @submit.prevent="submitAdd"
          ref="addFormRef"
          class="add-form"
          autocomplete="off"
        >
          <el-form-item
            prop="content"
            :rules="[
              { required: true, message: '请输入格言内容', trigger: 'blur' },
            ]"
            class="motto-input-item"
          >
            <el-input
              v-model="form.content"
              type="textarea"
              :autosize="{ minRows: 2, maxRows: 6 }"
              placeholder="在此输入新的格言..."
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
          <div class="form-actions">
            <el-button type="primary" :loading="adding" @click="submitAdd">添加</el-button>
          </div>
        </el-form>
      </div>
    </div>

    <!-- 格言列表 -->
    <div class="card">
      <div class="card-header">
        <div class="header-title">
          <Icon icon="lucide:book-quote" class="title-icon" />
          <div class="title-text">
            <h5 class="card-title mb-0">我的格言库</h5>
            <p class="subtitle">共 {{ itemsSorted.length }} 条</p>
          </div>
        </div>
      </div>
      <div class="list-group list-group-flush" id="motto-list-container">
        <MottoItem
          v-for="m in itemsSorted"
          :key="m.id"
          :motto="m"
          @edit="openEdit"
        />
        <div
          v-if="!itemsSorted.length"
          id="no-mottos-placeholder"
          class="list-group-item text-center p-4 text-muted"
        >
          您的格言库是空的，快来添加第一条吧！
        </div>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog
      v-model="editVisible"
      title="编辑格言"
      width="500px"
      @opened="refreshIcons"
    >
      <el-form
        :model="editForm"
        @submit.prevent="submitEdit"
        ref="editFormRef"
        class="edit-form"
      >
        <el-form-item
          prop="content"
          :rules="[
            { required: true, message: '内容不能为空', trigger: 'blur' },
          ]"
        >
          <el-input
            type="textarea"
            v-model="editForm.content"
            rows="3"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <div class="dialog-footer" style="text-align: right">
          <el-button @click="editVisible = false">取消</el-button>
          <el-button type="primary" :loading="editing" @click="submitEdit"
            >保存更改</el-button
          >
        </div>
      </el-form>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, nextTick } from "vue";
import { useMottoStore } from "@/stores";
import MottoItem from "@/components/motto/MottoItem.vue";
import { ElMessage } from "element-plus";
import { Icon } from "@iconify/vue";

const store = useMottoStore();
const form = ref({ content: "" });
const addFormRef = ref();
const adding = ref(false);

const editVisible = ref(false);
const editForm = ref({ id: null, content: "" });
const editFormRef = ref();
const editing = ref(false);

const itemsSorted = computed(() => {
  return [...store.items].sort((a, b) => b.id - a.id); // 新增顶部
});

async function submitAdd() {
  if (adding.value) return;
  adding.value = true;
  try {
    if (!form.value.content || !form.value.content.trim()) {
      ElMessage.warning("格言内容不能为空");
      return;
    }
    await store.add({ content: form.value.content.trim() });
    form.value.content = "";
    // prepend 已通过排序实现
    ElMessage.success("新格言已添加。");
    await nextTick();
    refreshIcons();
  } catch (e) {
    console.error("add motto failed", e);
    ElMessage.error("添加失败");
  } finally {
    adding.value = false;
  }
}

function openEdit(motto) {
  editForm.value.id = motto.id;
  editForm.value.content = motto.content;
  editVisible.value = true;
}

async function submitEdit() {
  if (editing.value) return;
  editing.value = true;
  try {
    if (!editForm.value.content || !editForm.value.content.trim()) {
      ElMessage.warning("内容不能为空");
      return;
    }
    await store.save(editForm.value.id, {
      content: editForm.value.content.trim(),
    });
    ElMessage.success("格言已更新。");
    editVisible.value = false;
    await nextTick();
    refreshIcons();
  } catch (e) {
    console.error("edit motto failed", e);
    ElMessage.error("更新失败");
  } finally {
    editing.value = false;
  }
}

function refreshIcons() {
  try {
    createIcons();
  } catch (e) {
    /* ignore */
  }
}

onMounted(async () => {
  await store.fetch();
  refreshIcons();
});
</script>
<style scoped>
.settings-subview { padding: 0.5rem 0 1.5rem; }

.card {
  border: 1px solid var(--color-border-card);
  border-radius: 16px;
  background: var(--surface-card);
  box-shadow: var(--box-shadow);
  margin-bottom: 1.25rem;
}

.card-header {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--color-border-card);
}

.header-title { display: flex; align-items: center; gap: 12px; }
.title-icon { color: var(--color-primary); width: 22px; height: 22px; }
.title-text { display: flex; flex-direction: column; }
.card-title { margin: 0; font-weight: 700; color: var(--color-text-heading); }
.subtitle { margin: 2px 0 0; font-size: 12px; color: var(--color-text-secondary); }

/* 添加区域 */
.add-form { display: flex; flex-direction: column; gap: 0.5rem; }
.motto-input-item { margin-bottom: 0; }
.form-actions { display: flex; justify-content: flex-end; }

.add-form :deep(.el-textarea__inner) {
  box-shadow: none !important;
  border-radius: 12px;
}

/* 列表区域 */
#motto-list-container { min-height: 60px; }
.list-group-item { border-bottom: 1px dashed var(--stroke-soft); }
.list-group-item:last-child { border-bottom: none; }

.dialog-footer { margin-top: 0.5rem; }
</style>
