<template>
  <PageContainer
    title="🏷️ 成就分类管理"
    subtitle="管理您的成就时刻分类标签。"
    :custom-class="'milestone-category-manager'"
    :max-width="1400"
  >
    <template #actions>
      <div class="header-actions">
        <el-button @click="goBack" class="btn-outline-light">
          <Icon icon="lucide:arrow-left" class="me-2" />返回时间线
        </el-button>
      </div>
    </template>

    <div class="layout-grid">
      <div class="add-form-card card">
        <div class="card-header">
          <h5 class="card-title mb-0">添加新分类</h5>
        </div>
        <div class="card-body">
          <el-form :model="newCategory" @submit.prevent="createCategory">
            <el-form-item label="分类名称" required>
              <el-input v-model="newCategory.name" maxlength="100" />
            </el-form-item>
            <el-button
              type="primary"
              :loading="creating"
              @click="createCategory"
              >确认添加</el-button
            >
          </el-form>
        </div>
      </div>

      <div class="list-card card">
        <div class="card-header">
          <h5 class="card-title mb-0">现有分类</h5>
        </div>
        <div class="list-group list-group-flush">
          <template v-if="categories.length">
            <div
              v-for="cat in categories"
              :key="cat.id"
              class="list-group-item category-item-container"
            >
              <div v-if="editingId !== cat.id" class="category-item view-mode">
                <span class="category-name">{{ cat.name }}</span>
                <div class="item-actions">
                  <el-button
                    size="small"
                    @click="startEdit(cat)"
                    class="btn-outline-secondary"
                    title="编辑"
                  >
                    <Icon
                      icon="lucide:pencil"
                      style="width: 16px; height: 16px"
                    />
                  </el-button>
                  <el-popconfirm
                    title="确定删除此分类?"
                    @confirm="deleteCategory(cat)"
                  >
                    <template #reference>
                      <el-button
                        size="small"
                        type="danger"
                        class="btn-outline-danger"
                        title="删除"
                      >
                        <Icon
                          icon="lucide:trash-2"
                          style="width: 16px; height: 16px"
                        />
                      </el-button>
                    </template>
                  </el-popconfirm>
                </div>
              </div>
              <div v-else class="edit-form">
                <el-input
                  v-model="editName"
                  maxlength="100"
                  class="edit-input"
                />
                <div class="edit-actions">
                  <el-button
                    size="small"
                    type="success"
                    @click="confirmEdit(cat)"
                  >
                    <Icon
                      icon="lucide:check"
                      style="width: 16px; height: 16px"
                    />
                  </el-button>
                  <el-button size="small" @click="cancelEdit">
                    <Icon icon="lucide:x" style="width: 16px; height: 16px" />
                  </el-button>
                </div>
              </div>
            </div>
          </template>
          <div v-else class="list-group-item text-center p-4 text-muted">
            还没有任何分类。
          </div>
        </div>
      </div>
    </div>
  </PageContainer>
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
