<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-logo">VoiCal</div>
      <div class="auth-subtitle">智能语音日历助理</div>

      <div class="auth-tabs">
        <button :class="['auth-tab', { active: mode === 'login' }]" @click="mode = 'login'">登录</button>
        <button :class="['auth-tab', { active: mode === 'register' }]" @click="mode = 'register'">注册</button>
      </div>

      <form class="auth-form" @submit.prevent="handleSubmit">
        <div class="field">
          <label>用户名</label>
          <input v-model="name" type="text" placeholder="请输入用户名" autocomplete="username" />
        </div>
        <div class="field">
          <label>密码</label>
          <input v-model="password" type="password" placeholder="请输入密码" autocomplete="current-password" />
        </div>
        <div v-if="mode === 'register'" class="field">
          <label>确认密码</label>
          <input v-model="confirmPassword" type="password" placeholder="再次输入密码" />
        </div>

        <div v-if="error" class="auth-error">{{ error }}</div>

        <button class="auth-submit" type="submit" :disabled="loading">
          {{ loading ? '请稍候...' : (mode === 'login' ? '登 录' : '注 册') }}
        </button>
      </form>

      <div class="auth-footer">
        <template v-if="mode === 'login'">
          还没有账号？<a @click="mode = 'register'">立即注册</a>
        </template>
        <template v-else>
          已有账号？<a @click="mode = 'login'">去登录</a>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['login-success'])

const mode = ref('login')
const name = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const loading = ref(false)

const handleSubmit = async () => {
  error.value = ''

  if (!name.value.trim() || !password.value.trim()) {
    error.value = '请填写用户名和密码'
    return
  }

  if (mode.value === 'register') {
    if (password.value.length < 6) {
      error.value = '密码至少6个字符'
      return
    }
    if (password.value !== confirmPassword.value) {
      error.value = '两次密码不一致'
      return
    }
  }

  loading.value = true
  try {
    const url = mode.value === 'login' ? '/api/auth/login' : '/api/auth/register'
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name.value.trim(), password: password.value })
    })

    const text = await resp.text()
    let data
    try {
      data = JSON.parse(text)
    } catch {
      console.error('[Auth] 非 JSON 响应:', text.slice(0, 200))
      error.value = `服务器返回异常 (HTTP ${resp.status})`
      return
    }

    if (!resp.ok) {
      error.value = data.error || '操作失败'
      return
    }

    // 保存 token 和用户信息
    localStorage.setItem('voical_token', data.token)
    localStorage.setItem('voical_user', JSON.stringify(data.user))

    emit('login-success', data.user)
  } catch (err) {
    error.value = '网络错误，请检查后端是否启动'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(ellipse at 50% 30%, rgba(200,164,90,.08), var(--bg) 70%);
  background-color: var(--bg);
  padding: 24px;
}

.auth-card {
  width: 100%;
  max-width: 380px;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 36px 32px;
  text-align: center;
}

.auth-logo {
  font-family: var(--fu);
  font-size: 32px;
  font-weight: 300;
  color: var(--gold);
  letter-spacing: 0.08em;
  margin-bottom: 4px;
}

.auth-subtitle {
  font-size: 13px;
  color: var(--text3);
  margin-bottom: 28px;
}

.auth-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 24px;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.auth-tab {
  flex: 1;
  padding: 10px 0;
  font-size: 14px;
  font-weight: 500;
  background: transparent;
  border: none;
  color: var(--text2);
  cursor: pointer;
  transition: all 0.2s;
}
.auth-tab.active {
  background: var(--gold-dim);
  color: var(--gold);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  text-align: left;
}

.field label {
  display: block;
  font-size: 12px;
  color: var(--text2);
  margin-bottom: 6px;
  font-weight: 500;
}

.field input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}
.field input:focus {
  border-color: var(--gold);
}
.field input::placeholder {
  color: var(--text3);
}

.auth-error {
  background: rgba(200,60,60,.1);
  border: 1px solid rgba(200,60,60,.3);
  color: #ff6b6b;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  text-align: center;
}

.auth-submit {
  padding: 12px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--gold), #9B6B1A);
  color: #000;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.1em;
}
.auth-submit:hover { filter: brightness(1.1); }
.auth-submit:active { transform: scale(0.98); }
.auth-submit:disabled { opacity: 0.6; cursor: not-allowed; }

.auth-footer {
  margin-top: 20px;
  font-size: 12px;
  color: var(--text3);
}
.auth-footer a {
  color: var(--gold);
  cursor: pointer;
  text-decoration: none;
}
.auth-footer a:hover { text-decoration: underline; }
</style>
