<template>
  <div class="tree-card">
    <div class="card-header">
      <h3>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path
            d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
          />
        </svg>
        分类树形结构
      </h3>
      <div class="card-actions">
        <el-button
          v-if="selectedNode && canAddChild"
          type="success"
          size="small"
          @click="
            () => {
              console.log('Add child clicked, node:', selectedNode);
              $emit('add-child', selectedNode);
            }
          "
          :icon="Plus"
        >
          添加子分类
        </el-button>
        <el-button
          v-if="selectedNode && canEdit"
          type="warning"
          size="small"
          @click="
            () => {
              console.log('Edit clicked, node:', selectedNode);
              $emit('edit', selectedNode);
            }
          "
          :icon="Edit"
        >
          编辑
        </el-button>
        <el-button
          v-if="selectedNode && canDelete"
          type="danger"
          size="small"
          @click="
            () => {
              console.log('Delete clicked, node:', selectedNode);
              $emit('delete', selectedNode);
            }
          "
          :icon="Delete"
        >
          删除
        </el-button>
      </div>
    </div>

    <div class="tree-container">
      <el-tree
        ref="treeRef"
        :data="treeData"
        :props="treeProps"
        :expand-on-click-node="false"
        :highlight-current="true"
        node-key="uniqueKey"
        @node-click="handleNodeClick"
        @node-expand="handleNodeExpand"
        @node-collapse="handleNodeCollapse"
        class="category-tree"
      >
        <template #default="{ node, data }">
          <div class="tree-node">
            <div class="node-content">
              <span class="node-icon">
                <svg
                  v-if="data.type === 'category'"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path
                    d="M10 4H4c-1.11 0-2 .89-2 2v12c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2h-8l-2-2z"
                  />
                </svg>
                <svg
                  v-else
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path
                    d="M9.5 3l-1.5 1.5L9.5 6 11 4.5 9.5 3m6 0L14 4.5 15.5 6 17 4.5 15.5 3M7.5 6l-1.5 1.5L7.5 9 9 7.5 7.5 6m9 0L15 7.5 16.5 9 18 7.5 16.5 6M12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4z"
                  />
                </svg>
              </span>
              <span class="node-label">{{ data.name }}</span>
            </div>
            <div v-if="data.recordCount !== undefined" class="node-stats">
              <span class="record-count">{{ data.recordCount }} 条记录</span>
            </div>
          </div>
        </template>
      </el-tree>
    </div>

    <div v-if="!treeData || treeData.length === 0" class="empty-state">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="currentColor"
        class="empty-icon"
      >
        <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
      </svg>
      <p>暂无分类数据</p>
      <p class="empty-tip">点击"新增分类"创建你的第一个分类</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { Plus, Edit, Delete } from "@element-plus/icons-vue";

const props = defineProps({
  treeData: {
    type: Array,
    default: () => [],
  },
  selectedNode: {
    type: Object,
    default: null,
  },
  treeProps: {
    type: Object,
    default: () => ({
      children: "children",
      label: "name",
    }),
  },
});

const emit = defineEmits([
  "node-click",
  "node-expand",
  "node-collapse",
  "add-child",
  "edit",
  "delete",
]);

const treeRef = ref(null);

// 计算属性
const canEdit = computed(() => {
  return props.selectedNode && props.selectedNode.id;
});

// 只有顶级分类（没有category_id的）才能添加子分类
const canAddChild = computed(() => {
  console.log("canAddChild check:", {
    selectedNode: props.selectedNode,
    hasId: !!props.selectedNode?.id,
    categoryId: props.selectedNode?.category_id,
    result:
      props.selectedNode &&
      props.selectedNode.id &&
      !props.selectedNode.category_id,
  });
  return (
    props.selectedNode &&
    props.selectedNode.id &&
    !props.selectedNode.category_id // 如果有category_id，说明是子分类，不能再添加子分类
  );
});

const canDelete = computed(() => {
  return (
    props.selectedNode &&
    props.selectedNode.id &&
    (!props.selectedNode.children || props.selectedNode.children.length === 0)
  );
});

// 事件处理
function handleNodeClick(data, node) {
  emit("node-click", data, node);
}

function handleNodeExpand(data, node) {
  emit("node-expand", data, node);
}

function handleNodeCollapse(data, node) {
  emit("node-collapse", data, node);
}

// 暴露方法
defineExpose({
  getTree: () => treeRef.value,
  setCurrentKey: (key) => treeRef.value?.setCurrentKey(key),
  getCurrentKey: () => treeRef.value?.getCurrentKey(),
  getCurrentNode: () => treeRef.value?.getCurrentNode(),
});
</script>

<style scoped>
.tree-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e8eaf6;
  background: #fafbfc;
}

.card-header h3 {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: #1e293b;
}

.card-header svg {
  width: 20px;
  height: 20px;
  color: #667eea;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.tree-container {
  max-height: 600px;
  overflow-y: auto;
  padding: 16px 0;
}

.category-tree {
  padding: 0 24px;
}

.tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background-color 0.2s ease;
}

.tree-node:hover {
  background: #f8fafc;
}

.node-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.node-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.node-icon svg {
  width: 16px;
  height: 16px;
  color: #6b7280;
}

.node-label {
  font-weight: 600;
  color: #1f2937;
  font-size: 14px;
}

.node-stats {
  display: flex;
  align-items: center;
  gap: 8px;
}

.record-count {
  background: #e8eaf6;
  color: #667eea;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

.empty-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
  color: #d1d5db;
}

.empty-state p {
  margin: 8px 0;
  font-size: 16px;
}

.empty-tip {
  font-size: 14px;
  color: #9ca3af;
}

:deep(.el-tree-node__content) {
  height: auto;
  min-height: 40px;
  padding: 0;
}

:deep(.el-tree-node__expand-icon) {
  color: #6b7280;
  font-size: 14px;
}

:deep(
  .el-tree--highlight-current .el-tree-node.is-current > .el-tree-node__content
) {
  background: #e8eaf6;
  color: #667eea;
}

:deep(.el-tree--highlight-current .el-tree-node.is-current .node-label) {
  color: #667eea;
  font-weight: 700;
}
</style>
