<template>
  <!-- eslint-disable vue/no-v-html -->
  <div class="ai-chat-view">
    <PageContainer
      :title="{ icon: 'lucide:sparkles', text: '智能规划' }"
      subtitle="基于你的学习数据，帮你梳理重点、拆解问题和安排下一步。"
      fill-height
      custom-class="ai-chat-page"
      max-width="wide"
      density="compact"
    >
      <template #actions>
        <button
          type="button"
          class="page-tool-btn mobile-only"
          @click="sidebarOpen = !sidebarOpen"
        >
          <Icon :icon="sidebarOpen ? 'lucide:panel-left-close' : 'lucide:panel-left-open'" />
          <span>{{ sidebarOpen ? "收起历史" : "历史对话" }}</span>
        </button>
        <button type="button" class="page-primary-btn" @click="handleNewChat">
          <Icon icon="lucide:plus" />
          <span>新对话</span>
        </button>
      </template>

      <div class="planner-shell">
        <aside class="planner-sidebar" :class="{ open: sidebarOpen }">
          <div class="planner-sidebar__header">
            <strong>历史对话</strong>
            <span>保留最近的规划和追问，方便回看。</span>
          </div>

          <div class="session-list" v-loading="sessionsLoading">
            <button
              v-for="session in sessions"
              :key="session.id"
              type="button"
              class="session-item"
              :class="{ active: currentSession?.id === session.id }"
              @click="handleOpenSession(session.id)"
            >
              <strong>{{ session.title }}</strong>
              <span>{{ sessionPreview(session) }}</span>
            </button>
            <div v-if="!sessions.length && !sessionsLoading" class="session-empty">
              还没有历史对话
            </div>
          </div>
        </aside>

        <section class="planner-main">
          <header class="planner-main__header">
            <div class="planner-main__title">
              <strong>{{ currentSession ? currentSession.title : "开始一段新的规划对话" }}</strong>
              <span>{{ currentSessionSummary }}</span>
            </div>
            <div class="planner-main__badge">全局概览已开启</div>
          </header>

          <div ref="threadRef" class="chat-thread" v-loading="messagesLoading">
            <div class="thread-inner">
              <template v-if="currentMessages.length">
                <article
                  v-for="message in currentMessages"
                  :key="message.id"
                  class="message-row"
                  :class="message.role"
                >
                  <div v-if="message.role === 'assistant'" class="message-avatar assistant">
                    <Icon icon="lucide:sparkles" />
                  </div>
                  <div class="message-block">
                    <div
                      class="message-surface markdown-body"
                      :class="message.role"
                      v-html="renderMessage(message)"
                    ></div>
                    <div v-if="message.role === 'assistant'" class="message-meta">
                      <span>{{ message.meta?.generation_label || fallbackGenerationLabel(message.generation_mode) }}</span>
                      <span>{{ scopeLabelMap[message.scope] }}</span>
                      <span>{{ formatDateTime(message.created_at) }}</span>
                    </div>
                  </div>
                </article>
              </template>

              <section v-else class="empty-state">
                <div class="empty-state__badge">智能规划</div>
                <h2>从一个具体问题开始</h2>
                <p>它会结合你的学习数据，直接给出判断、建议和下一步动作。</p>
                <div class="starter-grid">
                  <button
                    v-for="prompt in starterPrompts"
                    :key="prompt"
                    type="button"
                    class="starter-card"
                    @click="inputTextValue = prompt"
                  >
                    {{ prompt }}
                  </button>
                </div>
              </section>

              <article v-if="sending" class="message-row assistant">
                <div class="message-avatar assistant">
                  <Icon icon="lucide:sparkles" />
                </div>
                <div class="message-block">
                  <div class="message-surface assistant thinking-surface">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </article>
            </div>
          </div>

          <footer class="chat-composer">
            <div class="composer-card">
              <textarea
                v-model="inputTextValue"
                class="composer-input"
                rows="1"
                placeholder="直接提问，比如：我下周最该砍掉什么？"
                @keydown="handleComposerKeydown"
              ></textarea>
              <div class="composer-footer">
                <span class="composer-hint">会优先使用全局概览，再补充必要的时间窗口信息</span>
                <button
                  type="button"
                  class="page-primary-btn send-btn"
                  :disabled="sending || !inputTextValue.trim()"
                  @click="handleSend"
                >
                  <Icon icon="lucide:send-horizontal" />
                  <span>{{ sending ? "发送中..." : "发送" }}</span>
                </button>
              </div>
            </div>
          </footer>
        </section>
      </div>
    </PageContainer>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import dayjs from "dayjs";
import { marked } from "marked";
import DOMPurify from "dompurify";
import { Icon } from "@iconify/vue";

import PageContainer from "@/components/layout/PageContainer.vue";
import { useAIAssistantStore } from "@/stores/modules/aiAssistant";
import type { AIChatMessage, AIChatScope, AIChatSession } from "@/api/modules/ai";

marked.setOptions({ breaks: true, gfm: true });

const scopeLabelMap: Record<AIChatScope, string> = {
  global: "全局",
  day: "日度",
  week: "周度",
  month: "月度",
  stage: "阶段",
};

const starterPrompts = [
  "我这周最大的问题到底是什么？",
  "如果下周只能抓三件事，你建议我抓什么？",
  "为什么我最近看起来很忙，但结果不够好？",
  "按我现在的数据，最该砍掉哪个方向？",
];

const aiStore = useAIAssistantStore();
const sidebarOpen = ref(false);
const threadRef = ref<HTMLElement | null>(null);
const inputTextValue = computed<string>({
  get: () => aiStore.inputText,
  set: (value) => {
    aiStore.inputText = value;
  },
});

const sessions = computed(() => aiStore.sessions);
const currentSession = computed(() => aiStore.currentSession);
const currentMessages = computed(() => aiStore.currentMessages);
const sessionsLoading = computed(() => aiStore.sessionsLoading);
const messagesLoading = computed(() => aiStore.messagesLoading);
const sending = computed(() => aiStore.sending);

const currentSessionSummary = computed(() => {
  if (!currentSession.value) {
    return "从一个具体问题开始，AI 会结合你的学习数据给出建议。";
  }

  return sessionPreview(currentSession.value);
});

function renderMarkdown(text?: string) {
  if (!text) return "";
  return DOMPurify.sanitize(marked.parse(text) as string);
}

function renderMessage(message: AIChatMessage) {
  return renderMarkdown(message.content);
}

function fallbackGenerationLabel(mode?: string | null) {
  return mode === "llm_enhanced" ? "LLM增强" : "规则兜底";
}

function formatDateTime(value?: string | null) {
  if (!value) return "";
  return dayjs(value).format("MM-DD HH:mm");
}

function sessionPreview(session: AIChatSession) {
  return `${scopeLabelMap[session.scope]} · ${formatDateTime(session.last_message_at)}`;
}

async function handleSend() {
  await aiStore.sendCurrentMessage();
}

async function handleOpenSession(sessionId: number) {
  sidebarOpen.value = false;
  await aiStore.openSession(sessionId);
}

function handleNewChat() {
  aiStore.newChat();
  sidebarOpen.value = false;
}

function handleComposerKeydown(event: KeyboardEvent) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    void handleSend();
  }
}

async function scrollToBottom() {
  await nextTick();
  const el = threadRef.value;
  if (!el) return;
  el.scrollTop = el.scrollHeight;
}

watch(
  () => [currentMessages.value.length, sending.value],
  () => {
    void scrollToBottom();
  },
);

onMounted(async () => {
  await aiStore.init();
  await scrollToBottom();
});
</script>

<style scoped lang="scss">
.ai-chat-view {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

:deep(.ai-chat-page) {
  flex: 1;
  min-height: 0;
}

:deep(.ai-chat-page .page-body) {
  flex: 1;
  min-height: 0;
  gap: 0;
}

.page-primary-btn,
.page-tool-btn,
.session-item,
.starter-card {
  border: none;
  cursor: pointer;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    background 0.18s ease,
    border-color 0.18s ease,
    opacity 0.18s ease;
}

.page-primary-btn:hover,
.page-tool-btn:hover,
.session-item:hover,
.starter-card:hover {
  transform: translateY(-1px);
}

.page-primary-btn,
.page-tool-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 42px;
  padding: 0 16px;
  border-radius: 14px;
  font-size: 0.92rem;
  font-weight: 700;
}

.page-primary-btn {
  background: var(--brand-primary);
  color: white;
  box-shadow: var(--shadow-1);
}

.page-primary-btn :deep(svg),
.page-tool-btn :deep(svg),
.message-avatar :deep(svg) {
  width: 18px;
  height: 18px;
}

.page-tool-btn {
  border: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  color: var(--text-secondary);
}

.planner-shell {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 18px;
  flex: 1;
  min-height: 0;
}

.planner-sidebar,
.planner-main {
  min-height: 0;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--bg-elevated) 94%, white) 0%, var(--bg-surface) 100%);
  box-shadow: var(--shadow-1);
}

.planner-sidebar {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.planner-sidebar__header {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 18px 18px 14px;
  border-bottom: 1px solid var(--border-subtle);
}

.planner-sidebar__header strong,
.planner-main__title strong {
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 800;
}

.planner-sidebar__header span,
.planner-main__title span {
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.55;
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
  overflow: auto;
  padding: 14px;
}

.session-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 13px 14px;
  border-radius: 16px;
  border: 1px solid transparent;
  text-align: left;
  background: transparent;
}

.session-item strong {
  color: var(--text-primary);
  font-size: 0.92rem;
  line-height: 1.45;
}

.session-item span,
.session-empty,
.message-meta,
.composer-hint {
  color: var(--text-muted);
  font-size: 0.82rem;
}

.session-item.active {
  border-color: color-mix(in srgb, var(--brand-primary) 18%, var(--border-subtle));
  background: color-mix(in srgb, var(--brand-primary) 9%, var(--bg-surface));
}

.session-empty {
  padding: 18px 10px;
}

.planner-main {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  min-height: 0;
  overflow: hidden;
}

.planner-main__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--border-subtle);
  background: color-mix(in srgb, var(--bg-elevated) 76%, transparent);
}

.planner-main__title {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.planner-main__badge,
.empty-state__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  padding: 7px 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--brand-primary) 12%, var(--bg-surface));
  color: var(--brand-primary);
  font-size: 0.78rem;
  font-weight: 800;
}

.chat-thread {
  min-height: 0;
  overflow: auto;
  overscroll-behavior: contain;
}

.thread-inner {
  width: min(900px, calc(100% - 40px));
  margin: 0 auto;
  padding: 28px 0 34px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.message-row {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}

.message-row.user {
  grid-template-columns: minmax(0, 1fr);
  justify-items: end;
}

.message-avatar {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-avatar.assistant {
  background: color-mix(in srgb, var(--brand-primary) 14%, var(--bg-surface));
  color: var(--brand-primary);
}

.message-block {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message-row.user .message-block {
  align-items: flex-end;
}

.message-surface {
  max-width: min(760px, 100%);
  color: var(--text-primary);
  line-height: 1.8;
}

.message-surface.assistant {
  padding: 18px 20px;
  border-radius: 20px;
  border: 1px solid var(--border-subtle);
  background: color-mix(in srgb, var(--bg-elevated) 92%, white);
  box-shadow: var(--shadow-1);
}

.message-surface.user {
  padding: 14px 18px;
  border-radius: 18px;
  background: color-mix(in srgb, var(--brand-primary) 11%, var(--bg-surface));
  border: 1px solid color-mix(in srgb, var(--brand-primary) 16%, var(--border-subtle));
}

.message-meta {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 10px;
}

.empty-state {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 14px;
  padding: 24px 0;
}

.empty-state h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: clamp(1.8rem, 3.2vw, 2.6rem);
  line-height: 1.12;
  letter-spacing: -0.04em;
}

.empty-state p {
  margin: 0;
  max-width: 42rem;
  color: var(--text-secondary);
  font-size: 1rem;
  line-height: 1.75;
}

.starter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 6px;
}

.starter-card {
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid var(--border-subtle);
  text-align: left;
  background: color-mix(in srgb, var(--bg-elevated) 90%, white);
  color: var(--text-primary);
  line-height: 1.7;
  box-shadow: var(--shadow-1);
}

.chat-composer {
  padding: 0 20px 20px;
}

.composer-card {
  width: min(900px, 100%);
  margin: 0 auto;
  padding: 16px 16px 12px;
  border-radius: 22px;
  border: 1px solid var(--border-subtle);
  background: color-mix(in srgb, var(--bg-elevated) 94%, white);
  box-shadow: var(--shadow-1);
}

.composer-input {
  width: 100%;
  min-height: 92px;
  max-height: 220px;
  resize: vertical;
  border: none;
  outline: none;
  background: transparent;
  color: var(--text-primary);
  font: inherit;
  font-size: 0.98rem;
  line-height: 1.8;
}

.composer-input::placeholder {
  color: var(--text-muted);
}

.composer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 8px;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.thinking-surface {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 54px;
}

.thinking-surface span {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--brand-primary) 58%, white);
  animation: blink 1.2s infinite ease-in-out;
}

.thinking-surface span:nth-child(2) {
  animation-delay: 0.15s;
}

.thinking-surface span:nth-child(3) {
  animation-delay: 0.3s;
}

.mobile-only {
  display: none;
}

:deep(.markdown-body) {
  color: inherit;
}

:deep(.markdown-body p:first-child) {
  margin-top: 0;
}

:deep(.markdown-body p:last-child) {
  margin-bottom: 0;
}

:deep(.markdown-body ul),
:deep(.markdown-body ol) {
  padding-left: 1.35em;
}

:deep(.markdown-body code) {
  background: color-mix(in srgb, var(--brand-primary) 10%, var(--bg-surface));
  padding: 2px 6px;
  border-radius: 6px;
}

@keyframes blink {
  0%,
  80%,
  100% {
    opacity: 0.25;
    transform: translateY(0);
  }

  40% {
    opacity: 1;
    transform: translateY(-2px);
  }
}

@media (max-width: 1120px) {
  .planner-shell {
    grid-template-columns: 1fr;
  }

  .planner-sidebar {
    display: none;
  }

  .planner-sidebar.open {
    display: flex;
    max-height: 42vh;
  }

  .mobile-only {
    display: inline-flex;
  }
}

@media (max-width: 760px) {
  .planner-main__header,
  .chat-composer {
    padding-left: 14px;
    padding-right: 14px;
  }

  .planner-main__header {
    align-items: flex-start;
    flex-direction: column;
  }

  .thread-inner {
    width: min(100%, calc(100% - 28px));
    padding-top: 22px;
  }

  .starter-grid {
    grid-template-columns: 1fr;
  }

  .composer-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .send-btn {
    width: 100%;
  }
}
</style>
