<template>
  <div class="voice-status" :class="`voice-status--${status}`" role="status" :aria-live="ariaLive">
    <span class="voice-status__dot" aria-hidden="true" />
    <span class="voice-status__label">{{ label }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { VoiceState } from '@/types/contracts'

const props = withDefaults(defineProps<{
  status?: VoiceState
}>(), {
  status: 'idle',
})

const label = computed(() => {
  const labels: Record<VoiceState, string> = {
    idle: '轻触开始语音输入',
    recording: '正在聆听...',
    processing: '正在理解...',
    tts_playing: '播报中',
    clarifying: '请补充信息',
    conflict: '检测到时间冲突',
    success: '操作成功',
    error: '出现错误',
    searching: '正在联网检索...',
  }
  return labels[props.status]
})

const ariaLive = computed(() =>
  ['idle', 'recording'].includes(props.status) ? 'off' : 'polite'
)
</script>

<style scoped>
.voice-status {
  display: inline-flex;
  align-items: center;
  gap: var(--vc-space-sm);
  padding: var(--vc-space-xs) var(--vc-space-md);
  border-radius: var(--vc-radius-full);
  font-size: var(--vc-text-sm);
  font-weight: var(--vc-weight-medium);
  color: var(--vc-text-secondary);
  background: var(--vc-bg-elevated);
  border: 1px solid var(--vc-border);
  transition: all var(--vc-transition-base);
}

.voice-status__dot {
  width: 8px;
  height: 8px;
  border-radius: var(--vc-radius-full);
  background: var(--vc-text-tertiary);
  transition: background var(--vc-transition-base);
}

.voice-status--recording {
  color: var(--vc-recording);
  border-color: hsla(0, 35%, 52%, 0.25);
  background: hsla(0, 35%, 52%, 0.06);
}
.voice-status--recording .voice-status__dot {
  background: var(--vc-recording);
  animation: vc-blink 1.2s ease-in-out infinite;
}

.voice-status--processing {
  color: var(--vc-processing);
  border-color: hsla(35, 30%, 45%, 0.25);
  background: hsla(35, 30%, 45%, 0.06);
}
.voice-status--processing .voice-status__dot {
  background: var(--vc-processing);
  animation: vc-blink 1.4s ease-in-out infinite;
}

.voice-status--tts_playing {
  color: var(--vc-info);
  border-color: hsla(210, 25%, 45%, 0.2);
  background: hsla(210, 25%, 45%, 0.04);
}
.voice-status--tts_playing .voice-status__dot {
  background: var(--vc-info);
}

.voice-status--success {
  color: var(--vc-success);
  border-color: hsla(150, 20%, 45%, 0.2);
  background: var(--vc-success-soft);
}
.voice-status--success .voice-status__dot {
  background: var(--vc-success);
}

.voice-status--conflict,
.voice-status--error {
  color: var(--vc-danger);
  border-color: hsla(0, 30%, 50%, 0.2);
  background: var(--vc-danger-soft);
}
.voice-status--conflict .voice-status__dot,
.voice-status--error .voice-status__dot {
  background: var(--vc-danger);
}

.voice-status--clarifying {
  color: var(--vc-accent);
  border-color: hsla(36, 16%, 48%, 0.2);
  background: hsla(36, 16%, 48%, 0.04);
}
.voice-status--clarifying .voice-status__dot {
  background: var(--vc-accent);
  animation: vc-blink 1.4s ease-in-out infinite;
}

.voice-status--searching {
  color: var(--vc-accent);
  border-color: hsla(36, 16%, 48%, 0.2);
  background: hsla(36, 16%, 48%, 0.04);
}
.voice-status--searching .voice-status__dot {
  background: var(--vc-accent);
  animation: vc-blink 1.4s ease-in-out infinite;
}
</style>
