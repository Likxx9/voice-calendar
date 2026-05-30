<template>
  <div class="search-card vc-anim-slide-up" role="region" aria-label="联网智能检索">
    <!-- 头部：Agent 状态 -->
    <div class="search-card__header">
      <span class="search-card__icon" :class="{ 'search-card__icon--spinning': status === 'searching' || status === 'parsing' }">
        <template v-if="status === 'searching'">🌐</template>
        <template v-else-if="status === 'parsing'">🧠</template>
        <template v-else>🔍</template>
      </span>
      <div class="search-card__title-area">
        <h3 class="search-card__title">M9 联网检索智能体</h3>
        <p class="search-card__query">“{{ query }}”</p>
      </div>
      <span v-if="status === 'results'" class="search-card__badge">
        {{ resultCountDisplay || `查到 ${events.length} 个活动` }}
      </span>
    </div>

    <!-- 状态 1：Web 检索中 -->
    <div v-if="status === 'searching'" class="search-card__loading search-card__loading--search">
      <div class="search-card__pulse-ring"></div>
      <div class="search-card__loading-text-flow">
        <p class="loading-step active">⚡ 正在连接外部 Web Search 适配器...</p>
        <p class="loading-step">🔍 检索 Tavily & Google Search 实时网页切片...</p>
        <p class="loading-step">📄 抓取最新互联网时效性活动排期段落...</p>
      </div>
      <div class="search-card__progress-bar">
        <div class="search-card__progress-fill search-card__progress-fill--searching"></div>
      </div>
    </div>

    <!-- 状态 2：LLM 提炼中 -->
    <div v-else-if="status === 'parsing'" class="search-card__loading search-card__loading--ai">
      <div class="search-card__ai-chip">
        <div class="chip-dot"></div>
        <div class="chip-line"></div>
      </div>
      <div class="search-card__loading-text-flow">
        <p class="loading-step done">✓ 互联网网页切片拉取完毕 (2.4KB)</p>
        <p class="loading-step active">🧠 大模型正在对非结构化文本进行深度解析...</p>
        <p class="loading-step">✨ 提取标准化日程字段：标题、起止时间、场馆...</p>
      </div>
      <div class="search-card__progress-bar">
        <div class="search-card__progress-fill search-card__progress-fill--parsing"></div>
      </div>
    </div>

    <!-- 状态 3：展示解析结果 -->
    <div v-else class="search-card__results">
      <div v-if="events.length === 0" class="search-card__empty">
        <p>📭 未搜索到匹配的时效性实践活动</p>
        <button class="search-card__retry-btn" @click="$emit('retry')">重新检索</button>
      </div>

      <div v-else class="search-card__list">
        <div
          v-for="(event, index) in events"
          :key="index"
          class="event-item vc-glass"
          :class="{ 'event-item--added': isEventAdded(event.title) }"
        >
          <div class="event-item__header">
            <h4 class="event-item__title">{{ event.title }}</h4>
            <span v-if="isEventAdded(event.title)" class="event-item__added-badge">
              ✓ 已添加入日程
            </span>
          </div>

          <p class="event-item__desc">{{ event.description }}</p>

          <div class="event-item__meta-grid">
            <div class="meta-item">
              <span class="meta-icon">📅</span>
              <span class="meta-text">{{ (event as any).start_time_display || event.start_time }} 至 {{ (event as any).end_time_display || event.end_time }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-icon">📍</span>
              <span class="meta-text">{{ event.location }}</span>
            </div>
            <div v-if="event.source_url" class="meta-item">
              <span class="meta-icon">🔗</span>
              <a :href="event.source_url" target="_blank" class="meta-link" rel="noopener noreferrer">
                来源检索网页
              </a>
            </div>
          </div>

          <div class="event-item__actions">
            <button
              class="event-item__add-btn"
              :class="{ 'event-item__add-btn--added': isEventAdded(event.title) }"
              :disabled="isEventAdded(event.title)"
              @click="handleAddEvent(event)"
            >
              <template v-if="isEventAdded(event.title)">
                <span>✓ 已添加入日历</span>
              </template>
              <template v-else>
                <span>➕ 一键加入日历</span>
              </template>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 联网搜索结果卡片 — 纯展示组件
 *
 * 所有数据由后端 ready-to-display 下发：
 *   - events 中每个事件含 start_time_display / end_time_display（后端已格式化）
 *   - resultCountDisplay: 后端提供的结果数量描述文本
 * 前端不做任何时间格式化或数据分析。
 */
import { ref } from 'vue'
import type { WebSearchEvent } from '@/types/contracts'

const props = withDefaults(defineProps<{
  query: string
  status?: 'searching' | 'parsing' | 'results'
  events?: WebSearchEvent[]
  resultCountDisplay?: string
}>(), {
  status: 'searching',
  events: () => [],
  resultCountDisplay: '',
})

const emit = defineEmits<{
  'add-event': [event: WebSearchEvent]
  'retry': []
}>()

// 追踪已添加的日程标题列表（纯 UI 状态，不含分析逻辑）
const addedTitles = ref<string[]>([])

function isEventAdded(title: string): boolean {
  return addedTitles.value.includes(title)
}

function handleAddEvent(event: WebSearchEvent) {
  if (isEventAdded(event.title)) return
  addedTitles.value.push(event.title)
  emit('add-event', event)
}
</script>

<style scoped>
.search-card {
  padding: var(--vc-space-lg);
  background: var(--vc-bg-elevated);
  border: 1px solid var(--vc-border);
  border-left: 4px solid var(--vc-accent);
  border-radius: var(--vc-radius-md);
  box-shadow: var(--vc-shadow-md);
  position: relative;
  overflow: hidden;
}

/* 头部样式 */
.search-card__header {
  display: flex;
  align-items: center;
  gap: var(--vc-space-sm);
  margin-bottom: var(--vc-space-lg);
  border-bottom: 1px solid var(--vc-divider);
  padding-bottom: var(--vc-space-sm);
}

.search-card__icon {
  font-size: 24px;
  display: inline-block;
}

.search-card__icon--spinning {
  animation: pulse-glow 2s infinite ease-in-out;
}

.search-card__title-area {
  flex: 1;
}

.search-card__title {
  font-size: var(--vc-text-sm);
  font-weight: var(--vc-weight-bold);
  color: var(--vc-accent-light);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.search-card__query {
  font-size: var(--vc-text-base);
  font-weight: var(--vc-weight-semibold);
  color: var(--vc-text-primary);
  margin: 2px 0 0 0;
}

.search-card__badge {
  font-size: var(--vc-text-xs);
  background: hsla(var(--vc-accent-h), var(--vc-accent-s), var(--vc-accent-l), 0.15);
  color: var(--vc-accent-light);
  padding: 4px 10px;
  border-radius: var(--vc-radius-full);
  border: 1px solid hsla(var(--vc-accent-h), var(--vc-accent-s), var(--vc-accent-l), 0.3);
}

/* 状态1 & 2：加载中 */
.search-card__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--vc-space-md) 0;
  gap: var(--vc-space-lg);
}

/* 搜索状态 - 流光雷达 */
.search-card__pulse-ring {
  width: 60px;
  height: 60px;
  border-radius: var(--vc-radius-full);
  background: hsla(var(--vc-accent-h), var(--vc-accent-s), var(--vc-accent-l), 0.1);
  border: 2px solid var(--vc-accent);
  position: relative;
  animation: radar-pulse 1.8s infinite ease-out;
}

.search-card__pulse-ring::after {
  content: '🌐';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 24px;
}

/* AI 提炼状态 - 微芯片 */
.search-card__ai-chip {
  width: 50px;
  height: 50px;
  background: var(--vc-bg-surface);
  border: 2px dashed var(--vc-accent);
  border-radius: var(--vc-radius-sm);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: rotate-dashed 8s infinite linear;
}

.search-card__ai-chip::after {
  content: '🧠';
  font-size: 22px;
  animation: scale-up-down 1.5s infinite ease-in-out;
}

.search-card__loading-text-flow {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-xs);
}

.loading-step {
  font-size: var(--vc-text-sm);
  color: var(--vc-text-tertiary);
  margin: 0;
  transition: all var(--vc-transition-base);
}

.loading-step.active {
  color: var(--vc-text-primary);
  font-weight: var(--vc-weight-medium);
  transform: translateX(4px);
  animation: text-pulse 1.5s infinite ease-in-out;
}

.loading-step.done {
  color: var(--vc-success);
}

/* 进度条 */
.search-card__progress-bar {
  width: 100%;
  height: 4px;
  background: var(--vc-bg-surface);
  border-radius: var(--vc-radius-full);
  overflow: hidden;
}

.search-card__progress-fill {
  height: 100%;
  border-radius: var(--vc-radius-full);
  width: 0;
}

.search-card__progress-fill--searching {
  background: linear-gradient(90deg, var(--vc-primary), var(--vc-accent));
  animation: progress-fill-step1 1.5s forwards linear;
}

.search-card__progress-fill--parsing {
  background: linear-gradient(90deg, var(--vc-accent), var(--vc-accent-light));
  animation: progress-fill-step2 1.2s forwards linear;
}

/* 结果列表 */
.search-card__results {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-md);
}

.search-card__list {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-md);
}

.event-item {
  padding: var(--vc-space-md);
  border: 1px solid var(--vc-border);
  border-radius: var(--vc-radius-sm);
  background: hsla(var(--vc-primary-h), 18%, 14%, 0.4);
  transition: all var(--vc-transition-base);
}

.event-item:hover {
  border-color: hsla(var(--vc-accent-h), var(--vc-accent-s), var(--vc-accent-l), 0.3);
  background: hsla(var(--vc-primary-h), var(--vc-primary-s), 16%, 0.6);
}

.event-item--added {
  border-color: hsla(150, 20%, 45%, 0.3);
  background: hsla(150, 20%, 45%, 0.05);
}

.event-item__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--vc-space-sm);
  margin-bottom: var(--vc-space-xs);
}

.event-item__title {
  font-size: var(--vc-text-base);
  font-weight: var(--vc-weight-bold);
  color: var(--vc-text-primary);
  margin: 0;
}

.event-item__added-badge {
  font-size: var(--vc-text-xs);
  color: var(--vc-success);
  font-weight: var(--vc-weight-semibold);
  background: var(--vc-success-soft);
  padding: 2px 8px;
  border-radius: var(--vc-radius-full);
}

.event-item__desc {
  font-size: var(--vc-text-sm);
  color: var(--vc-text-secondary);
  line-height: var(--vc-leading-normal);
  margin: 0 0 var(--vc-space-md) 0;
}

.event-item__meta-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--vc-space-xs);
  margin-bottom: var(--vc-space-md);
  padding: var(--vc-space-sm);
  background: rgba(0, 0, 0, 0.15);
  border-radius: var(--vc-radius-sm);
}

@media (min-width: 576px) {
  .event-item__meta-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.meta-item {
  display: flex;
  align-items: center;
  gap: var(--vc-space-xs);
  font-size: var(--vc-text-xs);
  color: var(--vc-text-secondary);
}

.meta-icon {
  font-size: 14px;
}

.meta-text {
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}

.meta-link {
  color: var(--vc-accent-light);
  text-decoration: none;
  font-weight: var(--vc-weight-medium);
  transition: color var(--vc-transition-fast);
}

.meta-link:hover {
  color: white;
  text-decoration: underline;
}

.event-item__actions {
  display: flex;
  justify-content: flex-end;
}

.event-item__add-btn {
  padding: 6px 14px;
  background: var(--vc-bg-surface);
  color: var(--vc-text-primary);
  border: 1px solid var(--vc-border);
  border-radius: var(--vc-radius-sm);
  font-size: var(--vc-text-xs);
  font-weight: var(--vc-weight-medium);
  cursor: pointer;
  transition: all var(--vc-transition-fast);
}

.event-item__add-btn:hover:not(:disabled) {
  border-color: var(--vc-accent);
  background: hsla(var(--vc-accent-h), var(--vc-accent-s), var(--vc-accent-l), 0.08);
}

.event-item__add-btn:active:not(:disabled) {
  transform: translateY(1px);
}

.event-item__add-btn--added {
  background: var(--vc-success-soft);
  color: var(--vc-success);
  border: 1px solid hsla(150, 20%, 45%, 0.2);
  cursor: not-allowed;
}

.search-card__empty {
  text-align: center;
  padding: var(--vc-space-xl) 0;
  color: var(--vc-text-secondary);
}

.search-card__retry-btn {
  margin-top: var(--vc-space-sm);
  padding: 6px 16px;
  background: transparent;
  color: var(--vc-text-primary);
  border: 1px solid var(--vc-border);
  border-radius: var(--vc-radius-full);
  cursor: pointer;
  font-size: var(--vc-text-xs);
  transition: all var(--vc-transition-fast);
}

.search-card__retry-btn:hover {
  border-color: var(--vc-accent);
  background: hsla(var(--vc-accent-h), var(--vc-accent-s), var(--vc-accent-l), 0.08);
}

/* 动画特效 */
@keyframes radar-pulse {
  0% {
    box-shadow: 0 0 0 0 hsla(var(--vc-accent-h), var(--vc-accent-s), var(--vc-accent-l), 0.4);
  }
  70% {
    box-shadow: 0 0 0 15px hsla(var(--vc-accent-h), var(--vc-accent-s), var(--vc-accent-l), 0);
  }
  100% {
    box-shadow: 0 0 0 0 hsla(var(--vc-accent-h), var(--vc-accent-s), var(--vc-accent-l), 0);
  }
}

@keyframes rotate-dashed {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes scale-up-down {
  0%, 100% {
    transform: scale(0.9);
  }
  50% {
    transform: scale(1.1);
  }
}

@keyframes pulse-glow {
  0%, 100% {
    opacity: 0.7;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.05);
  }
}

@keyframes text-pulse {
  0%, 100% {
    opacity: 0.8;
  }
  50% {
    opacity: 1;
  }
}

@keyframes progress-fill-step1 {
  0% { width: 0%; }
  100% { width: 60%; }
}

@keyframes progress-fill-step2 {
  0% { width: 60%; }
  100% { width: 100%; }
}
</style>
