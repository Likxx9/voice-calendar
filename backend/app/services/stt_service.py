"""
STT Service
语音转文本服务 - 云端/离线双轨 ASR 引擎

云端（首选）：科大讯飞极速 ASR API / 阿里达摩院 SenseVoice-Large
离线（降级）：阿里达摩院 FunASR / Paraformer-Large（搭配 Sherpa-onnx）
"""
import asyncio
from typing import AsyncGenerator, Optional
from datetime import datetime
import numpy as np

from app.core.config import settings


class STTService:
    """语音转文本服务类"""
    
    def __init__(self):
        self.model = settings.STT_MODEL
        self.language = settings.STT_LANGUAGE
        self.sample_rate = 16000  # 16kHz
        self.channels = 1  # 单声道
        self.sample_width = 2  # 16bit
        
        # TODO: 初始化云端/离线 ASR 引擎
        # 云端：科大讯飞极速 ASR API 或 SenseVoice-Large
        # 离线：FunASR Paraformer-Large + Sherpa-onnx
        # from funasr import AutoModel
        # self.asr_model = AutoModel(model="paraformer-zh")
    
    async def transcribe_stream(
        self,
        audio_chunks: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[dict, None]:
        """
        流式语音识别
        
        Args:
            audio_chunks: 音频数据流（16kHz 16bit PCM）
        
        Yields:
            识别结果：{"text": "...", "confidence": 0.95, "is_final": false}
        """
        buffer = bytearray()
        chunk_size = 4800  # 300ms的音频数据 (16000 * 2 * 0.3)
        
        async for chunk in audio_chunks:
            buffer.extend(chunk)
            
            # 当缓冲区足够大时进行识别
            if len(buffer) >= chunk_size:
                # 转换为numpy数组
                audio_data = np.frombuffer(bytes(buffer), dtype=np.int16)
                audio_float = audio_data.astype(np.float32) / 32768.0
                
                # TODO: 调用云端/离线 ASR 引擎进行识别
                # 云端：调用讯飞/SenseVoice API
                # 离线：调用 FunASR Paraformer 本地模型
                # result = self.asr_model.generate(
                #     input=audio_float,
                #     language=self.language
                # )
                
                # 模拟识别结果
                partial_text = "识别中..."
                confidence = 0.8
                
                yield {
                    "text": partial_text,
                    "confidence": confidence,
                    "is_final": False,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # 清空缓冲区（保留最后部分用于重叠）
                buffer = buffer[-1600:]  # 保留100ms用于重叠
        
        # 处理剩余音频
        if buffer:
            audio_data = np.frombuffer(bytes(buffer), dtype=np.int16)
            audio_float = audio_data.astype(np.float32) / 32768.0
            
            # TODO: 调用云端/离线 ASR 引擎进行最终识别
            final_text = "最终识别结果"
            confidence = 0.95
            
            yield {
                "text": final_text,
                "confidence": confidence,
                "is_final": True,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def transcribe_file(self, file_path: str) -> dict:
        """
        文件语音识别
        
        Args:
            file_path: 音频文件路径
        
        Returns:
            识别结果
        """
        # TODO: 实现文件识别
        return {
            "text": "文件识别结果",
            "confidence": 0.9,
            "duration": 10.5,
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
