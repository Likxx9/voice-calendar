<template>
  <div class="center-workspace" :class="{ 'desktop-mode': isDesktop }">
    <!-- Top 20%: Greeting & Indicators -->
    <header class="workspace-header">
      <div v-if="!isDesktop" class="swipe-indicators">
        <span class="indicator-text">&lt; 设置</span>
        <span class="indicator-text">日历 &gt;</span>
      </div>
      <div class="greeting">
        <h2 class="greeting-title">{{ greetingMessage }}</h2>
        <p class="greeting-sub">距离下一个会议还有 {{ nextMeetingIn }}</p>
      </div>
    </header>

    <!-- Middle 50%: Dynamic Island / Cards -->
    <main class="workspace-body">
      <!-- 冲突解决卡片 -->
      <transition name="fade-slide-up">
        <div v-if="voiceState === 'conflict'" class="inline-conflict-card">
          <div class="conflict-header">
            <span class="warning-icon">⚠️</span>
            <h3>发现时间冲突</h3>
          </div>
          <div class="conflict-content">
            <div v-for="(conflict, idx) in currentConflicts" :key="idx" class="conflict-item">
              <span class="dot"></span>
              {{ conflict.existing_title }}
            </div>
          </div>
          <div class="conflict-actions">
            <button 
              v-for="sug in conflictSuggestions" 
              :key="sug" 
              class="action-btn primary"
              @click="$emit('resolve-conflict', sug)"
            >
              {{ sug }}
            </button>
            <button class="action-btn outline" @click="$emit('cancel-conflict')">取消</button>
          </div>
        </div>
      </transition>
    </main>

    <!-- Bottom 30%: Floating Voice Hub & Optional Text Input -->
    <footer class="workspace-footer">
      <div v-if="isDesktop" class="desktop-input-container">
        <input 
          v-model="textInput"
          type="text" 
          placeholder="或者输入您的日程指令..." 
          class="desktop-text-input"
          @keyup.enter="submitText"
        />
        <button class="send-btn" @click="submitText" :disabled="!textInput.trim()">发送</button>
      </div>

      <FloatingVoiceHub
        :voice-state="voiceState"
        :partial-transcript="partialTranscript"
        :volume="volume"
        @press-start="$emit('press-start')"
        @press-end="$emit('press-end')"
        @tap="$emit('tap-mic')"
      />
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
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

const textInput = ref('')

function submitText() {
  if (textInput.value.trim()) {
    emit('send-text', textInput.value)
    textInput.value = ''
  }
}

const greetingMessage = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return '早上好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const nextMeetingIn = computed(() => '45 分钟')
</script>

<style scoped>
.center-workspace {
  width: 100%;
  height: 100%;
  background-color: transparent;
  display: flex;
  flex-direction: column;
}

/* Top 20% */
.workspace-header {
  flex: 0 0 20%;
  display: flex;
  flex-direction: column;
  padding: env(safe-area-inset-top) var(--vc-space-xl) 0;
}

.swipe-indicators {
  display: flex;
  justify-content: space-between;
  padding: var(--vc-space-md) 0;
  opacity: 0.5;
}

.indicator-text {
  font-size: var(--vc-text-xs);
  color: var(--vc-text-secondary);
  font-weight: var(--vc-weight-bold);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.greeting {
  margin-top: auto;
  padding-bottom: var(--vc-space-lg);
}

.desktop-mode .workspace-header {
  padding-top: var(--vc-space-2xl); /* 桌面端没有状态栏 */
}

.greeting-title {
  font-size: var(--vc-text-3xl);
  font-weight: var(--vc-weight-bold);
  color: var(--vc-text-primary);
  margin: 0 0 var(--vc-space-xs);
  letter-spacing: -0.5px;
}

.greeting-sub {
  font-size: var(--vc-text-base);
  color: var(--vc-text-secondary);
  margin: 0;
}

/* Middle 50% */
.workspace-body {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--vc-space-lg);
  position: relative;
}

.inline-conflict-card {
  width: 100%;
  max-width: 440px;
  background: var(--vc-bg-surface);
  border-radius: var(--vc-radius-lg);
  padding: var(--vc-space-lg);
  box-shadow: var(--vc-shadow-lg);
  border: 1px solid var(--vc-warning-soft);
}

.conflict-header {
  display: flex;
  align-items: center;
  gap: var(--vc-space-sm);
  color: var(--vc-warning);
  margin-bottom: var(--vc-space-md);
}

.conflict-header h3 {
  margin: 0;
  font-size: var(--vc-text-lg);
}

.conflict-content {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-sm);
  margin-bottom: var(--vc-space-lg);
}

.conflict-item {
  display: flex;
  align-items: center;
  gap: var(--vc-space-sm);
  font-size: var(--vc-text-sm);
  color: var(--vc-text-primary);
}

.dot {
  width: 8px;
  height: 8px;
  background: var(--vc-warning);
  border-radius: 50%;
}

.conflict-actions {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-sm);
}

.action-btn {
  padding: var(--vc-space-md);
  border-radius: var(--vc-radius-md);
  font-weight: var(--vc-weight-bold);
  font-size: var(--vc-text-sm);
  transition: opacity var(--vc-transition-fast);
  cursor: pointer;
}

.action-btn:active {
  opacity: 0.7;
}

.action-btn.primary {
  background: var(--vc-accent);
  color: var(--vc-text-inverse);
  border: none;
}

.action-btn.outline {
  background: transparent;
  color: var(--vc-text-secondary);
  border: 1px solid var(--vc-border);
}

/* Bottom 30% */
.workspace-footer {
  flex: 0 0 30%;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  gap: var(--vc-space-xl);
}

/* 桌面端文本输入框 */
.desktop-input-container {
  display: flex;
  gap: var(--vc-space-sm);
  width: 100%;
  max-width: 440px;
  padding: 0 var(--vc-space-lg);
  z-index: 50;
}

.desktop-text-input {
  flex: 1;
  padding: var(--vc-space-sm) var(--vc-space-md);
  border: 1px solid var(--vc-divider);
  border-radius: var(--vc-radius-full);
  font-size: var(--vc-text-base);
  background: var(--vc-bg-base);
  color: var(--vc-text-primary);
  outline: none;
  transition: border-color var(--vc-transition-fast);
}

.desktop-text-input:focus {
  border-color: var(--vc-accent);
  background: var(--vc-bg-surface);
}

.send-btn {
  background: var(--vc-accent);
  color: var(--vc-text-inverse);
  border: none;
  padding: 0 var(--vc-space-lg);
  border-radius: var(--vc-radius-full);
  font-weight: var(--vc-weight-semibold);
  cursor: pointer;
  transition: opacity 0.2s;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Transitions */
.fade-slide-up-enter-active,
.fade-slide-up-leave-active {
  transition: all var(--vc-transition-spring);
}
.fade-slide-up-enter-from,
.fade-slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}
</style>
