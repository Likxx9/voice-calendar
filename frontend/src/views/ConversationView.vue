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
          :message="'请问这个日程的主题是什么？比如“和产品经理对需求”'"
          :missingFields="['title']"
          @voice-reply="startVoiceInput"
          @skip="handleSkipClarification"
        />
      </div>

      <!-- 实时时间冲突卡片 (Conflict Negotiation) -->
      <div v-if="sessionStore.voiceState === 'conflict'" class="inline-card-container">
        <ConflictNegotiation
          :conflicts="mockConflicts"
          :suggestions="['改期至下午 3:30', '改期至明天下午同一时间', '仍然强制创建']"
          @select="handleResolveConflict"
          @voice-resolve="startVoiceInput"
          @force-create="handleForceCreate"
          @cancel="handleCancelConflict"
        />
      </div>

      <!-- 多方忙闲协同推荐 -->
      <div v-if="showFreeBusy" class="inline-card-container freebusy-container">
        <FreeBusyTimeline 
          :attendees="mockFreeBusySlots" 
          :freeWindows="mockFreeWindows"
          @select-window="handleSelectFreeBusyWindow"
        />
        <MeetingSuggestion 
          :suggestions="mockFreeWindows"
          @select-suggestion="handleSelectFreeBusyWindow"
        />
      </div>
    </section>

    <!-- 底部状态、频谱与操作区 -->
    <footer class="conversation-footer vc-glass">
      <!-- 实时逐字听写转写 -->
      <div class="footer-transcript">
        <StreamingTranscript
          :isActive="sessionStore.isRecording || sessionStore.isProcessing"
          :partialText="sessionStore.partialTranscript"
          :finalText="sessionStore.finalTranscript"
        />
      </div>

      <!-- 实时音频波形图 (录音中显示频谱柱) -->
      <div class="footer-visualizer">
        <WaveformVisualizer
          :isActive="sessionStore.isRecording"
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

      <!-- 麦克风控制区 -->
      <div class="footer-control-row">
        <!-- 播报控制条 (TTS) -->
        <TTSControlBar
          v-if="sessionStore.isTTSPlaying"
          :isPlaying="sessionStore.isTTSPlaying"
          @play="speakLastMessage"
          @pause="stopTTS"
          @stop="stopTTS"
        />

        <div class="main-mic-button">
          <VoiceButton
            :status="sessionStore.voiceState"
            :volume="mockVolume"
            @press-start="startVoiceInput"
            @press-end="stopVoiceInput"
            @tap="handleTapButton"
          />
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

// UI 组件
import VoiceStatusIndicator from '@/modules/sensory/VoiceStatusIndicator.vue'
import ConnectionStatus from '@/modules/gateway/ConnectionStatus.vue'
import ConversationFlow from '@/modules/stateMachine/ConversationFlow.vue'
import StreamingTranscript from '@/modules/gateway/StreamingTranscript.vue'
import WaveformVisualizer from '@/modules/sensory/WaveformVisualizer.vue'
import VoiceButton from '@/modules/sensory/VoiceButton.vue'
import ClarificationCard from '@/modules/stateMachine/ClarificationCard.vue'
import ConflictNegotiation from '@/modules/stateMachine/ConflictNegotiation.vue'
import FreeBusyTimeline from '@/modules/coordination/FreeBusyTimeline.vue'
import MeetingSuggestion from '@/modules/coordination/MeetingSuggestion.vue'
import TTSControlBar from '@/modules/sensory/TTSControlBar.vue'

import type { ConflictItem, FreeBusySlot } from '@/types/contracts'

const router = useRouter()
const sessionStore = useSessionStore()
const calendarStore = useCalendarStore()
const { vibrate } = useHapticFeedback()
const { speakText, stop: stopTTS } = useTTSPlayer()

const flowScrollContainer = ref<HTMLElement | null>(null)
const mockVolume = ref(0)
const showFreeBusy = ref(false)

const quickSuggestions = [
  '帮我创建明天下午三点的会',
  '明天下午两点开会',
  '添加买牛奶的待办',
  '查询大家明天的忙闲'
]

// 模拟忙闲与建议数据
const mockFreeBusySlots = ref<FreeBusySlot[]>([
  {
    email: 'alex@corp.com',
    busy_periods: [
      { start: `${new Date().toISOString().split('T')[0]}T10:00:00`, end: `${new Date().toISOString().split('T')[0]}T12:00:00` },
      { start: `${new Date().toISOString().split('T')[0]}T15:00:00`, end: `${new Date().toISOString().split('T')[0]}T16:30:00` }
    ]
  },
  {
    email: 'bob@corp.com',
    busy_periods: [
      { start: `${new Date().toISOString().split('T')[0]}T09:00:00`, end: `${new Date().toISOString().split('T')[0]}T10:30:00` },
      { start: `${new Date().toISOString().split('T')[0]}T14:00:00`, end: `${new Date().toISOString().split('T')[0]}T15:30:00` }
    ]
  }
])

const mockFreeWindows = computed(() => {
  const todayStr = new Date().toISOString().split('T')[0]
  return [
    { start: `${todayStr}T13:00:00`, end: `${todayStr}T14:00:00`, score: 0.95 },
    { start: `${todayStr}T16:30:00`, end: `${todayStr}T17:30:00`, score: 0.88 },
    { start: `${todayStr}T08:00:00`, end: `${todayStr}T09:00:00`, score: 0.65 }
  ]
})

const mockConflicts = computed<ConflictItem[]>(() => {
  const todayStr = new Date().toISOString().split('T')[0]
  return [{
    existing_event_id: 'ev-2',
    existing_title: '语音日历前端架构评审',
    overlap_start: `${todayStr}T14:00:00`,
    overlap_end: `${todayStr}T15:30:00`,
    severity: 'full'
  }]
})

function goHome() {
  router.push('/')
}

// 自动滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (flowScrollContainer.value) {
      flowScrollContainer.value.scrollTop = flowScrollContainer.value.scrollHeight
    }
  })
}

// 模拟音量变化
let volumeInterval: ReturnType<typeof setInterval> | null = null
function simulateVolume() {
  volumeInterval = setInterval(() => {
    mockVolume.value = Math.random() * 0.8
  }, 120)
}
function stopVolumeSimulation() {
  if (volumeInterval) {
    clearInterval(volumeInterval)
    volumeInterval = null
  }
  mockVolume.value = 0
}

// 语音交互状态流控制
function startVoiceInput() {
  stopTTS()
  vibrate('recording')
  sessionStore.setVoiceState('recording')
  sessionStore.setConnectionState('connected')
  sessionStore.updatePartialTranscript('正在倾听您的指令...')
  simulateVolume()
}

function stopVoiceInput() {
  stopVolumeSimulation()
  vibrate('processing')
  sessionStore.setVoiceState('processing')
  sessionStore.setFinalTranscript('明天下午三点和PM开会')
  
  setTimeout(() => {
    processUserInput('明天下午三点和PM开会')
  }, 1200)
}

function handleTapButton() {
  if (sessionStore.isTTSPlaying) {
    stopTTS()
    sessionStore.setVoiceState('idle')
  } else if (sessionStore.voiceState === 'idle') {
    startVoiceInput()
    setTimeout(() => {
      stopVoiceInput()
    }, 3000)
  }
}

function handleQuickInput(text: string) {
  stopTTS()
  sessionStore.setVoiceState('processing')
  sessionStore.setFinalTranscript(text)
  setTimeout(() => {
    processUserInput(text)
  }, 1000)
}

// 对话与场景核心逻辑
function processUserInput(text: string) {
  // 1. 添加用户消息
  sessionStore.addMessage({
    role: 'user',
    content: text,
    type: 'voice'
  })
  scrollToBottom()

  // 2. 规则路由与意图匹配模拟
  if (text.includes('大家') || text.includes('忙闲') || text.includes('空闲')) {
    // 触发多人忙闲协同视图
    showFreeBusy.value = true
    sessionStore.setVoiceState('tts_playing')
    sessionStore.addMessage({
      role: 'system',
      content: '我已获取到了 Alex 和 Bob 明天的忙闲信息。最佳共同空闲推荐为下午 1:00 至 2:00，匹配度高达 95%。您是否需要创建此时间的会议？',
      type: 'clarification'
    })
    speakText('我已获取到了所有参与者明天的忙闲信息。最推荐的时间段是下午一点。')
  } else if (text.includes('两点') || text.includes('14:00')) {
    // 触发时间冲突
    sessionStore.setVoiceState('conflict')
    sessionStore.addMessage({
      role: 'system',
      content: '检测到时间冲突！明天下午 14:00 有已存在日程“语音日历前端架构评审”。推荐改期至下午 3:30，或在明天同一时间强制创建。',
      type: 'conflict'
    })
    vibrate('conflict')
    speakText('对不起，两点钟您有另一个日程冲突。推荐改期到下午三点半，或者强制创建。')
  } else if (text.includes('待办') || text.includes('任务')) {
    // 创建待办
    const taskTitle = text.replace(/帮我|添加|待办|任务/g, '').trim() || '新待办任务'
    calendarStore.addTask({
      id: `task-${Date.now()}`,
      title: taskTitle,
      priority: 'medium',
      is_completed: false,
      is_deleted: false,
      version_tag: 'v1',
      created_at: new Date().toISOString()
    })
    sessionStore.setVoiceState('success')
    sessionStore.addMessage({
      role: 'system',
      content: `好的，已成功添加待办任务：${taskTitle}`,
      type: 'result'
    })
    vibrate('success')
    speakText(`已为您添加待办：${taskTitle}`)
    setTimeout(() => { sessionStore.setVoiceState('idle') }, 2000)
  } else if (text.includes('三点') || text.includes('下午3点') || text.includes('15:00')) {
    // 完美匹配创建日程
    const todayStr = new Date().toISOString().split('T')[0]
    calendarStore.addEvent({
      id: `ev-${Date.now()}`,
      title: '和 PM 沟通对齐会',
      start_time: `${todayStr}T15:00:00`,
      end_time: `${todayStr}T16:00:00`,
      calendar_id: 'work',
      calendar_name: '工作',
      color: '#8B5CF6',
      is_deleted: false,
      version_tag: 'v1',
      created_at: new Date().toISOString()
    })
    sessionStore.setVoiceState('success')
    sessionStore.addMessage({
      role: 'system',
      content: '好的，已为您成功创建明天下午 3:00 的日程：“和 PM 沟通对齐会”',
      type: 'result'
    })
    vibrate('success')
    speakText('好的，已为您成功创建明天下午三点的沟通会！')
    setTimeout(() => { sessionStore.setVoiceState('idle') }, 2000)
  } else {
    // 意图不明，触发追问 Clarification
    sessionStore.setVoiceState('clarifying')
    sessionStore.addMessage({
      role: 'system',
      content: '收到添加日程请求。但我没有抓取到明确的日程主题。请问您的日程标题是什么？',
      type: 'clarification'
    })
    speakText('收到日程请求。请问这个日程的主题是什么？')
  }
  scrollToBottom()
}

// 冲突解决
function handleResolveConflict(_suggestion: string) {
  const todayStr = new Date().toISOString().split('T')[0]
  calendarStore.addEvent({
    id: `ev-${Date.now()}`,
    title: '调整后的PM对齐会议',
    start_time: `${todayStr}T15:30:00`,
    end_time: `${todayStr}T16:30:00`,
    calendar_id: 'work',
    calendar_name: '工作',
    color: '#8B5CF6',
    is_deleted: false,
    version_tag: 'v1',
    created_at: new Date().toISOString()
  })
  
  sessionStore.setVoiceState('success')
  sessionStore.addMessage({
    role: 'system',
    content: `冲突已解决！已创建日程：调整后的PM对齐会议，时间调整为下午 15:30 - 16:30。`,
    type: 'result'
  })
  vibrate('success')
  speakText('冲突已解决，已为您把会议调整到下午三点半！')
  setTimeout(() => { sessionStore.setVoiceState('idle') }, 2000)
  scrollToBottom()
}

function handleForceCreate() {
  const todayStr = new Date().toISOString().split('T')[0]
  calendarStore.addEvent({
    id: `ev-${Date.now()}`,
    title: 'PM对齐会议 (强制覆盖)',
    start_time: `${todayStr}T14:00:00`,
    end_time: `${todayStr}T15:00:00`,
    calendar_id: 'work',
    calendar_name: '工作',
    color: '#D32F2F',
    is_deleted: false,
    version_tag: 'v1',
    created_at: new Date().toISOString()
  })
  
  sessionStore.setVoiceState('success')
  sessionStore.addMessage({
    role: 'system',
    content: `已为您强行创建明天下午 14:00 的日程，请注意与既有日程时间重叠！`,
    type: 'result'
  })
  vibrate('success')
  speakText('已强行创建日程，请注意日程存在时间上的冲突。')
  setTimeout(() => { sessionStore.setVoiceState('idle') }, 2000)
  scrollToBottom()
}

function handleCancelConflict() {
  sessionStore.setVoiceState('idle')
  sessionStore.addMessage({
    role: 'system',
    content: `已取消创建日程。`,
    type: 'text'
  })
  speakText('已取消。')
}

// 补充信息回答
function handleSkipClarification() {
  const todayStr = new Date().toISOString().split('T')[0]
  calendarStore.addEvent({
    id: `ev-${Date.now()}`,
    title: '未命名日程',
    start_time: `${todayStr}T16:00:00`,
    end_time: `${todayStr}T17:00:00`,
    calendar_id: 'personal',
    calendar_name: '个人',
    color: '#10B981',
    is_deleted: false,
    version_tag: 'v1',
    created_at: new Date().toISOString()
  })
  sessionStore.setVoiceState('success')
  speakText('已为您创建未命名日程')
  setTimeout(() => { sessionStore.setVoiceState('idle') }, 2000)
}

function handleSelectFreeBusyWindow(w: { start: string; end: string; score: number }) {
  showFreeBusy.value = false
  calendarStore.addEvent({
    id: `ev-${Date.now()}`,
    title: '多人协同联合技术交流会',
    start_time: w.start,
    end_time: w.end,
    calendar_id: 'work',
    calendar_name: '工作',
    color: '#8B5CF6',
    is_deleted: false,
    version_tag: 'v1',
    created_at: new Date().toISOString()
  })
  sessionStore.setVoiceState('success')
  sessionStore.addMessage({
    role: 'system',
    content: `好的，已成功协调所有参与者，创建明天联合会议于 ${w.start.substring(11, 16)} - ${w.end.substring(11, 16)}`,
    type: 'result'
  })
  vibrate('success')
  speakText('联合会议创建成功！')
  setTimeout(() => { sessionStore.setVoiceState('idle') }, 2000)
}

function speakLastMessage() {
  const last = latestSystemMessage.value
  if (last) {
    speakText(last.content)
    sessionStore.setVoiceState('tts_playing')
  }
}

// 最新的一条系统播报
const latestSystemMessage = computed(() => {
  return [...sessionStore.messages]
    .reverse()
    .find(m => m.role === 'system')
})

onMounted(() => {
  sessionStore.startSession()
  sessionStore.setConnectionState('connected')
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

.freebusy-container {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-md);
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

.footer-transcript {
  min-height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.footer-visualizer {
  display: flex;
  justify-content: center;
}

.footer-suggestions {
  display: flex;
  gap: var(--vc-space-sm);
  overflow-x: auto;
  padding-bottom: var(--vc-space-xs);
  scrollbar-width: none; /* Firefox */
}

.footer-suggestions::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
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
  background: rgba(var(--vc-primary-h), 76%, 0.08);
}

.footer-control-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--vc-space-sm);
}

.main-mic-button {
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
