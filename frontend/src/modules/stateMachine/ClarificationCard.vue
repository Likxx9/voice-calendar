<template>
  <div class="clarification-card vc-anim-slide-up" role="alert">
    <div class="clarification-card__header">
      <span class="clarification-card__icon" aria-hidden="true">❓</span>
      <h3 class="clarification-card__title">需要补充信息</h3>
    </div>

    <p class="clarification-card__message">{{ message }}</p>

    <div v-if="missingFields.length" class="clarification-card__fields">
      <span
        v-for="field in missingFields"
        :key="field"
        class="clarification-card__field-tag"
      >
        {{ fieldLabels[field] || field }}
      </span>
    </div>

    <div class="clarification-card__actions">
      <button class="clarification-card__btn clarification-card__btn--voice" @click="$emit('voice-reply')">
        🎤 语音回答
      </button>
      <button class="clarification-card__btn clarification-card__btn--skip" @click="$emit('skip')">
        跳过
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  message?: string
  missingFields?: string[]
}>(), {
  message: '请补充以下信息以完成创建',
  missingFields: () => [],
})

defineEmits<{
  'voice-reply': []
  'skip': []
}>()

const fieldLabels: Record<string, string> = {
  title: '标题',
  start_time: '开始时间',
  end_time: '结束时间',
  location: '地点',
  attendees: '参与者',
  due_time: '截止时间',
  priority: '优先级',
}
</script>

<style scoped>
.clarification-card {
  padding: var(--vc-space-lg);
  background: var(--vc-bg-elevated);
  border: 1px solid var(--vc-border);
  border-left: 4px solid var(--vc-warning);
  border-radius: var(--vc-radius-md);
}

.clarification-card__header {
  display: flex;
  align-items: center;
  gap: var(--vc-space-sm);
  margin-bottom: var(--vc-space-sm);
}

.clarification-card__icon { font-size: 20px; }

.clarification-card__title {
  font-size: var(--vc-text-base);
  font-weight: var(--vc-weight-semibold);
  color: var(--vc-warning);
}

.clarification-card__message {
  font-size: var(--vc-text-sm);
  color: var(--vc-text-secondary);
  margin-bottom: var(--vc-space-md);
  line-height: var(--vc-leading-relaxed);
}

.clarification-card__fields {
  display: flex;
  flex-wrap: wrap;
  gap: var(--vc-space-xs);
  margin-bottom: var(--vc-space-md);
}

.clarification-card__field-tag {
  padding: 2px 10px;
  border-radius: var(--vc-radius-full);
  background: var(--vc-warning-soft);
  color: var(--vc-warning);
  font-size: var(--vc-text-xs);
  font-weight: var(--vc-weight-semibold);
}

.clarification-card__actions {
  display: flex;
  gap: var(--vc-space-sm);
}

.clarification-card__btn {
  padding: var(--vc-space-sm) var(--vc-space-lg);
  border-radius: var(--vc-radius-full);
  font-size: var(--vc-text-sm);
  font-weight: var(--vc-weight-medium);
  transition: all var(--vc-transition-fast);
}

.clarification-card__btn--voice {
  background: var(--vc-primary);
  color: white;
}
.clarification-card__btn--voice:hover {
  background: var(--vc-primary-light);
  transform: translateY(-1px);
}

.clarification-card__btn--skip {
  background: transparent;
  color: var(--vc-text-tertiary);
  border: 1px solid var(--vc-border);
}
.clarification-card__btn--skip:hover {
  color: var(--vc-text-secondary);
  border-color: var(--vc-text-tertiary);
}
</style>
