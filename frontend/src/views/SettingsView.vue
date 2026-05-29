<template>
  <div class="settings-view vc-anim-fade-in">
    <header class="settings-header">
      <h2 class="settings-title">⚙️ 偏好设置</h2>
      <p class="settings-subtitle">个性化您的语音交互与日历呈现细节</p>
    </header>

    <div class="settings-content">
      <!-- 1. 无障碍与界面布局 -->
      <section class="settings-card vc-elevated">
        <h3 class="card-title">♿ 无障碍与布局</h3>
        
        <!-- 布局切换 -->
        <div class="settings-item">
          <div class="item-info">
            <span class="item-label">交互布局模式</span>
            <span class="item-desc">选择盲听无障碍模式或标准可视模式</span>
          </div>
          <select 
            :value="settingsStore.settings.layout_mode" 
            @change="handleLayoutChange"
            class="settings-select"
          >
            <option value="default">标准日程布局 (可视式)</option>
            <option value="eyes-free">无障碍盲听模式 (手势声控)</option>
          </select>
        </div>

        <!-- 主题切换 -->
        <div class="settings-item">
          <div class="item-info">
            <span class="item-label">界面色彩主题</span>
            <span class="item-desc">自适应光暗背景</span>
          </div>
          <select 
            :value="settingsStore.settings.theme" 
            @change="e => handleThemeChange((e.target as HTMLSelectElement).value as ThemeMode)"
            class="settings-select"
          >
            <option value="dark">🌑 极夜暗色</option>
            <option value="light">☀️ 晶莹亮色</option>
            <option value="system">🖥️ 跟随系统</option>
          </select>
        </div>
      </section>

      <!-- 2. M1 语音朗读 (TTS) 与端侧断句 -->
      <section class="settings-card vc-elevated">
        <h3 class="card-title">🎙️ 语音感知与播报</h3>

        <!-- TTS 语速 -->
        <div class="settings-item">
          <div class="item-info flex-row">
            <span class="item-label">语音播报语速 (TTS)</span>
            <span class="item-value">{{ settingsStore.settings.tts_speed.toFixed(1) }}x</span>
          </div>
          <div class="range-container">
            <input 
              type="range" 
              min="1.0" 
              max="2.5" 
              step="0.1" 
              :value="settingsStore.settings.tts_speed" 
              @input="handleTtsSpeedChange"
              class="settings-range"
            />
            <div class="range-labels">
              <span>常规 (1.0x)</span>
              <span>疾速 (2.5x)</span>
            </div>
          </div>
        </div>

        <!-- VAD 灵敏度 -->
        <div class="settings-item">
          <div class="item-info">
            <span class="item-label">自适应端侧断句 (VAD)</span>
            <span class="item-desc">设置静音检测断句的断点灵敏程度</span>
          </div>
          <div class="pill-toggle">
            <button 
              v-for="s in (['low', 'medium', 'high'] as const)" 
              :key="s"
              class="pill-btn"
              :class="{ 'pill-btn--active': settingsStore.settings.vad_sensitivity === s }"
              @click="settingsStore.updateSetting('vad_sensitivity', s)"
            >
              {{ vadLabels[s] }}
            </button>
          </div>
        </div>
      </section>

      <!-- 3. 触觉振动反馈 -->
      <section class="settings-card vc-elevated">
        <h3 class="card-title">📳 触觉振动反馈</h3>
        
        <div class="settings-item">
          <div class="item-info">
            <span class="item-label">指尖振动确认强度</span>
            <span class="item-desc">录音、处理、成功或冲突时的多态触觉振动提示</span>
          </div>
          <div class="pill-toggle">
            <button 
              v-for="intensity in (['off', 'light', 'medium', 'strong'] as const)" 
              :key="intensity"
              class="pill-btn"
              :class="{ 'pill-btn--active': settingsStore.settings.haptic_intensity === intensity }"
              @click="handleHapticChange(intensity)"
            >
              {{ hapticLabels[intensity] }}
            </button>
          </div>
        </div>
      </section>

      <!-- 4. 账号状态与重置 -->
      <div class="actions-row">
        <button class="reset-btn" @click="handleReset">恢复默认设置</button>
        <span class="divider-dot" aria-hidden="true">•</span>
        <button class="logout-btn" @click="handleLogout">退出当前账号</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSettingsStore } from '@/stores/useSettingsStore'
import { useHapticFeedback } from '@/composables/useHapticFeedback'
import { useTTSPlayer } from '@/composables/useTTSPlayer'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/useSessionStore'
import type { ThemeMode, LayoutMode } from '@/types/contracts'

const router = useRouter()
const sessionStore = useSessionStore()
const settingsStore = useSettingsStore()
const { vibrate } = useHapticFeedback()
const { speakText } = useTTSPlayer()

const vadLabels = {
  low: '宽松 (不易被打断)',
  medium: '标准平衡',
  high: '敏感 (即刻说话即断)'
}

const hapticLabels = {
  off: '关闭振动',
  light: '轻微微动',
  medium: '适中强度',
  strong: '高反馈强度'
}

function handleLayoutChange(e: Event) {
  const mode = (e.target as HTMLSelectElement).value as LayoutMode
  settingsStore.updateSetting('layout_mode', mode)
  vibrate('tap')
  if (mode === 'eyes-free') {
    speakText('盲听模式已开启，全屏可触发大面积手势操作。')
  }
}

function handleThemeChange(theme: ThemeMode) {
  settingsStore.updateSetting('theme', theme)
  vibrate('tap')
}

function handleTtsSpeedChange(e: Event) {
  const speed = parseFloat((e.target as HTMLInputElement).value)
  settingsStore.updateSetting('tts_speed', speed)
}

function handleHapticChange(intensity: 'off' | 'light' | 'medium' | 'strong') {
  settingsStore.updateSetting('haptic_intensity', intensity)
  // 即时振动反馈预览
  setTimeout(() => {
    vibrate('success')
  }, 100)
}

function handleReset() {
  settingsStore.resetSettings()
  vibrate('tap')
  speakText('设置已恢复为初始状态。')
}

function handleLogout() {
  vibrate('recording')
  sessionStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.settings-view {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-lg);
  padding-bottom: var(--vc-space-xl);
}

.settings-header {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.settings-title {
  font-size: var(--vc-text-xl);
  font-weight: var(--vc-weight-bold);
  color: var(--vc-text-primary);
}

.settings-subtitle {
  font-size: var(--vc-text-sm);
  color: var(--vc-text-secondary);
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-md);
}

.settings-card {
  padding: var(--vc-space-md);
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-md);
}

.card-title {
  font-size: var(--vc-text-sm);
  font-weight: var(--vc-weight-bold);
  color: var(--vc-primary-light);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--vc-divider);
  padding-bottom: var(--vc-space-xs);
}

.settings-item {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-xs);
}

.item-info {
  display: flex;
  flex-direction: column;
}

.flex-row {
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
}

.item-label {
  font-size: var(--vc-text-sm);
  font-weight: var(--vc-weight-semibold);
  color: var(--vc-text-primary);
}

.item-desc {
  font-size: var(--vc-text-xs);
  color: var(--vc-text-tertiary);
}

.item-value {
  font-size: var(--vc-text-sm);
  font-weight: var(--vc-weight-bold);
  color: var(--vc-accent-light);
}

/* 控件样式 */
.settings-select {
  width: 100%;
  background: var(--vc-bg-surface);
  border: 1px solid var(--vc-border);
  border-radius: var(--vc-radius-sm);
  padding: var(--vc-space-sm);
  color: var(--vc-text-primary);
  font-size: var(--vc-text-sm);
  cursor: pointer;
  outline: none;
}

.settings-select:focus {
  border-color: var(--vc-primary);
}

.range-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.settings-range {
  -webkit-appearance: none;
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: var(--vc-radius-full);
  outline: none;
  cursor: pointer;
}

.settings-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--vc-primary-light);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
  transition: transform 0.1s ease;
}

.settings-range::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}

.range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--vc-text-tertiary);
}

/* 药丸多选组 */
.pill-toggle {
  display: flex;
  background: var(--vc-bg-surface);
  border: 1px solid var(--vc-border);
  border-radius: var(--vc-radius-sm);
  padding: 3px;
  gap: 2px;
}

.pill-btn {
  flex: 1;
  text-align: center;
  padding: var(--vc-space-xs) 0;
  font-size: var(--vc-text-xs);
  font-weight: var(--vc-weight-medium);
  color: var(--vc-text-tertiary);
  border-radius: calc(var(--vc-radius-sm) - 2px);
  transition: all var(--vc-transition-fast);
}

.pill-btn--active {
  background: var(--vc-accent);
  color: white;
  box-shadow: var(--vc-shadow-sm);
}

.actions-row {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: var(--vc-space-md);
}

.divider-dot {
  font-size: var(--vc-text-xs);
  color: var(--vc-text-tertiary);
  margin: 0 var(--vc-space-sm);
  opacity: 0.5;
}

.reset-btn,
.logout-btn {
  font-size: var(--vc-text-xs);
  color: var(--vc-text-tertiary);
  text-decoration: underline;
  cursor: pointer;
  transition: color var(--vc-transition-fast);
}

.reset-btn:hover,
.logout-btn:hover {
  color: var(--vc-danger);
}
</style>
