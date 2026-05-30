<template>
  <transition name="slide-up">
    <div v-if="isVisible" class="conflict-bottom-sheet">
      <!-- Overlay to catch clicks outside -->
      <div class="sheet-overlay" @click="handleCancel"></div>

      <!-- Sheet Content -->
      <div class="sheet-content">
        <!-- Warning Header -->
        <header class="sheet-header">
          <div class="warning-icon">
            <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path>
              <line x1="12" y1="9" x2="12" y2="13"></line>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
          </div>
          <h3 class="header-title">发现时间冲突</h3>
        </header>

        <!-- Body -->
        <div class="sheet-body">
          <p class="conflict-desc">我们发现您的新日程与现有安排存在重叠或通勤时间不足。</p>
          
          <!-- Visual comparison of conflicts can go here (simplified for now) -->
          <div class="conflict-list">
            <div v-for="(conflict, index) in conflicts" :key="index" class="conflict-item">
              <span class="conflict-dot"></span>
              <span class="conflict-text">{{ conflict.title }} ({{ formatTime(conflict.start_time) }} - {{ formatTime(conflict.end_time) }})</span>
            </div>
          </div>

          <!-- Quick Actions (Suggestions) -->
          <div class="action-buttons">
            <button 
              v-for="(suggestion, index) in suggestions" 
              :key="index"
              class="btn-suggestion"
              @click="handleResolve(suggestion)"
            >
              {{ suggestion }}
            </button>
            <button class="btn-cancel" @click="handleCancel">
              取消并重新输入
            </button>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import type { ConflictItem } from '@/types/contracts'

const props = defineProps<{
  isVisible: boolean
  conflicts: ConflictItem[]
  suggestions: string[]
}>()

const emit = defineEmits<{
  (e: 'resolve', suggestion: string): void
  (e: 'cancel'): void
}>()

function formatTime(isoString: string) {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function handleResolve(suggestion: string) {
  emit('resolve', suggestion)
}

function handleCancel() {
  emit('cancel')
}
</script>

<style scoped>
.conflict-bottom-sheet {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  height: 100dvh;
  z-index: var(--vc-z-conflict-panel);
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.sheet-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: var(--vc-bg-overlay);
  z-index: 1;
}

.sheet-content {
  position: relative;
  z-index: 2;
  background-color: var(--vc-bg-surface);
  border-top-left-radius: var(--vc-radius-xl);
  border-top-right-radius: var(--vc-radius-xl);
  box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  max-height: 80vh;
  overflow: hidden;
}

.sheet-header {
  background-color: var(--vc-warning-soft);
  color: var(--vc-warning);
  padding: var(--vc-space-md) var(--vc-space-lg);
  display: flex;
  align-items: center;
  gap: var(--vc-space-sm);
  border-bottom: 1px solid var(--vc-divider);
}

.warning-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-title {
  font-size: var(--vc-text-lg);
  font-weight: var(--vc-weight-semibold);
  margin: 0;
}

.sheet-body {
  padding: var(--vc-space-lg);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-md);
}

.conflict-desc {
  font-size: var(--vc-text-sm);
  color: var(--vc-text-secondary);
}

.conflict-list {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-sm);
  background-color: var(--vc-bg-base);
  padding: var(--vc-space-md);
  border-radius: var(--vc-radius-md);
  border: 1px solid var(--vc-warning-soft);
}

.conflict-item {
  display: flex;
  align-items: center;
  gap: var(--vc-space-sm);
  font-size: var(--vc-text-sm);
  color: var(--vc-text-primary);
}

.conflict-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--vc-warning);
  flex-shrink: 0;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-sm);
  margin-top: var(--vc-space-sm);
}

.btn-suggestion {
  background-color: var(--vc-primary);
  color: var(--vc-text-inverse);
  padding: var(--vc-space-md);
  border-radius: var(--vc-radius-md);
  font-weight: var(--vc-weight-medium);
  text-align: center;
  transition: opacity var(--vc-transition-fast);
}

.btn-suggestion:active {
  opacity: 0.8;
}

.btn-cancel {
  background-color: transparent;
  color: var(--vc-text-secondary);
  padding: var(--vc-space-md);
  border-radius: var(--vc-radius-md);
  font-weight: var(--vc-weight-medium);
  text-align: center;
  border: 1px solid var(--vc-border);
}

/* Animations */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all var(--vc-transition-bottom-sheet);
}

.slide-up-enter-from .sheet-overlay,
.slide-up-leave-to .sheet-overlay {
  opacity: 0;
}

.slide-up-enter-from .sheet-content {
  transform: translateY(100%);
}
.slide-up-leave-to .sheet-content {
  transform: translateY(100%);
}
</style>
