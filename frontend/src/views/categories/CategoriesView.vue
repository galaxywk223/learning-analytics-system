<template>
  <div class="categories-view">
    <CategoryHeader
      title="分类管理"
      subtitle="维护学习分类与子分类层级结构"
      add-button-text="新增分类"
      :loading="store.loading"
      @add="addRoot"
      @refresh="refresh"
    />

    <div class="content-section" v-loading="store.loading">
      <CategoryTree
        ref="treeRef"
        :tree-data="treeData"
        :selected-node="selectedNode"
        @node-click="handleNodeClick"
        @node-expand="handleNodeExpand"
        @node-collapse="handleNodeCollapse"
        @add-child="addChild"
        @edit="editCategory"
        @delete="deleteCategory"
      />
    </div>

    <!-- 分类表单弹窗 -->
    <CategoryForm
      :visible="formVisible"
      :category-data="editingCategory"
      :parent-category="parentCategory"
      :loading="submitLoading"
      @close="closeForm"
      @submit="handleSubmit"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useCategoryStore } from "@/stores/category";
import CategoryHeader from "./components/CategoryHeader.vue";
import CategoryTree from "./components/CategoryTree.vue";
import CategoryForm from "./components/CategoryForm.vue";

const store = useCategoryStore();
const treeRef = ref(null);

// 响应式数据
const selectedNode = ref(null);
const formVisible = ref(false);
const editingCategory = ref(null);
const parentCategory = ref(null);
const submitLoading = ref(false);

// 计算属性
const treeData = computed(() => {
  return store.categoryTree || [];
});

// 事件处理方法
async function refresh() {
  try {
    await store.fetchCategories();
    ElMessage.success("数据刷新成功");
  } catch (error) {
    ElMessage.error("刷新失败: " + error.message);
  }
}

function handleNodeClick(data, node) {
  selectedNode.value = data;
  console.log("Selected node:", data);
  console.log("Selected node category_id:", data.category_id);
  console.log("Selected node children:", data.children);
  if (data.children && data.children.length > 0) {
    console.log("First child:", data.children[0]);
    console.log("First child category_id:", data.children[0].category_id);
  }
}

function handleNodeExpand(data, node) {
  console.log("Node expanded:", data);
}

function handleNodeCollapse(data, node) {
  console.log("Node collapsed:", data);
}

function addRoot() {
  editingCategory.value = null;
  parentCategory.value = null;
  formVisible.value = true;
}

function addChild(parentNode) {
  editingCategory.value = null;
  parentCategory.value = parentNode;
  formVisible.value = true;
}

function editCategory(categoryData) {
  editingCategory.value = categoryData;
  parentCategory.value = null; // 编辑时不显示父分类选择
  formVisible.value = true;
}

async function deleteCategory(categoryData) {
  try {
    const confirmText =
      categoryData.children && categoryData.children.length > 0
        ? "该分类包含子分类，删除后子分类也将被删除。是否确认删除？"
        : "确认删除该分类？";

    await ElMessageBox.confirm(confirmText, "删除确认", {
      confirmButtonText: "确定删除",
      cancelButtonText: "取消",
      type: "warning",
      dangerouslyUseHTMLString: false,
    });

    // 传递完整的节点对象，而不是只传递 id
    await store.deleteCategory(categoryData);
    ElMessage.success("删除成功");

    // 清除选中状态
    selectedNode.value = null;
  } catch (error) {
    if (error !== "cancel") {
      // 改进错误提示
      const errorMsg =
        error.response?.data?.message || error.message || "删除失败";
      if (
        errorMsg.includes("关联") ||
        errorMsg.includes("记录") ||
        error.response?.status === 400
      ) {
        ElMessage.error(
          "该分类下存在学习记录，无法删除。请先删除或转移相关记录。"
        );
      } else {
        ElMessage.error("删除失败: " + errorMsg);
      }
    }
  }
}

function closeForm() {
  formVisible.value = false;
  editingCategory.value = null;
  parentCategory.value = null;
}

async function handleSubmit(formData) {
  submitLoading.value = true;

  try {
    if (editingCategory.value) {
      // 更新分类 - 传递完整对象和数据
      await store.updateCategory(editingCategory.value, formData);
      ElMessage.success("更新成功");
    } else {
      // 创建分类
      if (parentCategory.value) {
        // 创建子分类
        await store.createSubCategory(parentCategory.value.id, formData);
        ElMessage.success("子分类创建成功");
      } else {
        // 创建主分类
        await store.createCategory(formData);
        ElMessage.success("分类创建成功");
      }
    }

    closeForm();
  } catch (error) {
    ElMessage.error("操作失败: " + error.message);
  } finally {
    submitLoading.value = false;
  }
}

// 生命周期
onMounted(async () => {
  if (!store.categories.length) {
    await refresh();
  }
});
</script>

<style scoped>
.categories-view {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  min-height: 100vh;
  background: transparent;
}

.content-section {
  margin-top: 24px;
}

@media (max-width: 768px) {
  .categories-view {
    padding: 16px;
  }

  .content-section {
    margin-top: 16px;
  }
}
</style>
