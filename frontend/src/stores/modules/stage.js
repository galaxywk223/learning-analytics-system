/**
 * 阶段状态管理
 */
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { stageAPI } from "@/api";
import { ElMessage } from "element-plus";

export const useStageStore = defineStore("stage", () => {
  const stages = ref([]);
  const activeStage = ref(null);
  const loading = ref(false);

  // 获取所有阶段
  async function fetchStages() {
    loading.value = true;
    try {
      const response = await stageAPI.getAll();
      if (response.success) {
        stages.value = response.stages;

        // 如果没有活动阶段且有阶段列表,设置第一个为活动阶段
        if (!activeStage.value && stages.value.length > 0) {
          activeStage.value = stages.value[0];
          localStorage.setItem("active_stage_id", activeStage.value.id);
        }
      }
    } catch (error) {
      console.error("获取阶段失败:", error);
    } finally {
      loading.value = false;
    }
  }

  // 创建阶段
  async function createStage(data) {
    try {
      const response = await stageAPI.create(data);
      if (response.success) {
        stages.value.unshift(response.stage);
        ElMessage.success(response.message || "阶段创建成功");
        return true;
      }
      return false;
    } catch (error) {
      console.error("创建阶段失败:", error);
      return false;
    }
  }

  // 更新阶段
  async function updateStage(id, data) {
    try {
      const response = await stageAPI.update(id, data);
      if (response.success) {
        const index = stages.value.findIndex((s) => s.id === id);
        if (index !== -1) {
          stages.value[index] = response.stage;
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

  // 删除阶段
  async function deleteStage(id) {
    try {
      const response = await stageAPI.delete(id);
      if (response.success) {
        stages.value = stages.value.filter((s) => s.id !== id);
        if (activeStage.value?.id === id) {
          activeStage.value = stages.value[0] || null;
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

  // 设置活动阶段
  function setActiveStage(stage) {
    activeStage.value = stage;
    localStorage.setItem("active_stage_id", stage.id);
  }

  return {
    stages,
    activeStage,
    loading,
    fetchStages,
    createStage,
    updateStage,
    deleteStage,
    setActiveStage,
  };
});
