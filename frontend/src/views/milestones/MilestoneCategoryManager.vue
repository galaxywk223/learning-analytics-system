<template>
  <PageContainer
    :title="{ icon: '🏆', text: '成就分类管理' }"
    subtitle="管理您的成就时刻分类标签。"
    :custom-class="'milestone-category-manager'"
    :max-width="900"
  >
    <div class="manager-card">
      <header class="manager-header">
        <div>
          <h2>成就分类管理</h2>
          <p>管理您的成就时刻分类标签。</p>
        </div>
      </header>

      <div class="add-row" @keyup.enter="createCategory">
        <input
          v-model="newCategory.name"
          type="text"
          maxlength="100"
          placeholder="输入新分类名称..."
        />
        <button
          class="add-btn"
          type="button"
          :disabled="creating || !newCategory.name.trim()"
          @click="createCategory"
        >
          {{ creating ? "…" : "＋" }}
        </button>
      </div>

      <div v-if="categories.length" class="category-grid">
        <div
          v-for="cat in categories"
          :key="cat.id"
          class="category-card"
          :class="{ editing: editingId === cat.id }"
        >
          <div v-if="editingId !== cat.id" class="card-actions">
            <button
              type="button"
              class="ghost-btn"
              title="编辑"
              @click="startEdit(cat)"
            >
              ✏️
            </button>
            <el-popconfirm
              title="确定删除此分类?"
              @confirm="deleteCategory(cat)"
            >
              <template #reference>
                <button type="button" class="ghost-btn danger" title="删除">
                  🗑️
                </button>
              </template>
            </el-popconfirm>
          </div>

          <div v-if="editingId !== cat.id" class="card-body">
            <div class="category-icon">🏷️</div>
            <div class="category-meta">
              <div class="name">{{ cat.name }}</div>
              <div class="count">{{ getCountText(cat) }}</div>
            </div>
          </div>

          <div v-else class="edit-inline">
            <el-input v-model="editName" maxlength="100" />
            <div class="edit-actions">
              <el-button size="small" type="primary" @click="confirmEdit(cat)"
                >保存</el-button
              >
              <el-button size="small" @click="cancelEdit">取消</el-button>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <div class="empty-illustration">📦</div>
        <p class="empty-title">还没有分类，快去添加一个吧</p>
        <p class="empty-sub">使用上方输入框即可创建你的第一个分类</p>
      </div>
    </div>
  </PageContainer>
  <div class="milestone-fab">
    <button class="fab fab-primary" title="返回时间线" @click="goBack">
      <Icon icon="lucide:arrow-left" />
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { Icon } from "@iconify/vue";
import PageContainer from "@/components/layout/PageContainer.vue";
import { milestoneAPI } from "@/api/modules/milestone";

const router = useRouter();
const categories = ref([]);
const loading = ref(false);
const creating = ref(false);
const newCategory = ref({ name: "" });
const editingId = ref(null);
const editName = ref("");

function getCountText(cat) {
  const count =
    cat.milestone_count ??
    cat.count ??
    cat.total ??
    (cat.stats ? cat.stats.count : 0) ??
    0;
  return `${count} 个成就`;
}

async function fetchCategories() {
  loading.value = true;
  try {
    const res = await milestoneAPI.categories();
    categories.value = res.categories || [];
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

function goBack() {
  router.push({ path: "/milestones" });
}

async function createCategory() {
  if (!newCategory.value.name.trim()) return;
  creating.value = true;
  try {
    const res = await milestoneAPI.createCategory({
      name: newCategory.value.name.trim(),
    });
    categories.value.push(res.category);
    newCategory.value.name = "";
  } catch (e) {
    console.error("create category failed", e);
  } finally {
    creating.value = false;
  }
}

function startEdit(cat) {
  editingId.value = cat.id;
  editName.value = cat.name;
}
function cancelEdit() {
  editingId.value = null;
  editName.value = "";
}

async function confirmEdit(cat) {
  if (!editName.value.trim()) return;
  try {
    const res = await milestoneAPI.updateCategory(cat.id, {
      name: editName.value.trim(),
    });
    // 更新本地
    const idx = categories.value.findIndex((c) => c.id === cat.id);
    if (idx !== -1) categories.value[idx] = res.category;
    cancelEdit();
  } catch (e) {
    console.error("update category failed", e);
  }
}

async function deleteCategory(cat) {
  try {
    await milestoneAPI.deleteCategory(cat.id);
    categories.value = categories.value.filter((c) => c.id !== cat.id);
  } catch (e) {
    console.error("delete category failed", e);
  }
}

onMounted(fetchCategories);
</script>

<style
  scoped
  src="@/styles/views/milestones/milestone-category-manager.scss"
></style>
