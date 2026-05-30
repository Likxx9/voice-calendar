/* ============================================================
 * Pinia Store — 会话与语音状态管理
 * 管理录音状态、会话 ID、对话历史、当前状态机节点
 * ============================================================ */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  VoiceState,
  ConnectionState,
  ConversationMessage,
  EventDraft,
  TaskDraft,
  ConflictResult,
} from '@/types/contracts'

export const useSessionStore = defineStore('session', () => {
  // ── 会话基础状态 ─────────────────────────────────
  const sessionId = ref<string>('')
  const voiceState = ref<VoiceState>('idle')
  const connectionState = ref<ConnectionState>('disconnected')

  // ── 登录与用户状态 ──────────────────────────────
  const isLoggedIn = ref<boolean>(localStorage.getItem('vc_logged_in') === 'true')
  const currentUser = ref<{ name: string; email: string; avatar: string } | null>(
    localStorage.getItem('vc_user') ? JSON.parse(localStorage.getItem('vc_user')!) : null
  )

  // ── 对话历史 ─────────────────────────────────────
  const messages = ref<ConversationMessage[]>([])

  // ── 当前草稿（多轮追问期间暂存）─────────────────
  const currentEventDraft = ref<EventDraft | null>(null)
  const currentTaskDraft = ref<TaskDraft | null>(null)

  // ── 冲突与忙闲（临时状态）─────────────────────
  const currentConflict = ref<ConflictResult | null>(null)

  // ── 流式转写（实时）──────────────────────────────
  const partialTranscript = ref<string>('')
  const finalTranscript = ref<string>('')

  // ── 计算属性 ─────────────────────────────────────
  const isRecording = computed(() => voiceState.value === 'recording')
  const isProcessing = computed(() => voiceState.value === 'processing')
  const isTTSPlaying = computed(() => voiceState.value === 'tts_playing')
  const isConnected = computed(() => connectionState.value === 'connected')
  const hasConflict = computed(() => currentConflict.value?.has_conflict ?? false)

  // ── 动作 ─────────────────────────────────────────
  function startSession() {
    sessionId.value = `sess_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
    voiceState.value = 'idle'
    messages.value = []
    currentEventDraft.value = null
    currentTaskDraft.value = null
    currentConflict.value = null
    partialTranscript.value = ''
    finalTranscript.value = ''
  }

  function setVoiceState(state: VoiceState) {
    voiceState.value = state
  }

  function setConnectionState(state: ConnectionState) {
    connectionState.value = state
  }

  function addMessage(message: Omit<ConversationMessage, 'id' | 'timestamp'>) {
    messages.value.push({
      ...message,
      id: `msg_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      timestamp: new Date().toISOString(),
    })
  }

  function updatePartialTranscript(text: string) {
    partialTranscript.value = text
  }

  function setFinalTranscript(text: string) {
    finalTranscript.value = text
    partialTranscript.value = ''
  }

  function setEventDraft(draft: EventDraft | null) {
    currentEventDraft.value = draft
  }

  function setTaskDraft(draft: TaskDraft | null) {
    currentTaskDraft.value = draft
  }

  function setConflict(conflict: ConflictResult | null) {
    currentConflict.value = conflict
  }

  function login(email: string, name: string) {
    isLoggedIn.value = true
    currentUser.value = { name, email, avatar: '🎙️' }
    localStorage.setItem('vc_logged_in', 'true')
    localStorage.setItem('vc_user', JSON.stringify(currentUser.value))
  }

  function logout() {
    isLoggedIn.value = false
    currentUser.value = null
    localStorage.removeItem('vc_logged_in')
    localStorage.removeItem('vc_user')
    clearSession()
  }

  function clearSession() {
    sessionId.value = ''
    voiceState.value = 'idle'
    messages.value = []
    currentEventDraft.value = null
    currentTaskDraft.value = null
    currentConflict.value = null
    partialTranscript.value = ''
    finalTranscript.value = ''
  }

  return {
    // 状态
    sessionId,
    voiceState,
    connectionState,
    isLoggedIn,
    currentUser,
    messages,
    currentEventDraft,
    currentTaskDraft,
    currentConflict,
    partialTranscript,
    finalTranscript,
    // 计算属性
    isRecording,
    isProcessing,
    isTTSPlaying,
    isConnected,
    hasConflict,
    // 动作
    startSession,
    setVoiceState,
    setConnectionState,
    addMessage,
    updatePartialTranscript,
    setFinalTranscript,
    setEventDraft,
    setTaskDraft,
    setConflict,
    clearSession,
    login,
    logout,
  }
})
