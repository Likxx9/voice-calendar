<template>
  <div class="default-layout">
    <!-- 顶部状态栏 -->
    <header class="default-layout__header vc-glass">
      <div class="header-brand">
        <span class="header-brand__logo">🎙️</span>
        <h1 class="header-brand__title vc-gradient-text">语音日历</h1>
      </div>
      <div class="header-status">
        <ConnectionStatus :state="sessionStore.connectionState" />
        <SyncStatusBanner :state="offlineQueueStore.syncState" />
      </div>
    </header>

    <!-- 主体区域 -->
    <main class="default-layout__main">
      <router-view v-slot="{ Component }">
        <transition name="fade-slide" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- 底部导航栏 -->
    <nav class="default-layout__nav vc-glass" role="navigation" aria-label="底部导航">
      <router-link to="/" class="nav-item" active-class="nav-item--active">
        <span class="nav-item__icon" aria-hidden="true">📅</span>
        <span class="nav-item__label">日程</span>
      </router-link>

      <!-- 核心语音气泡/麦克风按钮（中置高亮） -->
      <button 
        class="voice-fab"
        :class="{ 'voice-fab--recording': sessionStore.isRecording }"
        aria-label="语音助手"
        @click="goToAssistant"
      >
        <div class="voice-fab__circle">
          <span class="voice-fab__icon" aria-hidden="true">🎙️</span>
        </div>
        <div class="voice-fab__ring" />
      </button>

      <router-link to="/settings" class="nav-item" active-class="nav-item--active">
        <span class="nav-item__icon" aria-hidden="true">⚙️</span>
        <span class="nav-item__label">设置</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/useSessionStore'
import ConnectionStatus from '@/modules/gateway/ConnectionStatus.vue'
import SyncStatusBanner from '@/modules/sync/SyncStatusBanner.vue'

// Mock storage for offline sync state since actual composable might vary slightly
import { ref } from 'vue'
const offlineQueueStore = ref({ syncState: 'online' as const })

const router = useRouter()
const sessionStore = useSessionStore()

function goToAssistant() {
  router.push('/conversation')
}
</script>

<style scoped>
.default-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-height: 100dvh;
  background-color: var(--vc-bg-base);
  color: var(--vc-text-primary);
  position: relative;
  padding-bottom: calc(70px + var(--vc-space-md)); /* 为底部导航栏预留空间 */
}

/* 顶部状态栏 */
.default-layout__header {
  position: sticky;
  top: 0;
  z-index: var(--vc-z-sticky);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--vc-space-sm) var(--vc-space-md);
  height: 60px;
  border-bottom: 1px solid var(--vc-border);
}

.header-brand {
  display: flex;
  align-items: center;
  gap: var(--vc-space-xs);
}

.header-brand__logo {
  font-size: 20px;
}

.header-brand__title {
  font-size: var(--vc-text-lg);
  font-weight: var(--vc-weight-bold);
  letter-spacing: -0.5px;
}

.header-status {
  display: flex;
  align-items: center;
  gap: var(--vc-space-sm);
}

/* 主体区域 */
.default-layout__main {
  flex: 1;
  width: 100%;
  max-width: 768px; /* 居中显示，完美适配手机与平板 */
  margin: 0 auto;
  padding: var(--vc-space-md);
}

/* 底部导航栏 */
.default-layout__nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 70px;
  display: flex;
  justify-content: space-around;
  align-items: center;
  border-top: 1px solid var(--vc-border);
  z-index: var(--vc-z-sticky);
  padding: 0 var(--vc-space-lg);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  color: var(--vc-text-tertiary);
  transition: all var(--vc-transition-base);
  width: 64px;
  height: 100%;
}

.nav-item__icon {
  font-size: 20px;
  transition: transform var(--vc-transition-spring);
}

.nav-item__label {
  font-size: 10px;
  font-weight: var(--vc-weight-medium);
}

.nav-item:hover {
  color: var(--vc-text-secondary);
}

.nav-item--active {
  color: var(--vc-primary-light);
}

.nav-item--active .nav-item__icon {
  transform: scale(1.15);
}

/* 麦克风悬浮按钮 */
.voice-fab {
  width: 60px;
  height: 60px;
  position: relative;
  margin-top: -24px;
  z-index: var(--vc-z-fab);
  border-radius: var(--vc-radius-full);
}

.voice-fab__circle {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--vc-primary) 0%, var(--vc-accent) 100%);
  border-radius: var(--vc-radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px rgba(var(--vc-primary-h), 48%, 0.35);
  transition: all var(--vc-transition-spring);
  border: 2px solid var(--vc-bg-base);
}

.voice-fab__icon {
  font-size: 26px;
  transition: transform var(--vc-transition-spring);
}

.voice-fab__ring {
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  border-radius: var(--vc-radius-full);
  border: 2px solid var(--vc-accent-light);
  opacity: 0;
  transition: all var(--vc-transition-base);
  pointer-events: none;
}

.voice-fab:hover .voice-fab__circle {
  transform: translateY(-4px) scale(1.05);
  box-shadow: 0 8px 25px rgba(var(--vc-primary-h), 48%, 0.5);
}

.voice-fab:hover .voice-fab__icon {
  transform: rotate(-10deg);
}

.voice-fab:active .voice-fab__circle {
  transform: translateY(-2px) scale(0.95);
}

.voice-fab--recording .voice-fab__circle {
  background: var(--vc-recording);
  animation: pulse 1.5s infinite;
}

.voice-fab--recording .voice-fab__ring {
  animation: ripple 1.5s infinite;
  opacity: 1;
}

/* 动效定义 */
@keyframes pulse {
  0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
  70% { transform: scale(1.05); box-shadow: 0 0 0 15px rgba(239, 68, 68, 0); }
  100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

@keyframes ripple {
  0% { transform: scale(1); opacity: 0.8; }
  100% { transform: scale(1.4); opacity: 0; }
}

/* 过渡动效 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all var(--vc-transition-base);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
