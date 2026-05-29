/* ============================================================
 * M1 组合式函数 — 触觉振动反馈
 * Vibration API 封装，四种状态专属振动模式
 * ============================================================ */

import { ref } from 'vue'

export type HapticPattern =
  | 'tap'           // 轻触反馈
  | 'recording'     // 录音开始 — 轻振
  | 'processing'    // 解析中 — 持续沙漏振
  | 'success'       // 成功创建 — 哒哒双振
  | 'conflict'      // 时间冲突 — 急促三振
  | 'error'         // 错误 — 长振

export type HapticIntensity = 'off' | 'light' | 'medium' | 'strong'

// 振动模式定义 [振动ms, 间隔ms, ...]
const HAPTIC_PATTERNS: Record<HapticPattern, number[]> = {
  tap:        [15],
  recording:  [30],
  processing: [20, 80, 20, 80, 20, 80, 20],
  success:    [40, 60, 40],
  conflict:   [30, 40, 30, 40, 30],
  error:      [200],
}

// 强度系数
const INTENSITY_MULTIPLIER: Record<HapticIntensity, number> = {
  off: 0,
  light: 0.5,
  medium: 1,
  strong: 1.5,
}

export function useHapticFeedback() {
  const isSupported = ref('vibrate' in navigator)
  const intensity = ref<HapticIntensity>('medium')

  function vibrate(pattern: HapticPattern) {
    if (!isSupported.value || intensity.value === 'off') return

    const multiplier = INTENSITY_MULTIPLIER[intensity.value]
    const basePattern = HAPTIC_PATTERNS[pattern]
    const scaledPattern = basePattern.map(ms => Math.round(ms * multiplier))

    try {
      navigator.vibrate(scaledPattern)
    } catch {
      // 静默失败（某些浏览器/设备不支持）
    }
  }

  function stopVibration() {
    if (!isSupported.value) return
    try {
      navigator.vibrate(0)
    } catch {
      // 静默
    }
  }

  function setIntensity(level: HapticIntensity) {
    intensity.value = level
  }

  return {
    isSupported,
    intensity,
    vibrate,
    stopVibration,
    setIntensity,
  }
}
