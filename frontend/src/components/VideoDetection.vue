<template>
  <div class="video-detection">
    <!-- 左侧视频面板 - 扩大占比，占据大部分空间 -->
    <div class="video-panel">
      <div class="panel-header">
        <span class="panel-title">视频检测</span>
        <!-- 状态标签 -->
        <el-tag
          :type="getTagType()"
          effect="light"
          class="result-tag"
        >
          <el-icon class="el-icon--left" v-if="isDetecting"><Check /></el-icon>
          <el-icon class="el-icon--left" v-else-if="currentDetection"><CircleCheck /></el-icon>
          <el-icon class="el-icon--left" v-else><Upload /></el-icon>
          {{ getTagText() }}
        </el-tag>
      </div>

      <div class="video-container">
        <div v-if="!hasVideo" class="video-placeholder" @click="triggerFileInput">
          <el-icon class="placeholder-icon"><Monitor /></el-icon>
          <p class="placeholder-text">点击上传视频</p>
          <p class="placeholder-desc">支持 mp4、avi、mov 等格式</p>
          <input
            type="file"
            accept="video/*"
            class="video-file-input"
            @change="handleVideoUpload"
          />
        </div>

        <div v-else class="video-content">
          <div class="video-player-wrapper">
            <!-- 隐藏的视频元素用于捕获帧 -->
            <video
              ref="videoRef"
              :src="originalVideoUrl"
              class="video-player"
              controls
              @loadedmetadata="onVideoLoaded"
              @timeupdate="onTimeUpdate"
              @ended="onVideoEnded"
            />
            <!-- Canvas 用于绘制检测框 -->
            <canvas
              ref="canvasRef"
              class="detection-canvas"
              :class="{ 'canvas-active': isDetecting || currentDetection }"
            />
          </div>

          <!-- 实时检测统计 -->
          <div v-if="isDetecting" class="realtime-stats">
            <div class="stat-item">
              <span class="stat-label">当前帧</span>
              <span class="stat-value">{{ currentFrameIndex }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">检测目标</span>
              <span class="stat-value highlight">{{ currentDetection?.total_objects || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">检测耗时</span>
              <span class="stat-value">{{ (currentDetection?.detection_time || 0) * 1000 }}ms</span>
            </div>
          </div>

          <div class="video-info">
            <div class="info-row">
              <span class="info-label">视频时长</span>
              <span class="info-value">{{ formatDuration(videoDuration) }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">当前时间</span>
              <span class="info-value">{{ formatDuration(currentTime) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 检测设置 - 移到视频下方 -->
      <div class="settings-panel">
        <div class="settings-header">
          <el-icon><Setting /></el-icon>
          <span class="settings-title">检测设置</span>
        </div>
        <div class="settings-content">
          <!-- 参数设置 -->
          <div class="param-section">
            <div class="param-item">
              <span class="param-label">检测帧率: {{ detectionFPS }} fps</span>
              <el-slider
                v-model="detectionFPS"
                :min="2"
                :max="15"
                :step="1"
                :disabled="isDetecting"
              />
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="action-buttons">
            <el-button
              size="default"
              class="btn-upload"
              @click="triggerFileInput"
              :disabled="isDetecting"
            >
              <el-icon><Upload /></el-icon>
              上传视频
            </el-button>
            <el-button
              v-if="!isDetecting"
              type="primary"
              size="default"
              class="btn-detect"
              :disabled="!hasVideo"
              @click="performVideoDetection"
            >
              <el-icon><Refresh /></el-icon>
              开始检测
            </el-button>
            <el-button
              v-else
              type="danger"
              size="default"
              class="btn-stop"
              @click="stopRealtimeDetection"
            >
              <el-icon><VideoPause /></el-icon>
              停止检测
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧保持为空，使用页面原有的检测信息面板 -->
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted, nextTick } from "vue";
import { ElMessage } from "element-plus";
import {
  Monitor,
  Upload,
  Check,
  CircleCheck,
  Refresh,
  VideoPause,
  Setting,
} from "@element-plus/icons-vue";
import { detectVideo, detectRealtimeFrame } from "../api/detection";

// 定义事件发射器，向父组件传递检测结果
const emit = defineEmits(['detection-update']);

// 视频相关状态
const videoRef = ref(null);
const canvasRef = ref(null);
const hasVideo = ref(false);
const originalVideoUrl = ref(null);
const videoDuration = ref(0);
const currentTime = ref(0);
const currentFrameIndex = ref(0);

// 定义 props，接收从父组件传来的置信度阈值
const props = defineProps({
  confidenceThreshold: {
    type: Number,
    default: 0.25
  }
});

// 检测相关状态
const isDetecting = ref(false);
const currentDetection = ref(null);

// 检测参数
const iouThreshold = ref(0.7);
const detectionFPS = ref(5); // 实时检测的帧率

// 计算属性
const hasDetectionResult = computed(() => currentDetection.value !== null);

// 定时器和动画帧
let detectionTimer = null;
let canvasContext = null;
let animationFrameId = null;

// 保存上一帧检测结果，用于插值显示
let lastBoxes = [];
let lastVideoWidth = 0;
let lastVideoHeight = 0;
let isProcessingFrame = false; // 防止同时处理多帧

// 辅助函数
const formatDuration = (seconds) => {
  if (!seconds || seconds <= 0) return "--:--";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
};

const getTagType = () => {
  if (isDetecting.value) return 'success';
  if (currentDetection.value) return 'info';
  return 'info';
};

const getTagText = () => {
  if (isDetecting.value) return '实时检测中';
  if (currentDetection.value) return '实时检测已结束';
  return '等待检测';
};

// 获取当前检测结果（用于传给父组件）
const getCurrentDetections = computed(() => {
  if (currentDetection.value) {
    return currentDetection.value.boxes?.map(box => ({
      class: box.chinese_name || box.class_name,
      confidence: box.confidence
    })) || [];
  }
  return [];
});

// 视频上传
const triggerFileInput = () => {
  const input = document.querySelector(".video-file-input");
  if (input) {
    input.click();
  }
};

const handleVideoUpload = async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;

  try {
    // 清理之前的 URL，防止内存泄漏
    if (originalVideoUrl.value) {
      URL.revokeObjectURL(originalVideoUrl.value);
    }

    originalVideoUrl.value = URL.createObjectURL(file);
    hasVideo.value = true;
    detectionResult.value = null;
    currentDetection.value = null;
    currentFrameIndex.value = 0;
    currentTime.value = 0;

    // 等待视频元素挂载
    await nextTick();

    const video = videoRef.value;
    if (video) {
      // 监听视频元数据加载
      video.onloadedmetadata = () => {
        videoDuration.value = video.duration;
      };

      // 监听视频加载错误
      video.onerror = () => {
        console.error("视频加载错误");
        ElMessage.error("视频加载失败");
        hasVideo.value = false;
      };
    }
  } catch (error) {
    console.error("视频加载失败:", error);
    ElMessage.error("视频加载失败");
  }
};

// 视频事件处理
const onVideoLoaded = () => {
  const video = videoRef.value;
  if (video) {
    videoDuration.value = video.duration;

    // 初始化 Canvas
    nextTick(() => {
      initCanvas();
    });
  }
};

const onTimeUpdate = () => {
  const video = videoRef.value;
  if (video) {
    currentTime.value = video.currentTime;
  }
};

const onVideoEnded = () => {
  if (isDetecting.value) {
    stopRealtimeDetection();
    ElMessage.success("视频播放完成，检测结束");
  }
};

// Canvas 相关（优化版）
const initCanvas = () => {
  const video = videoRef.value;
  const canvas = canvasRef.value;

  if (!video || !canvas) return;

  // 设置 Canvas 尺寸与视频显示尺寸一致，确保坐标对齐
  const displayWidth = video.clientWidth || video.offsetWidth;
  const displayHeight = video.clientHeight || video.offsetHeight;
  canvas.width = displayWidth;
  canvas.height = displayHeight;

  // 获取 Canvas 2D 上下文
  canvasContext = canvas.getContext('2d');

  // 清空 Canvas
  canvasContext.clearRect(0, 0, canvas.width, canvas.height);
};

const clearCanvas = () => {
  if (!canvasContext || !canvasRef.value) return;
  canvasContext.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height);
};

const drawDetectionBoxes = (boxes, videoWidth, videoHeight, interpolate = false) => {
  if (!canvasContext || !canvasRef.value || !videoRef.value) return;

  const canvas = canvasRef.value;
  const video = videoRef.value;

  // 确保 Canvas 尺寸与视频显示尺寸一致（动态调整）
  const displayWidth = video.clientWidth || video.offsetWidth;
  const displayHeight = video.clientHeight || video.offsetHeight;

  if (canvas.width !== displayWidth || canvas.height !== displayHeight) {
    canvas.width = displayWidth;
    canvas.height = displayHeight;
  }

  // 计算缩放比例：视频原始尺寸 -> 显示尺寸
  const scaleX = displayWidth / videoWidth;
  const scaleY = displayHeight / videoHeight;

  // 清空画布
  canvasContext.clearRect(0, 0, displayWidth, displayHeight);

  // 如果需要插值且有上一帧数据，使用上一帧数据保持显示
  let boxesToDraw = boxes;
  if (interpolate && lastBoxes.length > 0) {
    boxesToDraw = lastBoxes;
    videoWidth = lastVideoWidth;
    videoHeight = lastVideoHeight;
  }

  // 颜色映射
  const colorMap = {
    'aircraft': '#FF6B6B',
    'oiltank': '#4ECDC4',
    'overpass': '#45B7D1',
    'playground': '#96CEB4',
  };

  // 绘制每个检测框
  boxesToDraw.forEach((box) => {
    const x1 = box.x1 * scaleX;
    const y1 = box.y1 * scaleY;
    const x2 = box.x2 * scaleX;
    const y2 = box.y2 * scaleY;
    const color = colorMap[box.class_name] || '#FF6B6B';

    // 绘制边框
    canvasContext.strokeStyle = color;
    canvasContext.lineWidth = 2;
    canvasContext.strokeRect(x1, y1, x2 - x1, y2 - y1);

    // 绘制标签背景
    canvasContext.fillStyle = color;
    const label = `${box.chinese_name || box.class_name} ${(box.confidence * 100).toFixed(0)}%`;
    const labelWidth = canvasContext.measureText(label).width + 10;
    canvasContext.fillRect(x1, y1 - 20, labelWidth, 20);

    // 绘制标签文字
    canvasContext.fillStyle = '#FFFFFF';
    canvasContext.font = '14px Arial';
    canvasContext.fillText(label, x1 + 5, y1 - 5);
  });

  // 保存当前帧数据（只有真实检测时才更新）
  if (!interpolate) {
    lastBoxes = boxes;
    lastVideoWidth = videoWidth;
    lastVideoHeight = videoHeight;
  }
};

// 实时检测核心逻辑（优化版）
const captureAndDetectFrame = async () => {
  const video = videoRef.value;
  if (!video || video.paused || video.ended || isProcessingFrame) return;

  isProcessingFrame = true;

  try {
    // 创建临时 Canvas 捕获当前帧 - 保持原图尺寸，确保坐标准确
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = video.videoWidth;
    tempCanvas.height = video.videoHeight;
    const ctx = tempCanvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    // 转换为 Blob - 适度压缩以平衡质量和速度
    const blob = await new Promise((resolve) => {
      tempCanvas.toBlob((b) => resolve(b), 'image/jpeg', 0.6);
    });

    if (!blob) {
      isProcessingFrame = false;
      return;
    }

    // 发送到后端检测 - 使用 props 中的置信度阈值
    const formData = new FormData();
    formData.append('file', blob, 'frame.jpg');
    formData.append('confidence_threshold', props.confidenceThreshold.toString());
    formData.append('iou_threshold', iouThreshold.value.toString());

    const response = await detectRealtimeFrame(formData);

    if (response.data && response.data.success && response.data.data) {
      currentDetection.value = response.data.data;

      // 向父组件发送检测结果更新
      emit('detection-update', {
        detections: getCurrentDetections.value,
        frameIndex: currentFrameIndex.value,
        fps: detectionFPS.value,
        detectionTime: response.data.data.detection_time,
        totalObjects: response.data.data.total_objects
      });

      // 直接使用后端返回的检测框，不需要缩放（因为我们保持了原图尺寸）
      const boxes = response.data.data.boxes || [];

      // 在 Canvas 上绘制检测框
      drawDetectionBoxes(boxes, response.data.data.image_width, response.data.data.image_height);

      // 更新帧计数
      currentFrameIndex.value++;
    }
  } catch (error) {
    console.error('帧检测失败:', error);
  } finally {
    isProcessingFrame = false;
  }
};

const animateCanvas = () => {
  if (!isDetecting.value) return;

  const video = videoRef.value;
  // 在动画帧中持续绘制上一帧的检测结果，保持视觉流畅
  if (video && !video.paused && !video.ended && lastBoxes.length > 0 && lastVideoWidth > 0) {
    drawDetectionBoxes([], lastVideoWidth, lastVideoHeight, true);
  }

  // 继续下一帧动画
  animationFrameId = requestAnimationFrame(animateCanvas);
};

const startRealtimeDetection = async () => {
  const video = videoRef.value;
  if (!video) {
    ElMessage.error("视频未加载");
    return;
  }

  // 确保视频已加载
  if (video.readyState < 2) {
    ElMessage.info("正在加载视频，请稍候...");
    await new Promise((resolve) => {
      video.onloadeddata = resolve;
      video.onerror = () => {
        ElMessage.error("视频加载失败");
        resolve();
      };
      // 超时处理
      setTimeout(resolve, 10000);
    });
  }

  if (video.readyState < 2) {
    ElMessage.error("视频加载失败");
    return;
  }

  isDetecting.value = true;
  currentDetection.value = null;
  currentFrameIndex.value = 0;
  lastBoxes = []; // 重置上一帧数据
  isProcessingFrame = false;

  // 初始化 Canvas
  nextTick(() => {
    initCanvas();
    clearCanvas();
  });

  // 延迟一点再开始播放，确保 Canvas 已初始化
  await nextTick();

  // 自动播放视频
  try {
    await video.play();
    ElMessage.success("开始实时检测");
  } catch (err) {
    console.error("播放失败:", err);
    ElMessage.warning("自动播放被阻止，请手动点击播放");
  }

  // 启动动画循环，保持检测框持续显示
  animateCanvas();

  // 设置定时器定期捕获帧
  const intervalMs = Math.floor(1000 / detectionFPS.value);
  detectionTimer = setInterval(captureAndDetectFrame, intervalMs);
};

const stopRealtimeDetection = () => {
  const video = videoRef.value;

  // 停止定时器
  if (detectionTimer) {
    clearInterval(detectionTimer);
    detectionTimer = null;
  }

  // 停止动画循环
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
  }

  // 暂停视频
  if (video) {
    video.pause();
  }

  isDetecting.value = false;

  // 清空 Canvas 和数据
  clearCanvas();
  lastBoxes = [];
  isProcessingFrame = false;
};

const performVideoDetection = async () => {
  if (!originalVideoUrl.value) {
    ElMessage.warning("请先上传视频");
    return;
  }

  // 直接开始实时检测
  startRealtimeDetection();
};



// 组件卸载时清理
onUnmounted(() => {
  stopRealtimeDetection();
  if (originalVideoUrl.value) {
    URL.revokeObjectURL(originalVideoUrl.value);
  }
});
</script>

<style scoped>
.video-detection {
  display: flex;
  height: 100%;
}

/* 左侧视频面板 - 占据全部空间 */
.video-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.result-tag {
  font-size: 12px;
}

.video-container {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  min-height: 500px;
}

.video-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.video-placeholder:hover {
  border-color: #409EFF;
  background: rgba(64, 158, 255, 0.05);
}

.placeholder-icon {
  font-size: 80px;
  color: #909399;
  margin-bottom: 16px;
}

.placeholder-text {
  font-size: 18px;
  color: #606266;
  margin: 8px 0;
}

.placeholder-desc {
  font-size: 14px;
  color: #909399;
}

.video-file-input {
  display: none;
}

.video-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
}

.video-player-wrapper {
  position: relative;
  width: 100%;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  flex: 1;
  min-height: 450px;
}

.video-player {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: contain;
}

.detection-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s;
}

.detection-canvas.canvas-active {
  opacity: 1;
}

.realtime-stats {
  display: flex;
  gap: 32px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: #fff;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 12px;
  opacity: 0.8;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
}

.stat-value.highlight {
  color: #ffd04b;
}

.video-info {
  display: flex;
  gap: 32px;
  padding: 12px 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-label {
  color: #909399;
  font-size: 14px;
}

.info-value {
  color: #303133;
  font-size: 14px;
  font-weight: 500;
}

/* 检测设置面板 - 放在视频下方 */
.settings-panel {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.settings-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.settings-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.settings-content {
  display: flex;
  align-items: center;
  gap: 32px;
  flex-wrap: wrap;
}

.mode-selection {
  display: flex;
  gap: 24px;
}

.param-section {
  display: flex;
  gap: 24px;
  flex: 1;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 200px;
}

.param-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.btn-upload, .btn-detect, .btn-stop {
  min-width: 120px;
}
</style>
