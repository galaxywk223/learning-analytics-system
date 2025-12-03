<template>
  <PageContainer
    :title="{ icon: '🏆', text: '成就时刻' }"
    subtitle="记录下每一个值得纪念的闪光瞬间。"
    :custom-class="'milestones-view'"
    :max-width="1400"
  >
    <div class="layout-grid">
      <aside class="sidebar-filter">
        <div class="filter-list">
          <button
            type="button"
            class="filter-item"
            :class="{ active: !state.category_id }"
            @click="selectCategory(null)"
          >
            全部成就
          </button>
          <button
            v-for="c in categories"
            :key="c.id"
            type="button"
            class="filter-item"
            :class="{ active: state.category_id === c.id }"
            @click="selectCategory(c.id)"
          >
            {{ c.name }}
          </button>
        </div>
      </aside>
      <main class="timeline-wrapper">
        <ul v-if="displayedItems.length" class="timeline">
          <MilestoneItem
            v-for="m in displayedItems"
            :key="m.id"
            :item="m"
            :categories="categories"
            @edit="editMilestone"
            @deleted="removeMilestone"
            @attachment-deleted="handleAttachmentDeleted"
          />
        </ul>
        <div v-else class="empty-box">
          <h3>还没有任何成就记录</h3>
          <p class="text-muted">
            点击右上角的按钮，开始记录你的第一个成就时刻吧！
          </p>
        </div>

        <div v-if="pagination.pages > 1" class="pagination-box">
          <ul class="pagination">
            <li :class="['page-item', !pagination.has_prev ? 'disabled' : '']">
              <a
                href="#"
                class="page-link"
                @click.prevent="goPage(pagination.page - 1)"
                >上一页</a
              >
            </li>
            <li
              v-for="n in pageNumbers"
              :key="n"
              :class="['page-item', n === pagination.page ? 'active' : '']"
            >
              <a href="#" class="page-link" @click.prevent="goPage(n)">{{
                n
              }}</a>
            </li>
            <li :class="['page-item', !pagination.has_next ? 'disabled' : '']">
              <a
                href="#"
                class="page-link"
                @click.prevent="goPage(pagination.page + 1)"
                >下一页</a
              >
            </li>
          </ul>
        </div>
      </main>
    </div>

    <MilestoneForm
      v-model="formVisible"
      :edit-data="editing"
      :categories="categories"
      @saved="onSaved"
    />

    <el-dialog
      v-model="categoryManagerVisible"
      width="560px"
      class="category-manager-dialog"
      :show-close="true"
      top="6vh"
      :destroy-on-close="true"
    >
      <div class="manager-card">
        <div class="manager-header">
          <h2>成就分类管理</h2>
          <p>管理您的成就时刻分类标签。</p>
        </div>

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
            :disabled="categoryCreating || !newCategory.name.trim()"
            @click="createCategory"
          >
            {{ categoryCreating ? "…" : "＋" }}
          </button>
        </div>

        <div v-if="categories.length" class="category-grid">
          <div
            v-for="cat in categories"
            :key="cat.id"
            class="category-card"
            :class="{ editing: editingId === cat.id }"
          >
            <div class="card-actions" v-if="editingId !== cat.id">
              <button type="button" class="ghost-btn" title="编辑" @click="startEdit(cat)">✏️</button>
              <el-popconfirm title="确定删除此分类?" @confirm="deleteCategory(cat)">
                <template #reference>
                  <button type="button" class="ghost-btn danger" title="删除">🗑️</button>
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
                <el-button size="small" type="primary" @click="confirmEdit(cat)">保存</el-button>
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
    </el-dialog>
  </PageContainer>
  <div class="milestone-fab">
    <button
      class="fab fab-secondary"
      @click="openCategoryManager"
      title="管理分类"
    >
      <Icon icon="lucide:folder-cog" />
    </button>
    <button class="fab fab-primary" @click="openCreate" title="记录新成就">
      <Icon icon="lucide:plus" />
    </button>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, computed } from "vue";
import { Icon } from "@iconify/vue";
import PageContainer from "@/components/layout/PageContainer.vue";
import MilestoneForm from "@/components/milestones/MilestoneForm.vue";
import MilestoneItem from "@/components/milestones/MilestoneItem.vue";
import { milestoneAPI } from "@/api/modules/milestone";

// 每页显示条目数调小，便于分页浏览
const state = reactive({ page: 1, per_page: 6, category_id: null });
const allItems = ref([]);
const displayedItems = ref([]);
const categories = ref([]);
const pagination = reactive({
  page: 1,
  pages: 1,
  has_next: false,
  has_prev: false,
});
const formVisible = ref(false);
const editing = ref(null);
const loading = ref(false);
const categoryManagerVisible = ref(false);
const categoryCreating = ref(false);
const editingId = ref(null);
const editName = ref("");
const newCategory = ref({ name: "" });

async function fetchCategories() {
  try {
    const res = await milestoneAPI.categories();
    categories.value = res.categories || [];
  } catch (e) {
    console.error(e);
  }
}
const RENDER_CHUNK = 12;
let renderHandle = null;

const requestFrame = (cb) =>
  typeof window !== "undefined"
    ? window.requestAnimationFrame(cb)
    : setTimeout(cb, 16);
const cancelFrame = (handle) => {
  if (handle === null) return;
  if (typeof window !== "undefined") {
    window.cancelAnimationFrame(handle);
  } else {
    clearTimeout(handle);
  }
};

function cancelRender() {
  if (renderHandle !== null) {
    cancelFrame(renderHandle);
    renderHandle = null;
  }
}

function scheduleRender() {
  cancelRender();
  displayedItems.value = [];
  let index = 0;

  const renderChunk = () => {
    const slice = allItems.value.slice(index, index + RENDER_CHUNK);
    if (slice.length) {
      displayedItems.value = [...displayedItems.value, ...slice];
      index += RENDER_CHUNK;
    }
    if (index < allItems.value.length) {
      renderHandle = requestFrame(renderChunk);
    } else {
      renderHandle = null;
    }
  };

  renderChunk();
}

async function fetchMilestones() {
  if (loading.value) return;
  loading.value = true;
  try {
    const params = { page: state.page, per_page: state.per_page };
    if (state.category_id) params.category_id = state.category_id;
    const res = await milestoneAPI.list(params);
    allItems.value = (res.milestones || []).map((m) => ({ ...m }));
    scheduleRender();
    if (res.pagination) {
      Object.assign(pagination, res.pagination);
    } else {
      pagination.page = 1;
      pagination.pages = 1;
      pagination.has_next = false;
      pagination.has_prev = false;
    }
  } catch (e) {
    console.error("fetch milestones failed", e);
  } finally {
    loading.value = false;
  }
}

function selectCategory(id) {
  state.category_id = id;
  state.page = 1;
  fetchMilestones();
}
function goPage(n) {
  if (n < 1 || n > pagination.pages) return;
  state.page = n;
  fetchMilestones();
}
const pageNumbers = computed(() => {
  const arr = [];
  for (let i = 1; i <= pagination.pages; i++) arr.push(i);
  return arr;
});
function openCreate() {
  editing.value = null;
  formVisible.value = true;
}
function openCategoryManager() {
  categoryManagerVisible.value = true;
}

function getCountText(cat) {
  const count =
    cat.milestone_count ??
    cat.count ??
    cat.total ??
    (cat.stats ? cat.stats.count : 0) ??
    0;
  return `${count} 个成就`;
}

async function createCategory() {
  if (!newCategory.value.name.trim() || categoryCreating.value) return;
  categoryCreating.value = true;
  try {
    const res = await milestoneAPI.createCategory({
      name: newCategory.value.name.trim(),
    });
    categories.value.push(res.category);
    newCategory.value.name = "";
  } catch (e) {
    console.error("create category failed", e);
  } finally {
    categoryCreating.value = false;
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
    if (state.category_id === cat.id) {
      state.category_id = null;
      fetchMilestones();
    }
  } catch (e) {
    console.error("delete category failed", e);
  }
}
function editMilestone(m) {
  editing.value = m;
  formVisible.value = true;
}
function removeMilestone(id) {
  allItems.value = allItems.value.filter((i) => i.id !== id);
  displayedItems.value = displayedItems.value.filter((i) => i.id !== id);
}
function handleAttachmentDeleted({ milestoneId, attachmentId }) {
  const m = allItems.value.find((i) => i.id === milestoneId);
  if (!m) return;
  m.attachments = (m.attachments || []).filter((a) => a.id !== attachmentId);
  const displayTarget = displayedItems.value.find((i) => i.id === milestoneId);
  if (displayTarget && displayTarget !== m) {
    displayTarget.attachments = (displayTarget.attachments || []).filter(
      (a) => a.id !== attachmentId
    );
  }
}
async function onSaved(payload) {
  await fetchMilestones();
}

onMounted(async () => {
  await fetchCategories();
  await fetchMilestones();
});

onBeforeUnmount(() => {
  cancelRender();
});
</script>

<style scoped src="@/styles/views/milestones/milestones-view.scss"></style>
