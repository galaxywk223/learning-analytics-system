/**
 * 专注计时器 composable
 * 处理计时器的逻辑和状态管理
 */
import { ref, onUnmounted, type Ref } from "vue";
import type { FocusFormData } from "@/types";

const FOCUS_STATE_KEY = "focus_session_state";

// 存储的状态类型
interface SavedState {
  formData: FocusFormData;
  isTimerRunning: boolean;
  isPaused: boolean;
  elapsedSeconds: number;
  startTime: string | null;
  pauseTime: string | null;
}

// 返回值类型
interface UseFocusTimerReturn {
  // 状态
  isTimerRunning: Ref<boolean>;
  isPaused: Ref<boolean>;
  elapsedSeconds: Ref<number>;
  startTime: Ref<Date | null>;
  pauseTime: Ref<Date | null>;

  // 方法
  startTimer: (formData: FocusFormData) => void;
  pauseTimer: (formData: FocusFormData) => void;
  resumeTimer: (formData: FocusFormData) => void;
  stopTimer: () => number;
  cancelSession: () => void;
  completeSession: () => number;
  restoreState: () => FocusFormData | null;
  clearState: () => void;
  resetTimer: () => void;
  saveState: (formData: FocusFormData) => void;
}

export function useFocusTimer(): UseFocusTimerReturn {
  // 计时器状态
  const isTimerRunning: Ref<boolean> = ref(false);
  const isPaused: Ref<boolean> = ref(false);
  const elapsedSeconds: Ref<number> = ref(0);
  const startTime: Ref<Date | null> = ref(null);
  const pauseTime: Ref<Date | null> = ref(null);
  const timerInterval: Ref<NodeJS.Timeout | number | null> = ref(null);

  // 保存状态到 localStorage
  const saveState = (formData: FocusFormData): void => {
    const state: SavedState = {
      formData,
      isTimerRunning: isTimerRunning.value,
      isPaused: isPaused.value,
      elapsedSeconds: elapsedSeconds.value,
      startTime: startTime.value ? startTime.value.toISOString() : null,
      pauseTime: pauseTime.value ? pauseTime.value.toISOString() : null,
    };
    localStorage.setItem(FOCUS_STATE_KEY, JSON.stringify(state));
    console.log("已保存专注状态:", state);
  };

  // 从 localStorage 恢复状态
  const restoreState = (): FocusFormData | null => {
    try {
      const savedState = localStorage.getItem(FOCUS_STATE_KEY);
      if (savedState) {
        const state: SavedState = JSON.parse(savedState);
        console.log("恢复的专注状态:", state);

        isTimerRunning.value = state.isTimerRunning || false;
        isPaused.value = state.isPaused || false;
        elapsedSeconds.value = state.elapsedSeconds || 0;

        if (state.startTime) {
          startTime.value = new Date(state.startTime);
        }
        if (state.pauseTime) {
          pauseTime.value = new Date(state.pauseTime);
        }

        // 如果计时器正在运行，需要计算实际经过的时间
        if (isTimerRunning.value && startTime.value) {
          const now = new Date();
          const actualElapsed = Math.floor(
            (now.getTime() - startTime.value.getTime()) / 1000
          );
          elapsedSeconds.value = actualElapsed;
          startTimerInterval();
        }

        return state.formData;
      }
    } catch (error) {
      console.error("恢复专注状态失败:", error);
      clearState();
    }
    return null;
  };

  // 清除状态
  const clearState = (): void => {
    localStorage.removeItem(FOCUS_STATE_KEY);
    resetTimer();
  };

  // 重置计时器
  const resetTimer = (): void => {
    isTimerRunning.value = false;
    isPaused.value = false;
    elapsedSeconds.value = 0;
    startTime.value = null;
    pauseTime.value = null;
    stopTimerInterval();
  };

  // 开始计时器间隔
  const startTimerInterval = (): void => {
    if (timerInterval.value) {
      clearInterval(timerInterval.value);
    }

    timerInterval.value = setInterval(() => {
      if (isTimerRunning.value && startTime.value) {
        const now = new Date();
        elapsedSeconds.value = Math.floor(
          (now.getTime() - startTime.value.getTime()) / 1000
        );
      }
    }, 1000);
  };

  // 停止计时器间隔
  const stopTimerInterval = (): void => {
    if (timerInterval.value) {
      clearInterval(timerInterval.value);
      timerInterval.value = null;
    }
  };

  // 开始计时
  const startTimer = (formData: FocusFormData): void => {
    const now = new Date();
    startTime.value = now;
    isTimerRunning.value = true;
    isPaused.value = false;
    elapsedSeconds.value = 0;

    startTimerInterval();
    saveState(formData);

    console.log("开始专注计时:", now);
  };

  // 暂停计时
  const pauseTimer = (formData: FocusFormData): void => {
    if (isTimerRunning.value) {
      pauseTime.value = new Date();
      isTimerRunning.value = false;
      isPaused.value = true;

      stopTimerInterval();
      saveState(formData);

      console.log("暂停专注计时:", pauseTime.value);
    }
  };

  // 恢复计时
  const resumeTimer = (formData: FocusFormData): void => {
    if (isPaused.value && pauseTime.value && startTime.value) {
      const now = new Date();
      const pauseDuration = now.getTime() - pauseTime.value.getTime();

      // 调整开始时间，排除暂停时间
      startTime.value = new Date(startTime.value.getTime() + pauseDuration);

      isTimerRunning.value = true;
      isPaused.value = false;
      pauseTime.value = null;

      startTimerInterval();
      saveState(formData);

      console.log("恢复专注计时");
    }
  };

  // 停止计时
  const stopTimer = (): number => {
    const finalElapsed = elapsedSeconds.value;
    stopTimerInterval();
    return finalElapsed;
  };

  // 取消会话
  const cancelSession = (): void => {
    clearState();
    console.log("已取消专注会话");
  };

  // 完成会话
  const completeSession = (): number => {
    const finalElapsed = elapsedSeconds.value;
    clearState();
    return finalElapsed;
  };

  // 组件销毁时清理
  onUnmounted(() => {
    stopTimerInterval();
  });

  return {
    // 状态
    isTimerRunning,
    isPaused,
    elapsedSeconds,
    startTime,
    pauseTime,

    // 方法
    startTimer,
    pauseTimer,
    resumeTimer,
    stopTimer,
    cancelSession,
    completeSession,
    restoreState,
    clearState,
    resetTimer,
    saveState,
  };
}
