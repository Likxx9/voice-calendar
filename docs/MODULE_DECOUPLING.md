# 🔌 核心模块解耦说明

## 概述

本文档详细说明智能语音日历系统中各核心模块的职责划分、接口设计和解耦原则。

---

## 模块总览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        M1: 语音感知模块                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ AudioRecorder│ │ VADController│ │ TTSPlayer   │ │ HapticFeedback│
│  │  音频采集    │  │  VAD断句    │  │  TTS播放    │  │  触觉反馈    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        M2: 网关通信模块                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │
│  │ ConnectionManager│ │ MessageRouter│ │ AuthMiddleware│                │
│  │  连接管理    │  │  消息路由    │  │  鉴权中间件  │                   │
│  └─────────────┘  └─────────────┘  └─────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        M3: 语义理解模块                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ STTService  │  │ LLMService  │  │ IntentParser│  │ EntityExtractor│
│  │  语音识别    │  │  语义清洗    │  │  意图识别    │  │  实体提取    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        M4: 状态机模块                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ SessionManager│ │ ConflictResolver│ │ ClarificationEngine│ │ StateGraph│
│  │  会话管理    │  │  冲突解决    │  │  追问引擎    │  │  状态图    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        M5: 日历管理模块                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ EventCRUD   │  │ ConflictDetector│ │ CalendarView│  │ SyncManager │
│  │  事件增删改查│  │  冲突检测    │  │  视图渲染    │  │  同步管理   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        M6: 离线同步模块                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │
│  │ OfflineQueue│  │ SyncEngine  │  │ ConflictHandler│                 │
│  │  离线队列    │  │  同步引擎    │  │  冲突处理    │                   │
│  └─────────────┘  └─────────────┘  └─────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## M1: 语音感知模块

### 职责
- 音频采集（Web Audio API）
- 语音活动检测（VAD）
- 文本转语音（TTS）
- 触觉反馈（Haptic Feedback）

### 接口定义

```typescript
// 音频采集器
interface AudioRecorder {
    startRecording(): void;
    stopRecording(): void;
    onAudioChunk: (chunk: AudioChunk) => void;
    isRecording: boolean;
    currentVolume: number;
}

// VAD控制器
interface VADController {
    feedVolume(volume: number): void;
    adjustTimeout(timeout: number): void;
    isSpeaking: boolean;
    silenceProgress: number; // 0-1
    onSilenceDetected: () => void;
}

// TTS播放器
interface TTSPlayer {
    speakText(text: string, speed?: number): void;
    stop(): void;
    isPlaying: boolean;
    speed: number;
    progress: number;
}

// 触觉反馈
interface HapticFeedback {
    tap(): void;
    recording(): void;
    processing(): void;
    success(): void;
    conflict(): void;
    error(): void;
}
```

### 解耦点
1. **与M2解耦**：M1只负责音频采集，不关心传输
2. **与M3解耦**：M1不负责语音识别
3. **与UI解耦**：通过事件回调通知状态变化

---

## M2: 网关通信模块

### 职责
- WebSocket连接管理
- 消息序列化/反序列化
- 心跳与重连
- 鉴权校验

### 接口定义

```typescript
// WebSocket管理器
interface WebSocketManager {
    connect(url: string): Promise<void>;
    disconnect(): void;
    sendFrame(frame: WSFrame): void;
    sendAudioChunk(chunk: AudioChunk): void;
    sendInterrupt(): void;
    
    onMessage: (message: WSFrame) => void;
    onConnect: () => void;
    onDisconnect: () => void;
    onError: (error: Error) => void;
    
    state: ConnectionState;
}

// WebSocket帧
interface WSFrame {
    type: WSFrameType;
    sessionId: string;
    data: any;
    timestamp: string;
}
```

### 解耦点
1. **与M1解耦**：M2只负责传输，不关心音频格式
2. **与M3解耦**：M2不负责语义理解
3. **协议无关**：支持WebSocket、HTTP、gRPC等多种协议

---

## M3: 语义理解模块

### 职责
- 语音转文本（STT）
- 语义清洗与纠错
- 意图识别
- 实体提取

### 接口定义

```typescript
// STT服务
interface STTService {
    transcribe(audioData: ArrayBuffer): Promise<TranscriptionResult>;
    transcribeStream(audioStream: AsyncIterable<ArrayBuffer>): AsyncIterable<TranscriptionResult>;
}

// LLM服务
interface LLMService {
    processVoiceInput(
        text: string,
        context: Context,
        referenceTime: Date
    ): Promise<SemanticOutput>;
    
    semanticCorrection(text: string, context: Context): Promise<string>;
    extractIntent(text: string): Promise<IntentType>;
    extractEntities(text: string, referenceTime: Date): Promise<Entities>;
}

// 语义输出
interface SemanticOutput {
    originalText: string;
    cleanedText: string;
    intent: IntentType;
    entities: Entities;
    missingFields: string[];
    confidence: number;
}
```

### 解耦点
1. **与M2解耦**：M3只处理文本，不关心传输
2. **与M4解耦**：M3只输出语义，不负责决策
3. **模型无关**：支持多种LLM和STT模型

---

## M4: 状态机模块

### 职责
- 多轮对话状态管理
- 信息完整性检查
- 追问引导
- 冲突协商

### 接口定义

```typescript
// 会话管理器
interface SessionManager {
    createSession(userId: string): Promise<Session>;
    getSession(sessionId: string): Promise<Session>;
    addMessage(sessionId: string, message: Message): Promise<void>;
    updateDraft(sessionId: string, draft: EventDraft): Promise<void>;
    clearDraft(sessionId: string): Promise<void>;
}

// 冲突解决器
interface ConflictResolver {
    checkConflicts(
        userId: string,
        startTime: Date,
        endTime: Date
    ): Promise<ConflictResult>;
    
    generateAlternatives(
        conflicts: CalendarEvent[],
        requestedTime: Date
    ): Promise<Alternative[]>;
}

// 追问引擎
interface ClarificationEngine {
    checkCompleteness(intent: IntentType, entities: Entities): string[];
    generateClarification(missingFields: string[]): string;
}

// 状态图
interface StateGraph {
    addNode(name: string, handler: StateHandler): void;
    addEdge(from: string, to: string, condition?: Condition): void;
    compile(): CompiledGraph;
}
```

### 解耦点
1. **与M3解耦**：M4只接收语义输出，不负责理解
2. **与M5解耦**：M4只负责决策，不负责执行
3. **状态无关**：支持多种存储后端（Redis、数据库）

---

## M5: 日历管理模块

### 职责
- 事件CRUD操作
- 时间冲突检测
- 日历视图渲染
- 数据同步

### 接口定义

```typescript
// 事件CRUD
interface EventCRUD {
    createEvent(userId: string, event: EventData): Promise<CalendarEvent>;
    updateEvent(eventId: string, event: EventData): Promise<CalendarEvent>;
    deleteEvent(eventId: string): Promise<void>;
    getEvent(eventId: string): Promise<CalendarEvent>;
    getEvents(userId: string, startDate: Date, endDate: Date): Promise<CalendarEvent[]>;
}

// 冲突检测
interface ConflictDetector {
    checkConflicts(
        userId: string,
        startTime: Date,
        endTime: Date,
        excludeEventId?: string
    ): Promise<CalendarEvent[]>;
}

// 日历视图
interface CalendarView {
    renderMonthView(year: number, month: number): MonthView;
    renderWeekView(date: Date): WeekView;
    renderDayView(date: Date): DayView;
}
```

### 解耦点
1. **与M4解耦**：M5只负责执行，不负责决策
2. **与UI解耦**：通过数据绑定更新视图
3. **存储无关**：支持多种数据库

---

## M6: 离线同步模块

### 职责
- 离线操作队列管理
- 增量同步
- 冲突解决
- 数据持久化

### 接口定义

```typescript
// 离线队列
interface OfflineQueue {
    enqueue(operation: SyncOperation): Promise<void>;
    dequeue(): Promise<SyncOperation>;
    getAll(): Promise<SyncOperation[]>;
    markSynced(operationId: string): Promise<void>;
    clearSynced(): Promise<void>;
}

// 同步引擎
interface SyncEngine {
    syncPending(): Promise<SyncResult>;
    resolveConflict(local: any, remote: any): any;
    getLastSyncTime(): Promise<Date>;
}

// 同步操作
interface SyncOperation {
    id: string;
    type: 'create' | 'update' | 'delete';
    entity: 'event' | 'task';
    data: any;
    timestamp: number;
    syncStatus: 'pending' | 'syncing' | 'synced';
}
```

### 解耦点
1. **与M5解耦**：M6只负责同步，不负责业务逻辑
2. **网络无关**：支持多种同步策略
3. **存储无关**：支持IndexedDB、localStorage等

---

## 解耦原则总结

### 1. 单一职责原则（SRP）
每个模块只负责一个核心功能，不承担多余职责。

### 2. 接口隔离原则（ISP）
模块间通过明确定义的接口通信，不暴露内部实现。

### 3. 依赖倒置原则（DIP）
高层模块不依赖低层模块，都依赖抽象接口。

### 4. 开闭原则（OCP）
对扩展开放，对修改关闭。通过插件机制支持新功能。

### 5. 最小知识原则（LoD）
模块间保持最小的了解，只通过接口通信。

---

## 依赖关系图

```
M1 (语音感知)
    │
    ├── 依赖: Web Audio API, Vibration API
    │
    └── 被依赖: M2 (通过事件回调)

M2 (网关通信)
    │
    ├── 依赖: WebSocket
    │
    ├── 被依赖: M1 (发送音频)
    └── 被依赖: M3 (接收文本)

M3 (语义理解)
    │
    ├── 依赖: STT模型, LLM模型
    │
    ├── 被依赖: M2 (接收文本)
    └── 被依赖: M4 (输出语义)

M4 (状态机)
    │
    ├── 依赖: Redis (会话存储)
    │
    ├── 被依赖: M3 (接收语义)
    └── 被依赖: M5 (输出决策)

M5 (日历管理)
    │
    ├── 依赖: PostgreSQL (数据存储)
    │
    ├── 被依赖: M4 (接收决策)
    └── 被依赖: M6 (数据同步)

M6 (离线同步)
    │
    ├── 依赖: IndexedDB (本地存储)
    │
    └── 被依赖: M5 (同步数据)
```

---

## 测试策略

### 单元测试
每个模块独立测试，mock依赖模块。

```python
# M3单元测试示例
def test_semantic_correction():
    mock_context = {"address_book": {"张总": ["赃总"]}}
    result = llm_service.semantic_correction("和赃总吃饭", mock_context)
    assert result == "和张总吃饭"
```

### 集成测试
测试模块间接口的正确性。

```python
# M3->M4集成测试示例
def test_voice_input_to_session():
    session = await session_service.create_session("user1")
    result = await llm_service.process_voice_input("提醒我明天开会", {}, datetime.now())
    await session_service.add_message(session["session_id"], "user", result["cleaned_text"])
    session = await session_service.get_session(session["session_id"])
    assert len(session["history"]) == 1
```

### 端到端测试
测试完整用户流程。

```python
# E2E测试示例
async def test_create_event_flow():
    async with websocket_connect("/ws/voice") as ws:
        # 发送语音
        await ws.send({"type": "audio_chunk", "data": audio_data, "is_final": True})
        
        # 接收转写
        transcription = await ws.receive()
        assert transcription["type"] == "transcription"
        
        # 接收语义输出
        semantic = await ws.receive()
        assert semantic["type"] == "semantic_output"
        
        # 接收事件创建
        event = await ws.receive()
        assert event["type"] == "event_created"
```
