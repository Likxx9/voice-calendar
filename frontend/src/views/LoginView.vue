<template>
  <div class="login-view vc-anim-fade-in">
    <!-- 背景流光特效层 -->
    <div class="login-bg-glow">
      <div class="glow-orb glow-orb--1" />
      <div class="glow-orb glow-orb--2" />
    </div>

    <!-- 登录卡片 -->
    <div class="login-card vc-glass">
      <header class="login-card__header">
        <div class="brand-logo" aria-hidden="true">🎙️</div>
        <h2 class="brand-title vc-gradient-text">语音日历</h2>
        <p class="brand-subtitle">智能日程，声临其境</p>
      </header>

      <form @submit.prevent="handleLogin" class="login-form">
        <!-- 邮箱输入框 -->
        <div class="form-group">
          <label for="email" class="form-label">电子邮箱</label>
          <div class="input-wrapper">
            <span class="input-icon">📧</span>
            <input 
              id="email" 
              type="email" 
              required 
              placeholder="请输入您的邮箱 (如 user@corp.com)"
              v-model="email"
              class="form-input"
            />
          </div>
        </div>

        <!-- 昵称输入框 -->
        <div class="form-group">
          <label for="username" class="form-label">用户昵称</label>
          <div class="input-wrapper">
            <span class="input-icon">👤</span>
            <input 
              id="username" 
              type="text" 
              required 
              placeholder="请输入您的昵称"
              v-model="username"
              class="form-input"
            />
          </div>
        </div>

        <button type="submit" class="login-btn" :disabled="isLoading">
          <span v-if="!isLoading">立即开启智能日程</span>
          <span v-else class="flex-row-center">
            <svg class="spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12a9 9 0 1 1-6.219-8.56" />
            </svg>
            验证并载入中...
          </span>
        </button>
      </form>

      <footer class="login-card__footer">
        <p class="footer-tip">无障碍盲听提示：按 Tab 键聚焦表单，直接输入即可</p>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/useSessionStore'
import { useHapticFeedback } from '@/composables/useHapticFeedback'
import { useTTSPlayer } from '@/composables/useTTSPlayer'

const router = useRouter()
const sessionStore = useSessionStore()
const { vibrate } = useHapticFeedback()
const { speakText } = useTTSPlayer()

const email = ref('')
const username = ref('')
const isLoading = ref(false)

function handleLogin() {
  if (!email.value || !username.value) return
  
  isLoading.value = true
  vibrate('processing')
  
  // 模拟登录鉴权与个人字典载入
  setTimeout(() => {
    sessionStore.login(email.value, username.value)
    vibrate('success')
    speakText(`欢迎回来，${username.value}！您的语音日历已准备就绪。`)
    isLoading.value = false
    router.push('/')
  }, 1200)
}
</script>

<style scoped>
.login-view {
  min-height: 100vh;
  min-height: 100dvh;
  width: 100vw;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--vc-space-lg);
  background-color: #050B14;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1000;
  overflow: hidden;
}

/* 流光特效 */
.login-bg-glow {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
}

.glow-orb {
  position: absolute;
  width: 280px;
  height: 280px;
  border-radius: var(--vc-radius-full);
  filter: blur(80px);
  opacity: 0.22;
  animation: floatOrb 8s infinite ease-in-out;
}

.glow-orb--1 {
  background: var(--vc-primary);
  top: 15%;
  left: 10%;
}

.glow-orb--2 {
  background: var(--vc-accent);
  bottom: 15%;
  right: 10%;
  animation-delay: -4s;
}

@keyframes floatOrb {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(30px, -20px) scale(1.1); }
}

/* 登录卡片 */
.login-card {
  width: 100%;
  max-width: 400px;
  padding: var(--vc-space-xl) var(--vc-space-lg);
  z-index: 2;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-lg);
  border-radius: var(--vc-radius-lg);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.login-card__header {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--vc-space-xs);
}

.brand-logo {
  font-size: 54px;
  margin-bottom: var(--vc-space-xs);
  animation: logoPulse 2s infinite ease-in-out;
}

@keyframes logoPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.06) rotate(5deg); }
}

.brand-title {
  font-size: var(--vc-text-2xl);
  font-weight: var(--vc-weight-bold);
  letter-spacing: -0.5px;
}

.brand-subtitle {
  font-size: var(--vc-text-xs);
  color: var(--vc-text-tertiary);
  letter-spacing: 1px;
}

/* 表单表单 */
.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-md);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-xs);
}

.form-label {
  font-size: var(--vc-text-xs);
  font-weight: var(--vc-weight-semibold);
  color: var(--vc-text-secondary);
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: var(--vc-space-md);
  font-size: 18px;
  opacity: 0.7;
}

.form-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--vc-border);
  border-radius: var(--vc-radius-md);
  padding: var(--vc-space-sm) var(--vc-space-md) var(--vc-space-sm) 44px;
  color: #FFFFFF;
  font-size: var(--vc-text-sm);
  transition: all var(--vc-transition-base);
}

.form-input:focus {
  border-color: var(--vc-accent);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 10px rgba(var(--vc-accent-h), 72%, 0.15);
}

/* 按钮 */
.login-btn {
  background: linear-gradient(135deg, var(--vc-primary) 0%, var(--vc-accent) 100%);
  color: white;
  font-weight: var(--vc-weight-bold);
  font-size: var(--vc-text-sm);
  padding: var(--vc-space-md);
  border-radius: var(--vc-radius-md);
  transition: all var(--vc-transition-base);
  box-shadow: 0 4px 15px rgba(var(--vc-primary-h), 76%, 0.25);
  margin-top: var(--vc-space-sm);
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(var(--vc-primary-h), 76%, 0.4);
}

.login-btn:active {
  transform: translateY(0);
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.flex-row-center {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--vc-space-xs);
}

.spinner {
  width: 18px;
  height: 18px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

.login-card__footer {
  text-align: center;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding-top: var(--vc-space-md);
}

.footer-tip {
  font-size: 10px;
  color: var(--vc-text-tertiary);
}
</style>
