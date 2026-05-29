<template>
  <div class="tts-control" :class="{ 'tts-control--playing': isPlaying }" role="region" aria-label="语音播报控制">
    <!-- 播放/暂停按钮 -->
    <button class="tts-control__btn" :aria-label="isPlaying ? '停止播报' : '暂无播报'" @click="$emit('stop')">
      <svg v-if="isPlaying" viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
        <rect x="6" y="4" width="4" height="16" rx="1" />
        <rect x="14" y="4" width="4" height="16" rx="1" />
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
        <polygon points="5 3 19 12 5 21 5 3" />
      </svg>
    </button>

    <!-- 进度条 -->
    <div class="tts-control__progress-track" aria-hidden="true">
      <div class="tts-control__progress-fill" :style="{ width: `${progress * 100}%` }" />
    </div>

    <!-- 语速控制 -->
    <div class="tts-control__speed">
      <button class="tts-control__speed-btn" aria-label="降低语速" @click="$emit('speed-change', speed - 0.1)">−</button>
      <span class="tts-control__speed-label">{{ speed.toFixed(1) }}x</span>
      <button class="tts-control__speed-btn" aria-label="提高语速" @click="$emit('speed-change', speed + 0.1)">+</button>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  isPlaying?: boolean
  progress?: number   // 0~1
  speed?: number      // 1.0~2.5
}>(), {
  isPlaying: false,
  progress: 0,
  speed: 1.2,
})

defineEmits<{
  'stop': []
  'speed-change': [speed: number]
}>()
</script>

<style scoped>
.tts-control {
  display: flex;
  align-items: center;
  gap: var(--vc-space-md);
  padding: var(--vc-space-sm) var(--vc-space-md);
  background: var(--vc-bg-elevated);
  border: 1px solid var(--vc-border);
  border-radius: var(--vc-radius-lg);
  opacity: 0.5;
  transition: opacity var(--vc-transition-base);
}

.tts-control--playing {
  opacity: 1;
  border-color: var(--vc-border-active);
}

.tts-control__btn {
  width: 36px;
  height: 36px;
  border-radius: var(--vc-radius-full);
  background: var(--vc-bg-surface);
  color: var(--vc-text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background var(--vc-transition-fast);
}

.tts-control__btn:hover {
  background: var(--vc-primary);
  color: white;
}

.tts-control__progress-track {
  flex: 1;
  height: 4px;
  background: var(--vc-bg-surface);
  border-radius: var(--vc-radius-full);
  overflow: hidden;
}

.tts-control__progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--vc-primary), var(--vc-accent));
  border-radius: var(--vc-radius-full);
  transition: width 100ms linear;
}

.tts-control__speed {
  display: flex;
  align-items: center;
  gap: var(--vc-space-xs);
}

.tts-control__speed-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--vc-radius-full);
  background: var(--vc-bg-surface);
  color: var(--vc-text-secondary);
  font-size: var(--vc-text-lg);
  font-weight: var(--vc-weight-bold);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--vc-transition-fast);
}

.tts-control__speed-btn:hover {
  background: var(--vc-primary);
  color: white;
}

.tts-control__speed-label {
  font-size: var(--vc-text-xs);
  font-weight: var(--vc-weight-semibold);
  color: var(--vc-text-secondary);
  min-width: 32px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}
</style>
