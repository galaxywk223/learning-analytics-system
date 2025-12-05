<template>
  <PageContainer
    :title="{ icon: '📂', text: '分类管理' }"
    subtitle="管理学习记录的大类与子类。"
    :custom-class="'settings-subpage'"
  >
    <template #actions>
      <button class="pill-btn primary" @click="showAddCategoryModal">
        <Icon icon="lucide:plus-circle" class="me-2" />添加新分类
      </button>
    </template>

    <div class="card">
      <div class="card-header">
        <h5 class="card-title mb-0">分类与标签</h5>
      </div>
      <div class="accordion accordion-flush" id="categoryAccordion">
        <div
          v-for="category in categories"
          :key="category.id"
          class="accordion-item"
          :id="`category-item-${category.id}`"
        >
          <h2 class="accordion-header">
            <div class="category-header-item">
              <button
                class="accordion-button collapsed d-flex align-items-center"
                type="button"
                data-bs-toggle="collapse"
                :data-bs-target="`#collapse-${category.id}`"
              >
                <Icon icon="lucide:folder" class="me-3" />
                <div class="category-title-wrapper">
                  <h6 class="mb-0 category-name">{{ category.name }}</h6>
                  <span class="badge bg-secondary fw-normal category-badge">
                    包含 {{ category.subcategories?.length || 0 }} 个标签
                  </span>
                </div>
              </button>
              <div class="item-actions">
                <button
                  class="btn btn-sm btn-outline-secondary btn-icon"
                  title="编辑"
                  @click="showEditCategoryModal(category)"
                >
                  <Icon icon="lucide:pencil" />
                </button>
                <button
                  class="btn btn-sm btn-outline-danger btn-icon"
                  title="删除"
                  @click="deleteCategory(category)"
                >
                  <Icon icon="lucide:trash-2" />
                </button>
              </div>
            </div>
          </h2>
          <div
            :id="`collapse-${category.id}`"
            class="accordion-collapse collapse"
            data-bs-parent="#categoryAccordion"
          >
            <div class="accordion-body subcategory-list">
              <div class="list-group list-group-flush">
                <div
                  v-for="sub in category.subcategories"
                  :key="sub.id"
                  class="list-group-item subcategory-item bg-transparent"
                >
                  <span class="d-flex align-items-center">
                    <Icon icon="lucide:tag" class="me-2" style="width: 16px" />
                    {{ sub.name }}
                  </span>
                  <div class="item-actions">
                    <button
                      class="btn btn-sm btn-outline-secondary btn-icon"
                      title="编辑"
                      @click="showEditSubcategoryModal(sub, category)"
                    >
                      <Icon icon="lucide:pencil" />
                    </button>
                    <button
                      class="btn btn-sm btn-outline-danger btn-icon"
                      title="删除"
                      @click="deleteSubcategory(sub, category)"
                    >
                      <Icon icon="lucide:trash-2" />
                    </button>
                  </div>
                </div>
              </div>
              <div class="d-flex justify-content-end mt-2">
                <button
                  class="btn btn-sm btn-outline-primary"
                  @click="showAddSubcategoryModal(category)"
                >
                  <Icon icon="lucide:plus" class="me-2" />添加子类
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加/编辑模态框 -->
    <el-dialog
      v-model="showCategoryModal"
      :title="modalTitle"
      width="480px"
      destroy-on-close
    >
      <div class="mb-3">
        <label class="form-label">分类名称</label>
        <el-input v-model="categoryForm.name" placeholder="输入分类名称" />
      </div>
      <template #footer>
        <div class="dialog-footer">
          <button class="pill-btn secondary" @click="showCategoryModal = false">取消</button>
          <button class="pill-btn primary" @click="saveCategory">保存</button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showSubcategoryModal"
      :title="modalSubTitle"
      width="480px"
      destroy-on-close
    >
      <div class="mb-3">
        <label class="form-label">子类名称</label>
        <el-input v-model="subcategoryForm.name" placeholder="输入子类名称" />
      </div>
      <template #footer>
        <div class="dialog-footer">
          <button class="pill-btn secondary" @click="showSubcategoryModal = false">取消</button>
          <button class="pill-btn primary" @click="saveSubcategory">保存</button>
        </div>
      </template>
    </el-dialog>
  </PageContainer>
</template>
<script setup>
import { ref, onMounted, computed } from "vue";
import { Icon } from "@iconify/vue";
import { ElMessageBox, ElMessage } from "element-plus";
import { useCategoryStore } from "@/stores/category";
import PageContainer from "@/components/layout/PageContainer.vue";

const categoryStore = useCategoryStore();

const categories = computed(() => categoryStore.categories || []);
const showCategoryModal = ref(false);
const showSubcategoryModal = ref(false);
const categoryForm = ref({ id: null, name: "" });
const subcategoryForm = ref({ id: null, name: "", categoryId: null });

const modalTitle = computed(() =>
  categoryForm.value.id ? "编辑分类" : "添加新分类"
);
const modalSubTitle = computed(() =>
  subcategoryForm.value.id ? "编辑子类" : "添加子类"
);

async function fetchCategories() {
  try {
    await categoryStore.fetchCategories();
  } catch (error) {
    ElMessage.error(error?.message || "加载分类失败");
  }
}

function showAddCategoryModal() {
  categoryForm.value = { id: null, name: "" };
  showCategoryModal.value = true;
}

function showEditCategoryModal(category) {
  categoryForm.value = { id: category.id, name: category.name };
  showCategoryModal.value = true;
}

async function saveCategory() {
  if (!categoryForm.value.name.trim()) {
    ElMessage.warning("请输入分类名称");
    return;
  }
  try {
    if (categoryForm.value.id) {
      await categoryStore.updateCategory(categoryForm.value);
      ElMessage.success("分类已更新");
    } else {
      await categoryStore.addCategory(categoryForm.value);
      ElMessage.success("分类已添加");
    }
    showCategoryModal.value = false;
  } catch (error) {
    ElMessage.error(error?.message || "保存失败");
  }
}

async function deleteCategory(category) {
  try {
    await ElMessageBox.confirm(
      "删除该分类将连同子类一起删除，确认继续？",
      "删除确认",
      { type: "warning" }
    );
    await categoryStore.deleteCategory(category);
    ElMessage.success("删除成功");
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error(error?.message || "删除失败");
    }
  }
}

function showAddSubcategoryModal(category) {
  subcategoryForm.value = { id: null, name: "", categoryId: category.id };
  showSubcategoryModal.value = true;
}

function showEditSubcategoryModal(sub, category) {
  subcategoryForm.value = { id: sub.id, name: sub.name, categoryId: category.id };
  showSubcategoryModal.value = true;
}

async function saveSubcategory() {
  if (!subcategoryForm.value.name.trim()) {
    ElMessage.warning("请输入子类名称");
    return;
  }
  try {
    if (subcategoryForm.value.id) {
      await categoryStore.updateSubcategory(subcategoryForm.value);
      ElMessage.success("子类已更新");
    } else {
      await categoryStore.addSubcategory(subcategoryForm.value);
      ElMessage.success("子类已添加");
    }
    showSubcategoryModal.value = false;
  } catch (error) {
    ElMessage.error(error?.message || "保存失败");
  }
}

async function deleteSubcategory(sub, category) {
  try {
    await ElMessageBox.confirm("确定删除此子类？", "删除确认", { type: "warning" });
    await categoryStore.deleteSubcategory(sub, category);
    ElMessage.success("删除成功");
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error(error?.message || "删除失败");
    }
  }
}

onMounted(fetchCategories);
</script>
<style scoped>
.category-header-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
}
.item-actions {
  display: flex;
  gap: 0.5rem;
}
.item-actions .btn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
}
.subcategory-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.category-title-wrapper {
  display: flex;
  flex-direction: column;
}
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
