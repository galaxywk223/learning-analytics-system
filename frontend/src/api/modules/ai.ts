import request from "@/utils/request";

export type AIChatScope = "global" | "day" | "week" | "month" | "stage";
export type AIMessageRole = "user" | "assistant";
export type AIGenerationMode = "llm_enhanced" | "rule_fallback";

export interface AIChatSendPayload {
  session_id?: number;
  scope: AIChatScope;
  date?: string;
  stage_id?: number;
  content: string;
}

export interface AIChatSession {
  id: number;
  user_id: number;
  title: string;
  scope: AIChatScope;
  scope_reference?: number | null;
  date_reference?: string | null;
  created_at: string;
  updated_at: string;
  last_message_at: string;
}

export interface AIChatMessage {
  id: number;
  session_id: number;
  user_id: number;
  role: AIMessageRole;
  content: string;
  scope: AIChatScope;
  scope_reference?: number | null;
  date_reference?: string | null;
  generation_mode?: AIGenerationMode | null;
  model_name?: string | null;
  meta?: Record<string, any>;
  created_at: string;
}

export interface AIChatMessageResponse {
  session: AIChatSession;
  user_message: AIChatMessage;
  assistant_message: AIChatMessage;
  meta: {
    generation_mode: AIGenerationMode;
    generation_label: string;
    model_name?: string | null;
    used_modules: string[];
    scope: AIChatScope;
    period_label: string;
  };
}

export const aiAPI = {
  sendMessage(data: AIChatSendPayload) {
    return request({
      url: "/api/ai/chat/messages",
      method: "post",
      data,
      timeout: 180000,
    });
  },
  fetchSessions() {
    return request({
      url: "/api/ai/chat/sessions",
      method: "get",
    });
  },
  fetchSessionMessages(sessionId: number) {
    return request({
      url: `/api/ai/chat/sessions/${sessionId}/messages`,
      method: "get",
      timeout: 120000,
    });
  },
};
