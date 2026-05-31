<template>
  <div class="settings-page">
    <div class="settings-header">
      <button class="back-btn" @click="$emit('close')">← 返回</button>
      <h2>设置</h2>
    </div>

    <div class="settings-body">
      <!-- 用户资料 -->
      <section class="settings-section">
        <div class="sec-head">
          <span class="sec-icon">👤</span>
          <span>用户资料</span>
        </div>
        <div class="setting-row">
          <label>用户名</label>
          <input v-model="profile.name" type="text" class="s-input" />
        </div>
        <div class="setting-row">
          <label>时区</label>
          <select v-model="profile.timezone" class="s-select">
            <option value="Asia/Shanghai">中国标准时间 (UTC+8)</option>
            <option value="Asia/Tokyo">日本标准时间 (UTC+9)</option>
            <option value="America/New_York">美国东部 (UTC-5)</option>
            <option value="Europe/London">英国 (UTC+0)</option>
          </select>
        </div>
        <button class="s-btn" @click="saveProfile" :disabled="profileSaving">
          {{ profileSaving ? '保存中...' : '保存资料' }}
        </button>
        <div v-if="profileMsg" :class="['s-msg', profileOk ? 'ok' : 'err']">{{ profileMsg }}</div>
      </section>

      <!-- 语音助手 -->
      <section class="settings-section">
        <div class="sec-head">
          <span class="sec-icon">🎙</span>
          <span>语音助手</span>
        </div>
        <div class="setting-row">
          <label>TTS 语速</label>
          <div class="range-wrap">
            <input type="range" v-model.number="store.settings.ttsSpeed" min="0" max="100" class="s-range" @change="save" />
            <span class="range-val">{{ store.settings.ttsSpeed }}</span>
          </div>
        </div>
        <div class="setting-row">
          <label>TTS 音色</label>
          <select v-model="store.settings.ttsVoice" class="s-select" @change="save">
            <option value="xiaoyan">小燕 (女声)</option>
            <option value="aisjiuxu">阿树 (男声)</option>
            <option value="aisxping">小萍 (女声)</option>
            <option value="aisjinger">小婧 (女声)</option>
          </select>
        </div>
        <div class="setting-row">
          <label>识别语言</label>
          <select v-model="store.settings.asrLanguage" class="s-select" @change="save">
            <option value="zh_cn">中文普通话</option>
            <option value="en_us">English</option>
            <option value="zh_cn_cantonese">粤语</option>
            <option value="zh_cn_sichuan">四川话</option>
          </select>
        </div>
        <div class="setting-row">
          <label>唤醒词</label>
          <input v-model="store.settings.wakeWord" type="text" class="s-input" placeholder="留空则不启用唤醒词" @change="save" />
        </div>
      </section>

      <!-- 日历偏好 -->
      <section class="settings-section">
        <div class="sec-head">
          <span class="sec-icon">📅</span>
          <span>日历偏好</span>
        </div>
        <div class="setting-row">
          <label>默认视图</label>
          <select v-model="store.settings.defaultView" class="s-select" @change="save">
            <option value="day">日视图</option>
            <option value="week">周视图</option>
            <option value="month">月视图</option>
          </select>
        </div>
        <div class="setting-row">
          <label>工作时间</label>
          <div class="time-range">
            <select v-model.number="store.settings.workHourStart" class="s-select sm" @change="save">
              <option v-for="h in 24" :key="h-1" :value="h-1">{{ String(h-1).padStart(2,'0') }}:00</option>
            </select>
            <span class="time-sep">至</span>
            <select v-model.number="store.settings.workHourEnd" class="s-select sm" @change="save">
              <option v-for="h in 24" :key="h" :value="h">{{ String(h).padStart(2,'0') }}:00</option>
            </select>
          </div>
        </div>
        <div class="setting-row">
          <label>每周起始日</label>
          <select v-model.number="store.settings.weekStartDay" class="s-select" @change="save">
            <option :value="0">周日</option>
            <option :value="1">周一</option>
          </select>
        </div>
        <div class="setting-row">
          <label>默认提醒提前</label>
          <select v-model.number="store.settings.reminderDefault" class="s-select" @change="save">
            <option :value="5">5 分钟</option>
            <option :value="10">10 分钟</option>
            <option :value="15">15 分钟</option>
            <option :value="30">30 分钟</option>
            <option :value="60">1 小时</option>
          </select>
        </div>
      </section>

      <!-- 账号安全 -->
      <section class="settings-section">
        <div class="sec-head">
          <span class="sec-icon">🔒</span>
          <span>账号安全</span>
        </div>
        <div class="setting-row">
          <label>当前密码</label>
          <input v-model="pwd.old" type="password" class="s-input" placeholder="输入当前密码" />
        </div>
        <div class="setting-row">
          <label>新密码</label>
          <input v-model="pwd.new1" type="password" class="s-input" placeholder="至少6个字符" />
        </div>
        <div class="setting-row">
          <label>确认新密码</label>
          <input v-model="pwd.new2" type="password" class="s-input" placeholder="再次输入新密码" />
        </div>
        <button class="s-btn" @click="changePassword" :disabled="pwdSaving">
          {{ pwdSaving ? '修改中...' : '修改密码' }}
        </button>
        <div v-if="pwdMsg" :class="['s-msg', pwdOk ? 'ok' : 'err']">{{ pwdMsg }}</div>

        <div class="danger-zone">
          <button class="s-btn danger" @click="clearData">清除对话记录</button>
          <button class="s-btn danger" @click="handleLogout">退出登录</button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { store, saveSettings, updateUser, logout, clearChatHistory } from '../services/store'

const emit = defineEmits(['close'])

const profile = reactive({
  name: store.currentUser?.name || '',
  timezone: store.currentUser?.timezone || 'Asia/Shanghai',
})
const profileSaving = ref(false)
const profileMsg = ref('')
const profileOk = ref(false)

const pwd = reactive({ old: '', new1: '', new2: '' })
const pwdSaving = ref(false)
const pwdMsg = ref('')
const pwdOk = ref(false)

const save = () => saveSettings()

const saveProfile = async () => {
  profileMsg.value = ''
  profileSaving.value = true
  try {
    const resp = await fetch('/api/auth/profile', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${store.authToken}`
      },
      body: JSON.stringify({ name: profile.name, timezone: profile.timezone })
    })
    const data = await resp.json()
    if (!resp.ok) {
      profileMsg.value = data.error || '保存失败'
      profileOk.value = false
      return
    }
    updateUser({ name: profile.name, timezone: profile.timezone })
    profileMsg.value = '保存成功'
    profileOk.value = true
  } catch {
    profileMsg.value = '网络错误'
    profileOk.value = false
  } finally {
    profileSaving.value = false
  }
}

const changePassword = async () => {
  pwdMsg.value = ''
  if (!pwd.old) { pwdMsg.value = '请输入当前密码'; pwdOk.value = false; return }
  if (pwd.new1.length < 6) { pwdMsg.value = '新密码至少6个字符'; pwdOk.value = false; return }
  if (pwd.new1 !== pwd.new2) { pwdMsg.value = '两次密码不一致'; pwdOk.value = false; return }

  pwdSaving.value = true
  try {
    const resp = await fetch('/api/auth/password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${store.authToken}`
      },
      body: JSON.stringify({ old_password: pwd.old, new_password: pwd.new1 })
    })
    const data = await resp.json()
    if (!resp.ok) {
      pwdMsg.value = data.error || '修改失败'
      pwdOk.value = false
      return
    }
    pwdMsg.value = '密码修改成功'
    pwdOk.value = true
    pwd.old = ''; pwd.new1 = ''; pwd.new2 = ''
  } catch {
    pwdMsg.value = '网络错误'
    pwdOk.value = false
  } finally {
    pwdSaving.value = false
  }
}

const clearData = () => {
  clearChatHistory()
}

const handleLogout = () => {
  logout()
}
</script>

<style scoped>
.settings-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg);
  overflow-y: auto;
}

.settings-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
  background: var(--bg2);
  position: sticky;
  top: 0;
  z-index: 10;
}
.settings-header h2 { font-size: 18px; font-weight: 500; color: var(--text); margin: 0; }
.back-btn {
  background: none; border: 1px solid var(--border); color: var(--text2);
  padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 13px;
  transition: all 0.2s;
}
.back-btn:hover { color: var(--gold); border-color: var(--gold-border); }

.settings-body {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 560px;
  width: 100%;
  margin: 0 auto;
}

.settings-section {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.sec-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
}
.sec-icon { font-size: 16px; }

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.setting-row label {
  font-size: 13px;
  color: var(--text2);
  white-space: nowrap;
  min-width: 80px;
}

.s-input, .s-select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text);
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
  max-width: 220px;
}
.s-input:focus, .s-select:focus { border-color: var(--gold); }
.s-select { cursor: pointer; }
.s-select.sm { max-width: 100px; }

.range-wrap { display: flex; align-items: center; gap: 10px; flex: 1; max-width: 220px; }
.s-range { flex: 1; accent-color: var(--gold); }
.range-val { font-size: 12px; color: var(--text2); min-width: 24px; text-align: right; }

.time-range { display: flex; align-items: center; gap: 6px; }
.time-sep { font-size: 12px; color: var(--text3); }

.s-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  background: var(--gold-dim);
  border: 1px solid var(--gold-border);
  color: var(--gold);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  align-self: flex-start;
}
.s-btn:hover { background: rgba(200,164,90,.2); }
.s-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.s-btn.danger {
  background: rgba(200,60,60,.1);
  border-color: rgba(200,60,60,.3);
  color: #ff6b6b;
}
.s-btn.danger:hover { background: rgba(200,60,60,.2); }

.s-msg {
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 4px;
}
.s-msg.ok { color: var(--teal); background: var(--teal-dim); }
.s-msg.err { color: #ff6b6b; background: rgba(200,60,60,.1); }

.danger-zone {
  display: flex;
  gap: 10px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
  margin-top: 6px;
}

@media (max-width: 767px) {
  .settings-body { padding: 16px; }
  .settings-section { padding: 16px; }
  .setting-row { flex-direction: column; align-items: stretch; gap: 6px; }
  .s-input, .s-select { max-width: none; }
  .range-wrap { max-width: none; }
}
</style>
