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
import pyaudio
import notifier
from agent import process_voice_intent
from dotenv import load_dotenv

load_dotenv()

STATUS_FIRST_FRAME = 0
STATUS_CONTINUE_FRAME = 1
STATUS_LAST_FRAME = 2


class ASRSession:
    """Per-session state for speech recognition, avoids global variable races."""

    def __init__(self):
        self.recognized_text = ""
        self.recording_active = True
        self.recording_thread = None
        self.lock = threading.Lock()
        self.audio_engine = pyaudio.PyAudio()

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

    def stop(self):
        self.recording_active = False

    def cleanup(self):
        try:
            self.audio_engine.terminate()
        except Exception:
            pass

    def run(self) -> str:
        websocket.enableTrace(False)
        ws_url = self.ws_param.create_url()
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        ws.on_open = self._on_open
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

        self.recording_active = False
        if self.recording_thread is not None:
            self.recording_thread.join()

        self.cleanup()
        return self.get_text()

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
                self.stop()
                if full_text.strip():
                    notifier.broadcast("asr_result", {"text": full_text, "final": True})

        except Exception as e:
            print("receive msg,but parse exception:", e)

    def _on_error(self, ws, error):
        self.stop()
        print("### error:", error)

    def _on_close(self, ws, *args):
        self.stop()
        print("### closed ###")

    def _on_open(self, ws):
        self.recording_active = True

        def run(*args):
            status = STATUS_FIRST_FRAME
            CHUNK = 1280
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000

            try:
                stream = self.audio_engine.open(
                    format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, frames_per_buffer=CHUNK
                )
                print("\n---- 开始录音 (按 Ctrl+C 停止) ----\n")
                notifier.broadcast("listening_start")
            except Exception as e:
                print(f"打开麦克风失败: {e}")
                ws.close()
                return

            try:
                while self.recording_active:
                    buf = stream.read(CHUNK, exception_on_overflow=False)
                    if status == STATUS_FIRST_FRAME:
                        d = {
                            "common": self.ws_param.CommonArgs,
                            "business": self.ws_param.BusinessArgs,
                            "data": {"status": 0, "format": "audio/L16;rate=16000",
                                     "audio": str(base64.b64encode(buf), 'utf-8'),
                                     "encoding": "raw"}
                        }
                        ws.send(json.dumps(d))
                        status = STATUS_CONTINUE_FRAME
                    elif status == STATUS_CONTINUE_FRAME:
                        d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                                      "audio": str(base64.b64encode(buf), 'utf-8'),
                                      "encoding": "raw"}}
                        ws.send(json.dumps(d))
            except Exception as e:
                print("录音异常/结束:", e)
            finally:
                try:
                    ws.send(json.dumps({"data": {"status": 2, "format": "audio/L16;rate=16000",
                                                  "audio": "", "encoding": "raw"}}))
                    time.sleep(1)
                except Exception:
                    pass
                try:
                    if 'stream' in locals() and stream.is_active():
                        stream.stop_stream()
                        stream.close()
                    ws.close()
                    notifier.broadcast("listening_stop")
                except Exception:
                    pass

        self.recording_thread = threading.Thread(target=run)
        self.recording_thread.start()


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


def start_listen_session() -> str:
    session = ASRSession()
    return session.run()


def run_assistant():
    print("=====================================================")
    print("   智能语音日历助手已启动 (L4/L5架构) [含 WebSocket 通知]")
    print("=====================================================")

    while True:
        try:
            text = start_listen_session()
            if text and text.strip():
                process_voice_intent(text)
            print("\n[系统] 准备进入下一轮对话...\n")
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n[系统] 收到退出信号，服务终止。")
            break
        except Exception as e:
            print(f"\n[系统] 发生异常: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run_assistant()
