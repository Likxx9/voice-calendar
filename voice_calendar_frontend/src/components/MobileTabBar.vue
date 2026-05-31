<template>
  <div class="tab-bar">
    <div 
      class="tab-item" 
      :class="{ active: store.mobileTab === 'today' }"
      @click="setTab('today')"
    >
      <div class="tab-icon-wrap">🗓</div>
      <div class="tab-label">今日</div>
    </div>
    
    <div 
      class="tab-item" 
      :class="{ active: store.mobileTab === 'calendar' }"
      @click="setTab('calendar')"
    >
      <div class="tab-icon-wrap">📋</div>
      <div class="tab-label">日程</div>
    </div>
    
    <div 
      class="tab-item voice-tab" 
      :class="{ active: store.showVoiceFullscreen }"
      @click="openVoice"
    >
      <div class="tab-icon-wrap">🎙</div>
    </div>
    
    <div 
      class="tab-item" 
      :class="{ active: store.mobileTab === 'tasks' }"
      @click="setTab('tasks')"
    >
      <div class="tab-icon-wrap">✓</div>
      <div class="tab-label">任务</div>
    </div>
    
    <div 
      class="tab-item" 
      :class="{ active: store.mobileTab === 'profile' }"
      @click="setTab('profile')"
    >
      <div class="tab-icon-wrap">⚙</div>
      <div class="tab-label">设置</div>
    </div>
  </div>
</template>

<script setup>
import { store } from '../services/store'

const setTab = (tab) => {
  store.mobileTab = tab
}

const openVoice = () => {
  store.showVoiceFullscreen = true
}
</script>

<style scoped>
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: calc(var(--tab-height, 56px) + env(safe-area-inset-bottom, 0px));
  background: rgba(7, 9, 15, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid var(--border);
  display: flex;
  align-items: flex-start;
  padding-top: 8px;
  z-index: 100;
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  height: var(--tab-height, 56px);
  cursor: pointer;
  color: var(--text2);
  transition: color 0.2s ease;
  -webkit-tap-highlight-color: transparent;
  position: relative;
}

.tab-icon-wrap {
  width: 44px;
  height: 32px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--tab-icon-sz, 24px);
  transition: background 0.2s ease, transform 0.15s ease;
}

.tab-label {
  font-size: var(--tab-label-sz, 10px);
  font-weight: 500;
  letter-spacing: 0.04em;
}

.tab-item.active { color: var(--gold); }
.tab-item.active .tab-icon-wrap {
  background: var(--gold-dim);
  transform: scale(1.05);
}

.tab-item.voice-tab .tab-icon-wrap {
  width: 50px;
  height: 34px;
  background: var(--gold-dim);
  border: 1px solid var(--gold-border);
}

.tab-item.voice-tab.active .tab-icon-wrap {
  background: linear-gradient(135deg, rgba(200,164,90,.3), rgba(200,164,90,.15));
  border-color: var(--gold);
}

.tab-item:active .tab-icon-wrap {
  transform: scale(0.9);
  background: var(--bg2);
}
</style>
