<script lang="ts" setup>
import { ref, watch, onBeforeUnmount } from 'vue'

const props = defineProps<{ 
  transcription: boolean, 
  errorHandler: (error: unknown) => void 
}>()
const emit = defineEmits<{
  (e: 'audioReady', blob: Blob): void
}>()

const VISUALIZER_CONFIG = {
  fftSize: 256,             // http://developer.mozilla.org/en-US/docs/Web/API/AnalyserNode/fftSize
  barWidth: 2,              // Width of each frequency bar in pixels
  barSpacing: 1,            // Gap between frequency bars in pixels
  frameSkip: 2,             // Determines how often in the animation loop the bars get updated
  amplificationFactor: 12,  // Controls the overall intensity of the visualization by multiplying the audio signal strength
  powerFactor: 0.4,         // Controls the non-linear scaling of the bars - lower values create more dramatic peaks
  minBarHeight: 1,          // Minimum bar height in pixels
  zeroLevel: 128,           // Reference point for silence in audio signal (used for normalization)
}

const getVisualizerColor = () => 
  getComputedStyle(document.documentElement).getPropertyValue('--color-abstracta').trim() || '#3c1464'

const canvasRef = ref<HTMLCanvasElement | null>(null)
const audioURL = ref<string | null>(null)
const recordedChunks = ref<Blob[]>([])

let audioContext: AudioContext
let analyser: AnalyserNode
let dataArray: Uint8Array
let source: MediaStreamAudioSourceNode
let mediaRecorder: MediaRecorder
let micStream: MediaStream
let animationId: number
let x = 0
let frameCount = 0

watch(() => props.transcription, (val) => {
  val ? startRecording() : stopRecording()
})

const startRecording = async () => {
  try {
    await initializeAudioContext()
    initializeMediaRecorder()
    startVisualizer()
  } catch (e) {
    props.errorHandler(e)
  }
}

const initializeAudioContext = async () => {
  micStream = await navigator.mediaDevices.getUserMedia({ audio: true })
  audioContext = new ((window.AudioContext || (window as any).webkitAudioContext))()
  analyser = audioContext.createAnalyser()
  analyser.fftSize = VISUALIZER_CONFIG.fftSize
  dataArray = new Uint8Array(analyser.frequencyBinCount)
  source = audioContext.createMediaStreamSource(micStream)
  source.connect(analyser)
}

const initializeMediaRecorder = () => {
  recordedChunks.value = []
  mediaRecorder = new MediaRecorder(micStream)
  mediaRecorder.ondataavailable = (e) => recordedChunks.value.push(e.data)
  mediaRecorder.onstop = handleStop
  mediaRecorder.start()
}

const handleStop = async () => {
  const blob = new Blob(recordedChunks.value, { type: 'audio/webm' })
  audioURL.value = URL.createObjectURL(blob)
  emit('audioReady', blob)
}

const startVisualizer = () => {
  const canvas = canvasRef.value
  const ctx = canvas?.getContext('2d')
  if (!canvas || !ctx) return
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  x = 0
  frameCount = 0
  draw(ctx, canvas)
}

const draw = (ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement) => {
  animationId = requestAnimationFrame(() => draw(ctx, canvas))

  if (++frameCount % VISUALIZER_CONFIG.frameSkip !== 0) return

  analyser.getByteTimeDomainData(dataArray)
  const barHeight = calculateBarHeight(dataArray, canvas)
  const y = (canvas.height - barHeight) / 2

  ctx.fillStyle = getVisualizerColor()
  drawRoundedBar( ctx, x, y, VISUALIZER_CONFIG.barWidth, barHeight, VISUALIZER_CONFIG.barWidth)

  x += VISUALIZER_CONFIG.barWidth + VISUALIZER_CONFIG.barSpacing
  if (x >= canvas.width) {
    const imageData = ctx.getImageData(
      VISUALIZER_CONFIG.barWidth + VISUALIZER_CONFIG.barSpacing,
      0,
      canvas.width - (VISUALIZER_CONFIG.barWidth + VISUALIZER_CONFIG.barSpacing),
      canvas.height
    )
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.putImageData(imageData, 0, 0)
    x = canvas.width - (VISUALIZER_CONFIG.barWidth + VISUALIZER_CONFIG.barSpacing)
  }
}

const calculateBarHeight = (dataArray: Uint8Array, canvas: HTMLCanvasElement): number => {
  const avg = dataArray.reduce((a, b) => a + b) / dataArray.length
  const normalized = Math.abs((avg - VISUALIZER_CONFIG.zeroLevel) / VISUALIZER_CONFIG.zeroLevel)
  const amplifiedSignal = Math.pow(
    normalized * VISUALIZER_CONFIG.amplificationFactor,
    VISUALIZER_CONFIG.powerFactor
  )
  return Math.max(amplifiedSignal * canvas.height, VISUALIZER_CONFIG.minBarHeight)
}

const drawRoundedBar = (ctx: CanvasRenderingContext2D, x: number, y: number, width: number, height: number, radius: number) => {
  ctx.beginPath()
  ctx.roundRect(x, y, width, height, radius)
  ctx.fill()
  ctx.closePath()
}

const stopRecording = () => {
  const canvas = canvasRef.value
  cancelAnimationFrame(animationId)
  if (audioContext && audioContext.state !== 'closed') audioContext.close()
  if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop()
  micStream?.getTracks().forEach(track => track.stop())

  x = 0
  frameCount = 0
  canvas?.getContext('2d')?.clearRect(0, 0, canvas!.width, canvas!.height)
  recordedChunks.value = []
}

onBeforeUnmount(() => stopRecording())
defineExpose({ stopRecording })
</script>

<template>
  <div class="flex flex-col items-center justify-center px-3 py-2 space-y-2">
    <canvas
      ref="canvasRef"
      width="600"
      height="40"
      class="w-full max-h-[36px] rounded-md"
    ></canvas>
  </div>
</template>
