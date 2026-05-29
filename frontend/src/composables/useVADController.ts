/* ============================================================
 * M1 组合式函数 — 自适应端侧断句 (VAD Controller)
 * 轻量级前端 VAD 控制器
 * 支持接收后端 VAD_TIMEOUT_ADJUST 帧动态调节断句阈值
 * ============================================================ */

import { ref, computed } from 'vue'

export interface VADOptions {
  defaultSilenceTimeout?: number   // 默认静音超时（ms），默认 1500
  minSilenceTimeout?: number       // 最小值（ms），默认 800
  maxSilenceTimeout?: number       // 最大值（ms），默认 4000
  volumeThreshold?: number         // 音量阈值 (0~1)，默认 0.02
  onSpeechEnd?: () => void         // 静音超时回调（自动断句）
  onSpeechStart?: () => void       // 检测到语音开始
}

export function useVADController(options: VADOptions = {}) {
  const {
    defaultSilenceTimeout = 1500,
    minSilenceTimeout = 800,
    maxSilenceTimeout = 4000,
    volumeThreshold = 0.02,
    onSpeechEnd,
    onSpeechStart,
  } = options

  const silenceTimeout = ref(defaultSilenceTimeout)
  const isSpeaking = ref(false)
  const silenceDuration = ref(0)

  let silenceTimer: ReturnType<typeof setTimeout> | null = null
  let lastSpeechTime = 0

  // 接收实时音量输入，判断是否在说话
  function feedVolume(volume: number) {
    const now = Date.now()

    if (volume > volumeThreshold) {
      // 检测到语音活动
      if (!isSpeaking.value) {
        isSpeaking.value = true
        onSpeechStart?.()
      }
      lastSpeechTime = now
      silenceDuration.value = 0

      // 清除静音定时器
      if (silenceTimer) {
        clearTimeout(silenceTimer)
        silenceTimer = null
      }

      // 重置静音定时器
      silenceTimer = setTimeout(() => {
        isSpeaking.value = false
        silenceDuration.value = silenceTimeout.value
        onSpeechEnd?.()
      }, silenceTimeout.value)
    } else {
      // 静音阶段
      if (isSpeaking.value && lastSpeechTime > 0) {
        silenceDuration.value = now - lastSpeechTime
      }
    }
  }

  // 接收后端 VAD_TIMEOUT_ADJUST 控制帧，动态调节断句阈值
  function adjustTimeout(deltaMs: number) {
    const newTimeout = Math.max(
      minSilenceTimeout,
      Math.min(maxSilenceTimeout, silenceTimeout.value + deltaMs)
    )
    silenceTimeout.value = newTimeout
  }

  // 直接设置超时值
  function setTimeout_value(ms: number) {
    silenceTimeout.value = Math.max(minSilenceTimeout, Math.min(maxSilenceTimeout, ms))
  }

  // 重置到默认值
  function reset() {
    silenceTimeout.value = defaultSilenceTimeout
    isSpeaking.value = false
    silenceDuration.value = 0
    lastSpeechTime = 0
    if (silenceTimer) {
      clearTimeout(silenceTimer)
      silenceTimer = null
    }
  }

  // 静音进度（0~1），用于 UI 可视化
  const silenceProgress = computed(() => {
    if (!isSpeaking.value || silenceDuration.value === 0) return 0
    return Math.min(1, silenceDuration.value / silenceTimeout.value)
  })

  return {
    silenceTimeout,
    isSpeaking,
    silenceDuration,
    silenceProgress,
    feedVolume,
    adjustTimeout,
    setTimeout: setTimeout_value,
    reset,
  }
}
