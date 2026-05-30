"""
WebSocket API Router
WebSocket API路由 - 实时语音通信

集成 Agent 编排层（技术文档 §3），支持：
- 多意图并行分析
- 关联任务合并
- 联网搜索
- 独立任务隔离

设计原则：后端负责所有数据处理与分析，前端仅负责展示。
"""
import json
import asyncio
import time
from typing import Dict, List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.agent_service import agent_service, AgentOutput
from app.services.llm_service import llm_service

router = APIRouter()


# ── 显示映射（前端不再做任何映射） ────────────────────────────
FIELD_LABELS: Dict[str, str] = {
    "title": "标题",
    "事件标题": "标题",
    "start_time": "开始时间",
    "开始时间": "开始时间",
    "end_time": "结束时间",
    "location": "地点",
    "attendees": "参与者",
    "due_time": "截止时间",
    "priority": "优先级",
}

INTENT_DISPLAY: Dict[str, Dict[str, str]] = {
    "create_event":          {"category": "event",   "icon": "📅", "label": "创建日程"},
    "update_event":          {"category": "event",   "icon": "📅", "label": "修改日程"},
    "delete_event":          {"category": "event",   "icon": "📅", "label": "删除日程"},
    "create_task":           {"category": "task",    "icon": "✅", "label": "创建待办"},
    "update_task":           {"category": "task",    "icon": "✅", "label": "修改待办"},
    "delete_task":           {"category": "task",    "icon": "✅", "label": "删除待办"},
    "convert_task_to_event": {"category": "event",   "icon": "📅", "label": "转为日程"},
    "clarification":         {"category": "clarify", "icon": "❓", "label": "需要确认"},
    "cancel":                {"category": "cancel",  "icon": "✖",  "label": "取消操作"},
    "unknown":               {"category": "unknown", "icon": "❔", "label": "未识别"},
    "CREATE":                {"category": "event",   "icon": "📅", "label": "创建日程"},
    "QUERY":                 {"category": "event",   "icon": "🔍", "label": "查询日程"},
    "MODIFY":                {"category": "event",   "icon": "✏️", "label": "修改日程"},
    "DELETE":                {"category": "event",   "icon": "🗑️", "label": "删除日程"},
    "SEARCH":                {"category": "search",  "icon": "🌐", "label": "联网搜索"},
    "PLAN":                  {"category": "plan",    "icon": "📋", "label": "规划行程"},
}


def _get_intent_display(intent_type: str) -> Dict[str, str]:
    return INTENT_DISPLAY.get(intent_type, INTENT_DISPLAY["unknown"])


def _format_datetime(iso_str: str) -> str:
    """后端统一格式化时间字符串，前端不再做任何时间解析"""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str)
        return f"{dt.year}年{dt.month:02d}月{dt.day:02d}日 {dt.hour:02d}:{dt.minute:02d}"
    except (ValueError, TypeError):
        return iso_str


def _format_time_short(iso_str: str) -> str:
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str)
        return f"{dt.hour:02d}:{dt.minute:02d}"
    except (ValueError, TypeError):
        return iso_str


def _build_quick_suggestions(dialog_history: List[Dict]) -> List[str]:
    """根据对话上下文动态生成快捷建议（前端不再硬编码）"""
    if not dialog_history:
        return [
            "帮我创建明天下午三点的会",
            "联网检索2026年杭州的动漫展",
            "搜一下上海最近的实践活动",
            "添加买牛奶的待办",
        ]
    # 基于最近对话历史生成上下文相关建议
    last_msg = dialog_history[-1].get("content", "") if dialog_history else ""
    suggestions = [
        "查看今天的日程",
        "帮我创建明天下午三点的会",
        "联网搜索最近的展会活动",
        "添加一个待办事项",
    ]
    return suggestions


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, dict] = {}

    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.user_sessions[session_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
            "dialog_history": [],
        }

    def disconnect(self, session_id: str):
        self.active_connections.pop(session_id, None)
        self.user_sessions.pop(session_id, None)

    async def send_message(self, session_id: str, message: dict):
        ws = self.active_connections.get(session_id)
        if ws:
            await ws.send_json(message)


manager = ConnectionManager()


@router.websocket("/voice/stream")
async def voice_websocket(
    websocket: WebSocket,
    session_id: str = None,
    user_id: str = None,
):
    """
    语音交互WebSocket端点

    消息帧协议：
    - SESSION_INIT: 会话初始化
    - AUDIO_CHUNK: 音频数据
    - TEXT_INPUT: 文本输入
    - SEARCH_ADD_EVENT: 用户选择将搜索结果加入日历
    - WS_INTENT_INTERRUPT: Barge-in 打断
    - HEARTBEAT: 心跳
    """
    if not session_id:
        session_id = f"session_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    await manager.connect(websocket, session_id, user_id or "anonymous")

    try:
        init_data = await websocket.receive_text()
        init_frame = json.loads(init_data)
        if init_frame.get("type") == "SESSION_INIT":
            new_session_id = init_frame.get("session_id") or session_id
            user_id = init_frame.get("user_id") or user_id
            
            # 如果session_id变了，更新连接映射
            if new_session_id != session_id:
                manager.active_connections.pop(session_id, None)
                manager.user_sessions.pop(session_id, None)
                session_id = new_session_id
                manager.active_connections[session_id] = websocket
                if session_id not in manager.user_sessions:
                    manager.user_sessions[session_id] = {
                        "user_id": user_id,
                        "connected_at": datetime.utcnow().isoformat(),
                        "dialog_history": [],
                    }

            # 发送初始状态 + 快捷建议（前端不再硬编码）
            dialog_history = manager.user_sessions.get(session_id, {}).get("dialog_history", [])
            await manager.send_message(session_id, {
                "type": "STATE_UPDATE",
                "state": "idle",
                "timestamp": datetime.utcnow().isoformat(),
                "quick_suggestions": _build_quick_suggestions(dialog_history),
            })

        while True:
            ws_message = await websocket.receive()
            if ws_message.get("type") == "websocket.receive":
                if "bytes" in ws_message and ws_message["bytes"]:
                    continue
                data = ws_message.get("text", "")
            elif "text" in ws_message:
                data = ws_message["text"]
            elif "bytes" in ws_message:
                continue
            else:
                continue
            if not data:
                continue
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "HEARTBEAT":
                await manager.send_message(session_id, {
                    "type": "HEARTBEAT",
                    "timestamp": datetime.utcnow().isoformat(),
                })
            elif msg_type == "AUDIO_CHUNK":
                await handle_audio_chunk(session_id, message)
            elif msg_type == "TEXT_INPUT":
                await handle_text_input(session_id, message)
            elif msg_type == "SEARCH_ADD_EVENT":
                await handle_search_add_event(session_id, message)
            elif msg_type == "WS_INTENT_INTERRUPT":
                await handle_interrupt(session_id)
            else:
                await manager.send_message(session_id, {
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                })

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(session_id)


async def handle_audio_chunk(session_id: str, message: dict):
    """处理音频数据块 - 支持前端WSFrame格式"""
    payload = message.get("payload", message)
    is_final = payload.get("is_final", False)

    if is_final:
        recognized_text = "提醒我明天下午三点开会"
        await manager.send_message(session_id, {
            "type": "TRANSCRIPT_FINAL",
            "text": recognized_text,
            "confidence": 0.95,
            "is_final": True,
        })
        await process_with_agent(session_id, recognized_text)
    else:
        await manager.send_message(session_id, {
            "type": "TRANSCRIPT_PARTIAL",
            "text": "识别中...",
            "confidence": 0.7,
            "is_final": False,
        })


async def handle_text_input(session_id: str, message: dict):
    """处理文本输入 - 支持前端WSFrame格式 {type, payload: {text}} 或扁平格式 {text}"""
    payload = message.get("payload", message)
    text = payload.get("text", "").strip()
    if not text:
        await manager.send_message(session_id, {"type": "error", "message": "Empty text input"})
        return
    await process_with_agent(session_id, text)


async def handle_interrupt(session_id: str):
    """处理打断信号（Barge-in）"""
    await manager.send_message(session_id, {
        "type": "STATE_UPDATE",
        "state": "parsing",
        "message": "打断成功，已暂停播报，正在听您说话...",
    })


async def handle_search_add_event(session_id: str, message: dict):
    """
    处理用户将搜索结果加入日历（前端不再本地构造事件）

    前端只发送原始搜索事件数据，后端负责：
    1. 创建日历事件
    2. 返回创建结果
    3. 返回 TTS 播报文本
    """
    payload = message.get("payload", message)
    event_data = payload.get("event", {})
    search_query = payload.get("search_query", "")

    event = await create_calendar_event({
        "title": event_data.get("title", "未命名事件"),
        "start_time": event_data.get("start_time", ""),
        "end_time": event_data.get("end_time", ""),
        "location": event_data.get("location", ""),
        "description": event_data.get("description", ""),
        "source_url": event_data.get("source_url", ""),
        "voice_raw_text": search_query,
    })

    title = event_data.get("title", "事件")
    reply_text = f"已成功将「{title}」添加入您的日历日程！"

    await manager.send_message(session_id, {
        "type": "ACTION_RESULT",
        "action": "search_add_event",
        "event": event,
        "message": reply_text,
    })
    await manager.send_message(session_id, {
        "type": "PLAYBACK_CONTROL",
        "action": "START_TTS",
        "reply_text": reply_text,
    })
    # 后端控制状态恢复，前端不再 setTimeout
    await asyncio.sleep(2)
    dialog_history = manager.user_sessions.get(session_id, {}).get("dialog_history", [])
    await manager.send_message(session_id, {
        "type": "STATE_UPDATE",
        "state": "idle",
        "quick_suggestions": _build_quick_suggestions(dialog_history),
    })


async def process_with_agent(session_id: str, text: str):
    """
    Agent 编排层处理入口（技术文档 §3）

    所有分析、判断、状态转换均在后端完成。
    前端仅接收 ready-to-render 数据并展示。
    """
    reference_time = datetime.utcnow()
    session_data = manager.user_sessions.get(session_id, {})
    dialog_history = session_data.get("dialog_history", [])
    user_profile = {"timezone": "Asia/Shanghai", "locale": "zh-CN"}

    # ── Step 1: NLU 语义解析 ──
    nlu_result = await llm_service.process_voice_input(
        text,
        context={"address_book": {}, "favorite_locations": {}},
        reference_time=reference_time,
    )

    intent = nlu_result.get("intent", "unknown")
    entities = nlu_result.get("entities", {})
    missing_fields = nlu_result.get("missing_fields", [])
    needs_agent = nlu_result.get("needs_agent", False)
    intents = nlu_result.get("intents", [])

    # 记录对话历史
    dialog_history.append({"role": "user", "content": text, "timestamp": reference_time.isoformat()})
    if len(dialog_history) > 20:
        dialog_history = dialog_history[-20:]
    session_data["dialog_history"] = dialog_history

    # ── Step 2: 判断是否需要 Agent 编排 ──
    if needs_agent or len(intents) > 1 or intent == "SEARCH":
        await _process_with_agent_pipeline(session_id, text, dialog_history, user_profile, reference_time)
        return

    # ── Step 3: 简单意图走规则路由 ──
    if missing_fields:
        # 后端构建显示用的字段标签，前端不再做映射
        display_fields = [
            {"key": f, "label": FIELD_LABELS.get(f, f)}
            for f in missing_fields
        ]
        msg = f"请补充以下信息：{'、'.join(d['label'] for d in display_fields)}"
        await manager.send_message(session_id, {
            "type": "CLARIFICATION_ASK",
            "missing_fields": display_fields,
            "message": msg,
        })
        return

    conflicts = await check_time_conflicts(entities)
    if conflicts:
        # 后端构建 ready-to-display 的冲突数据和建议
        formatted_conflicts = []
        for c in conflicts:
            formatted_conflicts.append({
                **c,
                "overlap_start_display": _format_time_short(c.get("overlap_start", "")),
                "overlap_end_display": _format_time_short(c.get("overlap_end", "")),
                "severity_label": "完全重叠" if c.get("severity") == "full" else "部分重叠",
            })
        alternatives = generate_alternatives(conflicts)
        formatted_suggestions = [
            {"text": alt["reason"], "value": alt["reason"]}
            for alt in alternatives
        ]
        await manager.send_message(session_id, {
            "type": "CONFLICT_ALERT",
            "conflicts": formatted_conflicts,
            "message": "检测到时间冲突",
            "suggestions": formatted_suggestions,
        })
        return

    event = await create_calendar_event(entities)
    title = entities.get("title", "事件")
    start = entities.get("start_time", "")
    start_display = _format_datetime(start)
    intent_display = _get_intent_display(intent)

    reply_text = f"好的，已为您创建{title}，时间是{start_display}" if start_display else f"好的，已为您创建{title}"

    await manager.send_message(session_id, {
        "type": "ACTION_RESULT",
        "event": event,
        "message": f"已创建事件：{title}",
        "intent_display": intent_display,
    })
    await manager.send_message(session_id, {
        "type": "PLAYBACK_CONTROL",
        "action": "START_TTS",
        "reply_text": reply_text,
    })
    # 后端控制状态恢复到 idle，前端不再 setTimeout
    await asyncio.sleep(2)
    await manager.send_message(session_id, {
        "type": "STATE_UPDATE",
        "state": "idle",
        "quick_suggestions": _build_quick_suggestions(dialog_history),
    })


async def _process_with_agent_pipeline(
    session_id: str,
    text: str,
    dialog_history: list,
    user_profile: dict,
    reference_time: datetime,
):
    """Agent 编排层完整 pipeline"""
    await manager.send_message(session_id, {
        "type": "STATE_UPDATE",
        "state": "processing",
        "message": "正在分析您的请求...",
    })

    agent_output: AgentOutput = await agent_service.process(
        session_id=session_id,
        text=text,
        dialog_history=dialog_history,
        user_profile=user_profile,
        reference_time=reference_time,
    )

    intents = agent_output.results.get("intents", [])
    has_search = any(i.get("type") == "SEARCH" for i in intents)

    # ── 搜索类结果：后端构建全部 ready-to-display 数据 ──
    if has_search:
        search_result = _extract_search_result(agent_output.results)

        if search_result:
            search_data = search_result if isinstance(search_result, dict) else {}
            query = search_data.get("query", text)
            answer = search_data.get("answer", f"关于「{query}」的搜索结果")
            results = search_data.get("results", [])

            # 后端构建完全格式化的事件列表，前端只做渲染
            extracted_events = []
            for r in results:
                start_time = r.get("start_time", "")
                end_time = r.get("end_time", "")
                extracted_events.append({
                    "title": r.get("title", ""),
                    "start_time": start_time,
                    "end_time": end_time,
                    "start_time_display": _format_datetime(start_time),
                    "end_time_display": _format_datetime(end_time),
                    "location": r.get("location", ""),
                    "description": r.get("content", r.get("description", "")),
                    "source_url": r.get("url", r.get("source_url", "")),
                })

            status = "success" if results else "no_results"
            await manager.send_message(session_id, {
                "type": "SEMANTIC_RESULT",
                "intent": "SEARCH",
                "intent_display": _get_intent_display("SEARCH"),
                "search_response": {
                    "status": status,
                    "search_raw_query": query,
                    "extracted_events": extracted_events,
                    "reply_text": answer,
                    "result_count": len(extracted_events),
                    "result_count_display": f"查到 {len(extracted_events)} 个活动",
                },
            })
            await manager.send_message(session_id, {
                "type": "PLAYBACK_CONTROL",
                "action": "START_TTS",
                "reply_text": answer,
            })
            return

    # ── 非搜索类多意图结果 ──
    response_parts = []
    created_events = []
    for intent_data in intents:
        itype = intent_data.get("type", "unknown")
        entities = intent_data.get("entities", {})
        title = entities.get("title", entities.get("raw_text", ""))
        intent_display = _get_intent_display(itype)

        if itype == "CREATE":
            event = await create_calendar_event(entities)
            created_events.append(event)
            response_parts.append(f"已创建事件「{title}」")
        elif itype == "QUERY":
            response_parts.append(f"查询「{title}」的结果")
        elif itype == "MODIFY":
            response_parts.append(f"已修改「{title}」")
        elif itype == "DELETE":
            response_parts.append(f"已删除「{title}」")
        else:
            response_parts.append(f"已处理「{title}」")

    reply = "；".join(response_parts) if response_parts else "请求已处理"
    latency = agent_output.planning_latency_ms

    await manager.send_message(session_id, {
        "type": "ACTION_RESULT",
        "events": created_events,
        "event": created_events[0] if created_events else None,
        "message": reply,
        "agent_metadata": {
            "task_groups": len(agent_output.task_groups),
            "intents_count": len(intents),
            "planning_latency_ms": round(latency, 1),
        },
    })
    await manager.send_message(session_id, {
        "type": "PLAYBACK_CONTROL",
        "action": "START_TTS",
        "reply_text": reply,
    })
    # 后端控制状态恢复
    await asyncio.sleep(2)
    await manager.send_message(session_id, {
        "type": "STATE_UPDATE",
        "state": "idle",
        "quick_suggestions": _build_quick_suggestions(dialog_history),
    })


def _extract_search_result(results: dict) -> Optional[dict]:
    """从 Agent 输出中提取搜索结果"""
    for key, val in results.items():
        if isinstance(val, dict) and "tool_result:web_search" in str(key):
            return val
        if key.startswith("group_") and isinstance(val, dict):
            for k2, v2 in val.items():
                if "web_search" in k2 and isinstance(v2, dict):
                    return v2.get("data", v2)
    return None


async def check_time_conflicts(entities: dict) -> list:
    return []


def generate_alternatives(conflicts: list) -> list:
    return [
        {"time": "2026-05-31T16:00:00", "reason": "会议结束后"},
        {"time": "2026-06-01T15:00:00", "reason": "第二天同一时间"},
    ]


async def create_calendar_event(entities: dict) -> dict:
    start = entities.get("start_time", "")
    end = entities.get("end_time", "")
    return {
        "id": f"evt_{int(time.time())}",
        "title": entities.get("title"),
        "start_time": start,
        "end_time": end,
        "start_time_display": _format_datetime(start),
        "end_time_display": _format_datetime(end),
        "location": entities.get("location", ""),
        "calendar_id": "default",
        "calendar_name": "默认日历",
        "color": "#4F46E5",
        "is_deleted": False,
        "version_tag": f"v_{int(time.time())}",
        "voice_raw_text": entities.get("voice_raw_text", ""),
        "created_at": datetime.utcnow().isoformat(),
    }
