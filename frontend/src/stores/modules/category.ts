import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { categoryAPI } from "@/api/modules/category";
import { ElMessage } from "element-plus";
import type { CategoriesResponse } from "@/types";

type CategoryNode = Record<string, any>;

export const useCategoryStore = defineStore("category", () => {
  const loading = ref(false);
  const tree = ref<CategoryNode[]>([]);
  const flat = ref<CategoryNode[]>([]);
  const expandedKeys = ref<string[]>([]);
  const lastFetched = ref(0);
  let pendingFetch: Promise<void> | null = null;

  const count = computed(() => flat.value.length);

  const categoryOptions = computed(() =>
    tree.value.map((cat) => ({
      value: cat.id,
      label: cat.name,
    })),
  );

  function getSubCategoryOptions(categoryId: number | string) {
    if (!categoryId) return [];
    const category = tree.value.find((cat) => cat.id === categoryId);
    if (!category) return [];
    const subs = category.subcategories || category.children || [];
    return subs.map((sub) => ({
      value: sub.id,
      label: sub.name,
    }));
  }

  const getSubCategories = getSubCategoryOptions;
  const fetchCategories = fetchAll;

  function buildTree(list: CategoryNode[]) {
    const map = new Map<number | string, CategoryNode>();
    list.forEach((item) => map.set(item.id, { ...item, children: [] }));
    const roots: CategoryNode[] = [];
    list.forEach((item) => {
      if (item.parent_id && map.has(item.parent_id)) {
        map.get(item.parent_id)!.children!.push(map.get(item.id)!);
      } else if (!item.parent_id) {
        roots.push(map.get(item.id)!);
      }
    });
    return roots;
  }

  async function fetchAll(force = false) {
    if (loading.value) {
      return pendingFetch ?? Promise.resolve();
    }
    if (
      !force &&
      Date.now() - lastFetched.value < 60_000 &&
      (tree.value.length || flat.value.length)
    ) {
      return Promise.resolve();
    }

    loading.value = true;
    pendingFetch = (async () => {
      try {
        const res = await categoryAPI.getAll({ include_subcategories: true });
        const response = res as unknown as CategoriesResponse;
        let data: CategoryNode[] = [];
        if (response.success && Array.isArray(response.categories)) {
          data = response.categories;
        } else if (Array.isArray(response)) {
          data = response as CategoryNode[];
        } else {
          data = response.data || response.items || [];
        }

        const isTree = data.some(
          (d: CategoryNode) =>
            Array.isArray(d.children) || Array.isArray(d.subcategories),
        );

        if (!isTree) {
          flat.value = data as CategoryNode[];
          tree.value = buildTree(data) as CategoryNode[];
        } else {
          tree.value = (data as CategoryNode[]).map((item) => {
            const children =
              (item.subcategories || item.children || []).map((child) => ({
                ...child,
                category_id: child.category_id || item.id,
                uniqueKey: `sub-${child.id}`,
              })) || [];
            return {
              ...item,
              children,
              subcategories: children,
              uniqueKey: `cat-${item.id}`,
            };
          });

          const collected: CategoryNode[] = [];
          const traverse = (
            node: CategoryNode,
            parent: CategoryNode | null,
          ) => {
            const flatNode: CategoryNode = {
              id: node.id,
              name: node.name,
              parent_id: node.parent_id ?? (parent?.id || null),
              category_id: node.category_id ?? parent?.id ?? null,
            } as CategoryNode;
            collected.push(flatNode);
            (node.children || node.subcategories || []).forEach((child) =>
              traverse(child, node),
            );
          };
          tree.value.forEach((root) => traverse(root, null));
          flat.value = collected;
        }

        expandedKeys.value = tree.value.map((item) => `${item.id}`);
        lastFetched.value = Date.now();
      } catch (error) {
        console.error("获取分类失败:", error);
        ElMessage.error("获取分类失败，请稍后再试");
        throw error;
      } finally {
        loading.value = false;
        pendingFetch = null;
      }
    })();

    return pendingFetch;
  }

  async function ensureLoaded(force = false) {
    if (!force && (tree.value.length || flat.value.length)) {
      return;
    }
    return fetchAll(force);
  }

  async function createRoot(data: any) {
    try {
      const payload = typeof data === "string" ? { name: data } : data;
      const res = await categoryAPI.create(payload);
      await fetchAll(true);
      return res;
    } catch (error) {
      console.error("Create root error:", error);
      throw error;
    }
  }

  async function createChild(parentId: number | string, data: any) {
    try {
      const payload = typeof data === "string" ? { name: data } : data;
      const res = await categoryAPI.createSubcategory(parentId, payload);
      await fetchAll(true);
      return res;
    } catch (error) {
      console.error("Create child error:", error);
      throw error;
    }
  }

  async function rename(idOrNode: any, dataOrName: any) {
    let nodeId;
    let categoryId;
    let payload;

    if (typeof idOrNode === "object" && idOrNode !== null) {
      nodeId = idOrNode.id;
      categoryId = idOrNode.category_id;
      payload =
        typeof dataOrName === "string" ? { name: dataOrName } : dataOrName;
    } else {
      console.warn(
        "Calling rename with id is deprecated. Use full node object instead.",
      );
      nodeId = idOrNode;
      payload =
        typeof dataOrName === "string" ? { name: dataOrName } : dataOrName;
      const node = flat.value.find((n) => n.id === nodeId);
      categoryId = node?.category_id;
    }

    if (!nodeId) return;

    if (categoryId) {
      await categoryAPI.updateSubcategory(nodeId, payload);
    } else {
      await categoryAPI.update(nodeId, payload);
    }
    await fetchAll(true);
  }

  async function remove(idOrNode: any) {
    let nodeId;
    let categoryId;

    if (typeof idOrNode === "object" && idOrNode !== null) {
      nodeId = idOrNode.id;
      categoryId = idOrNode.category_id;
    } else {
      console.warn(
        "Calling remove with id is deprecated. Use full node object instead.",
      );
      nodeId = idOrNode;
      const node = flat.value.find((n) => n.id === nodeId);
      categoryId = node?.category_id;
    }

    if (!nodeId) return;

    if (categoryId) {
      await categoryAPI.deleteSubcategory(nodeId);
    } else {
      await categoryAPI.delete(nodeId);
    }
    await fetchAll(true);
  }

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
    ensureLoaded,
    createRoot,
    createChild,
    rename,
    remove,
    categoryTree,
    categories,
    createCategory,
    createSubCategory,
    updateCategory,
    deleteCategory,
  };
});
