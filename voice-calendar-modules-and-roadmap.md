# 语音日历工具（Voice Calendar）— 应用模块拆分与研发路线规范

本规范基于《产品技术设计文档》与《可行性及实用性分析》进行深度整合，将系统分解为符合六边形架构与领域驱动设计（DDD）的 **8 大核心应用模块**。本文件详细定义了每个模块的功能职责、各模块间的**显式耦合依赖与契约数据结构**，并规划了**四阶段研发路线图**与并行开发策略，为开发团队提供切实可靠的模块级落地指南。

---

## 目录

1. [业务逻辑分层架构](#1-业务逻辑分层架构)
2. [应用模块细拆与功能规范](#2-应用模块细拆与功能规范)
3. [模块间的显式耦合与协同契约](#3-模块间的显式耦合与协同契约)
4. [模块级开发顺序与研发路线图](#4-模块级开发顺序与研发路线图)
5. [并行研发策略与测试边界](#5-并行研发策略与测试边界)

---

## 1. 业务逻辑分层架构

系统严格遵循**六边形架构（Ports & Adapters）**，自上而下分为四层。核心业务领域（Domain）位于最内层，绝不依赖外部具体技术和第三方服务，通过定义的端口（Ports）向外延伸，由外部适配器（Adapters）提供具体的 STT、TTS、日历及待办服务集成。

```
                   ┌──────────────────────────────────────────────┐
                   │          1. 感知与展现层 (UI / Audio)         │
                   └──────────────────────┬───────────────────────┘
                                          │ WebSocket 双向连接
                   ┌──────────────────────▼───────────────────────┐
                   │        2. 应用网关与长连接层 (FastAPI Gateway) │
                   └──────────────────────┬───────────────────────┘
                                          │ 意图路由 / 状态流转
   ┌──────────────────────────────────────┼──────────────────────────────────────┐
   │ 3. 核心领域服务层 (Core Domain)       │                                      │
   │   ┌────────────────────┐    ┌────────▼───────────┐    ┌──────────────────┐  │
   │   │  时间解析与实体识别  │    │  意图路由与状态机    │    │  冲突检测及同步  │  │
   │   │  (Semantic Domain) │    │  (State Machine)   │    │  (Sync Engine)   │  │
   │   └────────────────────┘    └────────────────────┘    └──────────────────┘  │
   └──────────────────────────────────────┬──────────────────────────────────────┘
                                          │ 端口抽象契约 (Ports)
                   ┌──────────────────────▼───────────────────────┐
                   │    4. 适配器与外设层 (Adapters & Infrastructure)  │
                   │    (讯飞/火山/Paraformer/CalDAV/MS To Do/PG DB)   │
                   └──────────────────────────────────────────────┘
```

---

## 2. 应用模块细拆与功能规范

### M1：语音流式感知与反馈控制模块 (Voice Streaming & Sensory Control Module)
* **所属分层**：1. 感知与展现层（运行于手机客户端前端）
* **职责**：负责麦克风原始音频采集、端侧轻量自适应断句（VAD）、全屏无障碍手势捕获、马达触觉反馈及 TTS 音频播放与语速适配。
* **核心功能**：
  1. **双通道流式采集**：通过 Web Audio API 以 16kHz/16bit 单声道采集音频，分片封装为 `AudioChunk` 实时发送至 WebSocket 网关。
  2. **自适应端侧断句**：前端内置轻量级 VAD 控制器，支持动态微调 `silence_timeout` 判定阈值，防止用户思考停顿时发生断句过早（场景十）。
  3. **无障碍全屏手势**：屏蔽精细按钮，支持全屏大范围手势触发操作（全屏长按录音、双击打断 TTS 播报、双指轻扫切换日程，场景十、十一）。
  4. **触觉与声学双重回馈**：利用手机线性马达，为录音、解析中、成功创建和时间冲突四种状态设计专属振动频率（如轻振、模拟沙漏持续振、哒哒双振）与清脆音反馈，增强掌控感。
  5. **TTS 智能语速匹配**：学习用户对读屏器的语速偏好，自动调整离线/在线合成 TTS 语速（拟合 1.0x 至 2.5x）。

### M2：WebSocket 全双工消息网关 (WebSocket Full-Duplex Gateway Module)
* **所属分层**：2. 应用网关与长连接层（运行于 FastAPI 后端）
* **职责**：维护客户端的实时长连接，管理会话握手、数据重组分发、自适应参数推送以及 TTS 播报打断（Barge-in）控制。
* **核心功能**：
  1. **长连接生命周期管理**：提供 `ws://` 全双工端点，维护 `SessionManager` 连接池，执行心跳及网络异常断开清理。
  2. **流式分包重组**：按 `sequence_number` 重组客户端发送的 `AUDIO_CHUNK`，提供流式音频缓冲写入 ASR 引擎。
  3. **Barge-in 播放中止协调**：监听客户端发送的打断信号 `WS_INTENT_INTERRUPT`，在毫秒级内强行通过 `Task.cancel()` 终止当前的流式 TTS 生成和网络传输任务，并通知前端重置本地音频通道（场景十）。
  4. **自适应控制帧下发**：将领域层解析出的 partial 倾向（如“在”、“时间是”等未完结词）转化为 `VAD_TIMEOUT_ADJUST` 控制帧，实时推送至前端（场景十）。

### M3：智能语义理解与分类引擎 (Smart Semantic & Classification Engine)
* **所属分层**：3. 核心领域服务层（运行于后端 AI 中枢）
* **职责**：进行 ASR 后处理（降噪、去语气词）、基准时间锚定、 Event/Task 意图判别、以及基于用户画像的实体/中文模糊时间对齐。
* **核心功能**：
  1. **后处理降噪与同音纠偏**：通过大模型与模糊匹配模块对 STT 原始文本进行口语废话剔除（如“呃...那个...”），并对齐用户字典纠偏同音字错误（场景二）。
  2. **上下文绝对时钟注入**：在语义提取瞬间，强行将客户端捕获的录音开始时刻（`started_at`）作为 System Prompt 基准绝对时间，以消除网速慢造成的日期越界（场景一）。
  3. **双通道分类器**：自动区分高频商务和移动人群说出的命令是“时钟排他性的日历事件（Event）”还是“非占坑式的待办任务（Task）”（场景十一）。
  4. **中文时间自适应歧义解析**：针对“下周一”、“这周末”、“傍晚”等高度依赖语境的模糊表达，结合权重矩阵计算置信度评分，低于 0.8时输出追问属性，防止静默创建错误日程（场景十三）。

### M4：状态机与多轮协商引擎 (State Machine & Multi-turn Negotiation Engine)
* **所属分层**：3. 核心领域服务层（运行于后端 AI 中枢）
* **职责**：管理用户与系统交互的多轮会话，追踪参数补全进度，执行时间冲突交互式协商，维护事件指代缓存队列。
* **核心功能**：
  1. **多轮参数补全状态机**：利用 LangGraph 定义状态图拓扑。当必要字段（标题、时间）缺失时，计算出缺失列表，触发 `ask_clarification` 并继承上一轮对话上下文（场景三）。
  2. **冲突交互协商流**：当收到数据库层返回的时间冲突信号时，自动暂停写入，进入冲突协商话术节点，生成包含“改期建议”的智能追问（场景四）。
  3. **会话事件指代消解**：在 Redis 缓存中维护最近 5 个提及或操作的日程/任务 ID，精确消解“刚才那个”、“明天的会议”等口语化代词指向（场景五）。

### M5：关系型冲突数据库与持久层 (Conflict Database & Persistent Layer)
* **所属分层**：4. 适配器与外设层（运行于 PostgreSQL 数据库及 ORM）
* **职责**：提供日历事件、待办任务、用户画像字典的物理存储；利用带时区的时间范围技术实现超高效的时钟冲突校验。
* **核心功能**：
  1. **实体持久化**：存储主表 `users`、`calendars`、`events`、`tasks`，以及辅助字典表 `contacts`、`favorite_locations`。
  2. **`TSTZRANGE` 时间冲突检测**：在 `events` 表上为 `(calendar_id, tstzrange(start_time, end_time))` 建立 `GIST` 索引。在新事件写入前，调用重叠运算符 `&&` 瞬间检索出有重叠的时间块（场景四）。
  3. **软删除与审计追溯**：保留 `voice_raw_text`（原始听写）与 `voice_corrected`（纠偏后文本）供审计；在 `events` 和 `tasks` 表增加 `is_deleted` 实现墓碑软删除（场景十二）。

### M6：双向增量同步引擎 (Bi-directional Incremental Sync Engine)
* **所属分层**：3. 核心领域服务层与端侧缓存
* **职责**：当客户端网络恢复重新上线时，计算本地离线操作日志与云端最新实体版本的差异，实现零冲突的双向对齐与交互式决策。
* **核心功能**：
  1. **客户端离线操作日志**：在无网弱网下，将用户的日程/待办改动追加至端侧 SQLite/IndexDB 队列，记录操作时间与原始版本戳 `local_v1`（场景八）。
  2. **乐观锁版本令牌对齐**：使用 UUID+时间戳生成 `version_tag`。重上线请求 `/api/v1/sync`，云端引擎比对版本标记，执行 Fast-Forward 或自动无交集字段级合并（场景十二）。
  3. **合并冲突分流追问**：对无法自动合并的同字段冲突（如双方均修改了开始时间），自动冻结该条日程，并向 M4 状态机抛出 `SyncConflict` 异常，触发多轮语音语音询问选择（场景十二）。

### M7：外部服务集成适配层 (External Services Integration Adapters)
* **所属分层**：4. 适配器与外设层（后端网关及集成）
* **职责**：遵循 M4 定义的端口契约，将内部统一实体转换为 Google Calendar、Microsoft Graph（日历及 To Do）和标准 CalDAV 协议的具体数据交互。
* **核心功能**：
  1. **多协议适配适配器**：提供 `createEvent`、`updateEvent`、`createTask` 等抽象接口，由 `GoogleCalendarAdapter`、`OutlookCalendarAdapter` 和 `LocalTodoAdapter` 进行底层映射实现。
  2. **日历别名与多日历分流**：根据 `UserDictionary` 对日历命名的语音别名（如“工作”、“私事”、“家里”），调用对应的适配器将日程投递到具体的个人/共享日历中（场景七）。

### M8：多方忙闲协同计算中心 (Multi-party FreeBusy Coordination Center)
* **所属分层**：3. 核心领域服务层与外部日历 API
* **职责**：当用户想要发起与多人的会议时，获取各参与者的繁忙时间段，在保护隐私的前提下自动计算出重合的空闲时间窗口。
* **核心功能**：
  1. **参与者邮箱对齐**：将口语提及的姓名（“李强”、“王芳”）对齐 M5 联系人表中的标准 Email 账号，并验证忙闲读取授权（场景九）。
  2. **敏感细节脱敏拉取**：调用 Google/CalDAV `FreeBusy` 接口，仅拉取包含起止时间的 `BUSY` 时段列表，严格屏蔽具体的会议标题与内容（保护隐私，场景九）。
  3. **空闲窗口重合度计算**：在内存中求出所有协同人员 `BUSY` 时间段的并集（Union），再取查询范围时间轴的补集，计算出重合的 `FREE` 空闲时间窗，为状态机 M4 提供推荐时间段（场景九）。

### M9：联网检索智能体模块 (Web Search Agent Module) [已在前端与状态机沙盒中完整集成实现（Phase 2）]
* **所属分层**：3. 核心领域服务层与外部 Web Search API
* **职责**：当用户查询超出系统本地知识或具有强时效性/未来时效性的外部信息时（如漫展时间、天气预报、突发事件、节日排期等），调用外部搜索引擎获取最新的互联网数据，并通过大模型对检索结果进行结构化日程/任务提取与规划。
* **核心功能**：
  1. **时效性意图嗅探与路由**：当 ASR 转写结果进入 M3 时，若语义分类引擎嗅探出用户指令涉及外部时效信息（如“我想参加2026年杭州的漫展”），判断其非系统内部静态指令，自动将控制权流转至 M9 联网检索模块。
  2. **Web 搜索工具集成**：通过六边形架构的 `IWebSearchPort`，调用外部搜索适配器（如 Tavily Search Adapter 或 Google Search Adapter），获取互联网实时网页切片与检索段落。
  3. **结构化日程实体提炼**：使用大模型（LLM）对检索返回的非结构化网页文本进行深度语义建模，提炼出规范的日程（标题、起止时间、举办场馆、购票链接、活动描述）或待办任务信息。
  4. **多值歧义主动追问**：若搜索结果发现多个匹配事件（例如 2026 年在杭州有多个不同日期举办 of 漫展），自动生成选项包，向 M4 状态机抛出 `AmbiguousSearch` 异常，触发多轮语音追问（如：“为您查到2026年杭州有5月的动漫节和10月的漫展，请问您想参加哪一个？”）。

---

## 3. 模块间的显式耦合与协同契约

为了实现高内聚并定义清晰的模块边界，各模块之间绝不直接进行紧密的代码级强调用，而是通过**强类型的契约对象和接口协议进行显式耦合**。以下为核心业务流中的契约数据结构：

```
                              流式音频传输管道
 M1：语音感知 ─────────────────── [AudioChunk] ─────────────────> M2：WebSocket网关
                                                                        │
                                                                        │ 文本与基准时间
 M4：状态机/LangGraph <────────── [SemanticOutput] <──────────── M3：语义分类引擎
        │                                                               │
        │                                                     嗅探外部检索指令
        │                                                               │
        ├───── 联网检索请求 ────── [SearchQuery] ──────────────────────> M9：联网检索Agent
        │                                                               │
        │<──── 结构化日程草稿 ─── [SemanticOutput] ─────────────────────┘
        │
        ├───── 写入前检查忙闲 ─── [EventDraft/Emails] ──────────> M8：多方协同计算
        │                                                               │
        ├───── 写入前时钟碰撞 ─── [CalendarEvent] ─────────────────> M5：冲突数据库
        │
        └───── 发送云端/端侧创建 ─ [TodoTask / Event] ───────────> M7：集成适配器
```

### 3.1 M1 ──(AudioChunk)──> M2
* **耦合通道**：WebSocket 双向连接。
* **契约数据结构 (`AudioChunk`)**：
```typescript
interface AudioChunk {
  session_id: string;
  sequence_number: number;   // 序列号，从 0 开始自增，网关检测丢包与重排
  payload: ArrayBuffer;      // 原始音频切片二进制数据 (16kHz PCM)
  is_final: boolean;         // 标志是否是最后一片
}
```

### 3.2 M2 ──(TranscriptionResult)──> M3
* **耦合通道**：后端内存数据流（ASR 引擎输出后事件）。
* **契约数据结构 (`TranscriptionResult`)**：
```typescript
interface TranscriptionResult {
  session_id: string;
  raw_text: string;           // STT 识别出的未经清洗的原始文本
  confidence: number;         // ASR 识别置信度 (0~1)
  started_at: string;        // 绝对基准时间戳，来自 ASR 接收端 (ISO 8601)
  device_timezone: string;    // 设备时区
}
```

### 3.3 M3 ──(SemanticOutput)──> M4
* **耦合通道**：LangGraph 状态机入参。
* **契约数据结构 (`SemanticOutput`)**：
```typescript
interface SemanticOutput {
  intent: "create_event" | "update_event" | "delete_event" | "create_task" | "update_task" | "delete_task" | "convert_task_to_event" | "clarification" | "cancel" | "unknown";
  extracted_entities: {
    event_draft?: {
      title?: string;
      start_time?: string;   // ISO 8601 格式，如 "2026-06-01T10:00:00+08:00"
      end_time?: string;
      location?: string;
      attendees?: string[];  // 参与者邮箱列表，触发 M8 多方忙闲协同
      recurrence_rule?: string;
    };
    task_draft?: {
      title?: string;
      due_time?: string;
      priority?: "low" | "medium" | "high";
    };
  };
  confidence: number;         // 语义与模糊时间整体解析置信度
  temporal_confidence_breakdown?: {
    time_segment: string;     // 如 "下周一"
    resolved_time: string;    // "2026-06-01"
    score: number;            // 置信度分数，低于0.8触发追问
  }[];
}
```

### 3.4 M4 ──(Pre-flight Checking)──> M5 / M8
* **耦合通道**：状态机业务检查端口调用。
* **契约数据结构 (`ConflictResult` & `FreeBusyRequest`)**：
```typescript
// 1. M4 耦合 M5 冲突数据库校验
interface ConflictResult {
  has_conflict: boolean;
  conflicts: {
    existing_event_id: string;
    existing_title: string;
    overlap_start: string;
    overlap_end: string;
    severity: "full" | "partial";
  }[];
}

// 2. M4 耦合 M8 多方忙闲协同查询
interface FreeBusyRequest {
  attendees: string[];       // 目标协同人员的 Email 列表
  start_time: string;        // 拟发起会议的开始时间段 (ISO 8601)
  end_time: string;          // 结束时间段
}
```

### 3.5 M6 ──(SyncPayload)──> M5
* **耦合通道**：增量同步 REST 契约。
* **契约数据结构 (`SyncPayload`)**：
```typescript
interface SyncPayload {
  user_id: string;
  client_timestamp: string;
  offline_operations: {
    operation_id: string;
    entity_type: "event" | "task";
    action: "create" | "update" | "delete";
    entity_id: string;
    payload: any;             // 被变更的具体字段集合
    original_version_tag: string; // 离线变更前的云端原始版本戳，用于冲突校验
    executed_at: string;      // 本地离线执行动作的时间戳
  ][];
}
```

### 3.6 M3/M4 ──(Search Request)──> M9 ──(Parse Result)──> M4
* **耦合通道**：智能体动作触发与 Function Calling 数据流。
* **契约数据结构 (`WebSearchRequest` & `WebSearchResponse`)**：
```typescript
// 1. M3/M4 触发 M9 的联网搜索请求
interface WebSearchRequest {
  session_id: string;
  query: string;             // 搜索检索词，如 "2026年杭州漫展 时间 地点"
  max_results?: number;      // 最大搜索条数
  search_depth?: "shallow" | "deep"; // 检索深度，默认为 deep
}

// 2. M9 检索并结构化解析后返回给 M4 状态机的数据
interface WebSearchResponse {
  session_id: string;
  status: "success" | "ambiguous" | "no_results" | "error";
  search_raw_query: string;
  extracted_events: {
    title: string;
    start_time: string;      // ISO 8601，如 "2026-05-01T09:00:00+08:00"
    end_time: string;
    location: string;
    description: string;
    source_url?: string;     // 检索来源网页链接
  }[];
  reply_text: string;        // 预置播报文本，若成功则为提示确认，若歧义则为追问列表
}
```

---

## 4. 模块级开发顺序与研发路线图

为了最大限度地保证项目成功率，降低由于全双工、离线同步等高级交互带来的技术开发失控，项目分为四个阶段依次进行研发。各模块对应其所处的阶段展开开发：

```
研发演进轴 ────►
【Phase 1: 核心骨架打通】  ──► 【Phase 2: 深度对话与分流】 ──► 【Phase 3: 极速全双工与感知】 ──► 【Phase 4: 增量同步与协同】
  - M5 冲突数据库基础表         - M4 LangGraph 多轮追问      - M2 WebSocket 消息网关        - M6 离线缓存与同步引擎
  - M7 日历适配器核心 CRUD      - M3 ASR 纠偏与模糊时间      - M2 Barge-in 强打断控制        - M8 多方忙闲协同计算
  - M3 LLM 基础解析             - M3 待办任务/事件双分流      - M1 流式 VAD & 手势控制
  - FastAPI 极简 HTTP API       - M5 待办/联系人/地点表建立  - M1 马达振动与提示音联调
```

### 4.1 Phase 1：核心骨架打通（MVP 阶段）
* **开发目的**：以最快速度打通系统最核心的主线功能闭环，允许用户口述一句话直接在云端日历创建事件。
* **开发模块范围**：
  1. **M5 冲突数据库设计**：建立 PostgreSQL，创建首版 `users`、`calendars` 和 `events` 表，部署带时区的时间索引。
  2. **M7 日历适配器**：编写 `GoogleCalendarAdapter` 及 `LocalCalendarAdapter`，实现基本的 `createEvent` 接口与 CRUD 操作。
  3. **M3 基础语义解析**：设计大模型基准时钟注入（Baseline Injector）提示词，限制模型必须单次输出标准的 ISO 8601 `start_time` 格式。
  4. **FastAPI HTTP 网关（M2 简化版）**：开发简易的 REST 接口 `POST /api/v1/voice/process`，支持用户整段音频 Base64 上传，后台同步转写并调 LLM 解析后直接入库日历。
  5. **M1 前端简易版**：实现基础的网页端录音功能，具备简易 of 日历月/周可视化视图。

### 4.2 Phase 2：深度对话与待办分流（意图深化阶段）
* **开发目的**：让系统具备处理残缺信息、多轮交互以及同音纠偏的智慧，实现待办和日程的逻辑分离。
* **开发模块范围**：
  1. **M4 LangGraph 状态机**：正式部署 LangGraph 多轮会话引擎，实现缺失字段追问节点（`ask_clarification`）和冲突协商推荐节点（`resolve_conflict`）。
  2. **M3 字典模糊对齐层**：开发拼音匹配和编辑距离比对，结合联系人与常用地点词典，在 LLM 提取前实现口语字模糊对齐（解决同音字识别错误，场景二）。
  3. **M3 双通道分类器**：在 Prompt 中注入任务/日历事件的分类判据。大模型输出 `create_task` 等工具参数。
  4. **M5 数据库全面升级**：在 PostgreSQL 中建 `tasks`（待办表）、`contacts`（联系人表）和 `favorite_locations`（常用地点表）。
  5. **M9 联网检索智能体**：集成外部网页搜索引擎适配器，实现时效性意图嗅探，大模型对非结构化网页进行深度实体提炼，并对多值歧义触发 `AmbiguousSearch` 追问与一键结构化日程写入。

### 4.3 Phase 3：极速全双工与感知硬件联调（全双工与无障碍阶段）
* **开发目的**：实现极其流畅的长连接交互，支持随时打断与全屏无障碍操作，完全释放驾驶与障碍场景价值。
* **开发模块范围**：
  1. **M2 WebSocket 双向长连接网关**：全面替代 HTTP API，开发 WebSocket 握手及流式数据帧分发核心。
  2. **M2 Barge-in 异步任务打断协调器**：设计流式 TTS 异步任务管理器，在接收到前端打断控制帧时，执行秒级协程取消。
  3. **M1 语音感知与前端 VAD**：前端开发自适应端点检测（VAD）控制器，接收后端 `VAD_TIMEOUT_ADJUST` 帧微调停顿超时。
  4. **M1 手机硬件感知适配**：联调手机大范围全屏手势控制，结合 iOS/Android 系统原生内置 TTS 硬件引擎，适配并实现马达高低频触觉振动以及各种状态铃声提示。

### 4.4 Phase 4：增量同步与协同（离线可用与社交扩展阶段）
* **开发目的**：弱网/无网时随心记日程，上线增量无冲突自动对齐；支持语音一键多方会议时间协商。
* **开发模块范围**：
  1. **M6 端侧缓存队列与乐观锁**：在前端轻量数据库中实现离线操作日志记录。为 `events` 和 `tasks` 生成基于 UUID 和时间的版本戳。
  2. **M6 增量同步引擎**：在云端实现 `/api/v1/sync` 增量包分析路由。开发 `SyncResolver` 冲突合并器，实现无交集字段 Merge 和交集冲突向 M4 状态机抛出异常以语音选择的功能。
  3. **M8 多方忙闲协同计算中心**：集成外部 CalDAV FreeBusy 服务，开发基于忙闲时段的“并集与补集”空闲时间段搜索算法。

---

## 5. 并行研发策略与测试边界

### 5.1 并行开发计划
通过定义的显式契约，研发团队可分为三组完全并行开发：
* **第一组（适配层与数据库开发）**：负责 M5 关系型冲突数据库与 M7 外部服务适配层接口实现。
* **第二组（AI中枢与语义状态机开发）**：负责 M3 语义理解与模糊纠偏、M4 LangGraph 追问状态机、以及冲突碰撞策略。
* **第三组（前端及网关通信开发）**：负责 M1 语音感知流式组件、M2 WebSocket 双向网关及 M6 离线缓存队列。

### 5.2 核心测试边界
为确保工业级稳定性，系统必须在研发期间对以下测试边界进行强制校验：
1. **边界时间测试（M3 & M5 联调）**：测试用例必须覆盖跨年（如 12-31 23:59:59）、跨月（如 2-28）、以及多时区差旅时，大模型绝对时间注入与数据库 `TSTZRANGE` 匹配的正确性。
2. **弱网与冲突同步测试（M6 & M5 联调）**：利用弱网测试工具（如丢包率达 30%，带宽 100kbps 模拟地铁和电梯），验证离线消息在极端网络下能平滑缓存，上线时能够完美对齐乐观锁版本。
3. **车载强噪声测试（M1 & M2 联调）**：测试在车内强背景胎噪、风噪干扰下，定向麦克风降噪和 ASR 识别的解析表现，以保障行车环境交互的绝对可靠。
