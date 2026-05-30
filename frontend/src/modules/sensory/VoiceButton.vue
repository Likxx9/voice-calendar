<template>
  <button
    :id="id"
    class="voice-button"
    :class="[
      `voice-button--${status}`,
      { 'voice-button--pressed': isPressed },
    ]"
    :aria-label="ariaLabel"
    :aria-pressed="isPressed"
    role="button"
    @pointerdown="handlePointerDown"
    @pointerup="handlePointerUp"
    @pointerleave="handlePointerUp"
    @touchstart.prevent="handleTouchStart"
    @touchend="handleTouchEnd"
    @touchcancel="handleTouchEnd"
  >
    <!-- 脉冲光环层 -->
    <span class="voice-button__pulse" aria-hidden="true" />
    <span class="voice-button__pulse voice-button__pulse--delayed" aria-hidden="true" />

    <!-- 图标容器 -->
    <span class="voice-button__icon-wrap">
      <!-- 麦克风图标 -->
      <svg v-if="status === 'idle' || status === 'recording'" class="voice-button__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
        <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
        <line x1="12" y1="19" x2="12" y2="22" />
      </svg>
      <!-- 加载中 -->
      <svg v-else-if="status === 'processing'" class="voice-button__icon vc-anim-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 12a9 9 0 1 1-6.219-8.56" />
      </svg>
      <!-- 播放中 -->
      <svg v-else-if="status === 'tts_playing'" class="voice-button__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
        <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
        <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
      </svg>
      <!-- 成功 -->
      <svg v-else-if="status === 'success'" class="voice-button__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="20 6 9 17 4 12" />
      </svg>
      <!-- 冲突/错误 -->
      <svg v-else class="voice-button__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
    </span>

    <!-- 音量环 -->
    <svg v-if="status === 'recording'" class="voice-button__volume-ring" viewBox="0 0 100 100" aria-hidden="true">
      <circle
        cx="50" cy="50" r="46"
        fill="none"
        stroke="currentColor"
        stroke-width="3"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="circumference * (1 - volume)"
        stroke-linecap="round"
        class="voice-button__volume-circle"
      />
    </svg>
  </button>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { VoiceState } from '@/types/contracts'

const props = withDefaults(defineProps<{
  id?: string
  status?: VoiceState
  volume?: number               // 0~1 实时音量
}>(), {
  id: 'voice-main-btn',
  status: 'idle',
  volume: 0,
})

const emit = defineEmits<{
  'press-start': []
  'press-end': []
  'tap': []
}>()

const isPressed = ref(false)
let pressTimer: ReturnType<typeof setTimeout> | null = null
let isPressStarted = false

const circumference = 2 * Math.PI * 46

const ariaLabel = computed(() => {
  const labels: Record<VoiceState, string> = {
    idle: '按住说话，添加日程',
    recording: '正在录音，松开结束',
    processing: '正在理解您说的内容',
    tts_playing: '正在播报，双击可打断',
    clarifying: '等待您的回答',
    conflict: '检测到时间冲突',
    success: '操作成功',
    error: '出现错误，请重试',
    searching: '正在联网检索',
  }
  return labels[props.status]
})

function handlePointerDown() {
  isPressed.value = true
  isPressStarted = false
  pressTimer = setTimeout(() => {
    isPressStarted = true
    emit('press-start')
  }, 200)
}

function handlePointerUp() {
  isPressed.value = false
  if (pressTimer) {
    clearTimeout(pressTimer)
    pressTimer = null
  }
  if (isPressStarted) {
    emit('press-end')
  } else {
    emit('tap')
  }
  isPressStarted = false
}

function handleTouchStart() {
  handlePointerDown()
}

function handleTouchEnd() {
  handlePointerUp()
}
</script>

<style scoped>
.voice-button {
  --btn-size: 80px;
  --btn-color: var(--vc-primary);

  position: relative;
  width: var(--btn-size);
  height: var(--btn-size);
  border-radius: var(--vc-radius-full);
  background: var(--btn-color);
  border: 1px solid var(--vc-border);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  user-select: none;
  -webkit-user-select: none;
  touch-action: manipulation;
  transition: all var(--vc-transition-fast);
  box-shadow: var(--vc-shadow-md);
  z-index: var(--vc-z-fab);
}

.voice-button:hover {
  border-color: var(--vc-accent-light);
  box-shadow: var(--vc-shadow-lg);
  background: var(--vc-primary-light);
}

.voice-button--pressed {
  transform: scale(0.96);
}

/* ── 状态色变 ──────────────────────────────────── */
.voice-button--recording {
  --btn-color: var(--vc-recording);
  border-color: var(--vc-recording);
}

.voice-button--processing {
  --btn-color: var(--vc-processing);
  border-color: var(--vc-processing);
}

.voice-button--tts_playing {
  --btn-color: var(--vc-info);
  border-color: var(--vc-info);
}

.voice-button--success {
  --btn-color: var(--vc-success);
  border-color: var(--vc-success);
}

.voice-button--conflict,
.voice-button--error {
  --btn-color: var(--vc-danger);
  border-color: var(--vc-danger);
}

.voice-button--clarifying {
  --btn-color: var(--vc-accent);
  border-color: var(--vc-accent);
}

.voice-button--searching {
  --btn-color: var(--vc-accent);
  border-color: var(--vc-accent);
}

/* ── 脉冲光环 ──────────────────────────────────── */
.voice-button__pulse {
  position: absolute;
  inset: -4px;
  border-radius: var(--vc-radius-full);
  border: 2px solid var(--btn-color);
  opacity: 0;
  pointer-events: none;
}

.voice-button--recording .voice-button__pulse {
  animation: voice-btn-pulse-ring 1.5s ease-out infinite;
}

.voice-button__pulse--delayed {
  animation-delay: 0.75s !important;
}

@keyframes voice-btn-pulse-ring {
  0% {
    transform: scale(1);
    opacity: 0.4;
  }
  100% {
    transform: scale(1.15);
    opacity: 0;
  }
}

/* ── 图标 ──────────────────────────────────────── */
.voice-button__icon-wrap {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
}

.voice-button__icon {
  width: 32px;
  height: 32px;
  transition: transform var(--vc-transition-spring);
}

.voice-button--recording .voice-button__icon {
  transform: scale(1.1);
}

/* ── 音量环 ────────────────────────────────────── */
.voice-button__volume-ring {
  position: absolute;
  inset: -6px;
  width: calc(100% + 12px);
  height: calc(100% + 12px);
  transform: rotate(-90deg);
  pointer-events: none;
}

.voice-button__volume-circle {
  color: var(--vc-recording);
  transition: stroke-dashoffset 100ms ease;
  filter: drop-shadow(0 0 4px var(--vc-recording-glow));
}

/* ── 响应式 ────────────────────────────────────── */
@media (min-width: 768px) {
  .voice-button {
    --btn-size: 88px;
  }
  .voice-button__icon {
    width: 36px;
    height: 36px;
  }
}
</style>
