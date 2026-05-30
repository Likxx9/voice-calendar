<template>
  <div class="conflict-card vc-anim-slide-up" role="alert" aria-label="时间冲突警告">
    <div class="conflict-card__header">
      <span class="conflict-card__icon" aria-hidden="true">⚠️</span>
      <h3 class="conflict-card__title">检测到时间冲突</h3>
    </div>

    <!-- 冲突列表（后端已提供 display-ready 数据） -->
    <div class="conflict-card__conflicts">
      <div
        v-for="conflict in conflicts"
        :key="conflict.existing_event_id"
        class="conflict-card__item"
      >
        <div class="conflict-card__item-header">
          <span class="conflict-card__severity" :class="`conflict-card__severity--${conflict.severity}`">
            {{ conflict.severity_label || (conflict.severity === 'full' ? '完全重叠' : '部分重叠') }}
          </span>
        </div>
        <p class="conflict-card__item-title">{{ conflict.existing_title }}</p>
        <p class="conflict-card__item-time">
          {{ conflict.overlap_start_display || conflict.overlap_start }} — {{ conflict.overlap_end_display || conflict.overlap_end }}
        </p>
      </div>
    </div>

    <!-- 建议操作 -->
    <div v-if="suggestions.length" class="conflict-card__suggestions">
      <p class="conflict-card__suggestions-label">建议方案：</p>
      <button
        v-for="(suggestion, idx) in suggestions"
        :key="idx"
        class="conflict-card__suggestion-btn"
        @click="$emit('select', suggestion)"
      >
        {{ idx + 1 }}. {{ suggestion }}
      </button>
    </div>

    <div class="conflict-card__actions">
      <button class="conflict-card__btn conflict-card__btn--voice" @click="$emit('voice-resolve')">
        🎤 语音选择
      </button>
      <button class="conflict-card__btn conflict-card__btn--force" @click="$emit('force-create')">
        强制创建
      </button>
      <button class="conflict-card__btn conflict-card__btn--cancel" @click="$emit('cancel')">
        取消
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 冲突协商卡片 — 纯展示组件
 *
 * 所有数据由后端 ready-to-display 下发：
 *   - conflicts: 包含 severity_label, overlap_start_display, overlap_end_display
 *   - suggestions: 由后端构建的建议列表
 * 前端不做任何时间格式化或默认值填充。
 */
import type { ConflictItem } from '@/types/contracts'

withDefaults(defineProps<{
  conflicts?: ConflictItem[]
  suggestions?: string[]
}>(), {
  conflicts: () => [],
  suggestions: () => [],
})

defineEmits<{
  'select': [suggestion: string]
  'voice-resolve': []
  'force-create': []
  'cancel': []
}>()
</script>

<style scoped>
.conflict-card {
  padding: var(--vc-space-lg);
  background: var(--vc-bg-elevated);
  border: 1px solid var(--vc-border);
  border-left: 4px solid var(--vc-danger);
  border-radius: var(--vc-radius-md);
}

.conflict-card__header {
  display: flex;
  align-items: center;
  gap: var(--vc-space-sm);
  margin-bottom: var(--vc-space-md);
}

.conflict-card__icon { font-size: 22px; }

.conflict-card__title {
  font-size: var(--vc-text-base);
  font-weight: var(--vc-weight-semibold);
  color: var(--vc-danger);
}

.conflict-card__conflicts {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-sm);
  margin-bottom: var(--vc-space-md);
}

.conflict-card__item {
  padding: var(--vc-space-sm) var(--vc-space-md);
  background: var(--vc-danger-soft);
  border-radius: var(--vc-radius-sm);
}

.conflict-card__item-header {
  margin-bottom: var(--vc-space-xs);
}

.conflict-card__severity {
  font-size: var(--vc-text-xs);
  font-weight: var(--vc-weight-semibold);
  padding: 1px 8px;
  border-radius: var(--vc-radius-full);
}

.conflict-card__severity--full {
  background: var(--vc-danger);
  color: white;
}
.conflict-card__severity--partial {
  background: var(--vc-warning);
  color: var(--vc-text-inverse);
}

.conflict-card__item-title {
  font-weight: var(--vc-weight-medium);
  color: var(--vc-text-primary);
  font-size: var(--vc-text-sm);
}

.conflict-card__item-time {
  font-size: var(--vc-text-xs);
  color: var(--vc-text-secondary);
  font-variant-numeric: tabular-nums;
}

.conflict-card__suggestions {
  margin-bottom: var(--vc-space-md);
}

.conflict-card__suggestions-label {
  font-size: var(--vc-text-sm);
  color: var(--vc-text-secondary);
  margin-bottom: var(--vc-space-sm);
}

.conflict-card__suggestion-btn {
  display: block;
  width: 100%;
  text-align: left;
  padding: var(--vc-space-sm) var(--vc-space-md);
  margin-bottom: var(--vc-space-xs);
  border-radius: var(--vc-radius-sm);
  background: var(--vc-bg-surface);
  border: 1px solid var(--vc-border);
  color: var(--vc-text-primary);
  font-size: var(--vc-text-sm);
  transition: all var(--vc-transition-fast);
  cursor: pointer;
}

.conflict-card__suggestion-btn:hover {
  border-color: var(--vc-accent);
  background: hsla(var(--vc-accent-h), var(--vc-accent-s), var(--vc-accent-l), 0.08);
}

.conflict-card__actions {
  display: flex;
  gap: var(--vc-space-sm);
  flex-wrap: wrap;
}

.conflict-card__btn {
  padding: var(--vc-space-sm) var(--vc-space-md);
  border-radius: var(--vc-radius-full);
  font-size: var(--vc-text-sm);
  font-weight: var(--vc-weight-medium);
  transition: all var(--vc-transition-fast);
}

.conflict-card__btn--voice {
  background: var(--vc-primary);
  color: white;
}
.conflict-card__btn--voice:hover { background: var(--vc-primary-light); }

.conflict-card__btn--force {
  background: transparent;
  color: var(--vc-warning);
  border: 1px solid var(--vc-warning);
}

.conflict-card__btn--cancel {
  background: transparent;
  color: var(--vc-text-tertiary);
  border: 1px solid var(--vc-border);
}
</style>
