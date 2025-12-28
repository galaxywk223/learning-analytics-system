/**
 * 分类相关API
 */
import request from "@/utils/request";

export const categoryAPI = {
  // 获取所有分类
  getAll(params) {
    return request({
      url: "/api/categories",
      method: "get",
      params,
    });
  },

  // 获取单个分类
  getById(id) {
    return request({
      url: `/api/categories/${id}`,
      method: "get",
    });
  },

  // 创建分类
  create(data) {
    return request({
      url: "/api/categories",
      method: "post",
      data,
    });
  },

  // 更新分类
  update(id, data) {
    return request({
      url: `/api/categories/${id}`,
      method: "put",
      data,
    });
  },

  // 删除分类
  delete(id) {
    return request({
      url: `/api/categories/${id}`,
      method: "delete",
    });
  },

  // 创建子分类
  createSubcategory(categoryId, data) {
    return request({
      url: `/api/categories/${categoryId}/subcategories`,
      method: "post",
      data,
    });
  },

  // 更新子分类
  updateSubcategory(subcategoryId, data) {
    return request({
      url: `/api/categories/subcategories/${subcategoryId}`,
      method: "put",
      data,
    });
  },

  // 删除子分类
  deleteSubcategory(subcategoryId) {
    return request({
      url: `/api/categories/subcategories/${subcategoryId}`,
      method: "delete",
    });
  },
};
