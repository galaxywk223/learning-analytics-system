<template>
  <PageContainer
    :title="{ icon: '⏰', text: '倒计时' }"
    :subtitle="relativeTime"
    :custom-class="'countdown-page'"
  >
    <el-skeleton v-if="store.loading" :rows="6" animated />
    <div v-else>
      <el-collapse
        v-model="activePanels"
        class="countdown-collapse"
        accordion="{false}"
      >
        <el-collapse-item name="active">
          <template #title>
            <div class="collapse-header">
              <span class="collapse-title">进行中</span>
              <span class="badge">{{ store.active.length }}</span>
            </div>
          </template>
          <div class="row-cards" id="active-events-container">
            <template v-if="store.active.length">
              <CountdownItem
                v-for="ev in store.active"
                :key="ev.id"
                :event="ev"
                @edit="edit(ev)"
                @delete="confirmDelete(ev)"
              />
            </template>
            <div v-else class="empty-state">
              <i class="ll-icon flag" />
              <h3>当前没有进行中的目标</h3>
              <p class="text-muted">点击右下角 “+” 创建你的第一个倒计时吧！</p>
            </div>
          </div>
        </el-collapse-item>

        <el-collapse-item name="expired">
          <template #title>
            <div class="collapse-header">
              <span class="collapse-title">已过期</span>
              <span class="badge muted">{{ store.expired.length }}</span>
            </div>
          </template>
          <div class="row-cards" id="expired-events-container">
            <template v-if="store.expired.length">
              <CountdownItem
                v-for="ev in store.expired"
                :key="ev.id"
                :event="ev"
                expired
                @edit="edit(ev)"
                @delete="confirmDelete(ev)"
              />
            </template>
            <p v-else class="text-center text-muted">还没有已完成的目标。</p>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>

    <!-- 表单弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="form.id ? '编辑倒计时' : '新建倒计时'"
      width="720px"
      destroy-on-close
    >
      <el-form
        :model="form"
        :rules="rules"
        ref="formRef"
        label-position="top"
        class="countdown-form"
        @submit.prevent
      >
        <el-form-item label="目标名称" prop="title">
          <el-input v-model="form.title" autocomplete="off" size="large" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="目标日期" prop="target_date">
              <el-date-picker
                v-model="form.target_date"
                type="date"
                value-format="YYYY-MM-DD"
                size="large"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="具体时间" prop="target_time">
              <el-time-picker
                v-model="form.target_time"
                value-format="HH:mm"
                format="HH:mm"
                placeholder="选择时间"
                size="large"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">{{
          form.id ? "更新目标" : "添加目标"
        }}</el-button>
      </template>
    </el-dialog>
  </PageContainer>
  <button class="fab-add" type="button" @click="openCreate">
    <span class="fab-icon">+</span>
  </button>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone";
dayjs.extend(utc);
dayjs.extend(timezone);
import { useCountdownStore } from "@/stores/modules/countdown";
import CountdownItem from "@/components/business/countdown/CountdownItem.vue";
import PageContainer from "@/components/layout/PageContainer.vue";

const store = useCountdownStore();
const dialogVisible = ref(false);
const formRef = ref(null);
const saving = ref(false);
const relativeTime = ref(""); // 后续可由后端提供，目前占位
const activePanels = ref(["active"]);

const form = ref({
  id: null,
  title: "",
  target_date: "",
  target_time: "00:00",
});

const rules = {
  title: [{ required: true, message: "请输入目标名称", trigger: "blur" }],
  target_date: [
    { required: true, message: "请选择目标日期", trigger: "change" },
  ],
};

function openCreate() {
  form.value = {
    id: null,
    title: "",
    target_date: today(),
    target_time: "00:00",
  };
  dialogVisible.value = true;
}

function edit(ev) {
  const { id, title, target_datetime_utc } = ev;
  // 解析 UTC -> 北京时间，统一用 Asia/Shanghai
  const local = dayjs.utc(target_datetime_utc).tz("Asia/Shanghai");
  const y = local.format("YYYY");
  const m = local.format("MM");
  const d = local.format("DD");
  const hh = local.format("HH");
  const mm = local.format("mm");
  form.value = {
    id,
    title,
    target_date: `${y}-${m}-${d}`,
    target_time: `${hh}:${mm}`,
  };
  dialogVisible.value = true;
}

function confirmDelete(ev) {
  ElMessageBox.confirm(`确定删除目标 “${ev.title}” ?`, "确认", {
    type: "warning",
  })
    .then(async () => {
      await store.remove(ev.id);
      ElMessage.success("目标已删除");
    })
    .catch(() => {});
}

function today() {
  // 以北京时区的“今天”
  return dayjs().tz("Asia/Shanghai").format("YYYY-MM-DD");
}

function submit() {
  if (!formRef.value) return;
  formRef.value.validate(async (valid) => {
    if (!valid) return;
    saving.value = true;
    try {
      if (form.value.id) {
        await store.save(form.value.id, {
          title: form.value.title,
          target_date: form.value.target_date,
          target_time: form.value.target_time,
        });
        ElMessage.success("更新成功");
      } else {
        await store.add({
          title: form.value.title,
          target_date: form.value.target_date,
          target_time: form.value.target_time,
        });
        ElMessage.success("创建成功");
      }
      dialogVisible.value = false;
    } catch (e) {
      ElMessage.error("操作失败");
    } finally {
      saving.value = false;
    }
  });
}

onMounted(() => {
  store.fetch();
});
</script>

<style scoped src="@/styles/views/countdown/countdown-view.scss"></style>
