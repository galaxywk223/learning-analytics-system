/**
 * Todo相关API
 */
import request from "@/utils/request";

export const todoAPI = {
  getAll(params) {
    return request({
      url: "/api/todos",
      method: "get",
      params,
    });
  },

  getById(id) {
    return request({
      url: `/api/todos/${id}`,
      method: "get",
    });
  },

  create(data) {
    return request({
      url: "/api/todos",
      method: "post",
      data,
    });
  },

  update(id, data) {
    return request({
      url: `/api/todos/${id}`,
      method: "put",
      data,
    });
  },

  toggle(id) {
    return request({
      url: `/api/todos/${id}/toggle`,
      method: "post",
    });
  },

  delete(id) {
    return request({
      url: `/api/todos/${id}`,
      method: "delete",
    });
  },
};

// 导出独立函数以兼容旧代码
export const listTodos = (params) => todoAPI.getAll(params);
export const createTodo = (data) => todoAPI.create(data);
export const updateTodo = (id, data) => todoAPI.update(id, data);
export const deleteTodo = (id) => todoAPI.delete(id);
