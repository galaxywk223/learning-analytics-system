import { ElMessage } from "element-plus";
import type { MessageHandler, MessageOptions } from "element-plus";

type MessageInput = string | MessageOptions | undefined;

const DEFAULT_OPTIONS: MessageOptions = {
  duration: 2200,
  grouping: true,
  showClose: false,
};

const MESSAGE_TYPES = ["success", "warning", "info", "error"] as const;
const DEDUP_WINDOW = 800;

let lastSignature = "";
let lastShownAt = 0;

const noopHandler: MessageHandler = {
  close: () => void 0,
};

function normalize(options: MessageInput): MessageOptions {
  if (!options) {
    return { message: "" };
  }
  if (typeof options === "string") {
    return { message: options };
  }
  return options;
}

function shouldSkip(signature: string): boolean {
  const now = Date.now();
  if (signature === lastSignature && now - lastShownAt < DEDUP_WINDOW) {
    return true;
  }
  lastSignature = signature;
  lastShownAt = now;
  return false;
}

function patchTypedMethod(type: (typeof MESSAGE_TYPES)[number]) {
  const origin = ElMessage[type];
  if (!origin) return;

  ElMessage[type] = ((options?: MessageInput) => {
    const normalized = {
      ...DEFAULT_OPTIONS,
      ...normalize(options),
      type,
    };
    const signature = `${type}:${normalized.message ?? ""}`;
    if (shouldSkip(signature)) {
      return noopHandler;
    }
    ElMessage.closeAll();
    return origin(normalized);
  }) as typeof origin;
}

export function setupMessageDefaults() {
  if ((ElMessage as any).__appMessagePatched) {
    return;
  }

  MESSAGE_TYPES.forEach(patchTypedMethod);

  (ElMessage as any).__appMessagePatched = true;
}
