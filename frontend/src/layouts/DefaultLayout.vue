<template>
  <div 
    class="default-layout"
    @touchstart="onTouchStart"
    @touchmove="onTouchMove"
    @touchend="onTouchEnd"
    @mousedown="onMouseDown"
    @mousemove="onMouseMove"
    @mouseup="onMouseUp"
    @mouseleave="onMouseUp"
  >
    <!-- 响应式容器：移动端滑动 / 桌面端三栏 -->
    <div 
      class="responsive-container" 
      :style="containerStyle"
      :class="{ 'is-animating': !isSwiping && !isDesktop, 'is-desktop': isDesktop }"
    >
      <!-- 左侧屏: 设置 -->
      <div class="page-wrapper page-left">
        <SettingsPanel />
      </div>

      <!-- 中心屏: 工作台 -->
      <div class="page-wrapper page-center">
        <CenterWorkspace 
          :voice-state="sessionStore.voiceState"
          :partial-transcript="sessionStore.partialTranscript"
          :volume="currentVolume"
          :current-conflicts="currentConflicts"
          :conflict-suggestions="conflictSuggestions"
          :is-desktop="isDesktop"
          @press-start="startVoiceInput"
          @press-end="stopVoiceInput"
          @tap-mic="handleTapButton"
          @resolve-conflict="handleResolveConflict"
          @cancel-conflict="handleCancelConflict"
          @send-text="handleTextSubmit"
        />
      </div>

      <!-- 右侧屏: 日历 -->
      <div class="page-wrapper page-right">
        <RightCalendar />
      </div>
    </div>

    <!-- 轻量级 Snackbar (静默任务完成提示) -->
    <transition name="fade-slide-up">
      <div v-if="snackbarMessage" class="global-snackbar">
        ✓ {{ snackbarMessage }}
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMediaQuery } from '@vueuse/core'
import { useSessionStore } from '@/stores/useSessionStore'
import { useCalendarStore } from '@/stores/useCalendarStore'
import { useHapticFeedback } from '@/composables/useHapticFeedback'
import { useTTSPlayer } from '@/composables/useTTSPlayer'
import { useWebSocket } from '@/composables/useWebSocket'
import { useAudioRecorder } from '@/composables/useAudioRecorder'
import { useVADController } from '@/composables/useVADController'

import SettingsPanel from '@/views/SettingsPanel.vue'
import CenterWorkspace from '@/views/CenterWorkspace.vue'
import RightCalendar from '@/views/RightCalendar.vue'
import type { ConflictItem, WSFrame } from '@/types/contracts'

const sessionStore = useSessionStore()
const calendarStore = useCalendarStore()
const { vibrate } = useHapticFeedback()
const { speakText, stop: stopTTS } = useTTSPlayer()

// ── Responsive Logic ──────────────────────────────────────────────────
const isDesktop = useMediaQuery('(min-width: 1024px)')

// ── Swipe Logic ────────────────────────────────────────────────────────
const currentPage = ref(1) // 0: Left, 1: Center, 2: Right
const isSwiping = ref(false)
const startX = ref(0)
const currentDeltaX = ref(0)
const viewWidth = typeof window !== 'undefined' ? window.innerWidth : 375

function onTouchStart(e: TouchEvent) {
  handleStart(e.touches[0].clientX)
}
function onMouseDown(e: MouseEvent) {
  handleStart(e.clientX)
}
function handleStart(clientX: number) {
  if (isDesktop.value) return
  isSwiping.value = true
  startX.value = clientX
  currentDeltaX.value = 0
}

function onTouchMove(e: TouchEvent) {
  handleMove(e.touches[0].clientX)
}
function onMouseMove(e: MouseEvent) {
  if (!isSwiping.value) return
  handleMove(e.clientX)
}
function handleMove(clientX: number) {
  if (!isSwiping.value || isDesktop.value) return
  const delta = clientX - startX.value
  
  if (currentPage.value === 0 && delta > 0) {
    currentDeltaX.value = delta * 0.3
  } else if (currentPage.value === 2 && delta < 0) {
    currentDeltaX.value = delta * 0.3
  } else {
    currentDeltaX.value = delta
  }
}

function onTouchEnd() {
  handleEnd()
}
function onMouseUp() {
  if (isSwiping.value) handleEnd()
}
function handleEnd() {
  if (isDesktop.value) return
  isSwiping.value = false
  const threshold = viewWidth * 0.25 
  
  if (currentDeltaX.value > threshold && currentPage.value > 0) {
    currentPage.value -= 1
  } else if (currentDeltaX.value < -threshold && currentPage.value < 2) {
    currentPage.value += 1
  }
  
  currentDeltaX.value = 0
}

const containerStyle = computed(() => {
  if (isDesktop.value) {
    return { transform: 'none' }
  }
  const baseOffset = -currentPage.value * 100
  const swipeOffset = (currentDeltaX.value / viewWidth) * 100
  const totalOffset = baseOffset + swipeOffset
  return {
    transform: `translate3d(${totalOffset}vw, 0, 0)`
  }
})

// ── Voice & Logic ────────────────────────────────────────────────────────
const currentVolume = ref(0)
const snackbarMessage = ref('')
const currentConflicts = ref<ConflictItem[]>([])
const conflictSuggestions = ref<string[]>([])

function showSnackbar(msg: string) {
  snackbarMessage.value = msg
  setTimeout(() => { snackbarMessage.value = '' }, 3000)
}

const wsUrl = `ws://${window.location.hostname}:8000/api/v1/voice/stream`
const ws = useWebSocket({
  url: wsUrl,
  onStateChange: (state) => sessionStore.setConnectionState(state),
  onMessage: (frame: WSFrame) => handleWebSocketMessage(frame)
})

function initWsSession() {
  ws.connect(sessionStore.sessionId)
  setTimeout(() => {
    if (ws.state.value === 'connected') {
      ws.sendFrame('SESSION_INIT', { 
        session_id: sessionStore.sessionId,
        user_id: sessionStore.currentUser?.email || 'user-001'
      }, sessionStore.sessionId)
    }
  }, 500)
}

function handleWebSocketMessage(frame: WSFrame) {
  const payload = frame.payload as any
  switch (frame.type) {
    case 'STATE_UPDATE':
      if (payload.state) sessionStore.setVoiceState(payload.state)
      break
    case 'TRANSCRIPT_PARTIAL':
      sessionStore.updatePartialTranscript(payload.text)
      break
    case 'TRANSCRIPT_FINAL':
      sessionStore.setFinalTranscript(payload.text)
      break
    case 'CONFLICT_ALERT':
      sessionStore.setVoiceState('conflict')
      currentConflicts.value = payload.conflicts || []
      conflictSuggestions.value = payload.suggestions ? payload.suggestions.map((s:any) => s.reason || s) : ['推迟至下一个可用时间', '取消']
      speakText(payload.message || '发现时间冲突')
      if (!isDesktop.value && currentPage.value !== 1) currentPage.value = 1
      break
    case 'ACTION_RESULT':
      sessionStore.setVoiceState('success')
      if (payload.event) calendarStore.addEvent(payload.event)
      showSnackbar(payload.message || '操作已完成')
      setTimeout(() => sessionStore.setVoiceState('idle'), 1500)
      break
  }
}

const vad = useVADController({
  onSpeechStart: () => {},
  onSpeechEnd: () => {
    if (sessionStore.voiceState === 'recording') stopVoiceInput()
  }
})

const recorder = useAudioRecorder({
  onVolumeChange: (vol) => {
    currentVolume.value = vol
    vad.feedVolume(vol)
  },
  onChunk: (chunk, seqNum, isFinal) => ws.sendAudioChunk(chunk, sessionStore.sessionId, seqNum, isFinal)
})

function startVoiceInput() {
  stopTTS()
  vibrate('recording')
  sessionStore.setVoiceState('recording')
  if (ws.state.value !== 'connected') initWsSession()
  recorder.startRecording()
  vad.reset()
}

function stopVoiceInput() {
  recorder.stopRecording()
  currentVolume.value = 0
  vibrate('processing')
  sessionStore.setVoiceState('processing')
}

function handleTapButton() {
  if (sessionStore.voiceState === 'idle') startVoiceInput()
  else if (sessionStore.voiceState === 'recording') stopVoiceInput()
}

function handleResolveConflict(suggestion: string) {
  sessionStore.setVoiceState('processing')
  ws.sendFrame('TEXT_INPUT', { text: suggestion }, sessionStore.sessionId)
}

function handleCancelConflict() {
  sessionStore.setVoiceState('idle')
  ws.sendFrame('TEXT_INPUT', { text: '取消' }, sessionStore.sessionId)
}

function handleTextSubmit(text: string) {
  if (!text.trim()) return
  if (ws.state.value !== 'connected') initWsSession()
  stopTTS()
  sessionStore.setVoiceState('processing')
  ws.sendFrame('TEXT_INPUT', { text: text }, sessionStore.sessionId)
}

onMounted(() => {
  sessionStore.startSession()
  initWsSession()
})
</script>

<style scoped>
.default-layout {
  position: relative;
  width: 100vw;
  height: 100vh;
  height: 100dvh;
  overflow: hidden; 
  background-color: var(--vc-primary); 
}

/* 移动端: 核心滑动容器 */
.responsive-container {
  display: flex;
  width: 300vw;
  height: 100%;
  will-change: transform;
}

.is-animating {
  transition: transform var(--vc-transition-spring);
}

.page-wrapper {
  width: 100vw;
  height: 100%;
  flex-shrink: 0;
  background-color: var(--vc-bg-base);
}

/* ── 桌面端适配 ──────────────────────────────────────────────────────── */
@media (min-width: 1024px) {
  .responsive-container.is-desktop {
    width: 100vw;
    height: 100vh;
    display: grid;
    grid-template-columns: 280px 1fr 380px;
  }

  .page-wrapper {
    width: auto;
    height: 100%;
    overflow: hidden;
  }

  .page-left {
    border-right: 1px solid var(--vc-divider);
  }

  .page-right {
    border-left: 1px solid var(--vc-divider);
    box-shadow: -4px 0 24px rgba(0,0,0,0.02);
    z-index: 2;
  }

  .page-center {
    background-color: var(--vc-bg-surface);
    z-index: 1;
  }
}

/* Snackbar (Toast) */
.global-snackbar {
  position: fixed;
  top: env(safe-area-inset-top, 24px);
  left: 50%;
  transform: translateX(-50%);
  background-color: var(--vc-bg-surface);
  color: var(--vc-success);
  padding: 10px 24px;
  border-radius: var(--vc-radius-full);
  box-shadow: var(--vc-shadow-md);
  font-size: var(--vc-text-sm);
  font-weight: var(--vc-weight-bold);
  z-index: var(--vc-z-toast);
  border: 1px solid var(--vc-success-soft);
}

.fade-slide-up-enter-active,
.fade-slide-up-leave-active {
  transition: all var(--vc-transition-fast);
}
.fade-slide-up-enter-from,
.fade-slide-up-leave-to {
  opacity: 0;
  transform: translate(-50%, -10px);
}
</style>
