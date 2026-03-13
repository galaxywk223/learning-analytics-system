import { computed, ref } from "vue";
import { defineStore } from "pinia";

export type ThemeId = "paper" | "midnight" | "forest" | "ocean" | "amber";

type ThemeOption = {
  id: ThemeId;
  name: string;
  mode: "light" | "dark";
  preview: string;
  description: string;
};

const STORAGE_KEY = "app-theme";

const LEGACY_THEME_MAP: Record<string, ThemeId> = {
  light: "paper",
  sakura: "paper",
  latte: "amber",
  ocean: "ocean",
  forest: "forest",
  dark: "midnight",
  cyberpunk: "midnight",
  violet: "midnight",
  sunset: "amber",
  coffee: "amber",
};

const DEFAULT_THEME: ThemeId = "paper";

const THEME_OPTIONS: ThemeOption[] = [
  {
    id: "paper",
    name: "纸感晨雾",
    mode: "light",
    preview: "linear-gradient(135deg, #8a9bce 0%, #f2ebdc 100%)",
    description: "默认主题，灰蓝与暖米白的学习工作台。",
  },
  {
    id: "midnight",
    name: "午夜墨蓝",
    mode: "dark",
    preview: "linear-gradient(135deg, #4f6aa8 0%, #0f172a 100%)",
    description: "深色模式，适合夜间浏览与沉浸复盘。",
  },
  {
    id: "forest",
    name: "松林草稿",
    mode: "light",
    preview: "linear-gradient(135deg, #5b8d77 0%, #ecf1e7 100%)",
    description: "低饱和绿色，偏自然和长时阅读。",
  },
  {
    id: "ocean",
    name: "静海坐标",
    mode: "light",
    preview: "linear-gradient(135deg, #4f8ca6 0%, #ebf4f7 100%)",
    description: "冷静青蓝，适合数据和图表场景。",
  },
  {
    id: "amber",
    name: "琥珀砂页",
    mode: "light",
    preview: "linear-gradient(135deg, #b27a3e 0%, #f5ead6 100%)",
    description: "暖砂色纸面感，更偏计划与整理。",
  },
];

function normalizeThemeId(rawTheme: string | null | undefined): ThemeId {
  if (!rawTheme) return DEFAULT_THEME;

  const matched = THEME_OPTIONS.find((item) => item.id === rawTheme);
  if (matched) return matched.id;

  return LEGACY_THEME_MAP[rawTheme] || DEFAULT_THEME;
}

function applyThemeToDocument(themeId: ThemeId) {
  const theme = THEME_OPTIONS.find((item) => item.id === themeId) || THEME_OPTIONS[0];
  document.documentElement.setAttribute("data-theme", theme.id);
  document.documentElement.classList.toggle("dark", theme.mode === "dark");
}

export const useThemeStore = defineStore("theme", () => {
  const currentTheme = ref<ThemeId>(DEFAULT_THEME);

  const themes = THEME_OPTIONS;

  const currentThemeMeta = computed(
    () => themes.find((theme) => theme.id === currentTheme.value) || themes[0],
  );

  const isDark = computed(() => currentThemeMeta.value.mode === "dark");

  function setTheme(themeId: string) {
    const normalized = normalizeThemeId(themeId);
    currentTheme.value = normalized;
    localStorage.setItem(STORAGE_KEY, normalized);
    applyThemeToDocument(normalized);
  }

  function initTheme() {
    const savedTheme = normalizeThemeId(localStorage.getItem(STORAGE_KEY));
    currentTheme.value = savedTheme;
    localStorage.setItem(STORAGE_KEY, savedTheme);
    applyThemeToDocument(savedTheme);
  }

  return {
    currentTheme,
    currentThemeMeta,
    themes,
    isDark,
    setTheme,
    initTheme,
  };
});
