# -*- coding: utf-8 -*-
"""
VoiCal - 全局事件总线
用于在后端各模块（ASR, Agent, Tools）中触发事件，并由 Server 统一推送到前端。
"""

_callbacks = []

def register_callback(cb):
    _callbacks.append(cb)

def broadcast(event_type: str, data: dict = None):
    if data is None:
        data = {}
    for cb in _callbacks:
        try:
            cb(event_type, data)
        except Exception as e:
            print(f"[Notifier] 回调执行失败: {e}")
