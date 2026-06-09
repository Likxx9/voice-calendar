# -*- coding: utf-8 -*-
"""
VoiCal 语音日历 - 后端 API 服务器 (flask-socketio)
唯一的服务器入口点。
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from flask import Flask, send_from_directory, jsonify, request, make_response
from flask_socketio import SocketIO, emit
import threading
import os
import sys

# Windows 平台控制台输出编码修正
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from app.core import notifier
from app.speech import asr
from app.services.agent import process_voice_intent
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


# ── CORS 处理 ─────────────────────────────────────────────
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return response


# ── 安全的 async 运行器 ───────────────────────────────────
def run_async(coro):
    """在任何线程中安全执行 async 协程，避免 asyncio.run() 冲突。"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
    except (RuntimeError, ImportError):
        pass
    try:
        return asyncio.run(coro)
    except RuntimeError:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(lambda: asyncio.run(coro)).result()


# ── WebSocket ─────────────────────────────────────────────
def ws_broadcast(event_type: str, data: dict):
    socketio.emit('server_event', {'type': event_type, 'data': data})

notifier.register_callback(ws_broadcast)


@socketio.on('connect')
def handle_connect():
    print('[SocketIO] 客户端已连接')
    emit('server_event', {'type': 'connected', 'data': {'message': '连接成功'}})


active_asr_sessions = {}

@socketio.on('disconnect')
def handle_disconnect():
    print('[SocketIO] 客户端已断开')
    sid = request.sid
    session = active_asr_sessions.pop(sid, None)
    if session:
        try:
            session.stop()
        except Exception:
            pass


from app.speech.tts import tts_client

@socketio.on('voice_input')
def handle_voice_input(msg):
    tts_client.stop()
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
    tts_client.stop()
    sid = request.sid
    if sid in active_asr_sessions:
        try:
            active_asr_sessions[sid].stop()
        except Exception:
            pass
    session = asr.ASRSession(sid)
    active_asr_sessions[sid] = session
    session.start()

@socketio.on('audio_chunk')
def handle_audio_chunk(data):
    sid = request.sid
    session = active_asr_sessions.get(sid)
    if session and session.active:
        session.send_audio_chunk(data)

@socketio.on('stop_recording')
def handle_stop_recording():
    print('[SocketIO] 收到客户端发起的停止录音请求')
    sid = request.sid
    session = active_asr_sessions.pop(sid, None)
    if session:
        session.stop()


# ── Auth API ──────────────────────────────────────────────
@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def api_register():
    if request.method == 'OPTIONS':
        return '', 204

    from app.database import AsyncSessionLocal
    from app.models.user import User, UserRole
    from app.core.security import hash_password, create_access_token
    from sqlalchemy import select

    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    password = (data.get('password') or '').strip()

    if not name or len(name) < 2:
        return jsonify({"error": "用户名至少2个字符"}), 400
    if not password or len(password) < 6:
        return jsonify({"error": "密码至少6个字符"}), 400

    async def _register():
        async with AsyncSessionLocal() as db:
            existing = await db.execute(select(User).where(User.name == name))
            if existing.scalar_one_or_none():
                return None, "该用户名已被注册"

            user = User(
                name=name,
                password_hash=hash_password(password),
                role=UserRole.BASIC,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user, None

    try:
        user, err = run_async(_register())
    except Exception as e:
        print(f"[Auth] 注册异常: {e}")
        return jsonify({"error": f"服务器错误: {e}"}), 500

    if err:
        return jsonify({"error": err}), 409

    token = create_access_token(user.id, user.role.value)
    return jsonify({
        "token": token,
        "user": {"id": str(user.id), "name": user.name, "role": user.role.value}
    })


@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def api_login():
    if request.method == 'OPTIONS':
        return '', 204

    from app.database import AsyncSessionLocal
    from app.models.user import User
    from app.core.security import verify_password, create_access_token
    from sqlalchemy import select

    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    password = (data.get('password') or '').strip()

    if not name or not password:
        return jsonify({"error": "请输入用户名和密码"}), 400

    try:
        async def _login():
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(User).where(User.name == name))
                return result.scalar_one_or_none()
        user = run_async(_login())
    except Exception as e:
        print(f"[Auth] 登录查询异常: {e}")
        return jsonify({"error": f"服务器错误: {e}"}), 500

    if not user or not user.password_hash:
        return jsonify({"error": "用户名或密码错误"}), 401
    if not verify_password(password, user.password_hash):
        return jsonify({"error": "用户名或密码错误"}), 401

    token = create_access_token(user.id, user.role.value)
    return jsonify({
        "token": token,
        "user": {"id": str(user.id), "name": user.name, "role": user.role.value}
    })


@app.route('/api/auth/profile', methods=['POST', 'OPTIONS'])
def api_profile():
    if request.method == 'OPTIONS':
        return '', 204

    from app.core.security import verify_token
    from app.database import AsyncSessionLocal
    from app.models.user import User
    from sqlalchemy import select

    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({"error": "未登录"}), 401
    payload = verify_token(auth[7:])
    if not payload:
        return jsonify({"error": "登录已过期"}), 401

    data = request.get_json(silent=True) or {}
    user_id = uuid.UUID(payload['sub'])

    async def _update():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return "用户不存在"
            if data.get('name'):
                user.name = data['name'].strip()
            if data.get('timezone'):
                user.timezone = data['timezone']
            await db.commit()
            return None

    try:
        err = run_async(_update())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    if err:
        return jsonify({"error": err}), 400
    return jsonify({"ok": True})


@app.route('/api/auth/password', methods=['POST', 'OPTIONS'])
def api_password():
    if request.method == 'OPTIONS':
        return '', 204

    from app.core.security import verify_token, verify_password, hash_password
    from app.database import AsyncSessionLocal
    from app.models.user import User
    from sqlalchemy import select

    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({"error": "未登录"}), 401
    payload = verify_token(auth[7:])
    if not payload:
        return jsonify({"error": "登录已过期"}), 401

    data = request.get_json(silent=True) or {}
    old_password = (data.get('old_password') or '').strip()
    new_password = (data.get('new_password') or '').strip()

    if not old_password or not new_password:
        return jsonify({"error": "请填写密码"}), 400
    if len(new_password) < 6:
        return jsonify({"error": "新密码至少6个字符"}), 400

    user_id = uuid.UUID(payload['sub'])

    async def _change():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return "用户不存在"
            if not user.password_hash or not verify_password(old_password, user.password_hash):
                return "当前密码错误"
            user.password_hash = hash_password(new_password)
            await db.commit()
            return None

    try:
        err = run_async(_change())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    if err:
        return jsonify({"error": err}), 401
    return jsonify({"ok": True})


@app.route('/api/auth/me')
def api_me():
    from app.core.security import verify_token
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({"error": "未登录"}), 401
    payload = verify_token(auth[7:])
    if not payload:
        return jsonify({"error": "登录已过期"}), 401
    return jsonify({"id": payload["sub"], "role": payload.get("role", "basic")})


# ── Events API ────────────────────────────────────────────
@app.route('/api/events')
def api_events():
    """返回当前用户指定时间范围内的所有日程"""
    from app.database import AsyncSessionLocal
    from app.services.schedule_service import ScheduleService

    user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

    range_start_str = request.args.get('start')
    range_end_str = request.args.get('end')

    now = datetime.now()
    if range_start_str:
        range_start = datetime.fromisoformat(range_start_str)
    else:
        js_day = (now.weekday() + 1) % 7
        range_start = (now - timedelta(days=js_day)).replace(hour=0, minute=0, second=0, microsecond=0)

    if range_end_str:
        range_end = datetime.fromisoformat(range_end_str)
    else:
        range_end = range_start + timedelta(days=35)

    try:
        async def _fetch():
            async with AsyncSessionLocal() as db:
                svc = ScheduleService(db)
                return await svc.list_events(user_id, range_start, range_end)
        events = run_async(_fetch())
    except Exception as e:
        print(f"[API] events 查询异常: {e}")
        return jsonify([])

    print(f"[API /api/events] 返回 {len(events)} 条日程")

    color_map = {'HIGH': 'red', 'MEDIUM': 'blue', 'LOW': 'teal'}
    result = []
    for ev in events:
        s_hour = ev.start_time.hour + ev.start_time.minute / 60
        e_hour = ev.end_time.hour + ev.end_time.minute / 60
        priority_name = ev.priority.name if ev.priority else 'MEDIUM'

        result.append({
            'id': str(ev.id),
            'title': ev.title,
            'start_time': ev.start_time.isoformat(),
            'end_time': ev.end_time.isoformat(),
            's': s_hour,
            'e': e_hour,
            'c': color_map.get(priority_name, 'amber'),
            'loc': ev.location or '',
            'type': '项目' if priority_name == 'MEDIUM' else '会议',
            'isNew': False,
        })

    return jsonify(result)


@app.route('/api/events/<event_id>', methods=['DELETE', 'OPTIONS'])
def api_delete_event(event_id):
    if request.method == 'OPTIONS':
        return '', 204

    from app.database import AsyncSessionLocal
    from app.services.schedule_service import ScheduleService

    user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

    try:
        async def _delete():
            async with AsyncSessionLocal() as db:
                svc = ScheduleService(db)
                ok = await svc.delete_event(user_id, uuid.UUID(event_id))
                if ok:
                    await db.commit()
                return ok
        ok = run_async(_delete())
    except Exception as e:
        print(f"[API] 删除日程异常: {e}")
        return jsonify({"error": str(e)}), 500

    if not ok:
        return jsonify({"error": "日程不存在或删除失败"}), 404

    return jsonify({"status": "success", "message": "日程已成功取消"})


# ── Static Files ──────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('voice_calendar_frontend', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('voice_calendar_frontend', path)


# ── Startup ───────────────────────────────────────────────
if __name__ == '__main__':
    asyncio.run(init_db())

    # 确保 password_hash 列存在（SQLite ALTER TABLE）
    import sqlite3
    try:
        conn = sqlite3.connect('voical.db')
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cur.fetchall()]
        if 'password_hash' not in columns:
            cur.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(256)")
            conn.commit()
            print("[DB] 已添加 password_hash 列")
        conn.close()
    except Exception as e:
        print(f"[DB] 检查列时出错: {e}")

    print("=" * 50)
    print("  VoiCal 语音日历 API 服务器启动")
    print("  访问地址: http://localhost:5000")
    print("=" * 50)

    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
