<template>
  <PageContainer
    title="🏆 成就时刻"
    subtitle="记录下每一个值得纪念的闪光瞬间。"
    :custom-class="'milestones-view'"
    :max-width="1400"
  >
    <template #actions>
      <div class="header-actions">
        <el-button
          size="small"
          @click="openCategoryManager"
          class="btn-outline-light"
        >
          <Icon icon="lucide:folder-cog" class="me-1" /> 管理分类
        </el-button>
        <el-button type="primary" @click="openCreate" class="btn-primary">
          <Icon icon="lucide:plus-circle" class="me-2" />记录新成就
        </el-button>
      </div>
    </template>

    <div class="layout-grid">
      <aside class="sidebar-filter">
        <div class="card">
          <div class="card-header">
            <h5 class="card-title mb-0">
              <Icon icon="lucide:filter" class="me-2" />筛选
            </h5>
          </div>
          <div class="list-group">
            <a
              href="#"
              @click.prevent="selectCategory(null)"
              :class="['list-group-item', !state.category_id ? 'active' : '']"
              >全部成就</a
            >
            <a
              v-for="c in categories"
              :key="c.id"
              href="#"
              @click.prevent="selectCategory(c.id)"
              :class="[
                'list-group-item',
                state.category_id === c.id ? 'active' : '',
              ]"
              >{{ c.name }}</a
            >
          </div>
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
            点击右上角的按钮，开始记录你的第一个高光时刻吧！
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
  </PageContainer>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, computed } from "vue";
import { useRouter } from "vue-router";
import { Icon } from "@iconify/vue";
import PageContainer from "@/components/layout/PageContainer.vue";
import MilestoneForm from "@/components/milestones/MilestoneForm.vue";
import MilestoneItem from "@/components/milestones/MilestoneItem.vue";
import { milestoneAPI } from "@/api/modules/milestone";

const router = useRouter();
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
  typeof window !== "undefined" ? window.requestAnimationFrame(cb) : setTimeout(cb, 16);
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
function openCategoryManager() {
  router.push({ path: "/milestones/categories" });
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
