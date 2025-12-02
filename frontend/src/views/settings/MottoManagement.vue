<template>
  <PageContainer
    :title="{ icon: '💬', text: '格言管理' }"
    subtitle="写下一句激励你的话语，启发每一天。"
    :custom-class="'settings-subpage'"
  >
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

    <el-dialog
      v-model="editVisible"
      title="编辑格言"
      width="500px"
      @opened="refreshIcons"
    >
      <el-form
        :model="editForm"
        :rules="[
          { required: true, message: '请输入格言内容', trigger: 'blur' },
        ]"
      >
        <el-form-item prop="content">
          <el-input
            v-model="editForm.content"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 6 }"
            placeholder="在此输入新的格言..."
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="updating" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { Icon } from "@iconify/vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useMottoStore } from "@/stores/modules/motto";
import MottoItem from "@/components/motto/MottoItem.vue";
import PageContainer from "@/components/layout/PageContainer.vue";

const mottoStore = useMottoStore();
const form = ref({ content: "" });
const editForm = ref({ id: null, content: "" });
const addFormRef = ref(null);
const adding = ref(false);
const updating = ref(false);
const editVisible = ref(false);

const itemsSorted = computed(() =>
  (mottoStore.items || []).slice().sort((a, b) => (b.id || 0) - (a.id || 0))
);

async function submitAdd() {
  if (!form.value.content.trim()) {
    ElMessage.warning("请输入格言内容");
    return;
  }
  adding.value = true;
  try {
    await mottoStore.add(form.value.content.trim());
    form.value.content = "";
    ElMessage.success("添加成功");
  } catch (e) {
    ElMessage.error(e?.message || "添加失败");
  } finally {
    adding.value = false;
  }
}

function openEdit(motto) {
  editForm.value = { ...motto };
  editVisible.value = true;
}

async function submitEdit() {
  if (!editForm.value.content.trim()) {
    ElMessage.warning("请输入格言内容");
    return;
  }
  updating.value = true;
  try {
    await mottoStore.update(editForm.value.id, editForm.value.content.trim());
    ElMessage.success("更新成功");
    editVisible.value = false;
  } catch (e) {
    ElMessage.error(e?.message || "更新失败");
  } finally {
    updating.value = false;
  }
}

function refreshIcons() {
  // 触发 Iconify 刷新
}

onMounted(() => {
  mottoStore.fetch();
});
</script>

<style scoped>
.add-card .card-header,
.card .card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  width: 24px;
  height: 24px;
  color: #6366f1;
}

.title-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.subtitle {
  margin: 0;
  color: #6b7280;
  font-size: 13px;
}
</style>
