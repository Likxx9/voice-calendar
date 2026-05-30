"""
STT Service
语音转文本服务 - 接入科大讯飞流式听写 (IAT) WebSocket API
"""
import asyncio
import json
import base64
import hmac
import hashlib
import websockets
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
from typing import AsyncGenerator

from app.core.config import settings


class STTService:
    """科大讯飞流式语音转文本服务类"""
    
    def __init__(self):
        self.appid = settings.XFYUN_APPID
        self.api_key = settings.XFYUN_API_KEY
        self.api_secret = settings.XFYUN_API_SECRET
        self.host = "iat-api.xfyun.cn"
        self.path = "/v2/iat"
        
        self.sample_rate = 16000  # 16kHz
        self.channels = 1  # 单声道
        self.sample_width = 2  # 16bit

    def create_url(self) -> str:
        """生成鉴权URL"""
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        
        # 拼接签名原文字符串
        signature_origin = f"host: {self.host}\ndate: {date}\nGET {self.path} HTTP/1.1"
        
        # 使用hmac-sha256进行加密
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
        
        # 拼接authorization
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        # 组装最终URL
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        url = f"wss://{self.host}{self.path}?{urlencode(v)}"
        return url

    async def transcribe_stream(
        self,
        audio_chunks: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[dict, None]:
        """
        全双工流式语音识别 (WebSocket)
        
        Args:
            audio_chunks: 音频数据流（16kHz 16bit PCM）
        """
        if not self.appid or not self.api_key or not self.api_secret:
            yield {
                "text": "[系统错误：未配置科大讯飞 API 密钥]",
                "confidence": 0.0,
                "is_final": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            return

        ws_url = self.create_url()
        try:
            async with websockets.connect(ws_url) as ws:
                
                # 发送协程：将前端发来的音频 chunk 发给讯飞
                async def sender():
                    status = 0  # 0: 握手第一帧, 1: 中间帧, 2: 结束帧
                    async for chunk in audio_chunks:
                        # 讯飞要求单次发送不超过 8000 bytes
                        # 若 chunk 较大，需在外部或此处做切片，此处假设前端 chunk 大小合理
                        payload = {
                            "data": {
                                "status": status,
                                "format": "audio/L16;rate=16000",
                                "encoding": "raw",
                                "audio": base64.b64encode(chunk).decode('utf-8')
                            }
                        }
                        if status == 0:
                            payload["common"] = {"app_id": self.appid}
                            payload["business"] = {
                                "domain": "iat",
                                "language": "zh_cn",
                                "accent": "mandarin",
                                "vinfo": 1,
                                "vad_eos": 3000, # 后端 VAD 停顿判定
                                # "dwa": "wpgs"  # 开启后支持动态修正，为了处理简单暂不开启
                            }
                            status = 1
                        
                        await ws.send(json.dumps(payload))
                        await asyncio.sleep(0.01)
                    
                    # 录音结束，发送最后帧
                    end_payload = {
                        "data": {
                            "status": 2,
                            "format": "audio/L16;rate=16000",
                            "encoding": "raw",
                            "audio": ""
                        }
                    }
                    await ws.send(json.dumps(end_payload))

                send_task = asyncio.create_task(sender())
                
                # 接收循环
                async for message in ws:
                    res = json.loads(message)
                    code = res.get("code")
                    if code != 0:
                        print(f"[STT Error] 讯飞返回错误码: {code}, 信息: {res.get('message')}")
                        break
                    
                    data = res.get("data", {})
                    if not data:
                        continue
                        
                    result = data.get("result", {})
                    ws_obj = result.get("ws", [])
                    
                    text_segment = ""
                    for w in ws_obj:
                        for cw in w.get("cw", []):
                            text_segment += cw.get("w", "")
                            
                    ws_status = data.get("status")
                    is_final = (ws_status == 2)
                    
                    if text_segment:
                        yield {
                            "text": text_segment,
                            "confidence": 0.95,
                            "is_final": is_final,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        
                    if is_final:
                        break
                        
                # 等待发送协程结束
                await send_task

        except websockets.exceptions.ConnectionClosed as e:
            print(f"[STT Warning] WebSocket closed abnormally: {e}")
        except Exception as e:
            print(f"[STT Error] Unexpected error during transcribe: {e}")
            yield {
                "text": "[系统错误：语音识别连接异常]",
                "confidence": 0.0,
                "is_final": True,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def transcribe_file(self, file_path: str) -> dict:
        """文件语音识别（预留给非流式场景）"""
        return {
            "text": "文件识别功能尚未接入",
            "confidence": 0.0,
            "duration": 0,
            "language": "zh"
        }
    
    def get_audio_config(self) -> dict:
        """获取音频配置"""
        return {
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "sample_width": self.sample_width,
            "encoding": "pcm_s16le"
        }

# 全局STT服务实例
stt_service = STTService()
