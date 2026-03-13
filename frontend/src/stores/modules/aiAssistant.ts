import { computed, ref } from "vue";
import { defineStore } from "pinia";
import dayjs from "dayjs";
import { ElMessage } from "element-plus";

import {
  aiAPI,
  type AIChatMessage,
  type AIChatSendPayload,
  type AIChatScope,
  type AIChatSession,
} from "@/api/modules/ai";
import { useAuthStore } from "@/stores/modules/auth";

const STORAGE_KEY = "ai-chat-state";

type SessionMessageMap = Record<number, AIChatMessage[]>;

function todayString() {
  return dayjs().format("YYYY-MM-DD");
}

function resolveWeekStart(value: string) {
  const base = dayjs(value);
  const weekday = base.day();
  const diff = (weekday + 6) % 7;
  return base.subtract(diff, "day").format("YYYY-MM-DD");
}

function normalizeDateForScope(scope: AIChatScope, value: string) {
  if (scope === "week") return resolveWeekStart(value);
  if (scope === "month") return dayjs(value).startOf("month").format("YYYY-MM-DD");
  return value;
}

export const useAIAssistantStore = defineStore("ai-assistant", () => {
  const authStore = useAuthStore();
  const scope = ref<AIChatScope>("global");
  const selectedDate = ref(todayString());
  const selectedStageId = ref<number | null>(null);
  const currentSessionId = ref<number | null>(null);

  const sessions = ref<AIChatSession[]>([]);
  const messagesBySession = ref<SessionMessageMap>({});
  const inputText = ref("");

  const initializing = ref(false);
  const sessionsLoading = ref(false);
  const messagesLoading = ref(false);
  const sending = ref(false);

  const currentSession = computed(() =>
    sessions.value.find((item) => item.id === currentSessionId.value) || null,
  );
  const currentMessages = computed(() =>
    currentSessionId.value ? messagesBySession.value[currentSessionId.value] || [] : [],
  );
  const hasMessages = computed(() => currentMessages.value.length > 0);

  function persistState() {
    sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        scope: scope.value,
        selectedDate: selectedDate.value,
        selectedStageId: selectedStageId.value,
        currentSessionId: currentSessionId.value,
      }),
    );
  }

  function restoreState() {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      scope.value = parsed.scope || "global";
      selectedDate.value = parsed.selectedDate || todayString();
      selectedStageId.value = parsed.selectedStageId ?? null;
      currentSessionId.value = parsed.currentSessionId ?? null;
    } catch {
      // ignore broken cache
    }
  }

  async function init() {
    if (initializing.value) return;
    initializing.value = true;
    if (!(await ensureAuthenticated())) {
      initializing.value = false;
      return;
    }
    restoreState();
    await loadSessions();
    if (currentSessionId.value) {
      await openSession(currentSessionId.value);
    } else if (sessions.value.length) {
      await openSession(sessions.value[0].id);
    }
    persistState();
    initializing.value = false;
  }

  async function loadSessions() {
    if (!(await ensureAuthenticated())) return;
    sessionsLoading.value = true;
    try {
      const response: any = await aiAPI.fetchSessions();
      if (response?.success) {
        sessions.value = Array.isArray(response.data) ? response.data : [];
        if (
          currentSessionId.value &&
          !sessions.value.some((item) => item.id === currentSessionId.value)
        ) {
          currentSessionId.value = sessions.value[0]?.id ?? null;
        }
      }
    } catch (error) {
      console.error("加载 AI 会话失败:", error);
    } finally {
      sessionsLoading.value = false;
      persistState();
    }
  }

  async function openSession(sessionId: number) {
    if (!(await ensureAuthenticated())) return;
    currentSessionId.value = sessionId;
    persistState();
    if (messagesBySession.value[sessionId]) return;
    messagesLoading.value = true;
    try {
      const response: any = await aiAPI.fetchSessionMessages(sessionId);
      if (response?.success) {
        messagesBySession.value = {
          ...messagesBySession.value,
          [sessionId]: Array.isArray(response.data?.messages)
            ? response.data.messages
            : [],
        };
      }
    } catch (error) {
      ElMessage.error("加载会话消息失败");
    } finally {
      messagesLoading.value = false;
    }
  }

  function setScope(value: AIChatScope) {
    scope.value = value;
    persistState();
  }

  function setDate(value: string) {
    selectedDate.value = value;
    persistState();
  }

  function setStage(value: number | null) {
    selectedStageId.value = value;
    persistState();
  }

  function newChat() {
    currentSessionId.value = null;
    inputText.value = "";
    persistState();
  }

  function buildPayload(content: string): AIChatSendPayload {
    const payload: AIChatSendPayload = {
      content,
      scope: "global",
    };
    if (currentSessionId.value) {
      payload.session_id = currentSessionId.value;
    }
    return payload;
  }

  async function sendCurrentMessage() {
    const content = inputText.value.trim();
    if (!content || sending.value) return;
    if (!(await ensureAuthenticated())) return;

    sending.value = true;
    try {
      const response: any = await aiAPI.sendMessage(buildPayload(content));
      if (!response?.success) {
        throw new Error(response?.message || "发送失败");
      }

      const payload = response.data;
      const session = payload.session as AIChatSession;
      const nextMessages = [
        payload.user_message as AIChatMessage,
        payload.assistant_message as AIChatMessage,
      ];

      currentSessionId.value = session.id;
      inputText.value = "";
      messagesBySession.value = {
        ...messagesBySession.value,
        [session.id]: [...(messagesBySession.value[session.id] || []), ...nextMessages],
      };

      sessions.value = [
        session,
        ...sessions.value.filter((item) => item.id !== session.id),
      ];
      persistState();
    } catch (error: any) {
      ElMessage.error(error.message || "发送失败");
    } finally {
      sending.value = false;
    }
  }

  async function ensureAuthenticated() {
    const accessToken = localStorage.getItem("access_token");
    const refreshToken = localStorage.getItem("refresh_token");
    if (!accessToken && !refreshToken) {
      ElMessage.error("登录已过期，请重新登录");
      authStore.logout();
      return false;
    }

    if (!accessToken && refreshToken) {
      const refreshed = await authStore.refresh();
      if (!refreshed) {
        ElMessage.error("登录已过期，请重新登录");
        return false;
      }
      return true;
    }

    return true;
  }

  return {
    scope,
    selectedDate,
    selectedStageId,
    currentSessionId,
    sessions,
    currentSession,
    currentMessages,
    inputText,
    hasMessages,
    initializing,
    sessionsLoading,
    messagesLoading,
    sending,
    init,
    loadSessions,
    openSession,
    setScope,
    setDate,
    setStage,
    newChat,
    sendCurrentMessage,
  };
});
