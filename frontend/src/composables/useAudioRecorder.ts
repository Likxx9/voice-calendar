/* ============================================================
 * M1 组合式函数 — 音频采集器
 * Web Audio API 实现 16kHz/16bit 单声道流式采集
 * 分片封装为 AudioChunk，通过回调实时输出
 * ============================================================ */

import { ref, onUnmounted } from 'vue'

export interface AudioRecorderOptions {
  sampleRate?: number          // 采样率，默认 16000
  chunkIntervalMs?: number     // 分片间隔，默认 250ms
  onChunk?: (chunk: ArrayBuffer, seqNum: number, isFinal: boolean) => void
  onVolumeChange?: (volume: number) => void
}

export function useAudioRecorder(options: AudioRecorderOptions = {}) {
  const {
    sampleRate = 16000,
    chunkIntervalMs = 250,
    onChunk,
    onVolumeChange,
  } = options

  const isRecording = ref(false)
  const currentVolume = ref(0)
  const error = ref<string | null>(null)

  let audioContext: AudioContext | null = null
  let mediaStream: MediaStream | null = null
  let sourceNode: MediaStreamAudioSourceNode | null = null
  let analyserNode: AnalyserNode | null = null
  let processorNode: ScriptProcessorNode | null = null
  let sequenceNumber = 0
  let volumeAnimationFrame = 0

  // 下采样 Float32 音频数据到目标采样率
  function downsample(buffer: Float32Array, inputRate: number, outputRate: number): Float32Array {
    if (inputRate === outputRate) return buffer
    const ratio = inputRate / outputRate
    const newLength = Math.round(buffer.length / ratio)
    const result = new Float32Array(newLength)
    for (let i = 0; i < newLength; i++) {
      const pos = Math.round(i * ratio)
      result[i] = buffer[pos] ?? 0
    }
    return result
  }

  // Float32 转 Int16 PCM
  function floatTo16BitPCM(input: Float32Array): ArrayBuffer {
    const buffer = new ArrayBuffer(input.length * 2)
    const view = new DataView(buffer)
    for (let i = 0; i < input.length; i++) {
      const s = Math.max(-1, Math.min(1, input[i]))
      view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true)
    }
    return buffer
  }

  // 实时音量分析
  function updateVolume() {
    if (!analyserNode) return
    const data = new Uint8Array(analyserNode.frequencyBinCount)
    analyserNode.getByteFrequencyData(data)
    const sum = data.reduce((a, b) => a + b, 0)
    const avg = sum / data.length / 255
    currentVolume.value = avg
    onVolumeChange?.(avg)
    if (isRecording.value) {
      volumeAnimationFrame = requestAnimationFrame(updateVolume)
    }
  }

  async function startRecording() {
    try {
      error.value = null
      sequenceNumber = 0

      mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: { ideal: sampleRate },
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      })

      audioContext = new AudioContext({ sampleRate: mediaStream.getAudioTracks()[0].getSettings().sampleRate || 44100 })
      sourceNode = audioContext.createMediaStreamSource(mediaStream)

      // 音量分析节点
      analyserNode = audioContext.createAnalyser()
      analyserNode.fftSize = 256
      sourceNode.connect(analyserNode)

      // 音频处理节点：分片
      const bufferSize = Math.round((audioContext.sampleRate * chunkIntervalMs) / 1000)
      processorNode = audioContext.createScriptProcessor(
        Math.min(16384, Math.max(256, Math.pow(2, Math.ceil(Math.log2(bufferSize))))),
        1,
        1,
      )

      processorNode.onaudioprocess = (e) => {
        if (!isRecording.value) return
        const inputData = e.inputBuffer.getChannelData(0)
        const downsampled = downsample(inputData, audioContext!.sampleRate, sampleRate)
        const pcmBuffer = floatTo16BitPCM(downsampled)
        onChunk?.(pcmBuffer, sequenceNumber++, false)
      }

      sourceNode.connect(processorNode)
      processorNode.connect(audioContext.destination)

      isRecording.value = true
      updateVolume()
    } catch (err) {
      error.value = err instanceof Error ? err.message : '无法访问麦克风'
      console.error('[AudioRecorder] 启动失败:', err)
    }
  }

  function stopRecording() {
    if (!isRecording.value) return

    isRecording.value = false
    cancelAnimationFrame(volumeAnimationFrame)

    // 发送最终空块标识
    onChunk?.(new ArrayBuffer(0), sequenceNumber, true)

    // 清理资源
    processorNode?.disconnect()
    sourceNode?.disconnect()
    analyserNode?.disconnect()
    mediaStream?.getTracks().forEach(t => t.stop())
    audioContext?.close()

    processorNode = null
    sourceNode = null
    analyserNode = null
    mediaStream = null
    audioContext = null
    currentVolume.value = 0
  }

  onUnmounted(() => {
    stopRecording()
  })

  return {
    isRecording,
    currentVolume,
    error,
    startRecording,
    stopRecording,
  }
}
