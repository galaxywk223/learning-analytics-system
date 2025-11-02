import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { categoryAPI } from "@/api/modules/category";
import { ElMessage } from "element-plus";
import type { Category, CategoriesResponse } from "@/types";

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
  const tree = ref<Category[]>([]); // 规范化的树
  const flat = ref<Category[]>([]); // 扁平数组缓存
  const expandedKeys = ref<string[]>([]); // UI 展开用

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

  // 别名：用于兼容不同的调用方式
  const getSubCategories = getSubCategoryOptions;

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
      const response = res as unknown as CategoriesResponse;
      let data: Category[] = [];
      if (response.success && Array.isArray(response.categories)) {
        data = response.categories;
      } else if (Array.isArray(response)) {
        data = response as Category[];
      } else {
        data = response.data || response.items || [];
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
        // 将树展开成 flat，同时保留 category_id 字段
        tree.value = data.map((item) => {
          const children = (item.subcategories || item.children || []).map(
            (child) => {
              const childNode = {
                ...child,
                category_id: child.category_id || item.id, // 确保子分类有 category_id
                uniqueKey: `sub-${child.id}`, // 添加唯一标识：sub-{id}
              };
              console.log("Processing child node:", childNode); // 调试
              return childNode;
            }
          );
          const parentNode = {
            ...item,
            children,
            uniqueKey: `cat-${item.id}`, // 添加唯一标识：cat-{id}
          };
          console.log("Processing parent node:", parentNode); // 调试
          return parentNode;
        });

        console.log("Final tree structure:", tree.value); // 调试

        const collect = [];
        const dfs = (node, parent = null) => {
          const flatNode: any = {
            id: node.id,
            name: node.name,
            parent_id: node.parent_id ?? (parent?.id || null),
          };
          // 保留 category_id（对于子分类）
          if (node.category_id) {
            flatNode.category_id = node.category_id;
          }
          collect.push(flatNode);

          const children = node.subcategories || node.children || [];
          if (children) children.forEach((c) => dfs(c, node));
        };
        tree.value.forEach((r) => dfs(r));
        flat.value = collect;
      }
      expandedKeys.value = tree.value.map((r) => String(r.id));
      console.log("Tree built:", tree.value); // 调试日志
    } catch (e) {
      console.error("Fetch categories error:", e); // 调试日志
      ElMessage.error("获取分类失败: " + (e.message || "未知错误"));
    } finally {
      loading.value = false;
    }
  }

  async function createRoot(data) {
    try {
      // data 可以是字符串或对象
      const payload = typeof data === "string" ? { name: data } : data;
      const res = await categoryAPI.create(payload);
      console.log("Create root response:", res); // 调试日志
      await fetchAll();
      return res;
    } catch (e) {
      console.error("Create root error:", e); // 调试日志
      throw e;
    }
  }

  async function createChild(parentId, data) {
    try {
      // data 可以是字符串或对象
      const payload = typeof data === "string" ? { name: data } : data;
      const res = await categoryAPI.createSubcategory(parentId, payload);
      console.log("Create child response:", res); // 调试日志
      await fetchAll();
      return res;
    } catch (e) {
      console.error("Create child error:", e); // 调试日志
      throw e;
    }
  }

  async function rename(idOrNode, dataOrName) {
    let nodeId, categoryId, payload;

    // 兼容两种调用方式：
    // 1. rename(node, name) - 旧方式
    // 2. rename(id, { name }) - 新方式（不推荐，因为 Category 和 SubCategory 的 id 可能重复）
    if (typeof idOrNode === "object" && idOrNode !== null) {
      // 第一个参数是 node 对象 - 推荐方式
      nodeId = idOrNode.id;
      categoryId = (idOrNode as any).category_id; // 只检查 category_id，不检查 parent_id
      payload =
        typeof dataOrName === "string" ? { name: dataOrName } : dataOrName;
      console.log("rename node object:", {
        nodeId,
        category_id: (idOrNode as any).category_id,
        categoryId,
        isSubcategory: !!categoryId,
      });
    } else {
      // 第一个参数是 id - 不推荐，可能导致混淆
      console.warn(
        "Calling rename with id is deprecated. Use full node object instead."
      );
      nodeId = idOrNode;
      payload =
        typeof dataOrName === "string" ? { name: dataOrName } : dataOrName;

      // 需要从 flat 数组中查找节点来判断是否是子分类
      const node = flat.value.find((n) => n.id === nodeId);
      categoryId = (node as any)?.category_id;
      console.log("rename by id (deprecated):", { nodeId, node, categoryId });
    }

    if (!nodeId) return;

    if (categoryId) {
      await categoryAPI.updateSubcategory(nodeId, payload);
    } else {
      await categoryAPI.update(nodeId, payload);
    }
    await fetchAll();
  }

  async function remove(idOrNode) {
    let nodeId, categoryId;

    // 兼容两种调用方式：
    // 1. remove(node) - 推荐方式
    // 2. remove(id) - 不推荐（Category 和 SubCategory 的 id 可能重复）
    if (typeof idOrNode === "object" && idOrNode !== null) {
      // 第一个参数是 node 对象 - 推荐方式
      nodeId = idOrNode.id;
      categoryId = (idOrNode as any).category_id; // 只检查 category_id，不检查 parent_id
      console.log("remove node object:", {
        nodeId,
        category_id: (idOrNode as any).category_id,
        categoryId,
        isSubcategory: !!categoryId,
        fullNode: idOrNode,
      });
    } else {
      // 第一个参数是 id - 不推荐，可能导致混淆
      console.warn(
        "Calling remove with id is deprecated. Use full node object instead."
      );
      nodeId = idOrNode;
      // 需要从 flat 数组中查找节点来判断是否是子分类
      const node = flat.value.find((n) => n.id === nodeId);
      categoryId = (node as any)?.category_id;
      console.log("remove by id (deprecated):", { nodeId, node, categoryId });
    }

    if (!nodeId) return;

    console.log("Deleting:", {
      nodeId,
      categoryId,
      isSubcategory: !!categoryId,
    });

    if (categoryId) {
      await categoryAPI.deleteSubcategory(nodeId);
    } else {
      await categoryAPI.delete(nodeId);
    }
    await fetchAll();
  }

  // 别名：用于兼容 CategoriesView.vue
  const categoryTree = computed(() => tree.value);
  const categories = computed(() => flat.value);
  const createCategory = createRoot;
  const createSubCategory = createChild;
  const updateCategory = rename;
  const deleteCategory = remove;

  return {
    loading,
    tree,
    flat,
    expandedKeys,
    count,
    categoryOptions,
    getSubCategoryOptions,
    getSubCategories,
    fetchAll,
    fetchCategories,
    createRoot,
    createChild,
    rename,
    remove,
    // 别名
    categoryTree,
    categories,
    createCategory,
    createSubCategory,
    updateCategory,
    deleteCategory,
  };
});
