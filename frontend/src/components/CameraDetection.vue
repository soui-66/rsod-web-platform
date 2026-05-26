<template>
  <div class="camera-detection">
    <!-- 摄像头预览区域 -->
    <div class="camera-container">
      <div class="video-wrapper">
        <video ref="videoRef" autoplay muted playsinline class="camera-video"></video>
        <canvas ref="canvasRef" class="detection-canvas"></canvas>
        <canvas ref="captureCanvasRef" class="capture-canvas"></canvas>
        
        <!-- 状态遮罩 -->
        <div v-if="!isRunning" class="status-overlay">
          <div class="status-content">
            <el-icon class="status-icon" :class="statusIconClass"><VideoCamera /></el-icon>
            <p class="status-text">{{ statusText }}</p>
          </div>
        </div>
        
        <!-- 暂停遮罩 -->
        <div v-if="isPaused" class="pause-overlay">
          <div class="pause-content">
            <el-icon class="pause-icon"><VideoPause /></el-icon>
            <p class="pause-text">检测已暂停</p>
          </div>
        </div>
      </div>
      
      <!-- 控制按钮 -->
      <div class="control-panel">
        <el-button 
          v-if="!isRunning" 
          type="primary" 
          size="large" 
          @click="startCameraDetection"
          :loading="isStarting"
        >
          <el-icon><VideoPlay /></el-icon> 开始检测
        </el-button>
        
        <template v-else>
          <el-button 
            type="warning" 
            size="large" 
            @click="togglePause"
          >
            <el-icon v-if="isPaused"><VideoPlay /></el-icon>
            <el-icon v-else><VideoPause /></el-icon>
            {{ isPaused ? '恢复' : '暂停' }}
          </el-button>
          <el-button 
            type="danger" 
            size="large" 
            @click="stopCameraDetection"
          >
            <el-icon><CircleClose /></el-icon> 停止检测
          </el-button>
        </template>
      </div>
    </div>
    
    <!-- 统计信息 -->
    <div class="stats-panel">
      <div class="stat-card">
        <span class="stat-label">帧率</span>
        <span class="stat-value">{{ fps.toFixed(1) }} FPS</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">帧数</span>
        <span class="stat-value">{{ frameIndex }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">目标数</span>
        <span class="stat-value">{{ totalObjects }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">延迟</span>
        <span class="stat-value">{{ (detectionTime * 1000).toFixed(0) }}ms</span>
      </div>
    </div>
    
    <!-- 参数设置 -->
    <div class="settings-panel">
      <el-form :model="settings" label-width="120px">
        <el-form-item label="置信度阈值">
          <el-slider 
            v-model="settings.confidenceThreshold" 
            :min="0.1" 
            :max="0.9" 
            :step="0.05"
            @change="updateSettings"
          />
          <span class="slider-value">{{ settings.confidenceThreshold.toFixed(2) }}</span>
        </el-form-item>
        <el-form-item label="推理间隔">
          <el-slider 
            v-model="settings.inferenceInterval" 
            :min="1" 
            :max="10" 
            :step="1"
            @change="updateSettings"
          />
          <span class="slider-value">{{ settings.inferenceInterval }} 帧</span>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue';
import { VideoCamera, VideoPlay, VideoPause, CircleClose } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { detectFrame, startCameraDetection as apiStart, stopCameraDetection as apiStop } from '../api/detection';

// 定义 emit 事件
const emit = defineEmits(['detection-update']);

// 视频和画布引用
const videoRef = ref(null);
const canvasRef = ref(null);
const captureCanvasRef = ref(null);

// 状态变量
const isRunning = ref(false);
const isPaused = ref(false);
const isStarting = ref(false);
const videoStream = ref(null);

// 检测结果
const currentBoxes = ref([]);
const frameIndex = ref(0);
const fps = ref(0);
const detectionTime = ref(0);
const totalObjects = ref(0);

// 转换检测框格式为统一格式
const formatDetections = (boxes) => {
  return boxes.map(box => ({
    class: box.class_name || box.class,
    confidence: box.confidence,
    bbox: [box.x1, box.y1, box.x2, box.y2],
    chinese_name: box.chinese_name
  }));
};

// 设置参数
const settings = ref({
  confidenceThreshold: 0.5,
  inferenceInterval: 2
});

// 循环ID
let detectionFrameId = null;
let lastDetectionTime = 0;

// 状态图标和文字
const statusIconClass = computed(() => {
  if (isStarting.value) return 'starting';
  return 'stopped';
});

const statusText = computed(() => {
  if (isStarting.value) return '正在启动...';
  return '点击开始按钮启动摄像头检测';
});

// 获取摄像头权限并启动检测
const startCameraDetection = async () => {
  isStarting.value = true;
  
  try {
    // 启动后端检测服务
    const startResponse = await apiStart({
      camera_id: 0,
      confidence_threshold: settings.value.confidenceThreshold,
      inference_interval: settings.value.inferenceInterval
    });
    
    if (!startResponse.success) {
      ElMessage.error(startResponse.message || '启动检测服务失败');
      isStarting.value = false;
      return;
    }
    
    // 请求摄像头权限
    videoStream.value = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        frameRate: { ideal: 30 },
      },
      audio: false,
    });
    
    // 绑定视频流
    if (videoRef.value) {
      videoRef.value.srcObject = videoStream.value;
      videoRef.value.onloadedmetadata = () => {
        initCanvas();
        isRunning.value = true;
        isStarting.value = false;
        startDetectionStream();
      };
    }
  } catch (error) {
    handleCameraError(error);
    isStarting.value = false;
  }
};

// 初始化画布
const initCanvas = () => {
  if (!videoRef.value || !canvasRef.value || !captureCanvasRef.value) return;
  
  const video = videoRef.value;
  const canvas = canvasRef.value;
  const captureCanvas = captureCanvasRef.value;
  
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  captureCanvas.width = video.videoWidth || 640;
  captureCanvas.height = video.videoHeight || 480;
};

// 启动检测流
const startDetectionStream = () => {
  lastDetectionTime = performance.now();
  sendFrameForDetection();
};

// 发送帧进行检测
const sendFrameForDetection = async () => {
  if (!isRunning.value) return;
  
  const currentTime = performance.now();
  const timeSinceLastDetection = currentTime - lastDetectionTime;
  const targetInterval = (settings.value.inferenceInterval * 1000) / 30;
  
  if (!videoRef.value || !captureCanvasRef.value) {
    detectionFrameId = requestAnimationFrame(sendFrameForDetection);
    return;
  }
  
  if (!isPaused.value && timeSinceLastDetection >= targetInterval) {
    try {
      const captureCanvas = captureCanvasRef.value;
      const ctx = captureCanvas.getContext('2d');
      ctx.drawImage(videoRef.value, 0, 0, captureCanvas.width, captureCanvas.height);
      
      const imageData = captureCanvas.toDataURL('image/jpeg', 0.7);
      const response = await detectFrame({ image: imageData });
      
      if (response.success) {
        currentBoxes.value = response.data.boxes || [];
        frameIndex.value = response.data.frame_index || frameIndex.value;
        fps.value = response.data.fps || fps.value;
        detectionTime.value = response.data.detection_time || 0;
        totalObjects.value = response.data.total_objects || 0;
        lastDetectionTime = currentTime;
        drawBoxes();
        
        // 发送检测结果更新事件给父组件
        const formattedDetections = formatDetections(currentBoxes.value);
        emit('detection-update', {
          detections: formattedDetections,
          frameIndex: frameIndex.value,
          fps: fps.value,
          detectionTime: detectionTime.value,
          totalObjects: totalObjects.value
        });
      } else {
        handleDetectionError(response.message);
      }
    } catch (error) {
      handleDetectionError(error.message || '网络请求失败');
    }
  }
  
  drawBoxes();
  detectionFrameId = requestAnimationFrame(sendFrameForDetection);
};

// 绘制检测框
const drawBoxes = () => {
  if (!canvasRef.value || !videoRef.value) return;
  
  const canvas = canvasRef.value;
  const ctx = canvas.getContext('2d');
  const video = videoRef.value;
  
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  const scaleX = canvas.width / video.videoWidth;
  const scaleY = canvas.height / video.videoHeight;
  
  currentBoxes.value.forEach((box) => {
    const x1 = box.x1 * scaleX;
    const y1 = box.y1 * scaleY;
    const x2 = box.x2 * scaleX;
    const y2 = box.y2 * scaleY;
    const width = x2 - x1;
    const height = y2 - y1;
    
    ctx.strokeStyle = getBoxColor(box.class_name);
    ctx.lineWidth = 2;
    ctx.strokeRect(x1, y1, width, height);
    
    ctx.fillStyle = getBoxColor(box.class_name);
    ctx.globalAlpha = 0.1;
    ctx.fillRect(x1, y1, width, height);
    ctx.globalAlpha = 1;
    
    const label = `${box.chinese_name || box.class_name} ${(box.confidence * 100).toFixed(0)}%`;
    ctx.font = '12px Arial';
    ctx.fillStyle = getBoxColor(box.class_name);
    const labelWidth = ctx.measureText(label).width + 8;
    const labelHeight = 16;
    
    if (y1 >= labelHeight) {
      ctx.fillRect(x1, y1 - labelHeight, labelWidth, labelHeight);
      ctx.fillStyle = '#ffffff';
      ctx.fillText(label, x1 + 4, y1 - 4);
    } else {
      ctx.fillRect(x1, y1 + height, labelWidth, labelHeight);
      ctx.fillStyle = '#ffffff';
      ctx.fillText(label, x1 + 4, y1 + height + 12);
    }
  });
};

// 获取检测框颜色
const getBoxColor = (className) => {
  const colorMap = {
    'aircraft': '#ef4444',
    'ship': '#3b82f6',
    'vehicle': '#22c55e',
    'building': '#f59e0b',
    'person': '#a855f7',
    'tree': '#10b981'
  };
  return colorMap[className] || '#667eea';
};

// 切换暂停状态
const togglePause = () => {
  isPaused.value = !isPaused.value;
};

// 停止检测
const stopCameraDetection = async () => {
  try {
    await apiStop();
  } catch (error) {
    console.error('停止检测失败:', error);
  }
  
  isRunning.value = false;
  isPaused.value = false;
  
  if (detectionFrameId) {
    cancelAnimationFrame(detectionFrameId);
    detectionFrameId = null;
  }
  
  if (videoStream.value) {
    videoStream.value.getTracks().forEach(track => track.stop());
    videoStream.value = null;
  }
  
  if (videoRef.value) {
    videoRef.value.srcObject = null;
  }
  
  // 清空检测框和Canvas
  currentBoxes.value = [];
  if (canvasRef.value) {
    const ctx = canvasRef.value.getContext('2d');
    ctx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height);
  }
  
  currentBoxes.value = [];
  frameIndex.value = 0;
  fps.value = 0;
  detectionTime.value = 0;
  totalObjects.value = 0;
  
  ElMessage.success('摄像头检测已停止');
};

// 更新设置
const updateSettings = () => {
  // 设置已通过双向绑定更新
  ElMessage.info('设置已更新，下次检测生效');
};

// 处理摄像头错误
const handleCameraError = (error) => {
  console.error('摄像头错误:', error);
  
  switch (error.name) {
    case 'NotAllowedError':
      ElMessage.error('摄像头权限被拒绝，请在浏览器设置中允许访问');
      break;
    case 'NotFoundError':
      ElMessage.error('未检测到摄像头设备，请检查设备连接');
      break;
    case 'NotReadableError':
      ElMessage.error('摄像头被其他应用占用，请关闭其他应用后重试');
      break;
    default:
      ElMessage.error('无法访问摄像头，请检查设备和权限设置');
  }
};

// 处理检测错误
const handleDetectionError = (message) => {
  console.error('检测错误:', message);
};

// 清理资源
onUnmounted(() => {
  stopCameraDetection();
});
</script>

<style scoped>
.camera-detection {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
}

.camera-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.video-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 4/3;
  background: #000;
  border-radius: 12px;
  overflow: hidden;
}

.camera-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.detection-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.capture-canvas {
  display: none;
}

.status-overlay, .pause-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.7);
}

.status-content, .pause-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.status-icon, .pause-icon {
  font-size: 64px;
  color: #667eea;
}

.status-icon.starting {
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text, .pause-text {
  font-size: 18px;
  color: #fff;
}

.control-panel {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.stats-panel {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: #f8fafc;
  border-radius: 8px;
  padding: 12px;
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
}

.settings-panel {
  background: #f8fafc;
  border-radius: 12px;
  padding: 20px;
}

.slider-value {
  margin-left: 12px;
  font-size: 14px;
  color: #667eea;
  font-weight: 500;
}
</style>