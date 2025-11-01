<template>
  <div class="categories-view">
    <div class="header">
      <div>
        <h1>分类管理</h1>
        <p class="sub">维护学习分类与子分类层级</p>
      </div>
      <div class="actions">
        <el-button type="primary" @click="addRoot">新增顶级分类</el-button>
        <el-button :loading="store.loading" @click="refresh">刷新</el-button>
      </div>
    </div>
    <div class="content" v-loading="store.loading">
      <div class="tree-pane">
        <el-tree
          v-if="store.tree.length"
          :data="store.tree"
          :props="treeProps"
          node-key="id"
          highlight-current
          :expand-on-click-node="false"
          :default-expanded-keys="store.expandedKeys"
          @node-click="onNodeClick"
        >
          <template #default="{ node, data }">
            <div class="tree-node-row">
              <span class="name">{{ data.name }}</span>
              <span class="toolbar">
                <el-button text size="small" @click.stop="addChild(data)"
                  >子</el-button
                >
                <el-button text size="small" @click.stop="rename(data)"
                  >改</el-button
                >
                <el-button
                  text
                  size="small"
                  type="danger"
                  @click.stop="removeNode(data)"
                  >删</el-button
                >
              </span>
            </div>
          </template>
        </el-tree>
        <el-empty v-else description="暂无分类" />
      </div>
      <div class="detail-pane" v-if="current">
        <h3>详情</h3>
        <el-descriptions :column="1" size="small" border>
          <el-descriptions-item label="ID">{{
            current.id
          }}</el-descriptions-item>
          <el-descriptions-item label="名称">{{
            current.name
          }}</el-descriptions-item>
          <el-descriptions-item label="父级">{{
            current.parent_id || "无"
          }}</el-descriptions-item>
          <el-descriptions-item label="子项数">{{
            current.children?.length || 0
          }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from "vue";
import { useCategoryStore } from "@/stores/category";
import { ElMessageBox, ElMessage } from "element-plus";

const store = useCategoryStore();
const current = ref(null);

const treeProps = { label: "name", children: "children" };

function refresh() {
  store.fetchAll();
}
function onNodeClick(data) {
  current.value = data;
}

async function addRoot() {
  const name = await promptName("输入顶级分类名称");
  if (name) {
    await store.createRoot(name);
    ElMessage.success("已创建");
  }
}
async function addChild(parent) {
  const name = await promptName(`在「${parent.name}」下添加子分类`);
  if (name) {
    await store.createChild(parent.id, name);
    ElMessage.success("已创建");
  }
}
async function rename(node) {
  const name = await promptName(`重命名「${node.name}」`, node.name);
  if (name && name !== node.name) {
    await store.rename(node, name);
    ElMessage.success("已更新");
  }
}
async function removeNode(node) {
  try {
    await ElMessageBox.confirm(
      `确定删除分类「${node.name}」及其所有子级?`,
      "提示",
      { type: "warning" }
    );
    await store.remove(node);
    if (current.value?.id === node.id) current.value = null;
    ElMessage.success("已删除");
  } catch (e) {}
}

function promptName(title, defaultValue = "") {
  return new Promise((resolve) => {
    ElMessageBox.prompt("", title, {
      inputValue: defaultValue,
      confirmButtonText: "确定",
      cancelButtonText: "取消",
    })
      .then(({ value }) => resolve(value && value.trim()))
      .catch(() => resolve(null));
  });
}

onMounted(() => refresh());
</script>
<style scoped>
.categories-view {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}
.header h1 {
  margin: 0;
  font-size: 24px;
}
.sub {
  margin: 4px 0 0;
  color: #666;
  font-size: 13px;
}
.actions {
  display: flex;
  gap: 8px;
}
.content {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}
.tree-pane {
  flex: 1;
  min-width: 320px;
}
.detail-pane {
  width: 320px;
  position: sticky;
  top: 80px;
  align-self: flex-start;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.tree-node-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2px 4px;
  gap: 8px;
}
.tree-node-row .name {
  flex: 1;
}
.tree-node-row .toolbar {
  display: flex;
  gap: 4px;
}
</style>
