<template>
  <div class="settings-panel">
    <div class="panel-header">
      <h2 class="panel-title">个人设置</h2>
    </div>
    <div class="panel-content">
      <!-- 个人画像 -->
      <section class="settings-section">
        <h3 class="section-title">个人画像</h3>
        <div class="settings-card">
          <div class="settings-item">
            <span class="item-label">默认出发地</span>
            <span class="item-value">北京市朝阳区</span>
          </div>
          <div class="settings-item">
            <span class="item-label">工作时间</span>
            <span class="item-value">09:00 - 18:00</span>
          </div>
        </div>
      </section>

      <!-- 服务授权 -->
      <section class="settings-section">
        <h3 class="section-title">服务授权</h3>
        <div class="settings-card">
          <div class="settings-item">
            <span class="item-label">Google Calendar</span>
            <span class="item-status status-active">已绑定</span>
          </div>
          <div class="settings-item">
            <span class="item-label">Outlook</span>
            <span class="item-status">未绑定</span>
          </div>
          <div class="settings-item">
            <span class="item-label">高德地图</span>
            <span class="item-status status-active">已绑定</span>
          </div>
        </div>
      </section>

      <!-- AI 助理偏好 -->
      <section class="settings-section">
        <h3 class="section-title">AI 助理偏好</h3>
        <div class="settings-card">
          <div class="settings-item">
            <span class="item-label">语音播报风格</span>
            <span class="item-value">干练简短</span>
          </div>
          <div class="settings-item">
            <span class="item-label">TTS 音色</span>
            <span class="item-value">成熟商务男声</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
// Settings Logic
</script>

<style scoped>
.settings-panel {
  width: 100%;
  height: 100vh;
  height: 100dvh;
  background-color: var(--vc-bg-base);
  overflow-y: auto;
  padding: env(safe-area-inset-top) 0 env(safe-area-inset-bottom);
}

.panel-header {
  padding: var(--vc-space-xl) var(--vc-space-lg) var(--vc-space-md);
}

.panel-title {
  font-size: var(--vc-text-2xl);
  font-weight: var(--vc-weight-bold);
  color: var(--vc-text-primary);
  margin: 0;
}

.panel-content {
  padding: 0 var(--vc-space-lg) var(--vc-space-2xl);
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-lg);
}

.settings-section {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-sm);
}

.section-title {
  font-size: var(--vc-text-sm);
  font-weight: var(--vc-weight-medium);
  color: var(--vc-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 0 var(--vc-space-xs);
}

.settings-card {
  background-color: var(--vc-bg-surface);
  border-radius: var(--vc-radius-lg);
  overflow: hidden;
}

.settings-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--vc-space-md);
  border-bottom: 1px solid var(--vc-divider);
}

.settings-item:last-child {
  border-bottom: none;
}

.item-label {
  font-size: var(--vc-text-base);
  color: var(--vc-text-primary);
  font-weight: var(--vc-weight-medium);
}

.item-value {
  font-size: var(--vc-text-base);
  color: var(--vc-text-secondary);
}

.item-status {
  font-size: var(--vc-text-sm);
  color: var(--vc-text-secondary);
  background: var(--vc-bg-base);
  padding: 4px 10px;
  border-radius: var(--vc-radius-full);
}

.item-status.status-active {
  color: var(--vc-accent);
  background: var(--vc-accent-glow);
}
</style>
