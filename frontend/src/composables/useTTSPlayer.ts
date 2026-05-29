/* ============================================================
 * M1 组合式函数 — TTS 音频播放与语速适配
 * 支持流式 TTS 音频缓冲播放，Barge-in 打断
 * ============================================================ */

import { ref, onUnmounted } from 'vue'

export interface TTSPlayerOptions {
  defaultSpeed?: number      // 默认语速 1.0~2.5
  onPlayStart?: () => void
  onPlayEnd?: () => void
  onInterrupted?: () => void
}

export function useTTSPlayer(options: TTSPlayerOptions = {}) {
  const {
    defaultSpeed = 1.2,
    onPlayStart,
    onPlayEnd,
    onInterrupted,
  } = options

  const isPlaying = ref(false)
  const speed = ref(defaultSpeed)
  const progress = ref(0)      // 0~1
  const duration = ref(0)

  let audioContext: AudioContext | null = null
  let currentSource: AudioBufferSourceNode | null = null
  let gainNode: GainNode | null = null
  let startTime = 0

  function getAudioContext(): AudioContext {
    if (!audioContext) {
      audioContext = new AudioContext()
    }
    return audioContext
  }

  // 播放 TTS 音频 ArrayBuffer
  async function play(audioData: ArrayBuffer) {
    stop() // 先停止当前播放

    try {
      const ctx = getAudioContext()
      const audioBuffer = await ctx.decodeAudioData(audioData.slice(0))

      currentSource = ctx.createBufferSource()
      currentSource.buffer = audioBuffer
      currentSource.playbackRate.value = speed.value

      gainNode = ctx.createGain()
      gainNode.gain.value = 1.0

      currentSource.connect(gainNode)
      gainNode.connect(ctx.destination)

      duration.value = audioBuffer.duration / speed.value
      startTime = ctx.currentTime
      isPlaying.value = true
      onPlayStart?.()

      // 播放进度追踪
      const updateProgress = () => {
        if (!isPlaying.value || !audioContext) return
        const elapsed = audioContext.currentTime - startTime
        progress.value = Math.min(1, elapsed / duration.value)
        if (progress.value < 1) {
          requestAnimationFrame(updateProgress)
        }
      }
      requestAnimationFrame(updateProgress)

      currentSource.onended = () => {
        if (isPlaying.value) {
          isPlaying.value = false
          progress.value = 1
          onPlayEnd?.()
        }
      }

      currentSource.start(0)
    } catch (err) {
      console.error('[TTSPlayer] 播放失败:', err)
      isPlaying.value = false
    }
  }

  // 使用 Web Speech API 作为备用 TTS
  function speakText(text: string) {
    if (!('speechSynthesis' in window)) return

    stop()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'zh-CN'
    utterance.rate = speed.value
    utterance.pitch = 1.0

    utterance.onstart = () => {
      isPlaying.value = true
      onPlayStart?.()
    }

    utterance.onend = () => {
      isPlaying.value = false
      progress.value = 1
      onPlayEnd?.()
    }

    window.speechSynthesis.speak(utterance)
  }

  // Barge-in 打断：立即停止播放
  function stop() {
    const wasPlaying = isPlaying.value

    if (currentSource) {
      try { currentSource.stop() } catch { /* 已停止 */ }
      currentSource.disconnect()
      currentSource = null
    }

    if (gainNode) {
      gainNode.disconnect()
      gainNode = null
    }

    // 同时停止 Web Speech API
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
    }

    isPlaying.value = false
    progress.value = 0

    if (wasPlaying) {
      onInterrupted?.()
    }
  }

  function setSpeed(newSpeed: number) {
    speed.value = Math.max(0.5, Math.min(3.0, newSpeed))
    if (currentSource) {
      currentSource.playbackRate.value = speed.value
    }
  }

  onUnmounted(() => {
    stop()
    audioContext?.close()
  })

  return {
    isPlaying,
    speed,
    progress,
    duration,
    play,
    speakText,
    stop,
    setSpeed,
  }
}
