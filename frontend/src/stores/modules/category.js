import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { categoryAPI } from "@/api/modules/category";
import { ElMessage } from "element-plus";

// ================= 分类数据结构与后端假设 =================
// 假设后端 GET /api/categories 返回：
// 1) 直接嵌套树: [{ id, name, parent_id: null, children:[{ id, name, parent_id, children:[]}, ...] }, ...]
// 或 2) 扁平数组: [{ id, name, parent_id }, ...]
// 本 store 自动检测是否存在 children 字段决定是否需要自行构建树。
// 创建顶级: POST /api/categories  { name }
// 创建子级: POST /api/categories/:id/subcategories { name }
// 更新分类: PUT /api/categories/:id { name }
// 删除分类: DELETE /api/categories/:id  （递归删除其子项）
// 更新子分类: PUT /api/categories/subcategories/:id { name }
// 删除子分类: DELETE /api/categories/subcategories/:id
// ==========================================================

export const useCategoryStore = defineStore("category", () => {
  const loading = ref(false);
  const tree = ref([]); // 规范化的树
  const flat = ref([]); // 扁平数组缓存
  const expandedKeys = ref([]); // UI 展开用

  const count = computed(() => flat.value.length);

  // 计算属性：用于下拉选择的分类选项（只包含顶级分类）
  const categoryOptions = computed(() => {
    return tree.value.map((cat) => ({
      value: cat.id,
      label: cat.name,
    }));
  });

  // 获取指定分类的子分类选项
  function getSubCategoryOptions(categoryId) {
    if (!categoryId) return [];
    const category = tree.value.find((cat) => cat.id === categoryId);
    if (!category) return [];
    
    // 处理 subcategories 或 children 字段
    const subcategories = category.subcategories || category.children || [];
    return subcategories.map((sub) => ({
      value: sub.id,
      label: sub.name,
    }));
  }

  // 别名：用于兼容
  const fetchCategories = fetchAll;

  function buildTree(list) {
    const map = new Map();
    list.forEach((item) => map.set(item.id, { ...item, children: [] }));
    const roots = [];
    list.forEach((item) => {
      if (item.parent_id && map.has(item.parent_id)) {
        map.get(item.parent_id).children.push(map.get(item.id));
      } else if (!item.parent_id) {
        roots.push(map.get(item.id));
      }
    });
    return roots;
  }

  async function fetchAll() {
    loading.value = true;
    try {
      const res = await categoryAPI.getAll({ include_subcategories: true });
      console.log("Category store fetchAll response:", res); // 调试日志

      // 处理后端返回的 { success: true, categories: [...] } 格式
      let data = [];
      if (res.success && Array.isArray(res.categories)) {
        data = res.categories;
      } else if (Array.isArray(res)) {
        data = res;
      } else {
        data = res.data || res.items || [];
      }

      console.log("Processed data:", data); // 调试日志

      // 判定是否已是树结构
      const isTree = data.some(
        (d) => Array.isArray(d.children) || Array.isArray(d.subcategories)
      );
      if (!isTree) {
        flat.value = data;
        tree.value = buildTree(data);
      } else {
        // 将树展开成 flat
        tree.value = data.map((item) => ({
          ...item,
          children: item.subcategories || item.children || [],
        }));
        const collect = [];
        const dfs = (node, parent = null) => {
          collect.push({
            id: node.id,
            name: node.name,
            parent_id: node.parent_id ?? (parent?.id || null),
          });
          const children = node.subcategories || node.children || [];
          if (children) children.forEach((c) => dfs(c, node));
        };
        tree.value.forEach((r) => dfs(r));
        flat.value = collect;
      }
      expandedKeys.value = tree.value.map((r) => r.id);
      console.log("Tree built:", tree.value); // 调试日志
    } catch (e) {
      console.error("Fetch categories error:", e); // 调试日志
      ElMessage.error("获取分类失败: " + (e.message || "未知错误"));
    } finally {
      loading.value = false;
    }
  }

  async function createRoot(name) {
    try {
      const res = await categoryAPI.create({ name });
      console.log("Create root response:", res); // 调试日志
      await fetchAll();
      return res;
    } catch (e) {
      console.error("Create root error:", e); // 调试日志
      throw e;
    }
  }

  async function createChild(parentId, name) {
    try {
      const res = await categoryAPI.createSubcategory(parentId, { name });
      console.log("Create child response:", res); // 调试日志
      await fetchAll();
      return res;
    } catch (e) {
      console.error("Create child error:", e); // 调试日志
      throw e;
    }
  }

  async function rename(node, name) {
    if (!node) return;
    if (node.parent_id) {
      await categoryAPI.updateSubcategory(node.id, { name });
    } else {
      await categoryAPI.update(node.id, { name });
    }
    await fetchAll();
  }

  async function remove(node) {
    if (!node) return;
    if (node.parent_id) {
      await categoryAPI.deleteSubcategory(node.id);
    } else {
      await categoryAPI.delete(node.id);
    }
    await fetchAll();
  }

  return {
    loading,
    tree,
    flat,
    expandedKeys,
    count,
    categoryOptions,
    getSubCategoryOptions,
    fetchAll,
    fetchCategories,
    createRoot,
    createChild,
    rename,
    remove,
  };
});
