<template>
  <div class="meeting-suggestions vc-elevated" role="region" aria-label="会议时间推荐">
    <div class="meeting-suggestions__header">
      <span class="meeting-suggestions__icon" aria-hidden="true">💡</span>
      <div class="meeting-suggestions__title-group">
        <h3 class="meeting-suggestions__title">最佳时间推荐</h3>
        <p class="meeting-suggestions__subtitle">基于所有参与者的忙闲日程智能计算</p>
      </div>
    </div>

    <div v-if="suggestions.length === 0" class="meeting-suggestions__empty">
      <span class="meeting-suggestions__empty-icon" aria-hidden="true">🚫</span>
      <p class="meeting-suggestions__empty-text">未找到合适的共同空闲时间窗</p>
    </div>

    <div v-else class="meeting-suggestions__list">
      <button
        v-for="(w, idx) in sortedSuggestions"
        :key="idx"
        class="suggestion-card"
        :class="[
          `suggestion-card--rank-${idx + 1}`,
          { 'suggestion-card--selected': selectedIndex === idx }
        ]"
        @click="selectSuggestion(idx, w)"
      >
        <!-- 勋章标识最好的一项 -->
        <div v-if="idx === 0" class="suggestion-card__badge">
          ✨ 智能首选
        </div>

        <div class="suggestion-card__body">
          <div class="suggestion-card__time-info">
            <div class="suggestion-card__date">{{ formatDate(w.start) }}</div>
            <div class="suggestion-card__time">
              {{ formatTime(w.start) }} - {{ formatTime(w.end) }}
            </div>
          </div>

          <div class="suggestion-card__score-group">
            <div class="suggestion-card__score-value" :style="scoreColor(w.score)">
              {{ Math.round(w.score * 100) }}<span class="suggestion-card__score-pct">%</span>
            </div>
            <div class="suggestion-card__score-label">匹配度</div>
          </div>
        </div>

        <!-- 进度条表示匹配度 -->
        <div class="suggestion-card__progress">
          <div 
            class="suggestion-card__progress-fill" 
            :style="{ 
              width: `${w.score * 100}%`,
              background: getScoreGradient(w.score)
            }" 
          />
        </div>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface SuggestionWindow {
  start: string
  end: string
  score: number
}

const props = withDefaults(defineProps<{
  suggestions?: SuggestionWindow[]
}>(), {
  suggestions: () => []
})

const emit = defineEmits<{
  'select-suggestion': [window: SuggestionWindow]
}>()

const selectedIndex = ref<number | null>(null)

const sortedSuggestions = computed(() => {
  return [...props.suggestions].sort((a, b) => b.score - a.score)
})

function selectSuggestion(idx: number, w: SuggestionWindow) {
  selectedIndex.value = idx
  emit('select-suggestion', w)
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleDateString('zh-CN', { weekday: 'short', month: 'short', day: 'numeric' })
  } catch { return '' }
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } catch { return '' }
}

function scoreColor(score: number): Record<string, string> {
  if (score >= 0.85) return { color: 'var(--vc-success)' }
  if (score >= 0.6) return { color: 'var(--vc-warning)' }
  return { color: 'var(--vc-danger)' }
}

function getScoreGradient(score: number): string {
  if (score >= 0.85) {
    return 'linear-gradient(90deg, var(--vc-success) 0%, #10B981 100%)'
  } else if (score >= 0.6) {
    return 'linear-gradient(90deg, var(--vc-warning) 0%, #F59E0B 100%)'
  } else {
    return 'linear-gradient(90deg, var(--vc-danger) 0%, #EF4444 100%)'
  }
}
</script>

<style scoped>
.meeting-suggestions {
  padding: var(--vc-space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-md);
}

.meeting-suggestions__header {
  display: flex;
  align-items: center;
  gap: var(--vc-space-sm);
}

.meeting-suggestions__icon {
  font-size: 24px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

.meeting-suggestions__title-group {
  display: flex;
  flex-direction: column;
}

.meeting-suggestions__title {
  font-size: var(--vc-text-base);
  font-weight: var(--vc-weight-semibold);
  color: var(--vc-text-primary);
}

.meeting-suggestions__subtitle {
  font-size: var(--vc-text-xs);
  color: var(--vc-text-tertiary);
}

.meeting-suggestions__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--vc-space-xl) 0;
  text-align: center;
  background: var(--vc-bg-surface);
  border-radius: var(--vc-radius-lg);
  border: 1px dashed var(--vc-border);
}

.meeting-suggestions__empty-icon {
  font-size: 32px;
  margin-bottom: var(--vc-space-sm);
  opacity: 0.5;
}

.meeting-suggestions__empty-text {
  font-size: var(--vc-text-sm);
  color: var(--vc-text-secondary);
}

.meeting-suggestions__list {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-sm);
}

.suggestion-card {
  border: 1px solid var(--vc-border);
  background: var(--vc-bg-surface);
  border-radius: var(--vc-radius-md);
  padding: var(--vc-space-md);
  text-align: left;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all var(--vc-transition-normal) cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-sm);
}

.suggestion-card:hover {
  transform: translateY(-2px);
  border-color: var(--vc-accent);
  box-shadow: var(--vc-shadow-md);
  background: var(--vc-bg-surface-hover, var(--vc-bg-surface));
}

.suggestion-card--selected {
  border-color: var(--vc-accent);
  background: rgba(var(--vc-accent-rgb, 124, 58, 237), 0.08);
  box-shadow: 0 0 0 1px var(--vc-accent);
}

.suggestion-card__badge {
  position: absolute;
  top: 0;
  right: 0;
  background: linear-gradient(135deg, var(--vc-accent) 0%, #a855f7 100%);
  color: #ffffff;
  font-size: 10px;
  font-weight: var(--vc-weight-semibold);
  padding: 2px 8px;
  border-bottom-left-radius: var(--vc-radius-sm);
}

.suggestion-card__body {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.suggestion-card__time-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.suggestion-card__date {
  font-size: var(--vc-text-xs);
  color: var(--vc-text-secondary);
  font-weight: var(--vc-weight-medium);
}

.suggestion-card__time {
  font-size: var(--vc-text-base);
  font-weight: var(--vc-weight-bold);
  color: var(--vc-text-primary);
  font-variant-numeric: tabular-nums;
}

.suggestion-card__score-group {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.suggestion-card__score-value {
  font-size: var(--vc-text-lg);
  font-weight: var(--vc-weight-bold);
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}

.suggestion-card__score-pct {
  font-size: var(--vc-text-xs);
  font-weight: var(--vc-weight-medium);
}

.suggestion-card__score-label {
  font-size: 10px;
  color: var(--vc-text-tertiary);
  text-transform: uppercase;
}

.suggestion-card__progress {
  height: 4px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: var(--vc-radius-full);
  overflow: hidden;
}

.suggestion-card__progress-fill {
  height: 100%;
  border-radius: var(--vc-radius-full);
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
