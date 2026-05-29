/* ============================================================
 * Pinia Store — 用户偏好设置
 * TTS 语速 | 触觉强度 | 主题 | 无障碍模式
 * ============================================================ */

import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import type { UserSettings, ThemeMode, LayoutMode } from '@/types/contracts'

const SETTINGS_KEY = 'vc_user_settings'

const defaultSettings: UserSettings = {
  tts_speed: 1.2,
  haptic_intensity: 'medium',
  theme: 'dark',
  layout_mode: 'default',
  vad_sensitivity: 'medium',
}

function loadSettings(): UserSettings {
  try {
    const stored = localStorage.getItem(SETTINGS_KEY)
    return stored ? { ...defaultSettings, ...JSON.parse(stored) } : defaultSettings
  } catch {
    return defaultSettings
  }
}

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<UserSettings>(loadSettings())

  // 持久化到 localStorage
  watch(settings, (val) => {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(val))
  }, { deep: true })

  // 主题同步到 DOM
  watch(() => settings.value.theme, (theme) => {
    applyTheme(theme)
  }, { immediate: true })

  // 布局模式同步到 DOM
  watch(() => settings.value.layout_mode, (mode) => {
    applyLayoutMode(mode)
  }, { immediate: true })

  function applyTheme(theme: ThemeMode) {
    const root = document.documentElement
    if (theme === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      root.setAttribute('data-theme', prefersDark ? 'dark' : 'light')
    } else {
      root.setAttribute('data-theme', theme)
    }
  }

  function applyLayoutMode(mode: LayoutMode) {
    document.documentElement.setAttribute('data-mode', mode)
  }

  function updateSetting<K extends keyof UserSettings>(key: K, value: UserSettings[K]) {
    settings.value[key] = value
  }

  function resetSettings() {
    settings.value = { ...defaultSettings }
  }

  return {
    settings,
    updateSetting,
    resetSettings,
  }
})
