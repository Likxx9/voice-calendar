<template>
  <div class="conversation-view vc-anim-fade-in">
    <!-- 头部：导航与连接指示 -->
    <header class="conversation-header">
      <button class="back-btn" aria-label="返回日历" @click="goHome">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="19" y1="12" x2="5" y2="12" />
          <polyline points="12 19 5 12 12 5" />
        </svg>
      </button>
      <div class="header-center">
        <VoiceStatusIndicator :status="sessionStore.voiceState" />
      </div>
      <ConnectionStatus :state="sessionStore.connectionState" />
    </header>

    <!-- 核心对话流区域 -->
    <section class="conversation-flow-wrap" ref="flowScrollContainer">
      <ConversationFlow :messages="sessionStore.messages" />

      <!-- 实时追问卡片 (Clarification) -->
      <div v-if="sessionStore.voiceState === 'clarifying'" class="inline-card-container">
        <ClarificationCard
          :message="clarificationMessage"
          :missingFields="clarificationMissingFields"
          @voice-reply="startVoiceInput"
          @skip="handleSkipClarification"
        />
      </div>

      <!-- 实时时间冲突卡片 (Conflict Negotiation) -->
      <div v-if="sessionStore.voiceState === 'conflict'" class="inline-card-container">
        <ConflictNegotiation
          :conflicts="currentConflicts"
          :suggestions="conflictSuggestions"
          @select="handleResolveConflict"
          @voice-resolve="startVoiceInput"
          @force-create="handleForceCreate"
          @cancel="handleCancelConflict"
        />
      </div>



      <!-- 实时联网搜索卡片 (M9 Web Search Agent) -->
      <div v-if="sessionStore.voiceState === 'searching'" class="inline-card-container">
        <SearchAgentCard
          :query="currentSearchQuery"
          :status="currentSearchStatus"
          :events="currentSearchEvents"
          @add-event="handleSearchAddEvent"
          @retry="handleSearchRetry"
        />
      </div>
    </section>

    <!-- 底部状态、频谱与操作区 -->
    <footer class="conversation-footer vc-glass">
      <!-- 键盘文本输入模式与语音转写流模式的形态切换 -->
      <div class="footer-input-morph">
        <transition name="morph-fade" mode="out-in">
          <!-- 键盘键入形态：仅在闲置/未录音/未处理时展示 -->
          <div v-if="sessionStore.voiceState === 'idle'" class="morph-input-bar">
            <span class="morph-input-icon">⌨️</span>
            <input 
              type="text" 
              class="keyboard-text-input" 
              placeholder="输入您的日程指令... (例如：明早九点开会)" 
              v-model="keyboardInputText"
              @keyup.enter="handleKeyboardSubmit"
            />
            <button 
              class="morph-input-submit"
              :disabled="!keyboardInputText.trim()"
              @click="handleKeyboardSubmit"
              aria-label="提交日程"
            >
              ➔
            </button>
          </div>

          <!-- 语音输入形态：录音、解析或检索状态下展示 -->
          <div v-else class="morph-transcript-bar">
            <StreamingTranscript
              :isActive="sessionStore.isRecording || sessionStore.isProcessing || sessionStore.voiceState === 'searching'"
              :partialText="sessionStore.partialTranscript"
              :finalText="sessionStore.finalTranscript"
            />
          </div>
        </transition>
      </div>

      <!-- 实时音频波形图 (录音中显示频谱柱，支持实时音量微动) -->
      <div class="footer-visualizer" :class="{ 'footer-visualizer--visible': sessionStore.isRecording }">
        <WaveformVisualizer
          :isActive="sessionStore.isRecording"
          :volume="recorder.currentVolume.value"
          :width="300"
          :height="60"
        />
      </div>

      <!-- 快捷智能回复引导词 -->
      <div class="footer-suggestions" v-if="sessionStore.voiceState === 'idle'">
        <button 
          v-for="s in quickSuggestions" 
          :key="s" 
          class="suggestion-pill"
          @click="handleQuickInput(s)"
        >
          {{ s }}
        </button>
      </div>

      <!-- 麦克风控制与播报控制区 -->
      <div class="footer-control-row">
        <!-- 播报控制条 (TTS) -->
        <TTSControlBar
          v-if="sessionStore.isTTSPlaying"
          :isPlaying="sessionStore.isTTSPlaying"
          @play="speakLastMessage"
          @pause="stopTTS"
          @stop="stopTTS"
        />

        <div class="main-mic-button-row">
          <div class="main-mic-button">
            <VoiceButton
              :status="sessionStore.voiceState"
              :volume="recorder.currentVolume.value"
              @press-start="startVoiceInput"
              @press-end="stopVoiceInput"
              @tap="handleTapButton"
            />
          </div>
          <!-- 键盘/语音快捷形态说明标签 -->
          <span class="morph-mic-tip" v-if="sessionStore.voiceState === 'idle'">
            或按住/轻触麦克风进行语音添加
          </span>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/useSessionStore'
import { useCalendarStore } from '@/stores/useCalendarStore'
import { useHapticFeedback } from '@/composables/useHapticFeedback'
import { useTTSPlayer } from '@/composables/useTTSPlayer'
import { useWebSocket } from '@/composables/useWebSocket'
import { useAudioRecorder } from '@/composables/useAudioRecorder'
import { useVADController } from '@/composables/useVADController'

// UI 组件
import VoiceStatusIndicator from '@/modules/sensory/VoiceStatusIndicator.vue'
import ConnectionStatus from '@/modules/gateway/ConnectionStatus.vue'
import ConversationFlow from '@/modules/stateMachine/ConversationFlow.vue'
import StreamingTranscript from '@/modules/gateway/StreamingTranscript.vue'
import WaveformVisualizer from '@/modules/sensory/WaveformVisualizer.vue'
import VoiceButton from '@/modules/sensory/VoiceButton.vue'
import ClarificationCard from '@/modules/stateMachine/ClarificationCard.vue'
import ConflictNegotiation from '@/modules/stateMachine/ConflictNegotiation.vue'
import TTSControlBar from '@/modules/sensory/TTSControlBar.vue'
import SearchAgentCard from '@/modules/stateMachine/SearchAgentCard.vue'

import type { ConflictItem, WebSearchEvent, WSFrame, AgentMetadata } from '@/types/contracts'

const router = useRouter()
const sessionStore = useSessionStore()
const calendarStore = useCalendarStore()
const { vibrate } = useHapticFeedback()
const { speakText, stop: stopTTS } = useTTSPlayer()

const flowScrollContainer = ref<HTMLElement | null>(null)

// M9 Web Search Agent 状态
const currentSearchQuery = ref('')
const currentSearchStatus = ref<'searching' | 'parsing' | 'results'>('searching')
const currentSearchEvents = ref<WebSearchEvent[]>([])

const quickSuggestions = [
  '帮我创建明天下午三点的会',
  '联网检索2026年杭州的动漫展',
  '搜一下上海最近的实践活动',
  '添加买牛奶的待办'
]

// State for dynamically bound components
const currentConflicts = ref<ConflictItem[]>([])
const conflictSuggestions = ref<string[]>([])
const clarificationMissingFields = ref<string[]>([])
const clarificationMessage = ref('')

function goHome() {
  router.push('/')
}

function scrollToBottom() {
  nextTick(() => {
    if (flowScrollContainer.value) {
      flowScrollContainer.value.scrollTop = flowScrollContainer.value.scrollHeight
    }
  })
}

// ----------------------------------------------------------------------
// 真实通信：WebSocket 接入 (M2)
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
      if (payload.message) {
        sessionStore.addMessage({ role: 'system', content: payload.message, type: 'text' })
        scrollToBottom()
      }
      break
    case 'TRANSCRIPT_PARTIAL':
      sessionStore.updatePartialTranscript(payload.text)
      break
    case 'TRANSCRIPT_FINAL':
      sessionStore.setFinalTranscript(payload.text)
      break
    case 'CLARIFICATION_ASK':
      sessionStore.setVoiceState('clarifying')
      clarificationMissingFields.value = payload.missing_fields || []
      clarificationMessage.value = payload.message || '请补充信息'
      sessionStore.addMessage({ role: 'system', content: clarificationMessage.value, type: 'clarification' })
      speakText(clarificationMessage.value)
      scrollToBottom()
      break
    case 'CONFLICT_ALERT':
      sessionStore.setVoiceState('conflict')
      currentConflicts.value = payload.conflicts || []
      conflictSuggestions.value = payload.suggestions ? payload.suggestions.map((s:any) => s.reason) : []
      sessionStore.addMessage({ role: 'system', content: payload.message, type: 'conflict' })
      speakText(payload.message)
      scrollToBottom()
      break
    case 'SEMANTIC_RESULT':
      if (payload.intent === 'SEARCH' && payload.search_response) {
        sessionStore.setVoiceState('searching')
        currentSearchQuery.value = payload.search_response.search_raw_query || ''
        currentSearchStatus.value = payload.search_response.status === 'success' ? 'results' : 'searching'
        currentSearchEvents.value = (payload.search_response.extracted_events || []).map((e: any) => ({
          title: e.title || '',
          start_time: e.start_time || '',
          end_time: e.end_time || '',
          location: e.location || '',
          description: e.description || '',
          source_url: e.source_url || '',
        }))
        sessionStore.addMessage({
          role: 'system',
          content: payload.search_response.reply_text || '搜索完成',
          type: 'search',
        })
        scrollToBottom()
      }
      break
    case 'ACTION_RESULT':
      sessionStore.setVoiceState('success')
      sessionStore.addMessage({ role: 'system', content: payload.message, type: 'result' })
      if (payload.event) {
        calendarStore.addEvent(payload.event)
      }
      scrollToBottom()
      setTimeout(() => sessionStore.setVoiceState('idle'), 2000)
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
    case 'TTS_AUDIO_CHUNK':
      // 真实流式音频处理预留接口，当前直接使用前端 TTSPlayer 的 Web Speech API
      break
  }
}

// ----------------------------------------------------------------------
// 真实通信：录音采集与断句 (M1)
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
// 文本交互与快捷建议
// ----------------------------------------------------------------------
const keyboardInputText = ref('')

function handleKeyboardSubmit() {
  if (!keyboardInputText.value.trim()) return
  const text = keyboardInputText.value.trim()
  keyboardInputText.value = ''
  
  stopTTS()
  sessionStore.setVoiceState('processing')
  sessionStore.setFinalTranscript(text)
  
  sessionStore.addMessage({ role: 'user', content: text, type: 'text' })
  scrollToBottom()
  
  ws.sendFrame('TEXT_INPUT', { text }, sessionStore.sessionId)
}

function handleQuickInput(text: string) {
  stopTTS()
  sessionStore.setVoiceState('processing')
  sessionStore.setFinalTranscript(text)
  
  sessionStore.addMessage({ role: 'user', content: text, type: 'text' })
  scrollToBottom()
  
  ws.sendFrame('TEXT_INPUT', { text }, sessionStore.sessionId)
}

// ----------------------------------------------------------------------
// 组件事件：追问与冲突
// ----------------------------------------------------------------------
function handleSkipClarification() {
  ws.sendFrame('TEXT_INPUT', { text: '跳过' }, sessionStore.sessionId)
}

function handleResolveConflict(suggestion: string) {
  ws.sendFrame('TEXT_INPUT', { text: suggestion }, sessionStore.sessionId)
}

function handleForceCreate() {
  ws.sendFrame('TEXT_INPUT', { text: '强制创建' }, sessionStore.sessionId)
}

function handleCancelConflict() {
  ws.sendFrame('TEXT_INPUT', { text: '取消' }, sessionStore.sessionId)
}

// ----------------------------------------------------------------------
// 搜索代理 (Mock)
// ----------------------------------------------------------------------
function handleSearchAddEvent(event: WebSearchEvent) {
  vibrate('success')
  calendarStore.addEvent({
    id: `ev-search-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    title: event.title,
    start_time: event.start_time,
    end_time: event.end_time,
    location: event.location,
    calendar_id: 'work',
    calendar_name: '工作',
    color: '#8B5CF6',
    is_deleted: false,
    version_tag: 'v1',
    voice_raw_text: currentSearchQuery.value,
    created_at: new Date().toISOString()
  })
  
  const textFeedback = `已成功将“${event.title}”添加入您的日历日程！`
  sessionStore.addMessage({ role: 'system', content: textFeedback, type: 'result' })
  speakText(textFeedback)
  scrollToBottom()
}

function handleSearchRetry() {
  ws.sendFrame('TEXT_INPUT', { text: currentSearchQuery.value }, sessionStore.sessionId)
}

function speakLastMessage() {
  const last = latestSystemMessage.value
  if (last) {
    speakText(last.content)
    sessionStore.setVoiceState('tts_playing')
  }
}

const latestSystemMessage = computed(() => {
  return [...sessionStore.messages].reverse().find(m => m.role === 'system')
})

onMounted(() => {
  sessionStore.startSession()
  initWsSession()
  
  sessionStore.addMessage({
    role: 'system',
    content: '你好，我是你的语音日程管家。按住屏幕中下方麦克风并说话即可添加、修改或查询日程。例如你可以说：“帮我创建明天下午三点的项目评审会”',
    type: 'text'
  })
  scrollToBottom()
})
</script>

<style scoped>
.conversation-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 80px); /* 减去 Tab 导航高度 */
  height: calc(100dvh - 80px);
  gap: var(--vc-space-md);
  position: relative;
}

/* 顶部栏 */
.conversation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--vc-space-sm) 0;
  border-bottom: 1px solid var(--vc-divider);
}

.back-btn {
  width: 40px;
  height: 40px;
  border-radius: var(--vc-radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--vc-text-secondary);
  transition: all var(--vc-transition-fast);
}

.back-btn:hover {
  background: var(--vc-bg-surface);
  color: var(--vc-text-primary);
}

.header-center {
  display: flex;
  align-items: center;
}

/* 气泡流区域 */
.conversation-flow-wrap {
  flex: 1;
  overflow-y: auto;
  padding-right: var(--vc-space-xs);
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-md);
}

.inline-card-container {
  margin: var(--vc-space-sm) 0;
}



/* 底部操作区 */
.conversation-footer {
  border-top: 1px solid var(--vc-border);
  padding: var(--vc-space-md) var(--vc-space-sm) var(--vc-space-sm);
  border-radius: var(--vc-radius-lg);
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-md);
}

/* 形态切换容器 (Morph Input Block) */
.footer-input-morph {
  width: 100%;
  min-height: 52px;
  position: relative;
}

.morph-input-bar {
  display: flex;
  align-items: center;
  gap: var(--vc-space-sm);
  background: var(--vc-bg-surface);
  border: 1px solid var(--vc-border);
  border-radius: var(--vc-radius-md);
  padding: var(--vc-space-xs) var(--vc-space-sm);
  transition: all var(--vc-transition-base);
  box-shadow: var(--vc-shadow-sm);
}

.morph-input-bar:focus-within {
  border-color: var(--vc-accent);
  box-shadow: 0 0 0 3px hsla(var(--vc-accent-h), var(--vc-accent-s), var(--vc-accent-l), 0.12);
  background: var(--vc-bg-elevated);
}

.morph-input-icon {
  font-size: 16px;
  opacity: 0.6;
}

.keyboard-text-input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 8px var(--vc-space-xs);
  color: var(--vc-text-primary);
  font-size: var(--vc-text-sm);
  outline: none;
}

.keyboard-text-input::placeholder {
  color: var(--vc-text-tertiary);
}

.morph-input-submit {
  width: 28px;
  height: 28px;
  border-radius: var(--vc-radius-sm);
  background: var(--vc-bg-elevated);
  border: 1px solid var(--vc-border);
  color: var(--vc-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  cursor: pointer;
  transition: all var(--vc-transition-fast);
}

.morph-input-submit:hover:not(:disabled) {
  border-color: var(--vc-accent);
  background: hsla(var(--vc-accent-h), var(--vc-accent-s), var(--vc-accent-l), 0.08);
  color: var(--vc-text-primary);
}

.morph-input-submit:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.morph-transcript-bar {
  width: 100%;
}

/* 动效过渡 */
.morph-fade-enter-active,
.morph-fade-leave-active {
  transition: all var(--vc-transition-fast);
}

.morph-fade-enter-from,
.morph-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

.footer-visualizer {
  display: flex;
  justify-content: center;
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  transition: all var(--vc-transition-base);
}

.footer-visualizer--visible {
  max-height: 64px;
  opacity: 1;
  margin: var(--vc-space-sm) 0;
}

.footer-suggestions {
  display: flex;
  gap: var(--vc-space-sm);
  overflow-x: auto;
  padding-bottom: var(--vc-space-xs);
  scrollbar-width: none;
}

.footer-suggestions::-webkit-scrollbar {
  display: none;
}

.suggestion-pill {
  flex-shrink: 0;
  background: var(--vc-bg-surface);
  border: 1px solid var(--vc-border);
  color: var(--vc-text-secondary);
  font-size: var(--vc-text-xs);
  padding: 6px 14px;
  border-radius: var(--vc-radius-full);
  transition: all var(--vc-transition-fast);
}

.suggestion-pill:hover {
  border-color: var(--vc-primary-light);
  color: var(--vc-text-primary);
  background: hsla(var(--vc-primary-h), var(--vc-primary-s), var(--vc-primary-l), 0.08);
}

.footer-control-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--vc-space-sm);
}

.main-mic-button-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--vc-space-xs);
}

.main-mic-button {
  display: flex;
  justify-content: center;
  align-items: center;
}

.morph-mic-tip {
  font-size: 10px;
  color: var(--vc-text-tertiary);
  transition: opacity var(--vc-transition-base);
}
</style>
