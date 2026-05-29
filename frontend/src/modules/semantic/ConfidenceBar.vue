<template>
  <div class="confidence-bar" :aria-label="`置信度 ${Math.round(value * 100)}%`">
    <div class="confidence-bar__track">
      <div class="confidence-bar__fill" :class="levelClass" :style="{ width: `${value * 100}%` }" />
    </div>
    <span v-if="showLabel" class="confidence-bar__label">{{ Math.round(value * 100) }}%</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  value?: number       // 0~1
  showLabel?: boolean
}>(), {
  value: 0,
  showLabel: true,
})

const levelClass = computed(() => {
  if (props.value >= 0.8) return 'confidence-bar__fill--high'
  if (props.value >= 0.5) return 'confidence-bar__fill--medium'
  return 'confidence-bar__fill--low'
})
</script>

<style scoped>
.confidence-bar {
  display: flex;
  align-items: center;
  gap: var(--vc-space-sm);
}

.confidence-bar__track {
  flex: 1;
  height: 6px;
  background: var(--vc-bg-surface);
  border-radius: var(--vc-radius-full);
  overflow: hidden;
}

.confidence-bar__fill {
  height: 100%;
  border-radius: var(--vc-radius-full);
  transition: width var(--vc-transition-slow);
}

.confidence-bar__fill--high {
  background: linear-gradient(90deg, var(--vc-success), hsl(140, 68%, 52%));
}
.confidence-bar__fill--medium {
  background: linear-gradient(90deg, var(--vc-warning), hsl(45, 92%, 55%));
}
.confidence-bar__fill--low {
  background: linear-gradient(90deg, var(--vc-danger), hsl(15, 78%, 56%));
}

.confidence-bar__label {
  font-size: var(--vc-text-xs);
  font-weight: var(--vc-weight-semibold);
  color: var(--vc-text-tertiary);
  min-width: 36px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
</style>
