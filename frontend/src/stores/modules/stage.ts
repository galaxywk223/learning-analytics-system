/**
 * 阶段状态管理
 */
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { stageAPI } from "@/api";
import { ElMessage } from "element-plus";

type Stage = {
  id: number | string;
  name: string;
  [key: string]: any;
};

export const useStageStore = defineStore("stage", () => {
  const stages = ref<Stage[]>([]);
  const activeStage = ref<Stage | null>(null);
  const loading = ref(false);
  const lastFetched = ref(0);
  let pendingFetch: Promise<void> | null = null;

  function restoreActiveStage(list: Stage[]) {
    const savedId = localStorage.getItem("active_stage_id");
    if (savedId) {
      const found = list.find((item) => `${item.id}` === savedId);
      if (found) {
        activeStage.value = found;
        return;
      }
    }
    activeStage.value = list[0] || null;
    if (activeStage.value) {
      localStorage.setItem("active_stage_id", `${activeStage.value.id}`);
    } else {
      localStorage.removeItem("active_stage_id");
    }
  }

  async function fetchStages(force = false) {
    if (loading.value) {
      return pendingFetch ?? Promise.resolve();
    }
    if (!force && Date.now() - lastFetched.value < 60_000 && stages.value.length) {
      return Promise.resolve();
    }

    loading.value = true;
    pendingFetch = (async () => {
      try {
        const response = (await stageAPI.getAll()) as any;
        if (response?.success && Array.isArray(response.stages)) {
          stages.value = response.stages;
          restoreActiveStage(stages.value);
          lastFetched.value = Date.now();
        }
      } catch (error) {
        console.error("获取阶段失败:", error);
      } finally {
        loading.value = false;
        pendingFetch = null;
      }
    })();

    return pendingFetch;
  }

  async function ensureStages(force = false) {
    if (!force && stages.value.length && !loading.value) {
      return;
    }
    return fetchStages(force);
  }

  async function createStage(data: any) {
    try {
      const response = (await stageAPI.create(data)) as any;
      if (response?.success && response.stage) {
        stages.value.unshift(response.stage);
        if (!activeStage.value) {
          setActiveStage(response.stage);
        }
        ElMessage.success(response.message || "阶段创建成功");
        return true;
      }
      return false;
    } catch (error) {
      console.error("创建阶段失败:", error);
      return false;
    }
  }

  async function updateStage(id: number, data: any) {
    try {
      const response = (await stageAPI.update(id, data)) as any;
      if (response?.success && response.stage) {
        const index = stages.value.findIndex((s) => s.id === id);
        if (index !== -1) {
          stages.value[index] = response.stage;
        }
        if (activeStage.value?.id === id) {
          activeStage.value = response.stage;
          localStorage.setItem("active_stage_id", `${response.stage.id}`);
        }
        ElMessage.success(response.message || "阶段更新成功");
        return true;
      }
      return false;
    } catch (error) {
      console.error("更新阶段失败:", error);
      return false;
    }
  }

  async function deleteStage(id: number) {
    try {
      const response = (await stageAPI.delete(id)) as any;
      if (response?.success) {
        stages.value = stages.value.filter((s) => s.id !== id);
        if (activeStage.value?.id === id) {
          restoreActiveStage(stages.value);
        }
        ElMessage.success(response.message || "阶段已删除");
        return true;
      }
      return false;
    } catch (error) {
      console.error("删除阶段失败:", error);
      return false;
    }
  }

  function setActiveStage(stage: Stage) {
    activeStage.value = stage;
    localStorage.setItem("active_stage_id", `${stage.id}`);
  }

  const hasStages = computed(() => stages.value.length > 0);

  return {
    stages,
    activeStage,
    loading,
    lastFetched,
    hasStages,
    fetchStages,
    ensureStages,
    createStage,
    updateStage,
    deleteStage,
    setActiveStage,
  };
});
