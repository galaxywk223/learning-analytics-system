<template>
  <PageContainer
    :title="{ icon: 'lucide:folder-tree', text: '分类管理' }"
    subtitle="维护学习分类与子分类层级结构"
    :custom-class="'settings-subpage'"
  >
    <template #actions>
      <div class="actions">
        <button class="pill-btn primary" @click="addRoot">
          <span class="icon">+</span> 新增分类
        </button>
        <button
          class="pill-btn secondary"
          :disabled="store.loading"
          @click="refresh"
        >
          刷新
        </button>
      </div>
    </template>

    <div v-loading="store.loading" class="content-section">
      <CategoryTree
        ref="treeRef"
        :tree-data="treeData"
        :selected-node="selectedNode"
        @node-click="handleNodeClick"
        @node-expand="handleNodeExpand"
        @node-collapse="handleNodeCollapse"
        @add-child="addChild"
        @edit="editCategory"
        @merge="openMergeDialog"
        @delete="deleteCategory"
      />
    </div>

    <!-- 分类表单弹窗 -->
    <CategoryForm
      :visible="formVisible"
      :category-data="editingCategory"
      :parent-category="parentCategory"
      :available-parents="treeData"
      :loading="submitLoading"
      @close="closeForm"
      @submit="handleSubmit"
    />

    <!-- 子分类合并弹窗 -->
    <el-dialog
      v-model="mergeDialogVisible"
      title="合并子分类"
      width="460px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div class="merge-body">
        <p v-if="mergeSource" class="merge-hint">
          将
          <strong>{{ mergeSource.name }}</strong>
          合并到：
        </p>
        <el-select
          v-model="mergeTargetId"
          placeholder="请选择目标子分类"
          class="merge-select"
          filterable
        >
          <el-option
            v-for="option in mergeTargetOptions"
            :key="option.id"
            :label="`${option.categoryName} / ${option.name}`"
            :value="option.id"
          />
        </el-select>
        <p class="merge-note">
          合并后会删除源子分类，已关联学习记录将转移到目标子分类名称下。
        </p>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <button class="pill-btn secondary" @click="closeMergeDialog">
            取消
          </button>
          <button
            class="pill-btn primary"
            :disabled="mergeSubmitting"
            @click="submitMerge"
          >
            {{ mergeSubmitting ? "合并中..." : "确认合并" }}
          </button>
        </div>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useCategoryStore } from "@/stores/category";
import CategoryTree from "./components/CategoryTree.vue";
import CategoryForm from "./components/CategoryForm.vue";
import PageContainer from "@/components/layout/PageContainer.vue";

const store = useCategoryStore();
const treeRef = ref(null);

// 响应式数据
const selectedNode = ref(null);
const formVisible = ref(false);
const editingCategory = ref(null);
const parentCategory = ref(null);
const submitLoading = ref(false);
const mergeDialogVisible = ref(false);
const mergeSource = ref(null);
const mergeTargetId = ref(null);
const mergeSubmitting = ref(false);

// 计算属性
const treeData = computed(() => {
  return store.categoryTree || [];
});

const mergeTargetOptions = computed(() => {
  const sourceId = mergeSource.value?.id;
  const categories = treeData.value || [];
  const options = [];

  categories.forEach((category) => {
    const children = category.children || category.subcategories || [];
    children.forEach((sub) => {
      if (sub.id !== sourceId) {
        options.push({
          id: sub.id,
          name: sub.name,
          categoryName: category.name,
        });
      }
    });
  });

  return options;
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

function handleNodeClick(data) {
  selectedNode.value = data;
}

function handleNodeExpand() {}

function handleNodeCollapse() {}

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
          "该分类下存在学习记录，无法删除。请先删除或转移相关记录。",
        );
      } else {
        ElMessage.error("删除失败: " + errorMsg);
      }
    }
  }
}

function openMergeDialog(categoryData) {
  if (!categoryData?.category_id) {
    ElMessage.warning("仅支持对子分类执行合并");
    return;
  }
  const hasTarget = (treeData.value || []).some((category) =>
    (category.children || category.subcategories || []).some(
      (sub) => sub.id !== categoryData.id,
    ),
  );
  if (!hasTarget) {
    ElMessage.warning("暂无可合并的目标子分类");
    return;
  }
  mergeSource.value = categoryData;
  mergeTargetId.value = null;
  mergeDialogVisible.value = true;
}

function closeMergeDialog() {
  mergeDialogVisible.value = false;
  mergeSource.value = null;
  mergeTargetId.value = null;
  mergeSubmitting.value = false;
}

async function submitMerge() {
  if (!mergeSource.value) return;
  if (!mergeTargetId.value) {
    ElMessage.warning("请选择目标子分类");
    return;
  }

  const target = mergeTargetOptions.value.find((item) => item.id === mergeTargetId.value);
  const targetName = target ? `${target.categoryName} / ${target.name}` : "目标子分类";

  try {
    await ElMessageBox.confirm(
      `确认将“${mergeSource.value.name}”合并到“${targetName}”吗？`,
      "合并确认",
      {
        confirmButtonText: "确认合并",
        cancelButtonText: "取消",
        type: "warning",
      },
    );
  } catch (error) {
    if (error === "cancel" || error === "close") {
      return;
    }
    ElMessage.error("合并确认失败，请重试");
    return;
  }

  mergeSubmitting.value = true;
  try {
    await store.mergeSubcategory(mergeSource.value.id, mergeTargetId.value);
    ElMessage.success("子分类合并成功");
    selectedNode.value = null;
    closeMergeDialog();
  } catch (error) {
    const errorMsg = error.response?.data?.message || error.message || "合并失败";
    ElMessage.error("合并失败: " + errorMsg);
  } finally {
    mergeSubmitting.value = false;
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
      // 优先使用 formData.parent_id (用户在表单中选择的)
      if (formData.parent_id) {
        // 创建子分类
        await store.createSubCategory(formData.parent_id, formData);
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
.actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.content-section {
  margin-top: 24px;
}
.merge-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.merge-hint {
  margin: 0;
  color: var(--color-text-base);
  font-size: 14px;
}
.merge-select {
  width: 100%;
}
.merge-note {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 12px;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .content-section {
    margin-top: 16px;
  }
}
</style>
