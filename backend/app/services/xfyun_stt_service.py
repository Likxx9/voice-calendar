"""
iFlytek STT Service - 科大讯飞语音识别服务
"""
import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
from time import mktime
from wsgiref.handlers import format_date_time
import threading
import ssl
import asyncio
from typing import Optional

from app.core.config import settings


class XFYunSTTService:
    """科大讯飞语音识别服务"""
    
    def __init__(self):
        self.app_id = settings.XFYUN_APP_ID
        self.api_key = settings.XFYUN_API_KEY
        self.api_secret = settings.XFYUN_API_SECRET
    
    def create_url(self):
        """生成鉴权URL"""
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        now = datetime.datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
        
        authorization_origin = 'api_key="%s", algorithm="%s", headers="%s", signature="%s"' % (
            self.api_key, "hmac-sha256", "host date request-line", signature_sha
        )
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        
        url = url + '?' + urlencode(v)
        return url
    
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """
        将音频数据转换为文本
        
        Args:
            audio_data: 16kHz 16bit PCM音频数据
            
        Returns:
            识别出的文本
        """
        result_text = []
        result_event = threading.Event()
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                code = data.get("code", -1)
                
                if code != 0:
                    print(f"XFYun STT error: {data.get('message', 'Unknown error')}")
                    result_event.set()
                    return
                
                result = data.get("data", {}).get("result", {})
                ws_data = result.get("ws", [])
                
                for i in ws_data:
                    for w in i.get("cw", []):
                        result_text.append(w.get("w", ""))
                
                # 检查是否是最终结果
                pgs = result.get("pgs", "")
                if pgs == "apd":
                    result_event.set()
                    
            except Exception as e:
                print(f"Parse error: {e}")
                result_event.set()
        
        def on_error(ws, error):
            print(f"WebSocket error: {error}")
            result_event.set()
        
        def on_close(ws, close_status_code, close_msg):
            result_event.set()
        
        def on_open(ws):
            def send_audio():
                frame_size = 8000
                interval = 0.04
                status = 0  # 0: first, 1: continue, 2: last
                
                # 第一帧
                first_chunk = audio_data[:frame_size]
                d = {
                    "common": {"app_id": self.app_id},
                    "business": {
                        "domain": "iat",
                        "language": "zh_cn",
                        "accent": "mandarin",
                        "vinfo": 1,
                        "vad_eos": 10000
                    },
                    "data": {
                        "status": 0,
                        "format": "audio/L16;rate=16000",
                        "audio": str(base64.b64encode(first_chunk), 'utf-8'),
                        "encoding": "raw"
                    }
                }
                ws.send(json.dumps(d))
                status = 1
                
                # 中间帧
                offset = frame_size
                while offset < len(audio_data):
                    chunk = audio_data[offset:offset + frame_size]
                    if not chunk:
                        break
                    
                    d = {
                        "data": {
                            "status": 1,
                            "format": "audio/L16;rate=16000",
                            "audio": str(base64.b64encode(chunk), 'utf-8'),
                            "encoding": "raw"
                        }
                    }
                    ws.send(json.dumps(d))
                    offset += frame_size
                
                # 最后一帧
                d = {
                    "data": {
                        "status": 2,
                        "format": "audio/L16;rate=16000",
                        "audio": "",
                        "encoding": "raw"
                    }
                }
                ws.send(json.dumps(d))
            
            threading.Thread(target=send_audio, daemon=True).start()
        
        # 创建WebSocket连接
        ws_url = self.create_url()
        
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        ws.on_open = on_open
        
        # 在新线程中运行WebSocket
        ws_thread = threading.Thread(
            target=lambda: ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}),
            daemon=True
        )
        ws_thread.start()
        
        # 等待结果（最多10秒）
        result_event.wait(timeout=10)
        
        try:
            ws.close()
        except:
            pass
        
        return "".join(result_text)


# 全局实例
xfyun_stt_service = XFYunSTTService()
