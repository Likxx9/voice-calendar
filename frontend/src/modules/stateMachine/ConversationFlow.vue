<template>
  <div class="conversation-flow" ref="flowRef" role="log" aria-label="对话记录" aria-live="polite">
    <TransitionGroup name="vc-slide-up" tag="div" class="conversation-flow__list">
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="conversation-flow__bubble-wrap"
        :class="`conversation-flow__bubble-wrap--${msg.role}`"
      >
        <div class="conversation-flow__bubble" :class="`conversation-flow__bubble--${msg.role}`">
          <!-- 消息头部 -->
          <div class="conversation-flow__header">
            <span class="conversation-flow__avatar" aria-hidden="true">
              {{ msg.role === 'user' ? '🎤' : '🤖' }}
            </span>
            <span class="conversation-flow__time">{{ formatTime(msg.timestamp) }}</span>
          </div>

          <!-- 消息内容 -->
          <p class="conversation-flow__content">{{ msg.content }}</p>

          <!-- 追问选项 -->
          <div v-if="msg.type === 'clarification' && msg.metadata?.suggestions" class="conversation-flow__suggestions">
            <button
              v-for="(suggestion, idx) in msg.metadata.suggestions"
              :key="idx"
              class="conversation-flow__suggestion-btn"
              @click="$emit('select-suggestion', suggestion)"
            >
              {{ suggestion }}
            </button>
          </div>

          <!-- 冲突详情 -->
          <div v-if="msg.type === 'conflict' && msg.metadata?.conflict_result" class="conversation-flow__conflict">
            <div
              v-for="conflict in msg.metadata.conflict_result.conflicts"
              :key="conflict.existing_event_id"
              class="conversation-flow__conflict-item"
            >
              <span class="conversation-flow__conflict-icon">⚠️</span>
              <span>「{{ conflict.existing_title }}」{{ formatTimeRange(conflict.overlap_start, conflict.overlap_end) }}</span>
            </div>
          </div>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { ConversationMessage } from '@/types/contracts'

const props = defineProps<{
  messages: ConversationMessage[]
}>()

defineEmits<{
  'select-suggestion': [suggestion: string]
}>()

const flowRef = ref<HTMLElement | null>(null)

// 自动滚动到底部
watch(() => props.messages.length, async () => {
  await nextTick()
  if (flowRef.value) {
    flowRef.value.scrollTop = flowRef.value.scrollHeight
  }
})

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

function formatTimeRange(start: string, end: string): string {
  try {
    const s = new Date(start).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    const e = new Date(end).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    return `${s} - ${e}`
  } catch {
    return ''
  }
}
</script>

<style scoped>
.conversation-flow {
  flex: 1;
  overflow-y: auto;
  padding: var(--vc-space-md);
  scroll-behavior: smooth;
}

.conversation-flow__list {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-md);
}

.conversation-flow__bubble-wrap {
  display: flex;
  max-width: 85%;
}

.conversation-flow__bubble-wrap--user {
  align-self: flex-end;
  margin-left: auto;
}

.conversation-flow__bubble-wrap--system {
  align-self: flex-start;
}

.conversation-flow__bubble {
  padding: var(--vc-space-md);
  border-radius: var(--vc-radius-lg);
  animation: vc-scale-in 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.conversation-flow__bubble--user {
  background: linear-gradient(135deg, var(--vc-primary), var(--vc-primary-dark));
  color: white;
  border-bottom-right-radius: var(--vc-radius-sm);
}

.conversation-flow__bubble--system {
  background: var(--vc-bg-elevated);
  border: 1px solid var(--vc-border);
  color: var(--vc-text-primary);
  border-bottom-left-radius: var(--vc-radius-sm);
}

.conversation-flow__header {
  display: flex;
  align-items: center;
  gap: var(--vc-space-sm);
  margin-bottom: var(--vc-space-xs);
}

.conversation-flow__avatar {
  font-size: 14px;
}

.conversation-flow__time {
  font-size: var(--vc-text-xs);
  opacity: 0.6;
}

.conversation-flow__content {
  font-size: var(--vc-text-base);
  line-height: var(--vc-leading-relaxed);
  word-break: break-word;
}

/* 追问建议按钮 */
.conversation-flow__suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--vc-space-sm);
  margin-top: var(--vc-space-md);
}

.conversation-flow__suggestion-btn {
  padding: var(--vc-space-xs) var(--vc-space-md);
  border-radius: var(--vc-radius-full);
  background: var(--vc-bg-surface);
  border: 1px solid var(--vc-border-active);
  color: var(--vc-primary-light);
  font-size: var(--vc-text-sm);
  font-weight: var(--vc-weight-medium);
  transition: all var(--vc-transition-fast);
  cursor: pointer;
}

.conversation-flow__suggestion-btn:hover {
  background: var(--vc-primary);
  color: white;
  border-color: var(--vc-primary);
  transform: translateY(-1px);
}

/* 冲突详情 */
.conversation-flow__conflict {
  margin-top: var(--vc-space-sm);
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-xs);
}

.conversation-flow__conflict-item {
  display: flex;
  align-items: center;
  gap: var(--vc-space-xs);
  padding: var(--vc-space-xs) var(--vc-space-sm);
  background: var(--vc-danger-soft);
  border-radius: var(--vc-radius-sm);
  font-size: var(--vc-text-sm);
  color: var(--vc-danger);
}
</style>
