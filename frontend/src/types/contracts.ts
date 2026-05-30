/* ============================================================
 * Voice Calendar — M1-M8 模块间契约数据类型定义
 * 与《模块拆分与研发路线规范》中定义的接口 1:1 对应
 * ============================================================ */

// ────────────────────────────────────────────────────────────
// M1 → M2: 音频流式传输契约
// ────────────────────────────────────────────────────────────
export interface AudioChunk {
  session_id: string
  sequence_number: number       // 序列号，从 0 开始自增
  payload: ArrayBuffer          // 原始音频切片 (16kHz PCM)
  is_final: boolean             // 是否最后一片
}

// ────────────────────────────────────────────────────────────
// M2 → M3: ASR 转写结果
// ────────────────────────────────────────────────────────────
export interface TranscriptionResult {
  session_id: string
  raw_text: string              // 未经清洗的原始文本
  confidence: number            // ASR 置信度 (0~1)
  started_at: string            // 绝对基准时间戳 (ISO 8601)
  device_timezone: string       // 设备时区
  is_partial: boolean           // 是否为局部结果（流式中间态）
}

// ────────────────────────────────────────────────────────────
// M3 → M4: 语义理解输出
// ────────────────────────────────────────────────────────────
export type IntentType =
  | 'create_event'
  | 'update_event'
  | 'delete_event'
  | 'create_task'
  | 'update_task'
  | 'delete_task'
  | 'convert_task_to_event'
  | 'clarification'
  | 'cancel'
  | 'unknown'

export interface EventDraft {
  title?: string
  start_time?: string           // ISO 8601
  end_time?: string
  location?: string
  attendees?: string[]          // 参与者邮箱列表
  recurrence_rule?: string      // RRULE
  calendar_id?: string          // 目标日历 ID
}

export interface TaskDraft {
  title?: string
  due_time?: string
  priority?: 'low' | 'medium' | 'high'
}

export interface TemporalConfidence {
  time_segment: string          // 如 "下周一"
  resolved_time: string         // "2026-06-01"
  score: number                 // 低于 0.8 触发追问
}

export interface SemanticOutput {
  intent: IntentType
  extracted_entities: {
    event_draft?: EventDraft
    task_draft?: TaskDraft
  }
  confidence: number
  temporal_confidence_breakdown?: TemporalConfidence[]
}

// ────────────────────────────────────────────────────────────
// M4 → M5: 冲突检测结果
// ────────────────────────────────────────────────────────────
export interface ConflictItem {
  existing_event_id: string
  existing_title: string
  overlap_start: string
  overlap_end: string
  severity: 'full' | 'partial'
}

export interface ConflictResult {
  has_conflict: boolean
  conflicts: ConflictItem[]
}

// ────────────────────────────────────────────────────────────
// Agent 编排层数据契约（技术文档 §5）
// ────────────────────────────────────────────────────────────
export type AgentIntentType = 'CREATE' | 'QUERY' | 'MODIFY' | 'DELETE' | 'SEARCH' | 'PLAN'

export interface AgentIntent {
  id: string
  type: AgentIntentType
  entities: Record<string, unknown>
  confidence: number                 // 0~1
  raw_span?: [number, number]        // 原文字符区间
}

export interface ExecutionStep {
  step_index: number
  tool_calls: string[]
  parallel: boolean
  depends_on: number[]               // 依赖的前置步骤索引
}

export interface AgentTaskGroup {
  id: string
  intents: string[]                  // intent id 列表
  related: boolean
  tools_needed: string[]
  execution_plan: ExecutionStep[]
}

export interface AgentOutput {
  session_id: string
  task_groups: AgentTaskGroup[]
  results: Record<string, unknown>
  fallback_response?: string         // LLM 规划失败时的文本兜底
  planning_latency_ms: number
}

export interface AgentMetadata {
  task_groups: number
  intents_count: number
  planning_latency_ms: number
}

// ────────────────────────────────────────────────────────────
// M9: 联网检索数据契约
// ────────────────────────────────────────────────────────────
export interface WebSearchRequest {
  session_id: string
  query: string                 // 搜索词
  max_results?: number
  search_depth?: 'shallow' | 'deep'
}

export interface WebSearchEvent {
  title: string
  start_time: string            // ISO 8601
  end_time: string
  location: string
  description: string
  source_url?: string           // 来源链接
}

export interface WebSearchResponse {
  session_id: string
  status: 'success' | 'ambiguous' | 'no_results' | 'error'
  search_raw_query: string
  extracted_events: WebSearchEvent[]
  reply_text: string
}

// ────────────────────────────────────────────────────────────
// WebSocket 消息帧类型
// ────────────────────────────────────────────────────────────
export type WSFrameType =
  | 'SESSION_INIT'            // M1→M2 会话初始化
  | 'AUDIO_CHUNK'             // M1→M2 音频分片
  | 'TEXT_INPUT'              // M1→M2 文本输入
  | 'TRANSCRIPT_PARTIAL'      // M2→M1 局部转写
  | 'TRANSCRIPT_FINAL'        // M2→M1 最终转写
  | 'SEMANTIC_RESULT'         // M3→M1 语义结果（含 Agent 多意图/搜索结果）
  | 'AGENT_PLAN'              // L3→M1 Agent 任务规划结果
  | 'CLARIFICATION_ASK'       // M4→M1 追问请求
  | 'CONFLICT_ALERT'          // M4→M1 冲突通知
  | 'ACTION_RESULT'           // M4→M1 执行结果（含 agent_metadata）
  | 'PLAYBACK_CONTROL'        // M4→M1 播放控制
  | 'STATE_UPDATE'            // M2→M1 状态更新
  | 'TTS_AUDIO_CHUNK'         // M2→M1 TTS 音频分片
  | 'TTS_DONE'                // M2→M1 TTS 播报完毕
  | 'VAD_TIMEOUT_ADJUST'      // M2→M1 VAD 断句调控
  | 'WS_INTENT_INTERRUPT'     // M1→M2 Barge-in 打断
  | 'SEARCH_ADD_EVENT'        // M1→M2 将搜索结果加入日历（后端处理）
  | 'SYNC_STATUS'             // M6→M1 同步状态
  | 'HEARTBEAT'               // 心跳

export interface WSFrame<T = unknown> {
  type: WSFrameType
  session_id: string
  timestamp: string
  payload: T
}

// ────────────────────────────────────────────────────────────
// 前端应用状态类型
// ────────────────────────────────────────────────────────────
export type VoiceState =
  | 'idle'                    // 空闲
  | 'recording'              // 录音中
  | 'processing'             // AI 处理中
  | 'tts_playing'            // TTS 播报中
  | 'clarifying'             // 多轮追问中
  | 'conflict'               // 冲突协商中
  | 'success'                // 操作成功
  | 'error'                  // 错误
  | 'searching'              // 联网检索中

export type ConnectionState =
  | 'connected'
  | 'connecting'
  | 'reconnecting'
  | 'disconnected'

export type LayoutMode = 'default' | 'eyes-free'
export type ThemeMode = 'dark' | 'light' | 'system'

// ────────────────────────────────────────────────────────────
// 日历事件与待办任务（前端展示用）
// ────────────────────────────────────────────────────────────
export interface CalendarEvent {
  id: string
  title: string
  start_time: string
  end_time: string
  location?: string
  attendees?: string[]
  calendar_id: string
  calendar_name: string
  color: string                 // 日历颜色编码
  recurrence_rule?: string
  is_deleted: boolean
  version_tag: string
  voice_raw_text?: string       // 原始听写
  created_at: string
}

export interface TodoTask {
  id: string
  title: string
  due_time?: string
  priority: 'low' | 'medium' | 'high'
  is_completed: boolean
  is_deleted: boolean
  version_tag: string
  created_at: string
}

// ────────────────────────────────────────────────────────────
// 对话消息
// ────────────────────────────────────────────────────────────
export interface ConversationMessage {
  id: string
  role: 'user' | 'system'
  content: string
  timestamp: string
  type: 'text' | 'voice' | 'clarification' | 'conflict' | 'result' | 'search'
  metadata?: {
    event_draft?: EventDraft
    task_draft?: TaskDraft
    conflict_result?: ConflictResult
    web_search_response?: WebSearchResponse
    suggestions?: string[]
  }
}

// ────────────────────────────────────────────────────────────
// 用户设置
// ────────────────────────────────────────────────────────────
export interface UserSettings {
  tts_speed: number             // 1.0 ~ 2.5
  haptic_intensity: 'off' | 'light' | 'medium' | 'strong'
  theme: ThemeMode
  layout_mode: LayoutMode
  default_calendar_id?: string
  vad_sensitivity: 'low' | 'medium' | 'high'
}
