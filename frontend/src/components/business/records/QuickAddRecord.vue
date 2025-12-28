<template>
  <div class="quick-add-record">
    <el-button
      type="primary"
      circle
      :icon="Plus"
      size="large"
      class="add-button"
      @click="dialogVisible = true"
    ></el-button>

    <el-dialog
      v-model="dialogVisible"
      title="快速记录"
      width="500px"
      :before-close="handleClose"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="任务名称" prop="task">
          <el-input v-model="form.task" placeholder="请输入任务名称"></el-input>
        </el-form-item>
        <el-form-item label="学习时长" prop="duration">
          <el-input-number
            v-model="form.duration"
            :min="1"
            :max="600"
            controls-position="right"
          ></el-input-number>
          <span style="margin-left: 10px">分钟</span>
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-select v-model="form.category" placeholder="请选择分类">
            <el-option
              v-for="item in categories"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="notes">
          <el-input v-model="form.notes" type="textarea" :rows="3"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">提交</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { Icon } from "@iconify/vue";
import { useRecordsStore } from "@/stores/records";
// import { getCategories } from '@/api/categories'; // 假设有获取分类的API
// import { addRecord } from '@/api/records'; // 假设有添加记录的API

const dialogVisible = ref(false);
const formRef = ref(null);
const recordsStore = useRecordsStore();

const form = reactive({
  task: "",
  duration: 30,
  category: null,
  notes: "",
});

const rules = reactive({
  task: [{ required: true, message: "请输入任务名称", trigger: "blur" }],
  duration: [{ required: true, message: "请输入学习时长", trigger: "blur" }],
  category: [{ required: true, message: "请选择分类", trigger: "change" }],
});

const categories = ref([]);

onMounted(async () => {
  // 模拟获取分类数据
  // const { data } = await getCategories();
  categories.value = [
    { id: 1, name: "编程" },
    { id: 2, name: "英语" },
    { id: 3, name: "数学" },
  ];
});

const handleClose = () => {
  formRef.value.resetFields();
  dialogVisible.value = false;
};

const submitForm = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        // await addRecord(form);
        console.log("提交的数据:", form);
        ElMessage.success("记录添加成功");
        recordsStore.fetch(true); // 刷新记录列表
        handleClose();
      } catch (error) {
        ElMessage.error("记录添加失败");
      }
    }
  });
};
</script>

<style scoped>
.add-button {
  position: fixed;
  right: 40px;
  bottom: 40px;
  z-index: 100;
}
</style>
