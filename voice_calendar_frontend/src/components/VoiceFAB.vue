<template>
  <button 
    class="voice-fab" 
    :class="{ 
      listening: store.voiceState === 'listening', 
      processing: store.voiceState === 'processing',
      done: store.voiceState === 'idle' && showDoneIcon
    }"
    @mousedown="startVoice"
    @mouseup="stopVoice"
    @mouseleave="stopVoice"
    @touchstart.prevent="startVoice"
    @touchend.prevent="stopVoice"
    @touchcancel.prevent="stopVoice"
  >
    <span v-if="store.voiceState === 'processing'" class="fab-icon">⌛</span>
    <span v-else-if="showDoneIcon" class="fab-icon">✓</span>
    <span v-else class="fab-icon">🎙</span>
  </button>
</template>

<script setup>
import { ref, watch } from 'vue'
import { store } from '../services/store'
import { startBackendRecording as startRecording, stopBackendRecording as stopRecording } from '../services/socket'

const showDoneIcon = ref(false)
let doneTimer = null

const startVoice = () => {
  if (store.voiceState === 'processing') return
  store.voiceState = 'listening'
  store.currentQuery = ''
  startRecording()
}

const stopVoice = () => {
  if (store.voiceState === 'listening') {
    store.voiceState = 'processing'
    stopRecording()
  }
}

watch(() => store.voiceState, (newVal, oldVal) => {
  if (newVal === 'done' || (oldVal === 'processing' && newVal === 'idle')) {
    showDoneIcon.value = true
    clearTimeout(doneTimer)
    doneTimer = setTimeout(() => {
      showDoneIcon.value = false
    }, 3000)
  } else if (newVal === 'listening' || newVal === 'processing') {
    showDoneIcon.value = false
  }
})
</script>

<style scoped>
.voice-fab {
  position: fixed;
  bottom: var(--fab-bottom, 80px);
  right: var(--fab-right, 20px);
  width: var(--fab-size, 56px);
  height: var(--fab-size, 56px);
  border-radius: 50%;
  background: linear-gradient(135deg, var(--gold), #9B6B1A);
  border: none;
  cursor: pointer;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #000;
  box-shadow:
    0 4px 16px rgba(200,164,90,.35),
    0 2px 6px rgba(0,0,0,.4);
  -webkit-tap-highlight-color: transparent;
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.3s ease;
}

.voice-fab:active {
  transform: scale(0.92);
  box-shadow:
    0 2px 8px rgba(200,164,90,.25),
    0 1px 3px rgba(0,0,0,.4);
}

.voice-fab.listening {
  animation: fabGlow 1.1s ease-in-out infinite;
}

@keyframes fabGlow {
  0%, 100% { box-shadow: 0 4px 16px rgba(200,164,90,.4), 0 0 0 0 rgba(200,164,90,.3); }
  50%       { box-shadow: 0 4px 24px rgba(200,164,90,.6), 0 0 0 14px rgba(200,164,90,0); }
}

.voice-fab.processing {
  background: linear-gradient(135deg, var(--blue), #1a4a99);
  animation: fabProcessing 0.8s ease-in-out infinite;
}

@keyframes fabProcessing {
  0%, 100% { transform: scale(1); }
  50%       { transform: scale(1.05); }
}

.voice-fab.done {
  background: linear-gradient(135deg, var(--teal), #1a6b5f);
}

.fab-icon {
  line-height: 1;
}
</style>
