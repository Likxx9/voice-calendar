# -*- coding: utf-8 -*-
"""
VoiCal 语音日历 - 后端 API 服务器 (flask-socketio)
唯一的服务器入口点。
"""
import asyncio
from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
import threading
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import notifier
import iat_ws_python3
from agent import process_voice_intent
from app.database import init_db

app = Flask(__name__, static_folder='voice_calendar_frontend')
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'voical-secret')

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    ping_interval=10,
    ping_timeout=60,
    logger=False,
    engineio_logger=False,
)

def ws_broadcast(event_type: str, data: dict):
    socketio.emit('server_event', {'type': event_type, 'data': data})

notifier.register_callback(ws_broadcast)


@socketio.on('connect')
def handle_connect():
    print('[SocketIO] 客户端已连接')
    emit('server_event', {'type': 'connected', 'data': {'message': '连接成功'}})


@socketio.on('disconnect')
def handle_disconnect():
    print('[SocketIO] 客户端已断开')


@socketio.on('voice_input')
def handle_voice_input(msg):
    text = msg.get('text', '').strip()
    if text:
        notifier.broadcast("asr_result", {"text": text, "final": True})
        threading.Thread(
            target=process_voice_intent,
            args=(text,),
            daemon=True
        ).start()

@socketio.on('start_recording')
def handle_start_recording():
    print('[SocketIO] 收到客户端发起的开始录音请求')
    def record_and_process():
        text = iat_ws_python3.start_listen_session()
        if text and text.strip():
            process_voice_intent(text)
        else:
            notifier.broadcast("session_end", {"message": "未听到声音"})
    threading.Thread(target=record_and_process, daemon=True).start()


@app.route('/')
def index():
    return send_from_directory('voice_calendar_frontend', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('voice_calendar_frontend', path)


if __name__ == '__main__':
    asyncio.run(init_db())

    print("=" * 50)
    print("  VoiCal 语音日历 API 服务器启动")
    print("  访问地址: http://localhost:5000")
    print("=" * 50)

    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
