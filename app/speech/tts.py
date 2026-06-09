import websocket
import hashlib
import base64
import hmac
import json
import os
import threading
from urllib.parse import urlencode
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import time
from dotenv import load_dotenv

load_dotenv()


class XunfeiTTS:
    def __init__(self, appid, api_key, api_secret):
        self.APPID = appid
        self.APIKey = api_key
        self.APISecret = api_secret
        self.host = "tts-api.xfyun.cn"
        self.path = "/v2/tts"
        self._lock = threading.Lock()
        self._cancel_flag = False
        self.ws = None

    def stop(self):
        self._cancel_flag = True
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass

    def create_url(self):
        url = f'wss://{self.host}{self.path}'
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = f"host: {self.host}\ndate: {date}\nGET {self.path} HTTP/1.1"
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        return url + '?' + urlencode(v)

    def synthesize_and_play(self, text):
        with self._lock:
            self._do_synthesize(text)

    def _do_synthesize(self, text):
        self._cancel_flag = False
        print(f"\n[TTS 开始播报] {text}")

        # Broadcast that TTS has started
        from app.core import notifier
        notifier.broadcast("tts_start", {"text": text})

        def on_message(ws, message):
            if self._cancel_flag:
                ws.close()
                return
            try:
                msg = json.loads(message)
                code = msg["code"]
                if code != 0:
                    print(f"TTS 错误: {msg['message']}")
                    return
                audio = msg["data"]["audio"]
                
                # Broadcast audio chunk (base64 string) to the frontend
                notifier.broadcast("tts_chunk", {"audio": audio})

                if msg["data"]["status"] == 2:
                    ws.close()
                    notifier.broadcast("tts_end")
            except Exception as e:
                print("TTS 异常:", e)

        def on_error(ws, error):
            print("TTS error:", error)
            notifier.broadcast("tts_end")

        def on_close(ws, *args):
            pass

        def on_open(ws):
            def run(*args):
                d = {
                    "common": {"app_id": self.APPID},
                    "business": {"aue": "raw", "auf": "audio/L16;rate=16000", "vcn": "xiaoyan", "tte": "utf8"},
                    "data": {"status": 2, "text": str(base64.b64encode(text.encode('utf-8')), "UTF8")}
                }
                ws.send(json.dumps(d))
            thread.start_new_thread(run, ())

        websocket.enableTrace(False)
        ws_url = self.create_url()
        self.ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
        self.ws.on_open = on_open
        self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

        time.sleep(0.5)


tts_client = XunfeiTTS(
    appid=os.environ.get("XUNFEI_APPID", ""),
    api_key=os.environ.get("XUNFEI_API_KEY", ""),
    api_secret=os.environ.get("XUNFEI_API_SECRET", ""),
)
