<template>
  <div class="streaming-transcript" :class="{ 'streaming-transcript--active': isActive }" role="log" aria-live="polite" aria-label="语音转写文本">
    <p v-if="finalText || partialText" class="streaming-transcript__text">
      <span v-if="finalText" class="streaming-transcript__final">{{ finalText }}</span>
      <span v-if="partialText" class="streaming-transcript__partial">{{ partialText }}</span>
      <span v-if="isActive" class="streaming-transcript__cursor" aria-hidden="true" />
    </p>
    <p v-else class="streaming-transcript__placeholder">
      {{ isActive ? '正在聆听...' : '语音识别结果将在此显示' }}
    </p>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  finalText?: string
  partialText?: string
  isActive?: boolean
}>(), {
  finalText: '',
  partialText: '',
  isActive: false,
})
</script>

<style scoped>
.streaming-transcript {
  padding: var(--vc-space-md) var(--vc-space-lg);
  min-height: 48px;
  border-radius: var(--vc-radius-md);
  background: var(--vc-bg-surface);
  border: 1px solid var(--vc-border);
  transition: all var(--vc-transition-base);
}

.streaming-transcript--active {
  border-color: var(--vc-border-active);
  box-shadow: 0 0 0 3px hsla(224, 76%, 48%, 0.1);
}

.streaming-transcript__text {
  font-size: var(--vc-text-lg);
  line-height: var(--vc-leading-relaxed);
  color: var(--vc-text-primary);
  word-break: break-word;
}

.streaming-transcript__final {
  color: var(--vc-text-primary);
}

.streaming-transcript__partial {
  color: var(--vc-text-tertiary);
  font-style: italic;
}

.streaming-transcript__cursor {
  display: inline-block;
  width: 2px;
  height: 1.2em;
  background: var(--vc-primary);
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: vc-blink 1s step-end infinite;
}

.streaming-transcript__placeholder {
  color: var(--vc-text-tertiary);
  font-size: var(--vc-text-sm);
}
</style>
