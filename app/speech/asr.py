# -*- coding:utf-8 -*-
import websocket
import hashlib
import base64
import hmac
import json
import os
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import threading
from app.core import notifier
from app.services.agent import process_voice_intent
from dotenv import load_dotenv

load_dotenv()

STATUS_FIRST_FRAME = 0
STATUS_CONTINUE_FRAME = 1
STATUS_LAST_FRAME = 2


class ASRSession:
    """Per-session state for speech recognition, avoids global variable races."""

    def __init__(self, sid=None):
        self.sid = sid
        self.recognized_text = ""
        self.active = False
        self.ws = None
        self.status = STATUS_FIRST_FRAME
        self.lock = threading.Lock()
        self.ws_thread = None

        self.ws_param = _Ws_Param(
            APPID=os.environ.get("XUNFEI_APPID", ""),
            APISecret=os.environ.get("XUNFEI_API_SECRET", ""),
            APIKey=os.environ.get("XUNFEI_API_KEY", ""),
        )

    def append_text(self, text: str):
        with self.lock:
            self.recognized_text += text

    def get_text(self) -> str:
        with self.lock:
            return self.recognized_text

    def start(self):
        with self.lock:
            if self.active:
                return
            self.active = True
            
        websocket.enableTrace(False)
        ws_url = self.ws_param.create_url()
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        self.ws.on_open = self._on_open

        # Run the WebSocket event loop in a background thread
        self.ws_thread = threading.Thread(
            target=self.ws.run_forever,
            kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}},
            daemon=True
        )
        self.ws_thread.start()

    def send_audio_chunk(self, chunk: bytes):
        if not self.active or not self.ws:
            return

        try:
            base64_audio = base64.b64encode(chunk).decode('utf-8')
            if self.status == STATUS_FIRST_FRAME:
                d = {
                    "common": self.ws_param.CommonArgs,
                    "business": self.ws_param.BusinessArgs,
                    "data": {
                        "status": STATUS_FIRST_FRAME,
                        "format": "audio/L16;rate=16000",
                        "audio": base64_audio,
                        "encoding": "raw"
                    }
                }
                self.ws.send(json.dumps(d))
                self.status = STATUS_CONTINUE_FRAME
            elif self.status == STATUS_CONTINUE_FRAME:
                d = {
                    "data": {
                        "status": STATUS_CONTINUE_FRAME,
                        "format": "audio/L16;rate=16000",
                        "audio": base64_audio,
                        "encoding": "raw"
                    }
                }
                self.ws.send(json.dumps(d))
        except Exception as e:
            print(f"[ASRSession] Error sending audio chunk: {e}")
            self.stop()

    def stop(self):
        with self.lock:
            if not self.active:
                return
            self.active = False

        try:
            if self.ws and self.status == STATUS_CONTINUE_FRAME:
                # Send final frame to trigger final result from Xunfei
                d = {
                    "data": {
                        "status": STATUS_LAST_FRAME,
                        "format": "audio/L16;rate=16000",
                        "audio": "",
                        "encoding": "raw"
                    }
                }
                self.ws.send(json.dumps(d))
        except Exception as e:
            print(f"[ASRSession] Error sending last frame: {e}")

        # Note: We do not close the websocket immediately because we want to receive
        # the final response (which triggers status 2 in _on_message).
        # We only close if Xunfei takes too long or fails to respond.
        def force_close_after_delay():
            time.sleep(2)
            try:
                if self.ws:
                    self.ws.close()
            except Exception:
                pass
        threading.Thread(target=force_close_after_delay, daemon=True).start()

    def _on_message(self, ws, message):
        try:
            msg = json.loads(message)
            code = msg["code"]
            if code != 0:
                print("sid:%s call error:%s code is:%s" % (msg["sid"], msg["message"], code))
                self.stop()
                return

            data_dict = msg["data"]
            data = data_dict["result"]["ws"]
            result = ""
            for i in data:
                for w in i["cw"]:
                    result += w["w"]
            self.append_text(result)
            print(result, end="", flush=True)

            notifier.broadcast("asr_interim", {"text": self.get_text()})

            if data_dict["status"] == 2:
                full_text = self.get_text()
                print("\n\n[语音识别完成] 完整句子: ", full_text)
                
                notifier.broadcast("listening_stop")
                
                if full_text.strip():
                    notifier.broadcast("asr_result", {"text": full_text, "final": True})
                    # Process the intent in a separate thread
                    threading.Thread(
                        target=process_voice_intent,
                        args=(full_text,),
                        daemon=True
                    ).start()
                else:
                    notifier.broadcast("session_end", {"message": "未听到声音"})
                
                # Close the websocket connection since we are done
                try:
                    ws.close()
                except Exception:
                    pass

        except Exception as e:
            print("receive msg,but parse exception:", e)

    def _on_error(self, ws, error):
        print("### ASR error:", error)
        notifier.broadcast("listening_stop")

    def _on_close(self, ws, *args):
        print("### ASR closed ###")
        notifier.broadcast("listening_stop")

    def _on_open(self, ws):
        print("[ASRSession] Xunfei ASR WebSocket connected")
        notifier.broadcast("listening_start")


class _Ws_Param:
    def __init__(self, APPID, APIKey, APISecret):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.CommonArgs = {"app_id": self.APPID}
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "vinfo": 1, "vad_eos": 10000}

    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: ws-api.xfyun.cn\ndate: " + date + "\nGET /v2/iat HTTP/1.1"
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = 'api_key="%s", algorithm="hmac-sha256", headers="host date request-line", signature="%s"' % (
            self.APIKey, signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        return url + '?' + urlencode(v)
