<template>
  <div class="tree-container-flat">
    <div class="tree-header">
      <h4>分类结构</h4>
      <div class="header-actions">
        <button
          v-if="selectedNode && canAddChild"
          class="action-btn"
          title="添加子分类"
          @click="$emit('add-child', selectedNode)"
        >
          <span class="icon">+</span>
        </button>
        <button
          v-if="selectedNode && canEdit"
          class="action-btn"
          title="编辑"
          @click="$emit('edit', selectedNode)"
        >
          ✏️
        </button>
        <button
          v-if="selectedNode && canDelete"
          class="action-btn danger"
          title="删除"
          @click="$emit('delete', selectedNode)"
        >
          🗑️
        </button>
      </div>
    </div>

    <div class="tree-content">
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
                <span v-if="data.type === 'category'">📂</span>
                <span v-else>📄</span>
              </span>
              <span class="node-label">{{ data.name }}</span>
            </div>
            <div v-if="data.recordCount !== undefined" class="node-stats">
              <span class="record-count">{{ data.recordCount }}</span>
            </div>
          </div>
        </template>
      </el-tree>
    </div>

    <div v-if="!treeData || treeData.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <p>暂无分类数据</p>
      <p class="empty-tip">点击右上角“新增分类”开始</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

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
  return (
    props.selectedNode &&
    props.selectedNode.id &&
    !props.selectedNode.category_id
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
.tree-container-flat {
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.tree-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #111827;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid transparent;
  background: #ffffff;
  color: #6b7280;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.action-btn:hover {
  background: #f3f4f6;
  color: #111827;
  border-color: #d1d5db;
}

.action-btn.danger:hover {
  background: #fef2f2;
  color: #dc2626;
  border-color: #fecaca;
}

.tree-content {
  padding: 16px 0;
  max-height: 600px;
  overflow-y: auto;
}

.category-tree {
  padding: 0 16px;
}

.tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background-color 0.15s ease;
}

.tree-node:hover {
  background: #f9fafb;
}

.node-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.node-icon {
  font-size: 16px;
  color: #6b7280;
  display: flex;
  align-items: center;
}

.node-label {
  font-weight: 500;
  color: #1f2937;
  font-size: 14px;
}

.node-stats {
  display: flex;
  align-items: center;
}

.record-count {
  background: #f3f4f6;
  color: #6b7280;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #9ca3af;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.empty-state p {
  margin: 4px 0;
  font-size: 14px;
}

.empty-tip {
  font-size: 12px;
  color: #d1d5db;
}

/* Element Plus Tree Overrides */
:deep(.el-tree-node__content) {
  height: auto;
  min-height: 40px;
  padding: 0;
  border-radius: 8px;
  margin-bottom: 2px;
}

:deep(.el-tree-node__content:hover) {
  background-color: #f9fafb;
}

:deep(.el-tree-node__expand-icon) {
  color: #9ca3af;
  font-size: 14px;
  padding: 6px;
}

:deep(
  .el-tree--highlight-current .el-tree-node.is-current > .el-tree-node__content
) {
  background: #eff6ff; /* Light blue */
}

:deep(.el-tree--highlight-current .el-tree-node.is-current .node-label) {
  color: #2563eb; /* Blue */
  font-weight: 600;
}
</style>
