"""
WebSocket API Router
WebSocket API路由 - 实时语音通信

集成 Agent 编排层（技术文档 §3），支持：
- 多意图并行分析
- 关联任务合并
- 联网搜索
- 独立任务隔离
"""
import json
import asyncio
import time
from typing import Dict, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.agent_service import agent_service, AgentOutput
from app.services.llm_service import llm_service

router = APIRouter()


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

    消息帧协议（与设计文档 §9.9 保持一致）：
    - SESSION_INIT: 会话初始化
    - AUDIO_CHUNK: 音频数据
    - TEXT_INPUT: 文本输入
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
            session_id = init_frame.get("session_id") or session_id
            user_id = init_frame.get("user_id") or user_id
            await manager.send_message(session_id, {
                "type": "STATE_UPDATE",
                "state": "idle",
                "timestamp": datetime.utcnow().isoformat(),
            })

        while True:
            data = await websocket.receive_text()
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
    """处理音频数据块"""
    is_final = message.get("is_final", False)

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
    """处理文本输入"""
    text = message.get("text", "").strip()
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


async def process_with_agent(session_id: str, text: str):
    """
    Agent 编排层处理入口（技术文档 §3）

    处理流程：
    1. NLU 语义解析（L2）
    2. Agent 多意图提取与任务规划（L3）
    3. 并行工具调度与执行（L4）
    4. 结果聚合与 TTS 响应（L5）
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

    # ── Step 3: 简单意图走规则路由（技术文档 §3.1.1） ──
    if missing_fields:
        await manager.send_message(session_id, {
            "type": "CLARIFICATION_ASK",
            "missing_fields": missing_fields,
            "message": f"请补充以下信息：{', '.join(missing_fields)}",
        })
        return

    conflicts = await check_time_conflicts(entities)
    if conflicts:
        await manager.send_message(session_id, {
            "type": "CONFLICT_ALERT",
            "conflicts": conflicts,
            "message": "检测到时间冲突",
            "suggestions": generate_alternatives(conflicts),
        })
        return

    event = await create_calendar_event(entities)
    title = entities.get("title", "事件")
    start = entities.get("start_time", "")

    await manager.send_message(session_id, {
        "type": "ACTION_RESULT",
        "event": event,
        "message": f"已创建事件：{title}",
    })
    await manager.send_message(session_id, {
        "type": "PLAYBACK_CONTROL",
        "action": "START_TTS",
        "reply_text": f"好的，已为您创建{title}，时间是{start}",
    })


async def _process_with_agent_pipeline(
    session_id: str,
    text: str,
    dialog_history: list,
    user_profile: dict,
    reference_time: datetime,
):
    """Agent 编排层完整 pipeline（技术文档 §3）"""
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

    # 处理搜索结果
    if has_search:
        search_result = None
        for key, val in agent_output.results.items():
            if isinstance(val, dict) and "tool_result:web_search" in str(key):
                search_result = val
                break
            if key.startswith("group_") and isinstance(val, dict):
                for k2, v2 in val.items():
                    if "web_search" in k2 and isinstance(v2, dict):
                        search_result = v2.get("data", v2)
                        break

        if search_result:
            search_data = search_result if isinstance(search_result, dict) else {}
            query = search_data.get("query", text)
            answer = search_data.get("answer", f"关于「{query}」的搜索结果")
            results = search_data.get("results", [])

            extracted_events = []
            for r in results:
                extracted_events.append({
                    "title": r.get("title", ""),
                    "start_time": "",
                    "end_time": "",
                    "location": "",
                    "description": r.get("content", ""),
                    "source_url": r.get("url", ""),
                })

            await manager.send_message(session_id, {
                "type": "SEMANTIC_RESULT",
                "intent": "SEARCH",
                "search_response": {
                    "status": "success" if results else "no_results",
                    "search_raw_query": query,
                    "extracted_events": extracted_events,
                    "reply_text": answer,
                },
            })
            await manager.send_message(session_id, {
                "type": "PLAYBACK_CONTROL",
                "action": "START_TTS",
                "reply_text": answer,
            })
            return

    # 处理非搜索类多意图结果
    response_parts = []
    for intent_data in intents:
        itype = intent_data.get("type", "unknown")
        entities = intent_data.get("entities", {})
        title = entities.get("title", entities.get("raw_text", ""))

        if itype == "CREATE":
            event = await create_calendar_event(entities)
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
        "event": None,
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


async def check_time_conflicts(entities: dict) -> list:
    return []


def generate_alternatives(conflicts: list) -> list:
    return [
        {"time": "2026-05-31T16:00:00", "reason": "会议结束后"},
        {"time": "2026-06-01T15:00:00", "reason": "第二天同一时间"},
    ]


async def create_calendar_event(entities: dict) -> dict:
    return {
        "id": f"evt_{int(time.time())}",
        "title": entities.get("title"),
        "start_time": entities.get("start_time"),
        "end_time": entities.get("end_time"),
        "created_at": datetime.utcnow().isoformat(),
    }
