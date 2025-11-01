<template>
  <div class="category-management settings-subview">
    <div class="page-header">
      <h1>分类管理</h1>
      <p class="lead">管理学习记录的大类与子类。</p>
    </div>

    <div class="d-flex justify-content-end align-items-center mb-3">
      <button class="btn btn-primary" @click="showAddCategoryModal">
        <i data-lucide="plus-circle" class="me-2"></i>添加新分类
      </button>
    </div>

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
                <i data-lucide="folder" class="me-3"></i>
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
                  <i data-lucide="pencil"></i>
                </button>
                <button
                  class="btn btn-sm btn-outline-danger btn-icon"
                  title="删除"
                  @click="deleteCategory(category)"
                >
                  <i data-lucide="trash-2"></i>
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
                    <i data-lucide="tag" class="me-2" style="width: 16px"></i>
                    {{ sub.name }}
                  </span>
                  <div class="item-actions">
                    <button
                      class="btn btn-sm btn-outline-secondary btn-icon"
                      title="编辑"
                      @click="showEditSubcategoryModal(sub, category)"
                    >
                      <i data-lucide="pencil"></i>
                    </button>
                    <button
                      class="btn btn-sm btn-outline-danger btn-icon"
                      title="删除"
                      @click="deleteSubcategory(sub)"
                    >
                      <i data-lucide="trash-2"></i>
                    </button>
                  </div>
                </div>
                <p
                  v-if="
                    !category.subcategories ||
                    category.subcategories.length === 0
                  "
                  class="text-center text-muted p-3"
                >
                  这个分类下还没有标签。
                </p>

                <div class="list-group-item bg-transparent mt-2">
                  <div class="input-group">
                    <input
                      type="text"
                      class="form-control"
                      v-model="newSubcategoryNames[category.id]"
                      placeholder="在此添加新标签..."
                      @keyup.enter="addSubcategory(category.id)"
                    />
                    <button
                      type="button"
                      class="btn btn-outline-success"
                      @click="addSubcategory(category.id)"
                    >
                      <i data-lucide="plus"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <p
          v-if="!categories || categories.length === 0"
          class="text-center text-muted p-4"
        >
          还没有分类，点击上方按钮添加新分类。
        </p>
      </div>
    </div>

    <!-- 添加分类 Modal -->
    <div
      class="modal fade"
      id="addCategoryModal"
      tabindex="-1"
      ref="addCategoryModalRef"
    >
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">添加分类</h5>
            <button
              type="button"
              class="btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <label for="new-cat-name" class="form-label">分类名称</label>
            <input
              type="text"
              class="form-control"
              id="new-cat-name"
              v-model="newCategoryName"
              placeholder="例如：课程、科研..."
              @keyup.enter="addCategory"
            />
          </div>
          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary"
              data-bs-dismiss="modal"
            >
              取消
            </button>
            <button type="button" class="btn btn-primary" @click="addCategory">
              确认添加
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑分类 Modal -->
    <div
      class="modal fade"
      id="editCategoryModal"
      tabindex="-1"
      ref="editCategoryModalRef"
    >
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">编辑分类</h5>
            <button
              type="button"
              class="btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <label for="edit-cat-name" class="form-label">分类名称</label>
            <input
              type="text"
              class="form-control"
              id="edit-cat-name"
              v-model="editingCategory.name"
              @keyup.enter="updateCategory"
            />
          </div>
          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary"
              data-bs-dismiss="modal"
            >
              取消
            </button>
            <button
              type="button"
              class="btn btn-primary"
              @click="updateCategory"
            >
              保存更改
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑子分类 Modal -->
    <div
      class="modal fade"
      id="editSubcategoryModal"
      tabindex="-1"
      ref="editSubcategoryModalRef"
    >
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">编辑标签</h5>
            <button
              type="button"
              class="btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label for="edit-sub-name" class="form-label">标签名称</label>
              <input
                type="text"
                class="form-control"
                id="edit-sub-name"
                v-model="editingSubcategory.name"
              />
            </div>
            <div class="mb-3">
              <label for="parent-cat" class="form-label">所属分类</label>
              <select
                class="form-select"
                id="parent-cat"
                v-model="editingSubcategory.category_id"
              >
                <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                  {{ cat.name }}
                </option>
              </select>
            </div>
          </div>
          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary"
              data-bs-dismiss="modal"
            >
              取消
            </button>
            <button
              type="button"
              class="btn btn-primary"
              @click="updateSubcategory"
            >
              保存更改
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { categoryAPI } from "@/api";
import * as lucideIcons from "lucide";

const categories = ref([]);
const newCategoryName = ref("");
const newSubcategoryNames = ref({});
const editingCategory = ref({ id: null, name: "" });
const editingSubcategory = ref({ id: null, name: "", category_id: null });

const addCategoryModalRef = ref(null);
const editCategoryModalRef = ref(null);
const editSubcategoryModalRef = ref(null);

let addCategoryModal = null;
let editCategoryModal = null;
let editSubcategoryModal = null;

// 初始化 Lucide 图标
const initIcons = () => {
  nextTick(() => {
    try {
      lucideIcons.createIcons({
        icons: {
          Folder: lucideIcons.Folder,
          Tag: lucideIcons.Tag,
          Pencil: lucideIcons.Pencil,
          Trash2: lucideIcons.Trash2,
          PlusCircle: lucideIcons.PlusCircle,
          Plus: lucideIcons.Plus,
        },
      });
    } catch (error) {
      console.error("Lucide icons initialization error:", error);
    }
  });
};

// 加载所有分类
const loadCategories = async () => {
  try {
    const response = await categoryAPI.getAll({ include_subcategories: true });
    console.log("API Response:", response); // 调试日志
    if (response.success) {
      categories.value = response.categories;
      console.log("Categories loaded:", categories.value); // 调试日志
      // 初始化所有分类的新子分类名称
      categories.value.forEach((cat) => {
        newSubcategoryNames.value[cat.id] = "";
      });
      // 初始化图标
      initIcons();
    }
  } catch (error) {
    console.error("Load categories error:", error); // 调试日志
    ElMessage.error("加载分类失败：" + (error.message || "未知错误"));
  }
};

// 显示添加分类模态框
const showAddCategoryModal = () => {
  newCategoryName.value = "";
  addCategoryModal.show();
};

// 添加分类
const addCategory = async () => {
  if (!newCategoryName.value.trim()) {
    ElMessage.warning("分类名称不能为空");
    return;
  }

  try {
    const response = await categoryAPI.create({
      name: newCategoryName.value.trim(),
    });
    console.log("Create category response:", response); // 调试日志
    if (response.success) {
      ElMessage.success("分类添加成功");
      addCategoryModal.hide();
      await loadCategories();
    }
  } catch (error) {
    console.error("Create category error:", error); // 调试日志
    ElMessage.error("添加分类失败：" + (error.message || "未知错误"));
  }
};

// 显示编辑分类模态框
const showEditCategoryModal = (category) => {
  editingCategory.value = { id: category.id, name: category.name };
  editCategoryModal.show();
};

// 更新分类
const updateCategory = async () => {
  if (!editingCategory.value.name.trim()) {
    ElMessage.warning("分类名称不能为空");
    return;
  }

  try {
    const response = await categoryAPI.update(editingCategory.value.id, {
      name: editingCategory.value.name.trim(),
    });
    if (response.success) {
      ElMessage.success("分类更新成功");
      editCategoryModal.hide();
      await loadCategories();
    }
  } catch (error) {
    ElMessage.error("更新分类失败：" + (error.message || "未知错误"));
  }
};

// 删除分类
const deleteCategory = async (category) => {
  try {
    await ElMessageBox.confirm(
      `警告：确定要删除分类 "${category.name}" 吗？只有当它不包含任何标签时才能删除。`,
      "确认删除",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }
    );

    const response = await categoryAPI.delete(category.id);
    if (response.success) {
      ElMessage.success("分类删除成功");
      await loadCategories();
    }
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("删除分类失败：" + (error.message || "未知错误"));
    }
  }
};

// 添加子分类
const addSubcategory = async (categoryId) => {
  const name = newSubcategoryNames.value[categoryId];
  if (!name || !name.trim()) {
    ElMessage.warning("标签名称不能为空");
    return;
  }

  try {
    const response = await categoryAPI.createSubcategory(categoryId, {
      name: name.trim(),
    });
    if (response.success) {
      ElMessage.success("标签添加成功");
      newSubcategoryNames.value[categoryId] = "";
      await loadCategories();
    }
  } catch (error) {
    ElMessage.error("添加标签失败：" + (error.message || "未知错误"));
  }
};

// 显示编辑子分类模态框
const showEditSubcategoryModal = (subcategory, category) => {
  editingSubcategory.value = {
    id: subcategory.id,
    name: subcategory.name,
    category_id: subcategory.category_id || category.id,
  };
  editSubcategoryModal.show();
};

// 更新子分类
const updateSubcategory = async () => {
  if (!editingSubcategory.value.name.trim()) {
    ElMessage.warning("标签名称不能为空");
    return;
  }

  try {
    const response = await categoryAPI.updateSubcategory(
      editingSubcategory.value.id,
      {
        name: editingSubcategory.value.name.trim(),
        category_id: editingSubcategory.value.category_id,
      }
    );
    if (response.success) {
      ElMessage.success("标签更新成功");
      editSubcategoryModal.hide();
      await loadCategories();
    }
  } catch (error) {
    ElMessage.error("更新标签失败：" + (error.message || "未知错误"));
  }
};

// 删除子分类
const deleteSubcategory = async (subcategory) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除标签 "${subcategory.name}" 吗？只有当它未关联任何学习记录时才能删除。`,
      "确认删除",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }
    );

    const response = await categoryAPI.deleteSubcategory(subcategory.id);
    if (response.success) {
      ElMessage.success("标签删除成功");
      await loadCategories();
    }
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("删除标签失败：" + (error.message || "未知错误"));
    }
  }
};

onMounted(async () => {
  // 初始化 Bootstrap 模态框
  if (addCategoryModalRef.value) {
    addCategoryModal = new window.bootstrap.Modal(addCategoryModalRef.value);
  }
  if (editCategoryModalRef.value) {
    editCategoryModal = new window.bootstrap.Modal(editCategoryModalRef.value);
  }
  if (editSubcategoryModalRef.value) {
    editSubcategoryModal = new window.bootstrap.Modal(
      editSubcategoryModalRef.value
    );
  }

  // 加载数据
  await loadCategories();

  // 确保图标初始化
  initIcons();
});

onBeforeUnmount(() => {
  // 清理模态框
  if (addCategoryModal) addCategoryModal.dispose();
  if (editCategoryModal) editCategoryModal.dispose();
  if (editSubcategoryModal) editSubcategoryModal.dispose();
});
</script>

<style scoped>
.settings-subview {
  padding: 1rem 0;
}

/* --- Main Item Styles (Category Rows) --- */
.category-header-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 0.75rem 1.25rem;
  transition: background-color 0.2s ease-in-out;
}

.accordion-header:hover .category-header-item {
  background-color: #f8f9fa;
}

/* --- 核心修正 1：强制 item-actions 内部所有元素垂直居中 --- */
.item-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.category-header-item .item-actions {
  opacity: 0;
  transition: opacity 0.2s ease-in-out;
}

.category-header-item:hover .item-actions {
  opacity: 1;
}

.category-title-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.category-badge {
  font-size: 0.75em;
  vertical-align: baseline;
}

/* --- Subcategory Item Styles (Tag Rows) --- */
.subcategory-list {
  background-color: #f8f9fa;
  padding: 0.5rem;
  border-top: 1px solid #dee2e6;
}

.subcategory-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1.25rem;
  padding-left: 2.5rem !important;
  transition: background-color 0.2s ease-in-out;
  border: none !important;
}

.subcategory-item:hover {
  background-color: #e9ecef;
}

.subcategory-item .item-actions {
  opacity: 0;
  transition: opacity 0.2s ease-in-out;
}

.subcategory-item:hover .item-actions {
  opacity: 1;
}

.btn-icon {
  padding: 0.2rem 0.5rem;
  line-height: 1;
}

.btn-icon i {
  width: 16px;
  height: 16px;
  vertical-align: middle;
}

/* --- Bootstrap Accordion Overrides --- */
.accordion-button {
  padding: 0;
  background-color: transparent !important;
  box-shadow: none !important;
}

.accordion-button::after {
  margin-left: 1rem;
}

.accordion-button:not(.collapsed)::after {
  transform: rotate(-180deg);
}

.item-actions form {
  display: flex;
  align-items: center;
}

.card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
}

.card-header {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f0f0f0;
  background-color: #fff;
}
</style>
