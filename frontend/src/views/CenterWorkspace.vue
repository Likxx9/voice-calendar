<template>
  <div class="center-workspace" :class="{ 'desktop-mode': isDesktop }">
    <!-- Top: Header with greeting -->
    <header class="workspace-header">
      <div v-if="!isDesktop" class="swipe-indicators">
        <span class="indicator-text">&lt; 设置</span>
        <span class="indicator-text">日历 &gt;</span>
      </div>
      <div class="greeting">
        <h2 class="greeting-title">{{ greetingMessage }}</h2>
        <p class="greeting-sub">语音日历助手为您服务</p>
      </div>
    </header>

    <!-- Middle: Chat Messages Area -->
    <main class="workspace-chat">
      <div class="chat-messages" ref="chatContainer">
        <TransitionGroup name="chat-bubble">
          <div
            v-for="msg in sessionStore.messages"
            :key="msg.id"
            class="chat-message"
            :class="`chat-message--${msg.role}`"
          >
            <!-- Avatar -->
            <div class="chat-avatar">
              <span v-if="msg.role === 'user'">👤</span>
              <span v-else>🤖</span>
            </div>
            
            <!-- Message Bubble -->
            <div class="chat-bubble" :class="`chat-bubble--${msg.role}`">
              <p class="chat-text">{{ msg.content }}</p>
              <span class="chat-time">{{ formatTime(msg.timestamp) }}</span>
            </div>
          </div>
        </TransitionGroup>
        
        <!-- Loading indicator -->
        <div v-if="voiceState === 'processing' || voiceState === 'searching'" class="chat-message chat-message--system">
          <div class="chat-avatar"><span>🤖</span></div>
          <div class="chat-bubble chat-bubble--system chat-bubble--loading">
            <div class="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Bottom: Input Area -->
    <footer class="workspace-footer">
      <!-- Quick Suggestions -->
      <div v-if="voiceState === 'idle' && quickSuggestions.length" class="quick-suggestions">
        <button
          v-for="s in quickSuggestions"
          :key="s"
          class="suggestion-chip"
          @click="$emit('send-text', s)"
        >
          {{ s }}
        </button>
      </div>

      <!-- Input Bar -->
      <div class="input-bar">
        <!-- Text Input -->
        <div class="text-input-wrapper">
          <input 
            v-model="textInput"
            type="text" 
            placeholder="输入日程指令..." 
            class="text-input"
            @keyup.enter="submitText"
            :disabled="voiceState !== 'idle'"
          />
          <button 
            class="send-btn" 
            @click="submitText" 
            :disabled="!textInput.trim() || voiceState !== 'idle'"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>

        <!-- Voice Button -->
        <div class="voice-btn-wrapper">
          <FloatingVoiceHub
            :voice-state="voiceState"
            :partial-transcript="partialTranscript"
            :volume="volume"
            @press-start="$emit('press-start')"
            @press-end="$emit('press-end')"
            @tap="$emit('tap-mic')"
          />
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import { useSessionStore } from '@/stores/useSessionStore'
import FloatingVoiceHub from '@/components/FloatingVoiceHub.vue'
import type { VoiceState, ConflictItem } from '@/types/contracts'

const props = defineProps<{
  voiceState: VoiceState
  partialTranscript: string
  volume: number
  currentConflicts: ConflictItem[]
  conflictSuggestions: string[]
  isDesktop?: boolean
}>()

const emit = defineEmits<{
  (e: 'press-start'): void
  (e: 'press-end'): void
  (e: 'tap-mic'): void
  (e: 'resolve-conflict', suggestion: string): void
  (e: 'cancel-conflict'): void
  (e: 'send-text', text: string): void
}>()

const sessionStore = useSessionStore()
const textInput = ref('')
const chatContainer = ref<HTMLElement | null>(null)
const quickSuggestions = ref<string[]>([
  '帮我创建明天下午三点的会',
  '查看今天的日程',
  '添加买牛奶的待办'
])

// Auto scroll to bottom when new messages arrive
watch(() => sessionStore.messages.length, async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
})

function submitText() {
  if (textInput.value.trim() && props.voiceState === 'idle') {
    emit('send-text', textInput.value)
    textInput.value = ''
  }
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

const greetingMessage = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return '早上好'
  if (hour < 18) return '下午好'
  return '晚上好'
})
</script>

<style scoped>
.center-workspace {
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, var(--vc-bg-base) 0%, var(--vc-bg-elevated) 100%);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.workspace-header {
  flex: 0 0 auto;
  padding: env(safe-area-inset-top) var(--vc-space-lg) var(--vc-space-md);
}

.swipe-indicators {
  display: flex;
  justify-content: space-between;
  padding: var(--vc-space-sm) 0;
  opacity: 0.4;
}

.indicator-text {
  font-size: 11px;
  color: var(--vc-text-secondary);
  font-weight: 600;
  letter-spacing: 1px;
}

.greeting {
  padding: var(--vc-space-sm) 0;
}

.greeting-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--vc-text-primary);
  margin: 0;
}

.greeting-sub {
  font-size: 14px;
  color: var(--vc-text-secondary);
  margin: 4px 0 0;
}

/* Chat Area */
.workspace-chat {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 0 var(--vc-space-md);
  scroll-behavior: smooth;
}

/* Message Styles */
.chat-message {
  display: flex;
  gap: var(--vc-space-sm);
  margin-bottom: var(--vc-space-md);
  max-width: 85%;
}

.chat-message--user {
  align-self: flex-end;
  margin-left: auto;
  flex-direction: row-reverse;
}

.chat-message--system {
  align-self: flex-start;
}

.chat-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--vc-bg-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.chat-bubble {
  padding: var(--vc-space-sm) var(--vc-space-md);
  border-radius: 16px;
  position: relative;
}

.chat-bubble--user {
  background: linear-gradient(135deg, var(--vc-primary), var(--vc-primary-dark));
  color: white;
  border-bottom-right-radius: 4px;
}

.chat-bubble--system {
  background: var(--vc-bg-surface);
  border: 1px solid var(--vc-border);
  color: var(--vc-text-primary);
  border-bottom-left-radius: 4px;
}

.chat-bubble--loading {
  padding: var(--vc-space-sm) var(--vc-space-lg);
}

.chat-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}

.chat-time {
  font-size: 11px;
  opacity: 0.6;
  margin-top: 4px;
  display: block;
}

/* Typing Indicator */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--vc-text-secondary);
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4px); opacity: 1; }
}

/* Footer */
.workspace-footer {
  flex: 0 0 auto;
  padding: var(--vc-space-sm) var(--vc-space-md) env(safe-area-inset-bottom);
  background: var(--vc-bg-base);
  border-top: 1px solid var(--vc-border);
}

/* Quick Suggestions */
.quick-suggestions {
  display: flex;
  gap: var(--vc-space-sm);
  padding: var(--vc-space-sm) 0;
  overflow-x: auto;
  scrollbar-width: none;
}

.quick-suggestions::-webkit-scrollbar {
  display: none;
}

.suggestion-chip {
  flex-shrink: 0;
  padding: 6px 12px;
  border-radius: 20px;
  background: var(--vc-bg-surface);
  border: 1px solid var(--vc-border);
  color: var(--vc-text-primary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.suggestion-chip:hover {
  background: var(--vc-primary);
  color: white;
  border-color: var(--vc-primary);
}

/* Input Bar */
.input-bar {
  display: flex;
  align-items: center;
  gap: var(--vc-space-sm);
}

.text-input-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  background: var(--vc-bg-surface);
  border: 1px solid var(--vc-border);
  border-radius: 24px;
  padding: 4px 4px 4px 16px;
}

.text-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 14px;
  color: var(--vc-text-primary);
  outline: none;
}

.text-input::placeholder {
  color: var(--vc-text-secondary);
}

.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--vc-primary);
  border: none;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.send-btn:hover:not(:disabled) {
  background: var(--vc-primary-dark);
  transform: scale(1.05);
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.voice-btn-wrapper {
  flex-shrink: 0;
}

/* Desktop Mode */
.desktop-mode .workspace-header {
  padding-top: var(--vc-space-2xl);
}

.desktop-mode .chat-messages {
  max-width: 600px;
  margin: 0 auto;
  width: 100%;
}

/* Animations */
.chat-bubble-enter-active {
  animation: bubble-in 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes bubble-in {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>
