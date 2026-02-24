import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useThemeStore = defineStore('theme', () => {
  // State
  const currentTheme = ref<string>('light');
  
  // Available themes configuration
  const themes = [
    {
      id: 'light',
      name: '默认浅色',
      type: 'light',
      primaryColor: '#5564d8'
    },
    {
      id: 'forest',
      name: '清新森林',
      type: 'light',
      primaryColor: '#059669'
    },
    {
      id: 'ocean',
      name: '清爽海洋',
      type: 'light',
      primaryColor: '#0891b2'
    },
    {
      id: 'sakura',
      name: '樱花粉',
      type: 'light',
      primaryColor: '#ec4899'
    },
    {
      id: 'dark',
      name: '默认深色',
      type: 'dark',
      primaryColor: '#6c7ae0'
    },
    {
      id: 'cyberpunk',
      name: '赛博朋克',
      type: 'dark',
      primaryColor: '#00f0ff'
    },
    {
      id: 'sunset',
      name: '日落余晖',
      type: 'dark',
      primaryColor: '#f97316'
    },
    {
      id: 'violet',
      name: '暗夜紫罗兰',
      type: 'dark',
      primaryColor: '#8b5cf6'
    },
    {
      id: 'latte',
      name: '香醇拿铁',
      type: 'light',
      primaryColor: '#a16207'
    },
    {
      id: 'coffee',
      name: '浓郁咖啡',
      type: 'dark',
      primaryColor: '#d97706'
    }
  ];

  // Getters
  const isDark = computed(() => {
    const theme = themes.find(t => t.id === currentTheme.value);
    return theme?.type === 'dark';
  });

  // Actions
  function setTheme(themeId: string) {
    if (!themes.find(t => t.id === themeId)) {
      console.warn(`Theme ${themeId} not found, falling back to light`);
      themeId = 'light';
    }
    
    currentTheme.value = themeId;
    localStorage.setItem('app-theme', themeId);
    
    // Apply theme to document
    document.documentElement.setAttribute('data-theme', themeId);
    
    // Handle Element Plus dark mode class
    if (isDark.value) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }

  function initTheme() {
    const savedTheme = localStorage.getItem('app-theme');
    if (savedTheme) {
      setTheme(savedTheme);
    } else {
      // Check system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setTheme(prefersDark ? 'dark' : 'light');
    }
  }

  return {
    currentTheme,
    themes,
    isDark,
    setTheme,
    initTheme
  };
});
