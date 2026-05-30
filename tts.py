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
import pyaudio
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
        print(f"\n[TTS 开始播报] {text}")

        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, output=True)

        def on_message(ws, message):
            try:
                msg = json.loads(message)
                code = msg["code"]
                if code != 0:
                    print(f"TTS 错误: {msg['message']}")
                    return
                audio = msg["data"]["audio"]
                audio_bytes = base64.b64decode(audio)
                stream.write(audio_bytes)

                if msg["data"]["status"] == 2:
                    ws.close()
            except Exception as e:
                print("TTS 异常:", e)

        def on_error(ws, error):
            print("TTS error:", error)

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
        ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.on_open = on_open
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

        time.sleep(0.5)

        try:
            stream.stop_stream()
            stream.close()
        except Exception:
            pass
        try:
            p.terminate()
        except Exception:
            pass


tts_client = XunfeiTTS(
    appid=os.environ.get("XUNFEI_APPID", ""),
    api_key=os.environ.get("XUNFEI_API_KEY", ""),
    api_secret=os.environ.get("XUNFEI_API_SECRET", ""),
)

if __name__ == "__main__":
    tts_client.synthesize_and_play("您好，我是您的智能语音助手。路线已为您规划完毕。")
