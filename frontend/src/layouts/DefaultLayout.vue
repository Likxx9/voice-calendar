<template>
  <div class="default-layout">
    <!-- 主体区域：永远是核心内容（如日历时间轴） -->
    <main class="default-layout__main">
      <router-view v-slot="{ Component }">
        <transition name="fade-slide" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- 全局悬浮 AI 语音中枢 -->
    <FloatingVoiceHub
      :voice-state="sessionStore.voiceState"
      :partial-transcript="sessionStore.partialTranscript"
      :volume="currentVolume"
      @press-start="startVoiceInput"
      @press-end="stopVoiceInput"
      @tap="handleTapButton"
    />

    <!-- 全局时间冲突解决面板 (Bottom Sheet) -->
    <ConflictBottomSheet
      :is-visible="sessionStore.voiceState === 'conflict'"
      :conflicts="currentConflicts"
      :suggestions="conflictSuggestions"
      @resolve="handleResolveConflict"
      @cancel="handleCancelConflict"
    />

    <!-- 轻量级 Snackbar (静默任务完成提示) -->
    <transition name="fade-slide-up">
      <div v-if="snackbarMessage" class="global-snackbar">
        ✓ {{ snackbarMessage }}
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/useSessionStore'
import { useCalendarStore } from '@/stores/useCalendarStore'
import { useHapticFeedback } from '@/composables/useHapticFeedback'
import { useTTSPlayer } from '@/composables/useTTSPlayer'
import { useWebSocket } from '@/composables/useWebSocket'
import { useAudioRecorder } from '@/composables/useAudioRecorder'
import { useVADController } from '@/composables/useVADController'

import FloatingVoiceHub from '@/components/FloatingVoiceHub.vue'
import ConflictBottomSheet from '@/components/ConflictBottomSheet.vue'
import type { ConflictItem, WSFrame } from '@/types/contracts'

const sessionStore = useSessionStore()
const calendarStore = useCalendarStore()
const { vibrate } = useHapticFeedback()
const { speakText, stop: stopTTS } = useTTSPlayer()

const currentVolume = ref(0)
const snackbarMessage = ref('')

// Conflict State
const currentConflicts = ref<ConflictItem[]>([])
const conflictSuggestions = ref<string[]>([])

function showSnackbar(msg: string) {
  snackbarMessage.value = msg
  setTimeout(() => {
    snackbarMessage.value = ''
  }, 3000)
}

// ----------------------------------------------------------------------
// WebSocket 通信 (Agent 编排层通信)
// ----------------------------------------------------------------------
const wsUrl = `ws://${window.location.hostname}:8000/api/v1/voice/stream`
const ws = useWebSocket({
  url: wsUrl,
  onStateChange: (state) => {
    sessionStore.setConnectionState(state)
  },
  onMessage: (frame: WSFrame) => {
    handleWebSocketMessage(frame)
  }
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
      conflictSuggestions.value = payload.suggestions ? payload.suggestions.map((s:any) => s.reason || s) : ['推迟至下一个可用时间', '取消原有日程']
      speakText(payload.message || '发现时间冲突')
      break
    case 'SEMANTIC_RESULT':
      if (payload.intent === 'SEARCH' && payload.search_response) {
        sessionStore.setVoiceState('searching')
        // 处理搜索等逻辑...
      }
      break
    case 'ACTION_RESULT':
      sessionStore.setVoiceState('success')
      if (payload.event) {
        calendarStore.addEvent(payload.event)
      } else if (payload.task) {
        // 如果是后台任务组B完成
        showSnackbar(`已为您设置 ${payload.task.title}`)
      } else {
        showSnackbar(payload.message || '操作已完成')
      }
      setTimeout(() => sessionStore.setVoiceState('idle'), 1500)
      break
    case 'PLAYBACK_CONTROL':
      if (payload.action === 'START_TTS') {
        sessionStore.setVoiceState('tts_playing')
        if (payload.reply_text) {
          speakText(payload.reply_text)
        }
      }
      break
    case 'VAD_TIMEOUT_ADJUST':
      if (payload.suggested_silence_timeout_ms) {
        vad.setTimeout(payload.suggested_silence_timeout_ms)
      }
      break
  }
}

// ----------------------------------------------------------------------
// 录音采集与断句
// ----------------------------------------------------------------------
const vad = useVADController({
  onSpeechStart: () => {},
  onSpeechEnd: () => {
    if (sessionStore.voiceState === 'recording') {
      stopVoiceInput()
    }
  }
})

const recorder = useAudioRecorder({
  onVolumeChange: (vol) => {
    currentVolume.value = vol
    vad.feedVolume(vol)
  },
  onChunk: (chunk, seqNum, isFinal) => {
    ws.sendAudioChunk(chunk, sessionStore.sessionId, seqNum, isFinal)
  }
})

function startVoiceInput() {
  stopTTS()
  vibrate('recording')
  sessionStore.setVoiceState('recording')
  
  if (ws.state.value !== 'connected') {
    initWsSession()
  }

  if (sessionStore.isTTSPlaying) {
    ws.sendInterrupt(sessionStore.sessionId)
  }

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
  if (sessionStore.isTTSPlaying) {
    stopTTS()
    ws.sendInterrupt(sessionStore.sessionId)
    sessionStore.setVoiceState('idle')
  } else if (sessionStore.voiceState === 'idle') {
    startVoiceInput()
  } else if (sessionStore.voiceState === 'recording') {
    stopVoiceInput()
  }
}

// ----------------------------------------------------------------------
// 冲突解决
// ----------------------------------------------------------------------
function handleResolveConflict(suggestion: string) {
  sessionStore.setVoiceState('processing')
  ws.sendFrame('TEXT_INPUT', { text: suggestion }, sessionStore.sessionId)
}

function handleCancelConflict() {
  sessionStore.setVoiceState('idle')
  ws.sendFrame('TEXT_INPUT', { text: '取消' }, sessionStore.sessionId)
}

onMounted(() => {
  sessionStore.startSession()
  initWsSession()
})
</script>

<style scoped>
.default-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-height: 100dvh;
  background-color: var(--vc-bg-base);
  color: var(--vc-text-primary);
  position: relative;
  overflow: hidden;
}

/* 主体区域满屏 */
.default-layout__main {
  flex: 1;
  width: 100%;
  max-width: 768px; /* 适配平板与手机 */
  margin: 0 auto;
  overflow-y: auto;
  padding-bottom: 120px; /* 为悬浮 Voice Hub 留出底部空间 */
}

/* 过渡动效 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all var(--vc-transition-base);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-slide-up-enter-active,
.fade-slide-up-leave-active {
  transition: all var(--vc-transition-fast);
}

.fade-slide-up-enter-from,
.fade-slide-up-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* Snackbar (Toast) */
.global-snackbar {
  position: fixed;
  top: var(--vc-space-xl);
  left: 50%;
  transform: translateX(-50%);
  background-color: var(--vc-bg-surface);
  color: var(--vc-success);
  padding: 10px 20px;
  border-radius: var(--vc-radius-full);
  box-shadow: var(--vc-shadow-md);
  font-size: var(--vc-text-sm);
  font-weight: var(--vc-weight-medium);
  z-index: var(--vc-z-toast);
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--vc-success-soft);
}
</style>
