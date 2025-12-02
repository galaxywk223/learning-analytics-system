<template>
  <PageContainer
    title="✅ 待办事项"
    subtitle="集中管理日常任务，跟踪完成情况"
    :custom-class="'todos-view'"
  >
    <template #actions>
      <el-button type="primary" @click="openCreate">新增</el-button>
      <el-button @click="refresh" :loading="store.loading">刷新</el-button>
    </template>

    <div class="filters">
      <el-segmented v-model="filter" :options="filterOptions" size="small" />
      <el-input
        v-model="keyword"
        placeholder="搜索标题..."
        size="small"
        clearable
        style="width: 220px"
      />
    </div>

    <el-table
      :data="filtered"
      v-loading="store.loading"
      size="small"
      class="todo-table"
      stripe
    >
      <el-table-column type="selection" width="40" />
      <el-table-column label="完成" width="70">
        <template #default="{ row }">
          <el-checkbox :model-value="row.completed" @change="toggle(row)" />
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="180">
        <template #default="{ row }">
          <span :class="{ done: row.completed }">{{ row.title }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="90">
        <template #default="{ row }">
          <el-tag :type="priorityType(row.priority)" size="small">{{
            labelPriority(row.priority)
          }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="due_date" label="截止日期" width="120">
        <template #default="{ row }">{{ row.due_date || "-" }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="openEdit(row)"
            >编辑</el-button
          >
          <el-button size="small" text type="danger" @click="remove(row)"
            >删除</el-button
          >
        </template>
      </el-table-column>
    </el-table>

    <el-empty
      v-if="!store.loading && !filtered.length"
      description="暂无数据"
    />

    <TodoForm v-model="dialogVisible" :data="editing" @submit="submit" />
  </PageContainer>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useTodoStore } from "@/stores/modules/todo";
import { todoAPI } from "@/api/modules/todo";
import TodoForm from "@/components/business/todo/TodoForm.vue";
import { ElMessageBox, ElMessage } from "element-plus";
import PageContainer from "@/components/layout/PageContainer.vue";

const store = useTodoStore();
const filter = ref("all");
const keyword = ref("");
const dialogVisible = ref(false);
const editing = ref({});

const filterOptions = ["all", "pending", "completed"];

const filtered = computed(() => {
  let arr = store.items;
  if (filter.value === "pending") arr = arr.filter((i) => !i.completed);
  else if (filter.value === "completed") arr = arr.filter((i) => i.completed);
  if (keyword.value)
    arr = arr.filter((i) =>
      i.title.toLowerCase().includes(keyword.value.toLowerCase())
    );
  return arr;
});

function refresh() {
  store.fetch();
}

function openCreate() {
  editing.value = {};
  dialogVisible.value = true;
}
function openEdit(row) {
  editing.value = { ...row };
  dialogVisible.value = true;
}

function priorityType(p) {
  return { low: "info", medium: "warning", high: "danger" }[p] || "default";
}
function labelPriority(p) {
  return { low: "低", medium: "中", high: "高" }[p] || "-";
}

async function submit(payload) {
  try {
    if (payload.id) {
      await store.save(payload.id, payload);
      ElMessage.success("已保存");
    } else {
      await store.add(payload);
      ElMessage.success("已创建");
    }
    dialogVisible.value = false;
  } catch (e) {
    ElMessage.error("操作失败");
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.title}」?`, "提示", {
      type: "warning",
    });
    await store.remove(row.id);
    ElMessage.success("已删除");
  } catch (e) {}
}

async function toggle(row) {
  try {
    if (todoAPI.toggle) {
      await todoAPI.toggle(row.id);
      row.completed = !row.completed;
    } else {
      await store.save(row.id, { completed: !row.completed });
    }
  } catch (e) {
    ElMessage.error("更新失败");
  }
}

onMounted(() => refresh());
</script>

<style scoped>
.actions {
  display: flex;
  gap: 8px;
}
.filters {
  display: flex;
  gap: 12px;
  align-items: center;
}
.todo-table :deep(.done) {
  text-decoration: line-through;
  color: #999;
}
</style>
