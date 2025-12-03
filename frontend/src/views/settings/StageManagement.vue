<template>
  <PageContainer
    :title="{ icon: '🚩', text: '阶段管理' }"
    subtitle="梳理学习阶段，设置当前阶段并管理时间跨度"
    :custom-class="'settings-subpage'"
  >
    <div class="stage-shell">
      <div class="stage-card">
        <div class="stage-card__header">
          <div>
            <h2>阶段管理</h2>
            <p>创建、编辑你的学习阶段，设置当前进行中的阶段。</p>
          </div>
        </div>

        <div class="create-row">
          <input
            v-model="newStage.name"
            type="text"
            placeholder="输入阶段名称（如：大三上学期）"
          />
          <input
            v-model="newStage.start"
            type="date"
            placeholder="起始日期"
          />
          <button class="pill-btn primary" type="button" @click="addStage">
            创建
          </button>
        </div>

        <div class="stage-list" v-if="stages.length">
          <div
            v-for="stage in stages"
            :key="stage.id"
            class="stage-item"
            :class="{ current: stage.isCurrent }"
          >
            <div class="stage-info">
              <div class="stage-title">{{ stage.name }}</div>
              <div class="stage-sub">起始于 {{ stage.start }}</div>
            </div>
            <div class="stage-tags" v-if="stage.isCurrent">
              <span class="pill current">✅ 当前进行中</span>
            </div>
            <div class="stage-actions">
              <button
                class="ghost-btn"
                :disabled="stage.isCurrent"
                @click="setCurrent(stage.id)"
                title="设为当前阶段"
              >
                🚩
              </button>
              <button class="ghost-btn" title="编辑" @click="startEdit(stage)">
                ✏️
              </button>
              <button class="ghost-btn danger" title="删除" @click="removeStage(stage.id)">
                🗑️
              </button>
            </div>

            <div class="edit-row" v-if="editingId === stage.id">
              <input v-model="editStage.name" type="text" />
              <input v-model="editStage.start" type="date" />
              <div class="edit-actions">
                <button class="pill-btn primary" type="button" @click="saveEdit(stage.id)">
                  保存
                </button>
                <button class="pill-btn ghost" type="button" @click="cancelEdit">
                  取消
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="empty-state" v-else>
          <div class="empty-illustration">🏔️🚩</div>
          <p class="empty-title">开启你的第一个学习阶段</p>
          <p class="empty-sub">在上方输入名称与日期即可创建</p>
        </div>
      </div>
    </div>
  </PageContainer>
</template>

<script setup>
import { ref } from "vue";
import PageContainer from "@/components/layout/PageContainer.vue";

let uid = 3;
const stages = ref([
  { id: 1, name: "大三上学期", start: "2024-09-01", isCurrent: true },
  { id: 2, name: "寒假自律计划", start: "2025-01-15", isCurrent: false },
]);

const newStage = ref({ name: "", start: "" });
const editingId = ref(null);
const editStage = ref({ name: "", start: "" });

function addStage() {
  if (!newStage.value.name || !newStage.value.start) return;
  stages.value.unshift({
    id: ++uid,
    name: newStage.value.name,
    start: newStage.value.start,
    isCurrent: false,
  });
  newStage.value = { name: "", start: "" };
}

function setCurrent(id) {
  stages.value = stages.value.map((s) => ({
    ...s,
    isCurrent: s.id === id,
  }));
}

function startEdit(stage) {
  editingId.value = stage.id;
  editStage.value = { name: stage.name, start: stage.start };
}

function cancelEdit() {
  editingId.value = null;
  editStage.value = { name: "", start: "" };
}

function saveEdit(id) {
  if (!editStage.value.name || !editStage.value.start) return;
  stages.value = stages.value.map((s) =>
    s.id === id ? { ...s, ...editStage.value } : s
  );
  cancelEdit();
}

function removeStage(id) {
  stages.value = stages.value.filter((s) => s.id !== id);
  if (editingId.value === id) cancelEdit();
}
</script>

<style scoped>
.stage-shell {
  display: flex;
  justify-content: center;
}

.stage-card {
  width: 100%;
  max-width: 820px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #e5e7eb;
  border-radius: 24px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
  padding: 18px 18px 22px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.stage-card__header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
}

.stage-card__header p {
  margin: 6px 0 0;
  color: #6b7280;
  font-size: 13px;
}

.create-row {
  display: grid;
  grid-template-columns: 2fr 1fr auto;
  gap: 10px;
  align-items: center;
  padding-bottom: 6px;
  border-bottom: 1px solid #f1f5f9;
}

.create-row input {
  height: 42px;
  border: none;
  border-radius: 12px;
  background: #f3f4f6;
  padding: 0 12px;
  font-size: 14px;
  outline: none;
  transition: all 0.15s ease;
}

.create-row input:focus {
  background: #ffffff;
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.12);
}

.stage-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 4px;
}

.stage-item {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 10px;
  align-items: center;
  padding: 14px 12px;
  border-radius: 16px;
  transition: all 0.15s ease;
  min-height: 72px;
}

.stage-item:hover {
  background: #f9fafb;
}

.stage-item.current {
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.stage-info .stage-title {
  font-weight: 800;
  color: #0f172a;
  font-size: 15px;
}

.stage-info .stage-sub {
  color: #6b7280;
  font-size: 12px;
  margin-top: 2px;
}

.stage-tags .pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  background: rgba(16, 185, 129, 0.16);
  color: #0f766e;
}

.stage-actions {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
}

.ghost-btn {
  border: none;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 10px;
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 14px;
  color: #4b5563;
  transition: background 0.15s ease, color 0.15s ease;
}

.ghost-btn:hover {
  background: rgba(79, 70, 229, 0.12);
  color: #111827;
}

.ghost-btn.danger:hover {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
}

.ghost-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.edit-row {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: 2fr 1fr auto;
  gap: 10px;
  align-items: center;
  padding-top: 6px;
}

.edit-row input {
  height: 38px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 0 10px;
}

.edit-actions {
  display: flex;
  gap: 8px;
}

.pill-btn {
  border: none;
  border-radius: 12px;
  padding: 10px 14px;
  font-weight: 800;
  font-size: 13px;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.2s ease, opacity 0.15s ease;
}

.pill-btn.primary {
  background: linear-gradient(135deg, #6d7cff, #4f46e5);
  color: #ffffff;
  box-shadow: 0 10px 22px rgba(79, 70, 229, 0.28);
}

.pill-btn.ghost {
  background: #f8fafc;
  color: #475569;
  border: 1px solid #e5e7eb;
}

.pill-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.danger-row {
  display: flex;
  justify-content: center;
  gap: 6px;
  padding: 16px 0;
}

.empty-state {
  text-align: center;
  padding: 24px 0 12px;
  color: #6b7280;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.empty-illustration {
  font-size: 32px;
}

.empty-title {
  margin: 0;
  font-weight: 800;
  color: #0f172a;
}

.empty-sub {
  margin: 0;
  font-size: 13px;
  color: #9ca3af;
}

@media (max-width: 768px) {
  .create-row,
  .edit-row {
    grid-template-columns: 1fr;
  }

  .stage-item {
    grid-template-columns: 1fr;
    align-items: flex-start;
  }

  .stage-actions {
    justify-content: flex-start;
  }
}
</style>
