<template>
  <div class="floating-voice-hub" :class="[stateClass, { 'is-active': isActive }]">
    <!-- Thinking State (Agent Processing) Text -->
    <transition name="fade-slide-up">
      <div v-if="voiceState === 'processing' || voiceState === 'searching'" class="agent-status-text">
        <span class="pulse-dot"></span>
        {{ currentAgentStatusText }}
      </div>
    </transition>

    <!-- Listening State Text (ASR Transcript) -->
    <transition name="fade-slide-up">
      <div v-if="voiceState === 'recording'" class="listening-text">
        {{ partialTranscript || '正在聆听...' }}
      </div>
    </transition>

    <!-- The Hub Button -->
    <button 
      class="hub-button"
      @mousedown="startPress"
      @mouseup="endPress"
      @mouseleave="endPress"
      @touchstart.prevent="startPress"
      @touchend.prevent="endPress"
      @click="handleClick"
    >
      <div class="hub-circle" :style="circleStyle">
        <svg v-if="voiceState === 'idle' || voiceState === 'recording'" viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" y1="19" x2="12" y2="22" />
        </svg>

        <!-- Loading Spinner for Thinking state -->
        <svg v-else-if="voiceState === 'processing' || voiceState === 'searching'" class="spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="2" x2="12" y2="6"></line>
          <line x1="12" y1="18" x2="12" y2="22"></line>
          <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
          <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
          <line x1="2" y1="12" x2="6" y2="12"></line>
          <line x1="18" y1="12" x2="22" y2="12"></line>
          <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
          <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
        </svg>
      </div>

      <!-- Ripple Rings for Listening State -->
      <div v-if="voiceState === 'recording'" class="ripple-ring ring-1"></div>
      <div v-if="voiceState === 'recording'" class="ripple-ring ring-2"></div>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { VoiceState } from '@/types/contracts'

const props = defineProps<{
  voiceState: VoiceState
  partialTranscript: string
  volume: number
}>()

const emit = defineEmits<{
  (e: 'tap'): void
  (e: 'press-start'): void
  (e: 'press-end'): void
}>()

const isPressing = ref(false)
const pressTimer = ref<number | null>(null)
let tapFired = false

// Computed classes
const isActive = computed(() => props.voiceState !== 'idle')
const stateClass = computed(() => `state-${props.voiceState}`)

// Mock agent status text for demonstration
const currentAgentStatusText = computed(() => {
  if (props.voiceState === 'searching') return '正在联网检索...'
  return 'Agent 正在进行推理计算...'
})

// Dynamic style for volume visualization during recording
const circleStyle = computed(() => {
  if (props.voiceState !== 'recording') return {}
  const scale = 1 + (props.volume / 100) * 0.3
  return {
    transform: `scale(${scale})`
  }
})

// Interaction Handlers
function startPress() {
  if (props.voiceState === 'recording') return
  isPressing.value = true
  tapFired = false
  pressTimer.value = window.setTimeout(() => {
    emit('press-start')
    tapFired = true
  }, 300)
}

function endPress() {
  isPressing.value = false
  if (pressTimer.value) {
    clearTimeout(pressTimer.value)
    pressTimer.value = null
  }
  if (!tapFired && props.voiceState === 'recording') {
     emit('press-end')
  }
}

function handleClick() {
  if (!tapFired) {
    emit('tap')
  }
}
</script>

<style scoped>
.floating-voice-hub {
  position: fixed;
  bottom: var(--vc-space-xl);
  left: 50%;
  transform: translateX(-50%);
  z-index: var(--vc-z-voice-hub);
  display: flex;
  flex-direction: column;
  align-items: center;
  pointer-events: none; /* Let clicks pass through empty areas */
}

/* UI Elements that should receive events */
.hub-button {
  pointer-events: auto;
  position: relative;
  width: 64px;
  height: 64px;
  border-radius: var(--vc-radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--vc-transition-base);
  margin-top: var(--vc-space-md);
}

.hub-circle {
  width: 100%;
  height: 100%;
  border-radius: var(--vc-radius-full);
  background-color: var(--vc-primary);
  color: var(--vc-text-inverse);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--vc-shadow-glow);
  transition: transform 50ms linear, background-color var(--vc-transition-base);
  z-index: 2;
}

/* State Adjustments */
.state-idle .hub-button:hover .hub-circle {
  transform: scale(1.05);
  box-shadow: 0 6px 16px rgba(10, 102, 194, 0.3);
}

.state-idle .hub-button:active .hub-circle {
  transform: scale(0.95);
}

/* Agent text and Listening text */
.agent-status-text,
.listening-text {
  pointer-events: auto;
  background: var(--vc-bg-glass);
  backdrop-filter: blur(var(--vc-glass-blur));
  -webkit-backdrop-filter: blur(var(--vc-glass-blur));
  padding: 8px 16px;
  border-radius: var(--vc-radius-full);
  font-size: var(--vc-text-sm);
  color: var(--vc-text-primary);
  box-shadow: var(--vc-shadow-md);
  border: 1px solid var(--vc-border);
  display: flex;
  align-items: center;
  gap: 8px;
  max-width: 80vw;
  text-align: center;
  word-break: break-all;
}

.listening-text {
  font-size: var(--vc-text-base);
}

.agent-status-text {
  color: var(--vc-text-secondary);
}

/* Pulse dot for thinking state */
.pulse-dot {
  width: 8px;
  height: 8px;
  background-color: var(--vc-primary);
  border-radius: 50%;
  animation: pulse-dot 1.5s infinite;
}

/* Ripples */
.ripple-ring {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 2px solid var(--vc-primary);
  opacity: 0;
  pointer-events: none;
  z-index: 1;
}

.ring-1 {
  animation: ripple 2s infinite cubic-bezier(0.2, 0.8, 0.2, 1);
}

.ring-2 {
  animation: ripple 2s infinite cubic-bezier(0.2, 0.8, 0.2, 1);
  animation-delay: 1s;
}

/* Spinner */
.spinner {
  animation: spin 1.5s linear infinite;
}

/* Animations */
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes ripple {
  0% { transform: scale(1); opacity: 0.6; }
  100% { transform: scale(1.8); opacity: 0; }
}

@keyframes pulse-dot {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(0.6); opacity: 0.5; }
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
</style>
