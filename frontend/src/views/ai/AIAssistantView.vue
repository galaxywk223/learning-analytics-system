<template>
  <!-- eslint-disable vue/no-v-html -->
  <div class="ai-chat-view">
    <PageContainer custom-class="ai-chat-page">
      <div class="gpt-shell">
        <aside class="gpt-sidebar" :class="{ open: sidebarOpen }">
          <div class="sidebar-header">
            <button class="new-chat-btn" @click="handleNewChat">
              <span class="new-chat-btn__icon">+</span>
              <span>新对话</span>
            </button>
          </div>

          <div class="sidebar-section">
            <span class="sidebar-label">历史对话</span>
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
          </div>
        </aside>

        <section class="gpt-main">
          <header class="chat-topbar">
            <button class="topbar-btn mobile-only" @click="sidebarOpen = !sidebarOpen">
              {{ sidebarOpen ? "关闭历史" : "历史" }}
            </button>
            <div class="topbar-title">
              <strong>{{ currentSession ? currentSession.title : "智能规划" }}</strong>
              <span>默认已注入全局概览，AI 会自己决定还需要哪些时间窗口数据。</span>
            </div>
            <div class="topbar-chip">GPT 模式</div>
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
                    AI
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
                <h1>今天想直接问什么？</h1>
                <p>
                  它会先看你的聚合学习数据，再自己补足需要的时间窗口信息，最后像 GPT 一样直接回答。
                </p>
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
                <div class="message-avatar assistant">AI</div>
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
                <span class="composer-hint">全局概览上下文已开启</span>
                <button
                  class="send-btn"
                  :disabled="sending || !inputTextValue.trim()"
                  @click="handleSend"
                >
                  {{ sending ? "发送中..." : "发送" }}
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
  min-height: 100%;
}

:deep(.ai-chat-page.page-container) {
  max-width: 1520px;
  height: 100vh;
  padding: 12px 20px 20px;
  box-sizing: border-box;
}

:deep(.ai-chat-page .page-body) {
  gap: 0;
  height: 100%;
}

.gpt-shell {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 0;
  height: 100%;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 28px;
  overflow: hidden;
  background:
    radial-gradient(circle at top, rgba(120, 139, 255, 0.08), transparent 32%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.01)),
    #12192b;
  box-shadow: 0 28px 60px -42px rgba(0, 0, 0, 0.72);
}

.gpt-sidebar {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.015), rgba(255, 255, 255, 0.01)),
    #101727;
}

.sidebar-header {
  padding: 18px;
  position: sticky;
  top: 0;
  z-index: 2;
  background:
    linear-gradient(180deg, rgba(16, 23, 39, 0.96), rgba(16, 23, 39, 0.92)),
    #101727;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.new-chat-btn,
.session-item,
.starter-card,
.topbar-btn,
.send-btn {
  border: none;
  cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease, opacity 0.18s ease;
}

.new-chat-btn {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 13px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
  color: #eef2ff;
  font-weight: 700;
}

.new-chat-btn:hover,
.session-item:hover,
.starter-card:hover,
.topbar-btn:hover,
.send-btn:hover {
  transform: translateY(-1px);
}

.new-chat-btn__icon {
  width: 18px;
  height: 18px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.08);
}

.sidebar-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 2px 14px 16px;
  min-height: 0;
  flex: 1;
}

.sidebar-label {
  padding: 0 6px;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(186, 198, 255, 0.58);
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
  overflow: auto;
  padding-right: 2px;
}

.session-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 16px;
  text-align: left;
  background: transparent;
  color: rgba(225, 232, 255, 0.88);
}

.session-item strong {
  font-size: 14px;
  font-weight: 700;
  line-height: 1.45;
}

.session-item span {
  font-size: 12px;
  color: rgba(169, 179, 210, 0.78);
}

.session-item.active {
  background: rgba(116, 138, 255, 0.12);
  box-shadow: inset 0 0 0 1px rgba(116, 138, 255, 0.12);
}

.session-empty {
  padding: 18px 14px;
  font-size: 14px;
  color: rgba(169, 179, 210, 0.72);
}

.gpt-main {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  min-height: 0;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.012), rgba(255, 255, 255, 0.008)),
    #131b2d;
}

.chat-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 64px;
  padding: 16px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(10, 15, 26, 0.22);
  backdrop-filter: blur(10px);
  position: sticky;
  top: 0;
  z-index: 5;
}

.topbar-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.topbar-title strong {
  color: #f5f7ff;
  font-size: 15px;
  font-weight: 700;
}

.topbar-title span {
  color: rgba(177, 187, 214, 0.78);
  font-size: 13px;
  line-height: 1.45;
}

.topbar-chip,
.topbar-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  color: rgba(225, 232, 255, 0.86);
  font-size: 12px;
  font-weight: 700;
}

.topbar-chip {
  padding: 8px 12px;
  white-space: nowrap;
}

.topbar-btn {
  padding: 8px 12px;
}

.chat-thread {
  min-height: 0;
  overflow: auto;
  overscroll-behavior: contain;
}

.thread-inner {
  width: min(880px, calc(100% - 40px));
  margin: 0 auto;
  padding: 32px 0 40px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.message-row {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  gap: 16px;
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
  font-size: 12px;
  font-weight: 800;
}

.message-avatar.assistant {
  background: linear-gradient(135deg, #4f6df5, #7d5cff);
  color: #fff;
  box-shadow: 0 14px 28px -18px rgba(79, 109, 245, 0.9);
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
  line-height: 1.85;
  color: #eef2ff;
}

.message-surface.assistant {
  padding: 2px 0;
}

.message-surface.user {
  padding: 14px 18px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: 0 12px 28px -26px rgba(0, 0, 0, 0.85);
}

.message-meta {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 12px;
  color: rgba(169, 179, 210, 0.74);
}

.empty-state {
  min-height: calc(100vh - 280px);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 16px;
}

.empty-state__badge {
  width: fit-content;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(116, 138, 255, 0.12);
  color: #aab8ff;
  font-size: 12px;
  font-weight: 800;
}

.empty-state h1 {
  margin: 0;
  color: #f5f7ff;
  font-size: clamp(34px, 4vw, 54px);
  line-height: 1.08;
  letter-spacing: -0.03em;
}

.empty-state p {
  margin: 0;
  max-width: 720px;
  color: rgba(188, 197, 224, 0.84);
  font-size: 16px;
  line-height: 1.8;
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
  text-align: left;
  background: rgba(255, 255, 255, 0.035);
  color: #e8edff;
  line-height: 1.7;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.chat-composer {
  padding: 0 24px 24px;
  position: sticky;
  bottom: 0;
  z-index: 5;
  background: linear-gradient(180deg, rgba(19, 27, 45, 0), rgba(19, 27, 45, 0.88) 18%, rgba(19, 27, 45, 0.98));
}

.composer-card {
  width: min(880px, 100%);
  margin: 0 auto;
  padding: 16px 16px 12px;
  border-radius: 24px;
  background: rgba(20, 28, 47, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: 0 24px 48px -38px rgba(0, 0, 0, 0.9);
}

.composer-input {
  width: 100%;
  min-height: 92px;
  max-height: 220px;
  resize: vertical;
  border: none;
  outline: none;
  background: transparent;
  color: #eff3ff;
  font: inherit;
  font-size: 16px;
  line-height: 1.8;
}

.composer-input::placeholder {
  color: rgba(166, 177, 208, 0.72);
}

.composer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 8px;
}

.composer-hint {
  font-size: 12px;
  color: rgba(166, 177, 208, 0.72);
}

.send-btn {
  min-width: 92px;
  min-height: 44px;
  padding: 0 18px;
  border-radius: 16px;
  background: #ffffff;
  color: #101827;
  font-size: 14px;
  font-weight: 800;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.thinking-surface {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 40px;
}

.thinking-surface span {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: rgba(180, 190, 219, 0.8);
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
  background: rgba(148, 163, 184, 0.14);
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
  :deep(.ai-chat-page.page-container) {
    padding-left: 16px;
    padding-right: 16px;
  }

  .gpt-shell {
    grid-template-columns: 1fr;
  }

  .gpt-sidebar {
    display: none;
  }

  .gpt-sidebar.open {
    display: flex;
    min-height: 280px;
    max-height: 42vh;
    border-right: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }

  .mobile-only {
    display: inline-flex;
  }
}

@media (max-width: 760px) {
  :deep(.ai-chat-page.page-container) {
    padding: 8px 10px 10px;
  }

  .chat-topbar,
  .chat-composer {
    padding-left: 14px;
    padding-right: 14px;
  }

  .thread-inner {
    width: min(100%, calc(100% - 28px));
    padding-top: 24px;
  }

  .starter-grid {
    grid-template-columns: 1fr;
  }

  .chat-topbar {
    align-items: flex-start;
  }

  .topbar-chip {
    display: none;
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
