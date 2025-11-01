/**
 * 认证状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '@/api'
import { ElMessage } from 'element-plus'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  
  // 计算属性
  const isAuthenticated = computed(() => !!accessToken.value)
  
  // 登录
  async function login(credentials) {
    try {
      const response = await authAPI.login(credentials)
      
      if (response.success) {
        accessToken.value = response.access_token
        refreshToken.value = response.refresh_token
        user.value = response.user
        
        // 保存到localStorage
        localStorage.setItem('access_token', response.access_token)
        localStorage.setItem('refresh_token', response.refresh_token)
        
        ElMessage.success(response.message || '登录成功!')
        return true
      }
      return false
    } catch (error) {
      console.error('登录失败:', error)
      return false
    }
  }
  
  // 注册
  async function register(userInfo) {
    try {
      const response = await authAPI.register(userInfo)
      
      if (response.success) {
        ElMessage.success(response.message || '注册成功!')
        return true
      }
      return false
    } catch (error) {
      console.error('注册失败:', error)
      return false
    }
  }
  
  // 登出
  function logout() {
    accessToken.value = ''
    refreshToken.value = ''
    user.value = null
    
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    
    router.push('/login')
    ElMessage.info('已退出登录')
  }
  
  // 检查认证状态
  async function checkAuth() {
    if (!accessToken.value) {
      return false
    }
    
    try {
      const response = await authAPI.getCurrentUser()
      if (response.success) {
        user.value = response.user
        return true
      }
      return false
    } catch (error) {
      // Token无效,清除状态
      logout()
      return false
    }
  }
  
  // 刷新Token
  async function refresh() {
    try {
      const response = await authAPI.refreshToken()
      if (response.success) {
        accessToken.value = response.access_token
        localStorage.setItem('access_token', response.access_token)
        return true
      }
      return false
    } catch (error) {
      logout()
      return false
    }
  }
  
  return {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    login,
    register,
    logout,
    checkAuth,
    refresh
  }
})
