<template>
  <div class="countdown-page">
    <div class="page-header">
      <div>
        <h1>目标倒计时</h1>
        <p class="lead" v-if="relativeTime">{{ relativeTime }}</p>
      </div>
      <el-button type="primary" @click="openCreate" class="add-btn"
        >添加新目标</el-button
      >
    </div>

    <el-skeleton v-if="store.loading" :rows="6" animated />
    <div v-else>
      <h2 class="section-title">进行中</h2>
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
          <p class="text-muted">
            点击右上角的 “添加新目标” 来创建你的第一个倒计时吧！
          </p>
        </div>
      </div>

      <h2 class="section-title mt-40">已过期</h2>
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
        label-width="90px"
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
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import dayjs from "dayjs";
import { useCountdownStore } from "@/stores";
import CountdownItem from "@/components/business/countdown/CountdownItem.vue";

const store = useCountdownStore();
const dialogVisible = ref(false);
const formRef = ref(null);
const saving = ref(false);
const relativeTime = ref(""); // 后续可由后端提供，目前占位

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
  // 解析 UTC -> 本地(北京) 日期与时间
  const dt = new Date(target_datetime_utc);
  const beijingOffsetMs = 8 * 60 * 60 * 1000;
  const localMs = dt.getTime() + beijingOffsetMs;
  const local = new Date(localMs);
  const y = local.getFullYear();
  const m = String(local.getMonth() + 1).padStart(2, "0");
  const d = String(local.getDate()).padStart(2, "0");
  const hh = String(local.getHours()).padStart(2, "0");
  const mm = String(local.getMinutes()).padStart(2, "0");
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
  return dayjs().format("YYYY-MM-DD");
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
