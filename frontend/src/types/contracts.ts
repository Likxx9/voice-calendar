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
// M6: 离线同步有效载荷
// ────────────────────────────────────────────────────────────
export interface OfflineOperation {
  operation_id: string
  entity_type: 'event' | 'task'
  action: 'create' | 'update' | 'delete'
  entity_id: string
  payload: Record<string, unknown>
  original_version_tag: string
  executed_at: string
}

export interface SyncPayload {
  user_id: string
  client_timestamp: string
  offline_operations: OfflineOperation[]
}

export interface SyncResult {
  status: 'success' | 'partial_conflict'
  merged_count: number
  conflicts: Array<{
    operation_id: string
    server_value: Record<string, unknown>
    client_value: Record<string, unknown>
    field: string
  }>
}

// ────────────────────────────────────────────────────────────
// WebSocket 消息帧类型
// ────────────────────────────────────────────────────────────
export type WSFrameType =
  | 'AUDIO_CHUNK'             // M1→M2 音频分片
  | 'TRANSCRIPT_PARTIAL'      // M2→M1 局部转写
  | 'TRANSCRIPT_FINAL'        // M2→M1 最终转写
  | 'SEMANTIC_RESULT'         // M3→M1 语义结果
  | 'CLARIFICATION_ASK'       // M4→M1 追问请求
  | 'CONFLICT_ALERT'          // M4→M1 冲突通知
  | 'ACTION_RESULT'           // M4→M1 执行结果
  | 'TTS_AUDIO_CHUNK'         // M2→M1 TTS 音频分片
  | 'TTS_DONE'                // M2→M1 TTS 播报完毕
  | 'VAD_TIMEOUT_ADJUST'      // M2→M1 VAD 断句调控
  | 'WS_INTENT_INTERRUPT'     // M1→M2 Barge-in 打断
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

export type SyncState =
  | 'online'
  | 'offline'
  | 'syncing'
  | 'sync_error'

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
