/**
 * 认证相关API
 */
import request from '@/utils/request'

export const authAPI = {
  // 用户注册
  register(data) {
    return request({
      url: '/api/auth/register',
      method: 'post',
      data
    })
  },

  // 用户登录
  login(data) {
    return request({
      url: '/api/auth/login',
      method: 'post',
      data
    })
  },

  // 刷新token
  refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token')
    return request({
      url: '/api/auth/refresh',
      method: 'post',
      headers: {
        Authorization: `Bearer ${refreshToken}`
      }
    })
  },

  // 获取当前用户信息
  getCurrentUser() {
    return request({
      url: '/api/auth/me',
      method: 'get'
    })
  },

  // 修改密码
  changePassword(data) {
    return request({
      url: '/api/auth/change-password',
      method: 'post',
      data
    })
  }
}
