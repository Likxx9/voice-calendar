# 📡 API接口文档

## 概述

本文档详细说明智能语音日历系统的API接口设计，包括RESTful API和WebSocket API。

---

## 1. RESTful API

### 1.1 基础信息

- **Base URL**: `http://localhost:8000/api`
- **认证方式**: Bearer Token (JWT)
- **请求格式**: JSON
- **响应格式**: JSON

### 1.2 通用响应格式

```json
{
    "code": 200,
    "message": "success",
    "data": { ... }
}
```

### 1.3 错误响应格式

```json
{
    "code": 400,
    "message": "Bad Request",
    "detail": "Invalid parameter: start_time"
}
```

---

## 2. 用户认证

### 2.1 用户登录

**POST** `/auth/login`

```json
// 请求
{
    "email": "user@example.com",
    "password": "123456"
}

// 响应
{
    "code": 200,
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIs...",
        "token_type": "bearer",
        "user": {
            "id": "user_123",
            "email": "user@example.com",
            "nickname": "张三"
        }
    }
}
```

### 2.2 用户注册

**POST** `/auth/register`

```json
// 请求
{
    "email": "user@example.com",
    "nickname": "张三",
    "password": "123456"
}

// 响应
{
    "code": 200,
    "data": {
        "id": "user_123",
        "email": "user@example.com",
        "nickname": "张三"
    }
}
```

---

## 3. 日历事件管理

### 3.1 获取事件列表

**GET** `/calendar/events`

**查询参数**:
- `user_id` (必填): 用户ID
- `start_date` (可选): 开始日期 YYYY-MM-DD
- `end_date` (可选): 结束日期 YYYY-MM-DD

```json
// 响应
{
    "code": 200,
    "data": {
        "events": [
            {
                "id": "evt_123",
                "user_id": "user_123",
                "title": "产品评审会",
                "description": "Q2产品规划评审",
                "location": "会议室A",
                "start_time": "2026-05-31T14:00:00+08:00",
                "end_time": "2026-05-31T15:00:00+08:00",
                "timezone": "Asia/Shanghai",
                "is_all_day": false,
                "color": "#3B82F6",
                "reminder_minutes": 30,
                "created_at": "2026-05-30T10:00:00Z"
            }
        ]
    }
}
```

### 3.2 创建事件

**POST** `/calendar/events`

```json
// 请求
{
    "user_id": "user_123",
    "title": "开会",
    "description": "团队周会",
    "location": "会议室B",
    "start_time": "2026-06-01T14:00:00+08:00",
    "end_time": "2026-06-01T15:00:00+08:00",
    "timezone": "Asia/Shanghai",
    "participants": ["user_456", "user_789"],
    "reminder_minutes": 15
}

// 响应
{
    "code": 200,
    "data": {
        "event": {
            "id": "evt_456",
            "title": "开会",
            "start_time": "2026-06-01T14:00:00+08:00",
            "end_time": "2026-06-01T15:00:00+08:00",
            "created_at": "2026-05-30T12:00:00Z"
        },
        "message": "Event created successfully"
    }
}
```

### 3.3 更新事件

**PUT** `/calendar/events/{event_id}`

```json
// 请求
{
    "title": "产品评审会（更新）",
    "start_time": "2026-06-01T15:00:00+08:00"
}

// 响应
{
    "code": 200,
    "data": {
        "event": {
            "id": "evt_123",
            "title": "产品评审会（更新）",
            "start_time": "2026-06-01T15:00:00+08:00"
        },
        "message": "Event updated successfully"
    }
}
```

### 3.4 删除事件

**DELETE** `/calendar/events/{event_id}`

```json
// 响应
{
    "code": 200,
    "data": {
        "message": "Event deleted successfully"
    }
}
```

### 3.5 检查时间冲突

**GET** `/calendar/conflicts`

**查询参数**:
- `user_id` (必填): 用户ID
- `start_time` (必填): 开始时间 ISO格式
- `end_time` (必填): 结束时间 ISO格式
- `exclude_event_id` (可选): 排除的事件ID

```json
// 响应
{
    "code": 200,
    "data": {
        "has_conflict": true,
        "conflicts": [
            {
                "id": "evt_789",
                "title": "产品评审会",
                "start_time": "2026-06-01T14:30:00+08:00",
                "end_time": "2026-06-01T15:30:00+08:00"
            }
        ]
    }
}
```

---

## 4. WebSocket API

### 4.1 连接信息

```
ws://localhost:8000/api/v1/voice/stream?session_id={session_id}&user_id={user_id}
```

**查询参数**:
- `session_id` (可选): 会话ID，不传则自动生成
- `user_id` (可选): 用户ID

### 4.2 消息帧格式

所有消息都是JSON格式，包含以下字段：

```json
{
    "type": "message_type",
    "sessionId": "session_123",
    "data": { ... },
    "timestamp": "2026-05-30T14:30:00Z"
}
```

### 4.3 客户端 -> 服务端消息

#### 音频数据块

```json
{
    "type": "AUDIO_CHUNK",
    "sessionId": "session_123",
    "data": [0.1, 0.2, 0.3, ...],
    "sequence": 1,
    "isFinal": false
}
```

#### 文本输入

```json
{
    "type": "TEXT_INPUT",
    "sessionId": "session_123",
    "text": "提醒我明天下午三点开会"
}
```

#### 打断信号

```json
{
    "type": "WS_INTENT_INTERRUPT",
    "sessionId": "session_123"
}
```

#### 心跳

```json
{
    "type": "heartbeat",
    "sessionId": "session_123"
}
```

### 4.4 服务端 -> 客户端消息

#### 心跳响应

```json
{
    "type": "heartbeat_ack",
    "timestamp": "2026-05-30T14:30:00Z"
}
```

#### 转写结果

```json
{
    "type": "TRANSCRIPT_FINAL",
    "sessionId": "session_123",
    "text": "提醒我明天下午三点开会",
    "confidence": 0.95,
    "isFinal": true
}
```

#### 语义理解结果

```json
{
    "type": "SEMANTIC_RESULT",
    "sessionId": "session_123",
    "intent": "create_event",
    "entities": {
        "title": "开会",
        "start_time": "2026-05-31T15:00:00+08:00",
        "end_time": "2026-05-31T16:00:00+08:00",
        "timezone": "Asia/Shanghai"
    },
    "confidence": 0.92
}
```

#### 追问请求

```json
{
    "type": "CLARIFICATION_ASK",
    "sessionId": "session_123",
    "missing_fields": ["开始时间"],
    "message": "请问什么时候开会？"
}
```

#### 冲突检测结果

```json
{
    "type": "CONFLICT_ALERT",
    "sessionId": "session_123",
    "conflicts": [
        {
            "id": "evt_789",
            "title": "产品评审会",
            "start_time": "2026-05-31T14:30:00+08:00",
            "end_time": "2026-05-31T15:30:00+08:00"
        }
    ],
    "message": "检测到时间冲突",
    "suggestions": [
        {"time": "2026-05-31T16:00:00+08:00", "reason": "会议结束后"},
        {"time": "2026-06-01T15:00:00+08:00", "reason": "第二天同一时间"}
    ]
}
```

#### 事件创建成功

```json
{
    "type": "ACTION_RESULT",
    "sessionId": "session_123",
    "event": {
        "id": "evt_123",
        "title": "开会",
        "start_time": "2026-05-31T15:00:00+08:00",
        "end_time": "2026-05-31T16:00:00+08:00"
    },
    "message": "已创建事件：开会"
}
```

#### TTS播放指令

```json
{
    "type": "PLAYBACK_CONTROL",
    "sessionId": "session_123",
    "text": "好的，已为您创建开会，时间是明天下午三点"
}
```

---

## 5. 数据模型

### 5.1 CalendarEvent

```typescript
interface CalendarEvent {
    id: string;
    user_id: string;
    title: string;
    description?: string;
    location?: string;
    start_time: string;  // ISO 8601
    end_time: string;    // ISO 8601
    timezone: string;
    recurrence_rule?: string;  // iCalendar RRULE
    participants?: string[];
    is_all_day: boolean;
    color?: string;
    reminder_minutes: number;
    is_completed: boolean;
    created_at: string;
    updated_at?: string;
    deleted_at?: string;
}
```

### 5.2 TodoTask

```typescript
interface TodoTask {
    id: string;
    user_id: string;
    title: string;
    description?: string;
    due_date?: string;
    reminder_at?: string;
    category?: string;
    priority: 'low' | 'medium' | 'high';
    related_event_id?: string;
    is_completed: boolean;
    completed_at?: string;
    created_at: string;
}
```

### 5.3 SemanticOutput

```typescript
interface SemanticOutput {
    originalText: string;
    cleanedText: string;
    intent: IntentType;
    entities: {
        title?: string;
        startTime?: string;
        endTime?: string;
        location?: string;
        participants?: string[];
    };
    missingFields: string[];
    confidence: number;
}
```

### 5.4 ConflictResult

```typescript
interface ConflictResult {
    hasConflict: boolean;
    conflicts: CalendarEvent[];
    suggestions?: Alternative[];
}

interface Alternative {
    time: string;
    reason: string;
}
```

---

## 6. 错误码

| 错误码 | 说明 | 示例 |
|--------|------|------|
| 400 | 请求参数错误 | 缺少必填参数 |
| 401 | 未授权 | Token无效或过期 |
| 403 | 禁止访问 | 无权限访问资源 |
| 404 | 资源不存在 | 事件不存在 |
| 409 | 时间冲突 | 新事件与现有事件冲突 |
| 422 | 数据验证失败 | 时间格式错误 |
| 500 | 服务器内部错误 | 数据库连接失败 |

---

## 7. 认证说明

### 7.1 获取Token

通过 `/auth/login` 接口获取JWT Token。

### 7.2 使用Token

在请求头中添加：
```
Authorization: Bearer <token>
```

### 7.3 Token有效期

- Access Token: 24小时
- Refresh Token: 7天

---

## 8. 限流策略

| 接口类型 | 限流规则 |
|----------|----------|
| REST API | 100次/分钟 |
| WebSocket | 1个连接/用户 |
| 音频上传 | 10MB/分钟 |

---

## 9. 示例代码

### 9.1 JavaScript/TypeScript

```javascript
// 创建事件
const response = await fetch('/api/calendar/events', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
        user_id: 'user_123',
        title: '开会',
        start_time: '2026-06-01T14:00:00+08:00',
        end_time: '2026-06-01T15:00:00+08:00'
    })
});
```

### 9.2 WebSocket连接

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/voice/stream?session_id=xxx');

ws.onopen = () => {
    console.log('Connected');
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('Received:', message);
};

ws.send(JSON.stringify({
    type: 'TEXT_INPUT',
    text: '提醒我明天开会'
}));
```

### 9.3 Python

```python
import httpx

# 创建事件
async with httpx.AsyncClient() as client:
    response = await client.post(
        'http://localhost:8000/api/calendar/events',
        json={
            'user_id': 'user_123',
            'title': '开会',
            'start_time': '2026-06-01T14:00:00+08:00',
            'end_time': '2026-06-01T15:00:00+08:00'
        },
        headers={'Authorization': f'Bearer {token}'}
    )
```
