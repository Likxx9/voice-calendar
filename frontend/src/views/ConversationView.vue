<template>
  <div class="conversation-view vc-anim-fade-in">
    <!-- 头部：导航与连接指示 -->
    <header class="conversation-header">
      <button class="back-btn" aria-label="返回日历" @click="goHome">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="19" y1="12" x2="5" y2="12" />
          <polyline points="12 19 5 12 12 5" />
        </svg>
      </button>
      <div class="header-center">
        <VoiceStatusIndicator :status="sessionStore.voiceState" />
      </div>
      <ConnectionStatus :state="sessionStore.connectionState" />
    </header>

    <!-- 核心对话流区域 -->
    <section class="conversation-flow-wrap" ref="flowScrollContainer">
      <ConversationFlow :messages="sessionStore.messages" />

      <!-- 实时追问卡片 (Clarification) -->
      <div v-if="sessionStore.voiceState === 'clarifying'" class="inline-card-container">
        <ClarificationCard
          :message="'请问这个日程的主题是什么？比如“和产品经理对需求”'"
          :missingFields="['title']"
          @voice-reply="startVoiceInput"
          @skip="handleSkipClarification"
        />
      </div>

      <!-- 实时时间冲突卡片 (Conflict Negotiation) -->
      <div v-if="sessionStore.voiceState === 'conflict'" class="inline-card-container">
        <ConflictNegotiation
          :conflicts="mockConflicts"
          :suggestions="['改期至下午 3:30', '改期至明天下午同一时间', '仍然强制创建']"
          @select="handleResolveConflict"
          @voice-resolve="startVoiceInput"
          @force-create="handleForceCreate"
          @cancel="handleCancelConflict"
        />
      </div>



      <!-- 实时联网搜索卡片 (M9 Web Search Agent) -->
      <div v-if="sessionStore.voiceState === 'searching'" class="inline-card-container">
        <SearchAgentCard
          :query="currentSearchQuery"
          :status="currentSearchStatus"
          :events="currentSearchEvents"
          @add-event="handleSearchAddEvent"
          @retry="handleSearchRetry"
        />
      </div>
    </section>

    <!-- 底部状态、频谱与操作区 -->
    <footer class="conversation-footer vc-glass">
      <!-- 键盘文本输入模式与语音转写流模式的形态切换 -->
      <div class="footer-input-morph">
        <transition name="morph-fade" mode="out-in">
          <!-- 键盘键入形态：仅在闲置/未录音/未处理时展示 -->
          <div v-if="sessionStore.voiceState === 'idle'" class="morph-input-bar">
            <span class="morph-input-icon">⌨️</span>
            <input 
              type="text" 
              class="keyboard-text-input" 
              placeholder="输入您的日程指令... (例如：明早九点开会)" 
              v-model="keyboardInputText"
              @keyup.enter="handleKeyboardSubmit"
            />
            <button 
              class="morph-input-submit"
              :disabled="!keyboardInputText.trim()"
              @click="handleKeyboardSubmit"
              aria-label="提交日程"
            >
              ➔
            </button>
          </div>

          <!-- 语音输入形态：录音、解析或检索状态下展示 -->
          <div v-else class="morph-transcript-bar">
            <StreamingTranscript
              :isActive="sessionStore.isRecording || sessionStore.isProcessing || sessionStore.voiceState === 'searching'"
              :partialText="sessionStore.partialTranscript"
              :finalText="sessionStore.finalTranscript"
            />
          </div>
        </transition>
      </div>

      <!-- 实时音频波形图 (录音中显示频谱柱，支持实时音量微动) -->
      <div class="footer-visualizer" :class="{ 'footer-visualizer--visible': sessionStore.isRecording }">
        <WaveformVisualizer
          :isActive="sessionStore.isRecording"
          :volume="mockVolume"
          :width="300"
          :height="60"
        />
      </div>

      <!-- 快捷智能回复引导词 -->
      <div class="footer-suggestions" v-if="sessionStore.voiceState === 'idle'">
        <button 
          v-for="s in quickSuggestions" 
          :key="s" 
          class="suggestion-pill"
          @click="handleQuickInput(s)"
        >
          {{ s }}
        </button>
      </div>

      <!-- 麦克风控制与播报控制区 -->
      <div class="footer-control-row">
        <!-- 播报控制条 (TTS) -->
        <TTSControlBar
          v-if="sessionStore.isTTSPlaying"
          :isPlaying="sessionStore.isTTSPlaying"
          @play="speakLastMessage"
          @pause="stopTTS"
          @stop="stopTTS"
        />

        <div class="main-mic-button-row">
          <div class="main-mic-button">
            <VoiceButton
              :status="sessionStore.voiceState"
              :volume="mockVolume"
              @press-start="startVoiceInput"
              @press-end="stopVoiceInput"
              @tap="handleTapButton"
            />
          </div>
          <!-- 键盘/语音快捷形态说明标签 -->
          <span class="morph-mic-tip" v-if="sessionStore.voiceState === 'idle'">
            或按住/轻触麦克风进行语音添加
          </span>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/useSessionStore'
import { useCalendarStore } from '@/stores/useCalendarStore'
import { useHapticFeedback } from '@/composables/useHapticFeedback'
import { useTTSPlayer } from '@/composables/useTTSPlayer'

// UI 组件
import VoiceStatusIndicator from '@/modules/sensory/VoiceStatusIndicator.vue'
import ConnectionStatus from '@/modules/gateway/ConnectionStatus.vue'
import ConversationFlow from '@/modules/stateMachine/ConversationFlow.vue'
import StreamingTranscript from '@/modules/gateway/StreamingTranscript.vue'
import WaveformVisualizer from '@/modules/sensory/WaveformVisualizer.vue'
import VoiceButton from '@/modules/sensory/VoiceButton.vue'
import ClarificationCard from '@/modules/stateMachine/ClarificationCard.vue'
import ConflictNegotiation from '@/modules/stateMachine/ConflictNegotiation.vue'
import TTSControlBar from '@/modules/sensory/TTSControlBar.vue'
import SearchAgentCard from '@/modules/stateMachine/SearchAgentCard.vue'

import type { ConflictItem, WebSearchEvent } from '@/types/contracts'

const router = useRouter()
const sessionStore = useSessionStore()
const calendarStore = useCalendarStore()
const { vibrate } = useHapticFeedback()
const { speakText, stop: stopTTS } = useTTSPlayer()

const flowScrollContainer = ref<HTMLElement | null>(null)
const mockVolume = ref(0)

// M9 Web Search Agent 状态
const currentSearchQuery = ref('')
const currentSearchStatus = ref<'searching' | 'parsing' | 'results'>('searching')
const currentSearchEvents = ref<WebSearchEvent[]>([])

const quickSuggestions = [
  '帮我创建明天下午三点的会',
  '联网检索2026年杭州的动漫展',
  '搜一下上海最近的实践活动',
  '添加买牛奶的待办'
]



const mockConflicts = computed<ConflictItem[]>(() => {
  const todayStr = new Date().toISOString().split('T')[0]
  return [{
    existing_event_id: 'ev-2',
    existing_title: '语音日历前端架构评审',
    overlap_start: `${todayStr}T14:00:00`,
    overlap_end: `${todayStr}T15:30:00`,
    severity: 'full'
  }]
})

function goHome() {
  router.push('/')
}

// 自动滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (flowScrollContainer.value) {
      flowScrollContainer.value.scrollTop = flowScrollContainer.value.scrollHeight
    }
  })
}

// 键盘文本录入及提交
const keyboardInputText = ref('')

function handleKeyboardSubmit() {
  if (!keyboardInputText.value.trim()) return
  const text = keyboardInputText.value.trim()
  keyboardInputText.value = ''
  
  stopTTS()
  sessionStore.setVoiceState('processing')
  sessionStore.setFinalTranscript(text)
  
  setTimeout(() => {
    processUserInput(text)
  }, 800)
}

// 模拟音量变化
let volumeInterval: ReturnType<typeof setInterval> | null = null
function simulateVolume() {
  volumeInterval = setInterval(() => {
    mockVolume.value = 0.1 + Math.random() * 0.7
  }, 100)
}
function stopVolumeSimulation() {
  if (volumeInterval) {
    clearInterval(volumeInterval)
    volumeInterval = null
  }
  mockVolume.value = 0
}

// 实时转写流式上屏仿真 (Streaming Transcript Simulation)
let streamingInterval: ReturnType<typeof setInterval> | null = null

function startStreamingSimulation() {
  sessionStore.setFinalTranscript('')
  sessionStore.updatePartialTranscript('')
  
  const mockSpeechTemplates = [
    '帮我创建明天下午三点和PM开会',
    '添加买牛奶的待办日程',
    '联网检索2026年杭州的动漫展',
    '搜一下上海最近的实践活动',
    '查询大家明天的忙闲日程'
  ]
  const targetSentence = mockSpeechTemplates[Math.floor(Math.random() * mockSpeechTemplates.length)]
  const chars = targetSentence.split('')
  let currentIdx = 0
  
  if (streamingInterval) {
    clearInterval(streamingInterval)
  }
  
  streamingInterval = setInterval(() => {
    if (currentIdx < chars.length) {
      const partial = chars.slice(0, currentIdx + 1).join('')
      sessionStore.updatePartialTranscript(partial)
      currentIdx++
    } else {
      if (streamingInterval) {
        clearInterval(streamingInterval)
        streamingInterval = null
      }
    }
  }, 180)
}

function stopStreamingSimulation() {
  if (streamingInterval) {
    clearInterval(streamingInterval)
    streamingInterval = null
  }
}

// 语音识别相关
let recognition: any = null
let isRecording = false

// 初始化语音识别
function initSpeechRecognition() {
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  if (!SpeechRecognition) {
    console.warn('浏览器不支持语音识别')
    return null
  }
  
  const rec = new SpeechRecognition()
  rec.continuous = false
  rec.interimResults = true
  rec.lang = 'zh-CN'
  
  rec.onresult = (event: any) => {
    let interimTranscript = ''
    let finalTranscript = ''
    
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript
      if (event.results[i].isFinal) {
        finalTranscript += transcript
      } else {
        interimTranscript += transcript
      }
    }
    
    if (interimTranscript) {
      sessionStore.updatePartialTranscript(interimTranscript)
    }
    
    if (finalTranscript) {
      sessionStore.setFinalTranscript(finalTranscript)
      sessionStore.updatePartialTranscript('')
    }
  }
  
  rec.onend = () => {
    isRecording = false
    if (sessionStore.voiceState === 'recording') {
      stopVoiceInput()
    }
  }
  
  rec.onerror = (event: any) => {
    console.error('语音识别错误:', event.error)
    isRecording = false
    sessionStore.setVoiceState('idle')
  }
  
  return rec
}

// 语音交互状态流控制
function startVoiceInput() {
  stopTTS()
  vibrate('recording')
  sessionStore.setVoiceState('recording')
  sessionStore.setConnectionState('connected')
  simulateVolume()
  
  // 尝试使用浏览器语音识别
  if (!recognition) {
    recognition = initSpeechRecognition()
  }
  
  if (recognition && !isRecording) {
    try {
      recognition.start()
      isRecording = true
    } catch (e) {
      console.error('启动语音识别失败:', e)
      // 回退到模拟模式
      startStreamingSimulation()
    }
  } else {
    // 回退到模拟模式
    startStreamingSimulation()
  }
}

function stopVoiceInput() {
  stopVolumeSimulation()
  stopStreamingSimulation()
  
  if (recognition && isRecording) {
    try {
      recognition.stop()
    } catch (e) {
      // 忽略
    }
    isRecording = false
  }
  
  vibrate('processing')
  sessionStore.setVoiceState('processing')
  
  const finalSpeechText = sessionStore.partialTranscript || sessionStore.finalTranscript || '明天下午三点和PM开会'
  sessionStore.setFinalTranscript(finalSpeechText)
  sessionStore.updatePartialTranscript('')
  
  setTimeout(() => {
    processUserInput(finalSpeechText)
  }, 500)
}

function handleTapButton() {
  if (sessionStore.isTTSPlaying) {
    stopTTS()
    sessionStore.setVoiceState('idle')
  } else if (sessionStore.voiceState === 'idle') {
    startVoiceInput()
    setTimeout(() => {
      if (sessionStore.voiceState === 'recording') {
        stopVoiceInput()
      }
    }, 2800)
  }
}

function handleQuickInput(text: string) {
  stopTTS()
  sessionStore.setVoiceState('processing')
  sessionStore.setFinalTranscript(text)
  setTimeout(() => {
    processUserInput(text)
  }, 1000)
}

// 对话与场景核心逻辑
import { createEvent, checkConflicts, healthCheck } from '@/services/api'

const API_BASE_URL = 'http://localhost:8000'
const DEFAULT_USER_ID = 'user-001'

async function processUserInput(text: string) {
  // 1. 添加用户消息
  sessionStore.addMessage({
    role: 'user',
    content: text,
    type: 'voice'
  })
  scrollToBottom()

  // 检查后端是否可用
  const backendAvailable = await healthCheck()
  
  if (!backendAvailable) {
    sessionStore.addMessage({
      role: 'system',
      content: '后端服务未启动，请先启动后端服务 (python -m uvicorn app.main:app --port 8000)',
      type: 'error'
    })
    sessionStore.setVoiceState('idle')
    return
  }

  // 2. 规则路由与意图匹配模拟
  if (text.includes('搜') || text.includes('查') || text.includes('实践') || text.includes('活动') || text.includes('展') || text.includes('检索')) {
    // M9 联网检索意图嗅探与路由
    sessionStore.setVoiceState('searching')
    currentSearchQuery.value = text
    currentSearchStatus.value = 'searching'
    currentSearchEvents.value = []
    speakText('正在连接互联网搜索引擎为您检索实践活动...')

    // 模拟搜索流程延时
    setTimeout(() => {
      currentSearchStatus.value = 'parsing'
      speakText('已抓取到相关网页，大模型正在提炼日程实体...')
      
      setTimeout(() => {
        currentSearchStatus.value = 'results'
        
        // 构造针对城市的精品 mock 实践活动数据
        if (text.includes('杭州')) {
          currentSearchEvents.value = [
            {
              title: '2026年杭州国际动漫节 (CICAF)',
              start_time: '2026-06-01T09:00:00+08:00',
              end_time: '2026-06-05T18:00:00+08:00',
              location: '杭州白马湖动漫广场',
              description: '第二十二届中国国际动漫节，汇聚全国顶尖动漫游戏展商与数万名动漫同好，设有国漫高峰论坛、声优大赛与Cosplay盛典。',
              source_url: 'https://www.cicaf.com'
            },
            {
              title: '2026年杭州西湖荷花艺术节',
              start_time: '2026-07-10T08:00:00+08:00',
              end_time: '2026-07-20T17:00:00+08:00',
              location: '杭州西湖曲院风荷',
              description: '年度西湖江南文化艺术盛宴，包含千亩荷花水上观赏会、江南丝竹音乐会、古风非遗文创市集等丰富实践活动。',
              source_url: 'https://www.hzwestlake.gov.cn'
            }
          ]
        } else if (text.includes('北京')) {
          currentSearchEvents.value = [
            {
              title: '2026年北京国际汽车展览会 (Auto China)',
              start_time: '2026-06-15T09:00:00+08:00',
              end_time: '2026-06-20T17:30:00+08:00',
              location: '北京中国国际展览中心 (顺义馆)',
              description: '全球顶级车展，聚焦新能源智慧出行、自动驾驶技术与新一代概念车展示，设有科技先锋实践互动体验区。',
              source_url: 'https://www.autochina.com.cn'
            },
            {
              title: '2026年北京古风非遗手工文化沙龙',
              start_time: '2026-06-06T14:00:00+08:00',
              end_time: '2026-06-06T18:00:00+08:00',
              location: '北京南锣鼓巷文化艺术馆',
              description: '沉浸式非物质文化遗产手工实践，特邀非遗大师现场指导京剧脸谱绘制、剪纸及景泰蓝掐丝工艺制作。',
              source_url: 'https://www.bjheritage.org.cn'
            }
          ]
        } else if (text.includes('上海')) {
          currentSearchEvents.value = [
            {
              title: '2026年上海草莓音乐节',
              start_time: '2026-06-12T13:00:00+08:00',
              end_time: '2026-06-14T21:30:00+08:00',
              location: '上海世博公园',
              description: '大型户外音乐盛宴，设有草莓舞台、爱舞台、新血计划舞台，结合时尚创意市集、美食街区及环保实践营地。',
              source_url: 'https://www.modernsky.com'
            },
            {
              title: '2026年上海世博会智慧科技成果展',
              start_time: '2026-06-25T09:30:00+08:00',
              end_time: '2026-06-28T17:00:00+08:00',
              location: '上海世博展览馆 1号馆',
              description: '展示前沿人工智能、脑机接口、人形机器人与低空航行器，设有青少年科技创新实践互动专区。',
              source_url: 'https://www.shexpocenter.com'
            }
          ]
        } else {
          currentSearchEvents.value = [
            {
              title: '2026年人工智能开发者大会 (AI DevCon)',
              start_time: '2026-06-08T09:00:00+08:00',
              end_time: '2026-06-10T18:00:00+08:00',
              location: '国家会议中心',
              description: '汇聚前沿AI科学家与广大开发者的顶级技术大会，涵盖大模型微调、智能体编排及多模态交互实践工坊。',
              source_url: 'https://www.aidevcon.org'
            },
            {
              title: '2026年社区青年志愿者环保实践活动',
              start_time: '2026-06-05T08:30:00+08:00',
              end_time: '2026-06-05T12:00:00+08:00',
              location: '城市生态森林公园西门',
              description: '关爱生态，绿色出行。青年志愿环保实践活动，进行垃圾分类宣讲、湿地环境保护及爱心植树维护。',
              source_url: 'https://www.greenvolunteers.cn'
            }
          ]
        }
        
        const voiceText = `联网检索成功！我为您查到了 ${currentSearchEvents.value.length} 个相关的实践活动。您可以点击卡片一键添加至日历中。`
        sessionStore.addMessage({
          role: 'system',
          content: voiceText,
          type: 'search',
          metadata: {
            web_search_response: {
              session_id: sessionStore.sessionId,
              status: 'success',
              search_raw_query: text,
              extracted_events: currentSearchEvents.value,
              reply_text: voiceText
            }
          }
        })
        speakText(voiceText)
        scrollToBottom()
      }, 1200)
    }, 1500)

  } else if (text.includes('两点') || text.includes('14:00')) {
    // 触发时间冲突
    sessionStore.setVoiceState('conflict')
    sessionStore.addMessage({
      role: 'system',
      content: '检测到时间冲突！明天下午 14:00 有已存在日程“语音日历前端架构评审”。推荐改期至下午 3:30，或在明天同一时间强制创建。',
      type: 'conflict'
    })
    vibrate('conflict')
    speakText('对不起，两点钟您有另一个日程冲突。推荐改期到下午三点半，或者强制创建。')
  } else if (text.includes('待办') || text.includes('任务')) {
    // 创建待办
    const taskTitle = text.replace(/帮我|添加|待办|任务/g, '').trim() || '新待办任务'
    calendarStore.addTask({
      id: `task-${Date.now()}`,
      title: taskTitle,
      priority: 'medium',
      is_completed: false,
      is_deleted: false,
      version_tag: 'v1',
      created_at: new Date().toISOString()
    })
    sessionStore.setVoiceState('success')
    sessionStore.addMessage({
      role: 'system',
      content: `好的，已成功添加待办任务：${taskTitle}`,
      type: 'result'
    })
    vibrate('success')
    speakText(`已为您添加待办：${taskTitle}`)
    setTimeout(() => { sessionStore.setVoiceState('idle') }, 2000)
  } else if (text.includes('三点') || text.includes('下午3点') || text.includes('15:00') || text.includes('开会') || text.includes('会议')) {
    // 解析时间
    const now = new Date()
    let targetDate = new Date(now)
    targetDate.setDate(targetDate.getDate() + 1) // 默认明天
    
    if (text.includes('今天')) {
      targetDate = new Date(now)
    } else if (text.includes('后天')) {
      targetDate.setDate(targetDate.getDate() + 2)
    }
    
    let hour = 15 // 默认下午3点
    if (text.includes('两点') || text.includes('14:00') || text.includes('14点')) hour = 14
    else if (text.includes('三点') || text.includes('15:00') || text.includes('15点')) hour = 15
    else if (text.includes('四点') || text.includes('16:00') || text.includes('16点')) hour = 16
    else if (text.includes('上午') || text.includes('九点') || text.includes('9:00')) hour = 9
    
    const startTime = new Date(targetDate)
    startTime.setHours(hour, 0, 0, 0)
    const endTime = new Date(startTime)
    endTime.setHours(hour + 1, 0, 0, 0)
    
    const startTimeStr = startTime.toISOString().replace('Z', '+08:00')
    const endTimeStr = endTime.toISOString().replace('Z', '+08:00')
    
    // 提取标题
    let title = '新会议'
    if (text.includes('开会') || text.includes('会议')) {
      title = text.replace(/帮我|创建|添加|明天|今天|后天|下午|上午|的|和|开会|会议/g, '').trim() || '会议'
    }
    
    // 检查冲突
    try {
      const conflictResult = await checkConflicts(DEFAULT_USER_ID, startTimeStr, endTimeStr)
      
      if (conflictResult.has_conflict) {
        // 有冲突
        sessionStore.setVoiceState('conflict')
        mockConflicts.value = conflictResult.conflicts
        sessionStore.addMessage({
          role: 'system',
          content: `检测到时间冲突！您在 ${startTime.getHours()}:00 已有日程。`,
          type: 'conflict'
        })
        vibrate('conflict')
        speakText('对不起，这个时间段您有另一个日程冲突。推荐改期或强制创建。')
        return
      }
      
      // 无冲突，创建事件
      const newEvent = await createEvent({
        user_id: DEFAULT_USER_ID,
        title: title,
        start_time: startTimeStr,
        end_time: endTimeStr,
        timezone: 'Asia/Shanghai'
      })
      
      calendarStore.addEvent({
        id: newEvent.id || `ev-${Date.now()}`,
        title: title,
        start_time: startTimeStr,
        end_time: endTimeStr,
        calendar_id: 'work',
        calendar_name: '工作',
        color: '#8B5CF6',
        is_deleted: false,
        version_tag: 'v1',
        created_at: new Date().toISOString()
      })
      
      sessionStore.setVoiceState('success')
      sessionStore.addMessage({
        role: 'system',
        content: `好的，已为您成功创建日程：${title}，时间：${startTime.getMonth()+1}月${startTime.getDate()}日 ${hour}:00`,
        type: 'result'
      })
      vibrate('success')
      speakText(`好的，已为您成功创建${title}！`)
      setTimeout(() => { sessionStore.setVoiceState('idle') }, 2000)
    } catch (error) {
      console.error('创建事件失败:', error)
      sessionStore.addMessage({
        role: 'system',
        content: '创建事件失败，请重试',
        type: 'error'
      })
      sessionStore.setVoiceState('idle')
    }
  } else {
    // 意图不明，触发追问 Clarification
    sessionStore.setVoiceState('clarifying')
    sessionStore.addMessage({
      role: 'system',
      content: '收到添加日程请求。但我没有抓取到明确的日程主题。请问您的日程标题是什么？',
      type: 'clarification'
    })
    speakText('收到日程请求。请问这个日程的主题是什么？')
  }
  scrollToBottom()
}

// 冲突解决
function handleResolveConflict(_suggestion: string) {
  const todayStr = new Date().toISOString().split('T')[0]
  calendarStore.addEvent({
    id: `ev-${Date.now()}`,
    title: '调整后的PM对齐会议',
    start_time: `${todayStr}T15:30:00`,
    end_time: `${todayStr}T16:30:00`,
    calendar_id: 'work',
    calendar_name: '工作',
    color: '#8B5CF6',
    is_deleted: false,
    version_tag: 'v1',
    created_at: new Date().toISOString()
  })
  
  sessionStore.setVoiceState('success')
  sessionStore.addMessage({
    role: 'system',
    content: `冲突已解决！已创建日程：调整后的PM对齐会议，时间调整为下午 15:30 - 16:30。`,
    type: 'result'
  })
  vibrate('success')
  speakText('冲突已解决，已为您把会议调整到下午三点半！')
  setTimeout(() => { sessionStore.setVoiceState('idle') }, 2000)
  scrollToBottom()
}

function handleForceCreate() {
  const todayStr = new Date().toISOString().split('T')[0]
  calendarStore.addEvent({
    id: `ev-${Date.now()}`,
    title: 'PM对齐会议 (强制覆盖)',
    start_time: `${todayStr}T14:00:00`,
    end_time: `${todayStr}T15:00:00`,
    calendar_id: 'work',
    calendar_name: '工作',
    color: '#D32F2F',
    is_deleted: false,
    version_tag: 'v1',
    created_at: new Date().toISOString()
  })
  
  sessionStore.setVoiceState('success')
  sessionStore.addMessage({
    role: 'system',
    content: `已为您强行创建明天下午 14:00 的日程，请注意与既有日程时间重叠！`,
    type: 'result'
  })
  vibrate('success')
  speakText('已强行创建日程，请注意日程存在时间上的冲突。')
  setTimeout(() => { sessionStore.setVoiceState('idle') }, 2000)
  scrollToBottom()
}

function handleCancelConflict() {
  sessionStore.setVoiceState('idle')
  sessionStore.addMessage({
    role: 'system',
    content: `已取消创建日程。`,
    type: 'text'
  })
  speakText('已取消。')
}

// 补充信息回答
function handleSkipClarification() {
  const todayStr = new Date().toISOString().split('T')[0]
  calendarStore.addEvent({
    id: `ev-${Date.now()}`,
    title: '未命名日程',
    start_time: `${todayStr}T16:00:00`,
    end_time: `${todayStr}T17:00:00`,
    calendar_id: 'personal',
    calendar_name: '个人',
    color: '#10B981',
    is_deleted: false,
    version_tag: 'v1',
    created_at: new Date().toISOString()
  })
  sessionStore.setVoiceState('success')
  speakText('已为您创建未命名日程')
  setTimeout(() => { sessionStore.setVoiceState('idle') }, 2000)
}



function handleSearchAddEvent(event: WebSearchEvent) {
  vibrate('success')
  calendarStore.addEvent({
    id: `ev-search-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    title: event.title,
    start_time: event.start_time,
    end_time: event.end_time,
    location: event.location,
    calendar_id: 'work',
    calendar_name: '工作',
    color: '#8B5CF6',
    is_deleted: false,
    version_tag: 'v1',
    voice_raw_text: currentSearchQuery.value,
    created_at: new Date().toISOString()
  })
  
  const textFeedback = `已成功将“${event.title}”添加入您的日历日程！`
  sessionStore.addMessage({
    role: 'system',
    content: textFeedback,
    type: 'result'
  })
  speakText(textFeedback)
  scrollToBottom()
}

function handleSearchRetry() {
  processUserInput(currentSearchQuery.value)
}

function speakLastMessage() {
  const last = latestSystemMessage.value
  if (last) {
    speakText(last.content)
    sessionStore.setVoiceState('tts_playing')
  }
}

// 最新的一条系统播报
const latestSystemMessage = computed(() => {
  return [...sessionStore.messages]
    .reverse()
    .find(m => m.role === 'system')
})

onMounted(() => {
  sessionStore.startSession()
  sessionStore.setConnectionState('connected')
  sessionStore.addMessage({
    role: 'system',
    content: '你好，我是你的语音日程管家。按住屏幕中下方麦克风并说话即可添加、修改或查询日程。例如你可以说：“帮我创建明天下午三点的项目评审会”',
    type: 'text'
  })
  scrollToBottom()
})
</script>

<style scoped>
.conversation-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 80px); /* 减去 Tab 导航高度 */
  height: calc(100dvh - 80px);
  gap: var(--vc-space-md);
  position: relative;
}

/* 顶部栏 */
.conversation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--vc-space-sm) 0;
  border-bottom: 1px solid var(--vc-divider);
}

.back-btn {
  width: 40px;
  height: 40px;
  border-radius: var(--vc-radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--vc-text-secondary);
  transition: all var(--vc-transition-fast);
}

.back-btn:hover {
  background: var(--vc-bg-surface);
  color: var(--vc-text-primary);
}

.header-center {
  display: flex;
  align-items: center;
}

/* 气泡流区域 */
.conversation-flow-wrap {
  flex: 1;
  overflow-y: auto;
  padding-right: var(--vc-space-xs);
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-md);
}

.inline-card-container {
  margin: var(--vc-space-sm) 0;
}



/* 底部操作区 */
.conversation-footer {
  border-top: 1px solid var(--vc-border);
  padding: var(--vc-space-md) var(--vc-space-sm) var(--vc-space-sm);
  border-radius: var(--vc-radius-lg);
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-md);
}

/* 形态切换容器 (Morph Input Block) */
.footer-input-morph {
  width: 100%;
  min-height: 52px;
  position: relative;
}

.morph-input-bar {
  display: flex;
  align-items: center;
  gap: var(--vc-space-sm);
  background: var(--vc-bg-surface);
  border: 1px solid var(--vc-border);
  border-radius: var(--vc-radius-md);
  padding: var(--vc-space-xs) var(--vc-space-sm);
  transition: all var(--vc-transition-base);
  box-shadow: var(--vc-shadow-sm);
}

.morph-input-bar:focus-within {
  border-color: var(--vc-accent);
  box-shadow: 0 0 0 3px hsla(var(--vc-accent-h), var(--vc-accent-s), var(--vc-accent-l), 0.12);
  background: var(--vc-bg-elevated);
}

.morph-input-icon {
  font-size: 16px;
  opacity: 0.6;
}

.keyboard-text-input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 8px var(--vc-space-xs);
  color: var(--vc-text-primary);
  font-size: var(--vc-text-sm);
  outline: none;
}

.keyboard-text-input::placeholder {
  color: var(--vc-text-tertiary);
}

.morph-input-submit {
  width: 28px;
  height: 28px;
  border-radius: var(--vc-radius-sm);
  background: var(--vc-bg-elevated);
  border: 1px solid var(--vc-border);
  color: var(--vc-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  cursor: pointer;
  transition: all var(--vc-transition-fast);
}

.morph-input-submit:hover:not(:disabled) {
  border-color: var(--vc-accent);
  background: hsla(var(--vc-accent-h), var(--vc-accent-s), var(--vc-accent-l), 0.08);
  color: var(--vc-text-primary);
}

.morph-input-submit:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.morph-transcript-bar {
  width: 100%;
}

/* 动效过渡 */
.morph-fade-enter-active,
.morph-fade-leave-active {
  transition: all var(--vc-transition-fast);
}

.morph-fade-enter-from,
.morph-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

.footer-visualizer {
  display: flex;
  justify-content: center;
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  transition: all var(--vc-transition-base);
}

.footer-visualizer--visible {
  max-height: 64px;
  opacity: 1;
  margin: var(--vc-space-sm) 0;
}

.footer-suggestions {
  display: flex;
  gap: var(--vc-space-sm);
  overflow-x: auto;
  padding-bottom: var(--vc-space-xs);
  scrollbar-width: none;
}

.footer-suggestions::-webkit-scrollbar {
  display: none;
}

.suggestion-pill {
  flex-shrink: 0;
  background: var(--vc-bg-surface);
  border: 1px solid var(--vc-border);
  color: var(--vc-text-secondary);
  font-size: var(--vc-text-xs);
  padding: 6px 14px;
  border-radius: var(--vc-radius-full);
  transition: all var(--vc-transition-fast);
}

.suggestion-pill:hover {
  border-color: var(--vc-primary-light);
  color: var(--vc-text-primary);
  background: hsla(var(--vc-primary-h), var(--vc-primary-s), var(--vc-primary-l), 0.08);
}

.footer-control-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--vc-space-sm);
}

.main-mic-button-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--vc-space-xs);
}

.main-mic-button {
  display: flex;
  justify-content: center;
  align-items: center;
}

.morph-mic-tip {
  font-size: 10px;
  color: var(--vc-text-tertiary);
  transition: opacity var(--vc-transition-base);
}
</style>
