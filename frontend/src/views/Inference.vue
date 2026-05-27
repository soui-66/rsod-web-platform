<template>
  <div class="detection-page">
    <!-- 顶部标题区 -->
    <div class="page-header">
      <h1>🎯 上传遥感影像，立即识别多类目标</h1>
      <p>支持飞机 / 油罐 / 操场 / 建筑物 / 船舶 / 农业虫害 等多目标检测</p>
    </div>

    <!-- 模式选择区 -->
    <div class="mode-section">
      <div class="mode-label">模式选择</div>
      <div class="mode-cards">
        <div
          v-for="mode in detectionModes"
          :key="mode.key"
          class="mode-card"
          :class="{
            active: currentMode === mode.key,
            disabled: mode.disabled
          }"
          @click="!mode.disabled && (currentMode = mode.key)"
        >
          <el-icon class="mode-icon"><component :is="mode.icon" /></el-icon>
          <span class="mode-name">{{ mode.name }}</span>
        </div>
      </div>
    </div>

    <!-- 置信度阈值设置 -->
    <div class="threshold-section">
      <div class="threshold-label">
        <el-icon><Aim /></el-icon> 置信度阈值
      </div>
      <div class="threshold-slider">
        <el-slider 
          v-model="confidenceThreshold" 
          :min="0.1" 
          :max="0.9" 
          :step="0.05"
          :show-stops="true"
          :show-input="true"
        />
      </div>
      <div class="threshold-info">
        当前阈值: <span class="threshold-value">{{ (confidenceThreshold * 100).toFixed(0) }}%</span>
        <span class="threshold-hint">低于此阈值的检测结果将被过滤</span>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧：上传/检测区 -->
      <div class="left-panel">
        <!-- 单图检测模式 -->
        <template v-if="currentMode === 'single'">
          <div v-if="!hasFile" class="upload-area">
            <el-upload
              class="upload-box"
              drag
              action="#"
              :auto-upload="false"
              :on-change="handleFileChange"
              :show-file-list="false"
              accept="image/*"
            >
              <div class="upload-content">
                <el-icon class="upload-icon"><Upload /></el-icon>
                <p class="upload-main">点击或拖拽图片到此处</p>
                <p class="upload-sub">支持 JPG / PNG / WEBP 格式</p>
              </div>
            </el-upload>
          </div>

          <div v-else-if="!isDetected" class="preview-area">
            <div class="preview-header">
              <span class="preview-label">
                <el-icon><Picture /></el-icon> 待检测图片
              </span>
              <el-button type="danger" size="small" text @click="clearFile">
                <el-icon><Delete /></el-icon> 移除
              </el-button>
            </div>
            <div class="image-container">
              <img :src="previewUrl" alt="待检测图片" />
            </div>
            <div class="preview-info">
              <span>文件名：{{ fileName }}</span>
              <span>大小：{{ fileSize }}</span>
            </div>
            <el-button
              type="primary"
              size="large"
              class="detect-btn"
              :loading="loading"
              @click="handleInference"
            >
              {{ loading ? "检测中..." : "🚀 开始检测" }}
            </el-button>
          </div>

          <div v-else class="compare-area">
            <div class="compare-header">
              <span class="compare-label">📊 检测结果对比</span>
              <div class="view-toggle">
                <span
                  class="toggle-btn"
                  :class="{ active: viewMode === 'side' }"
                  @click="viewMode = 'side'"
                >并排</span>
                <span
                  class="toggle-btn"
                  :class="{ active: viewMode === 'grid' }"
                  @click="viewMode = 'grid'"
                >栅格</span>
              </div>
            </div>
            <div class="compare-images" :class="viewMode">
              <div class="compare-item">
                <div class="compare-item-label">原始图片</div>
                <div class="image-container">
                  <img :src="previewUrl" alt="原图" />
                </div>
              </div>
              <div class="compare-item">
                <div class="compare-item-label success">✅ 检测结果</div>
                <div class="image-container">
                  <img :src="resultImageUrl" alt="检测结果" />
                </div>
              </div>
            </div>
            <div class="action-buttons">
              <el-button @click="resetDetection" size="large">
                <el-icon><Refresh /></el-icon> 重新检测
              </el-button>
              <el-button type="primary" size="large">
                <el-icon><Document /></el-icon> 查看完整报告
              </el-button>
            </div>
          </div>
        </template>

        <!-- 批量检测模式 -->
        <template v-if="currentMode === 'batch'">
          <!-- 上传区域 -->
          <div v-if="batchFiles.length === 0" class="upload-area">
            <div class="batch-upload-wrapper">
              <el-upload
                class="upload-box"
                drag
                action="#"
                :auto-upload="false"
                :on-change="handleBatchFileChange"
                :show-file-list="false"
                multiple
                accept="image/*"
              >
                <div class="upload-content">
                  <el-icon class="upload-icon"><Upload /></el-icon>
                  <p class="upload-main">点击或拖拽图片到此处</p>
                  <p class="upload-sub">支持 JPG / PNG / WEBP 格式</p>
                </div>
              </el-upload>
              <div class="upload-divider">
                <span>或</span>
              </div>
              <div class="folder-select-area" @click="triggerFolderSelect">
                <el-icon class="folder-icon"><FolderOpened /></el-icon>
                <p class="folder-main">选择文件夹</p>
                <p class="folder-sub">自动识别文件夹中的所有图片</p>
              </div>
              <input
                ref="folderInput"
                type="file"
                webkitdirectory
                mozdirectory
                directory
                multiple
                class="hidden-file-input"
                @change="handleFolderInputChange"
              />
            </div>
          </div>

          <!-- 已上传文件列表 -->
          <div v-else-if="batchResults.length === 0" class="batch-preview">
            <div class="batch-header">
              <span class="batch-label">
                <el-icon><PictureRounded /></el-icon> 已选择 {{ batchFiles.length }} 张图片
              </span>
              <div class="batch-header-actions">
                <el-button type="primary" size="small" text @click="triggerAddMore">
                  <el-icon><Plus /></el-icon> 添加更多
                </el-button>
                <el-button type="danger" size="small" text @click="clearBatchFiles">
                  <el-icon><Delete /></el-icon> 清空
                </el-button>
              </div>
            </div>
            <div class="batch-grid">
              <div
                v-for="(file, index) in batchFiles"
                :key="index"
                class="batch-item"
              >
                <img :src="file.preview" :alt="file.name" />
                <div class="batch-item-info">
                  <span class="batch-item-name">{{ file.name }}</span>
                  <el-button type="text" size="small" class="batch-item-remove" @click="removeBatchFile(index)">
                    <el-icon><Close /></el-icon>
                  </el-button>
                </div>
              </div>
              <div class="batch-add-more" @click="triggerAddMore">
                <el-icon class="add-icon"><Plus /></el-icon>
                <span class="add-text">添加图片</span>
              </div>
            </div>
            <input
              ref="batchFileInput"
              type="file"
              multiple
              accept="image/*"
              class="hidden-file-input"
              @change="handleBatchFileInputChange"
            />
            <el-button
              type="primary"
              size="large"
              class="detect-btn"
              :loading="batchLoading"
              @click="handleBatchInference"
            >
              {{ batchLoading ? "批量检测中..." : "🚀 批量检测" }}
            </el-button>
          </div>

          <!-- 批量检测结果 -->
          <div v-else class="batch-results">
            <div class="batch-header">
              <span class="batch-label">
                <el-icon><CircleCheck /></el-icon> 批量检测完成
              </span>
              <div class="batch-stats">
                <span class="stat-item">图片: {{ batchTotalImages }}</span>
                <span class="stat-item">目标: {{ batchTotalTargets }}</span>
                <span class="stat-item">耗时: {{ batchDuration }}s</span>
              </div>
            </div>
            <div class="batch-results-grid">
              <div
                v-for="(result, index) in batchResults"
                :key="index"
                class="result-card"
              >
                <div class="result-header">
                  <span class="result-name">{{ result.file_name }}</span>
                  <span class="result-count">检测到 {{ result.target_count }} 个目标</span>
                </div>
                <div class="result-images">
                  <div class="result-image-item">
                    <span class="image-label">原图</span>
                    <img :src="result.original_url" :alt="result.file_name" />
                  </div>
                  <div class="result-image-item">
                    <span class="image-label success">结果</span>
                    <img :src="result.image_url" :alt="result.file_name" />
                  </div>
                </div>
                <div v-if="result.detections && result.detections.length > 0" class="result-detections">
                  <div
                    v-for="(det, detIndex) in result.detections.slice(0, 5)"
                    :key="detIndex"
                    class="mini-detection"
                  >
                    <span class="mini-class">{{ det.class }}</span>
                    <span class="mini-conf">{{ (det.confidence * 100).toFixed(0) }}%</span>
                  </div>
                  <div v-if="result.detections.length > 5" class="mini-more">
                    +{{ result.detections.length - 5 }} 更多
                  </div>
                </div>
              </div>
            </div>
            <div class="action-buttons">
              <el-button @click="resetBatchDetection" size="large">
                <el-icon><Refresh /></el-icon> 重新检测
              </el-button>
              <el-button type="primary" size="large">
                <el-icon><Download /></el-icon> 导出报告
              </el-button>
            </div>
          </div>
        </template>

        <!-- 摄像头检测模式 -->
        <template v-if="currentMode === 'camera'">
          <CameraDetection @detection-update="handleCameraDetectionUpdate" />
        </template>

        <!-- 视频检测模式 -->
        <template v-if="currentMode === 'video'">
          <!-- 视频上传 -->
          <div v-if="!videoFile" class="upload-area">
            <div class="upload-box-wrapper">
              <el-upload
                class="upload-box"
                drag
                action="#"
                :auto-upload="false"
                :show-file-list="false"
                :disabled="true"
              >
                <div class="upload-content">
                  <el-icon class="upload-icon"><VideoCamera /></el-icon>
                  <p class="upload-main">点击或拖拽视频到此处</p>
                  <p class="upload-sub">支持 MP4 / AVI / MOV 格式</p>
                </div>
              </el-upload>
              <div 
                class="upload-overlay"
                @click="triggerVideoSelect"
              ></div>
            </div>
            <input
              ref="videoFileInput"
              type="file"
              accept="video/*"
              class="hidden-file-input"
              @change="handleVideoFileChange"
            />
          </div>

          <!-- 视频预览和检测 -->
          <div v-else-if="!videoOutputUrl" class="video-preview">
            <div class="batch-header">
              <span class="batch-label">
                <el-icon><VideoCamera /></el-icon> 待检测视频: {{ videoFile.name }}
              </span>
              <div class="batch-header-actions">
                <el-button type="danger" size="small" text @click="resetVideoDetection">
                  <el-icon><Delete /></el-icon> 移除
                </el-button>
              </div>
            </div>
            <div class="video-container">
              <video :src="videoPreviewUrl" controls class="video-player"></video>
            </div>
            <el-button
              type="primary"
              size="large"
              class="detect-btn"
              :loading="videoLoading"
              @click="handleVideoInference"
            >
              {{ videoLoading ? "视频检测中..." : "🚀 开始检测" }}
            </el-button>
          </div>

          <!-- 视频检测结果 - 显示带有识别框的完整视频 -->
          <div v-else class="video-results">
            <div class="batch-header">
              <span class="batch-label">
                <el-icon><CircleCheck /></el-icon> 视频检测完成
              </span>
              <div class="batch-stats">
                <span class="stat-item">帧数: {{ videoTotalFrames }}</span>
                <span class="stat-item">目标: {{ videoTotalTargets }}</span>
                <span class="stat-item">耗时: {{ videoDuration }}s</span>
              </div>
            </div>
            <div class="video-container result-video">
              <video 
                :key="videoOutputUrl"
                :src="videoOutputUrl" 
                controls 
                class="video-player result-player"
                crossOrigin="anonymous"
                @error="handleVideoError"
                @loadedmetadata="handleVideoLoaded"
              ></video>
            </div>
            <div class="video-info-panel">
              <div class="info-title">检测结果摘要</div>
              <div class="info-content">
                <div class="info-item">
                  <span class="info-label">处理帧数</span>
                  <span class="info-value">{{ videoTotalFrames }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">检测目标</span>
                  <span class="info-value">{{ videoTotalTargets }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">处理耗时</span>
                  <span class="info-value">{{ videoDuration }}s</span>
                </div>
              </div>
            </div>
            <div class="action-buttons">
              <el-button @click="resetVideoDetection" size="large">
                <el-icon><Refresh /></el-icon> 重新检测
              </el-button>
            </div>
          </div>
        </template>
      </div>

      <!-- 右侧：结果面板 -->
      <div class="right-panel">
        <div class="result-card">
          <div class="card-section">
            <h3 class="section-title">
              <el-icon><InfoFilled /></el-icon> 检测信息
            </h3>
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">检测模型</span>
                <span class="info-value">yolo11n</span>
              </div>
              <div class="info-item">
                <span class="info-label">模型版本</span>
                <span class="info-value">v1.0.0</span>
              </div>
              <div class="info-item">
                <span class="info-label">检测耗时</span>
                <span class="info-value highlight">{{ currentInferenceTime }}s</span>
              </div>
            </div>
          </div>

          <div class="card-section">
            <h3 class="section-title">
              <el-icon><Aim /></el-icon> 识别清单 ({{ getCurrentDetectionsCount }})
            </h3>
            <div v-if="getCurrentDetections.length === 0" class="empty-state">
              <el-icon :size="32" color="#ddd"><PictureFilled /></el-icon>
              <p>暂无检测结果</p>
            </div>
            <div v-else class="detection-list">
              <div
                v-for="(item, index) in getCurrentDetections"
                :key="index"
                class="detection-item"
              >
                <div class="item-top">
                  <span class="item-class">{{ item.class }}</span>
                  <span class="item-conf">{{ (item.confidence * 100).toFixed(1) }}%</span>
                </div>
                <div class="progress-bar">
                  <div
                    class="progress-fill"
                    :style="{ width: item.confidence * 100 + '%' }"
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <div class="card-section">
            <h3 class="section-title">
              <el-icon><MagicStick /></el-icon> AI 诊断建议
            </h3>
            <div class="ai-advice">
              <template v-if="getCurrentDetections.length > 0">
                <p>检测到 <strong>{{ getCurrentDetections.length }}</strong> 个目标</p>
                <p>最高置信度：<strong>{{ currentMaxConfidence }}%</strong></p>
                <p>最低置信度：<strong>{{ currentMinConfidence }}%</strong></p>
              </template>
              <template v-else>
                <p>上传图片即可开始检测</p>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import axios from "axios";
import { ElMessage } from "element-plus";
import CameraDetection from "../components/CameraDetection.vue";
import { getUserId } from "../utils/user.js";
import {
  Upload,
  Picture,
  Delete,
  Refresh,
  Document,
  FolderOpened,
  VideoCamera,
  InfoFilled,
  Aim,
  MagicStick,
  PictureFilled,
  PictureRounded,
  CircleCheck,
  Download,
  Plus,
  Close,
  Camera,
} from "@element-plus/icons-vue";

const currentMode = ref("single");
const viewMode = ref("side");
const selectedFile = ref(null);
const previewUrl = ref("");
const resultImageUrl = ref("");
const detections = ref([]);
const inferenceTime = ref("0.000");
const loading = ref(false);
const isDetected = ref(false);
const hasFile = computed(() => selectedFile.value !== null);

// 置信度阈值
const confidenceThreshold = ref(0.25);

// 批量检测相关状态
const batchFiles = ref([]);
const batchResults = ref([]);
const batchLoading = ref(false);
const batchTotalImages = ref(0);
const batchTotalTargets = ref(0);
const batchDuration = ref(0);
const batchFileInput = ref(null);
const folderInput = ref(null);

// 视频检测相关状态
const videoFile = ref(null);
const videoPreviewUrl = ref("");
const videoOutputUrl = ref("");
const videoResults = ref([]);
const videoLoading = ref(false);
const videoDuration = ref(0);
const videoTotalFrames = ref(0);
const videoTotalTargets = ref(0);
const videoFileInput = ref(null);

// 摄像头检测相关状态
const cameraDetections = ref([]);
const cameraFrameIndex = ref(0);
const cameraFps = ref(0);
const cameraDetectionTime = ref(0);
const cameraTotalObjects = ref(0);

const detectionModes = [
  { key: "single", icon: "Picture", name: "单图检测", disabled: false },
  { key: "batch", icon: "FolderOpened", name: "批量检测", disabled: false },
  { key: "camera", icon: "Camera", name: "摄像头检测", disabled: false },
  { key: "video", icon: "VideoCamera", name: "视频检测", disabled: false },
];

const fileName = computed(() => {
  return selectedFile.value ? selectedFile.value.name : "";
});

const fileSize = computed(() => {
  if (!selectedFile.value) return "";
  const size = selectedFile.value.size;
  if (size < 1024) return size + " B";
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + " KB";
  return (size / (1024 * 1024)).toFixed(1) + " MB";
});

const maxConfidence = computed(() => {
  if (detections.value.length === 0) return "0";
  return Math.max(...detections.value.map((d) => d.confidence * 100)).toFixed(1);
});

const minConfidence = computed(() => {
  if (detections.value.length === 0) return "0";
  return Math.min(...detections.value.map((d) => d.confidence * 100)).toFixed(1);
});

// 处理摄像头检测更新
const handleCameraDetectionUpdate = (data) => {
  cameraDetections.value = data.detections || [];
  cameraFrameIndex.value = data.frameIndex || 0;
  cameraFps.value = data.fps || 0;
  cameraDetectionTime.value = data.detectionTime || 0;
  cameraTotalObjects.value = data.totalObjects || 0;
};

// 获取当前模式的检测结果
const getCurrentDetections = computed(() => {
  console.log("getCurrentDetections - currentMode:", currentMode.value);
  
  if (currentMode.value === 'single') {
    return detections.value;
  } else if (currentMode.value === 'batch') {
    const allDetections = [];
    batchResults.value.forEach(result => {
      if (result.detections) {
        result.detections.forEach(det => {
          allDetections.push({
            ...det,
            fileName: result.file_name
          });
        });
      }
    });
    return allDetections;
  } else if (currentMode.value === 'video') {
    // 视频检测：合并所有帧的检测结果
    console.log("videoResults.length:", videoResults.value.length);
    const allDetections = [];
    videoResults.value.forEach(result => {
      console.log("processing frame:", result.frame_index, "detections:", result.detections?.length);
      if (result.detections) {
        result.detections.forEach(det => {
          allDetections.push({
            ...det,
            frameIndex: result.frame_index
          });
        });
      }
    });
    console.log("total video detections:", allDetections.length);
    return allDetections;
  } else if (currentMode.value === 'camera') {
    // 摄像头检测：返回当前帧的检测结果
    return cameraDetections.value;
  }
  return [];
});

const getCurrentDetectionsCount = computed(() => {
  return getCurrentDetections.value.length;
});

const currentMaxConfidence = computed(() => {
  const currentDetections = getCurrentDetections.value;
  if (currentDetections.length === 0) return "0";
  return Math.max(...currentDetections.map((d) => d.confidence * 100)).toFixed(1);
});

const currentMinConfidence = computed(() => {
  const currentDetections = getCurrentDetections.value;
  if (currentDetections.length === 0) return "0";
  return Math.min(...currentDetections.map((d) => d.confidence * 100)).toFixed(1);
});

const currentInferenceTime = computed(() => {
  if (currentMode.value === 'single') {
    return inferenceTime.value;
  } else if (currentMode.value === 'batch') {
    return batchDuration.value;
  } else if (currentMode.value === 'video') {
    return videoDuration.value;
  }
  return "0.000";
});

const handleFileChange = (uploadFile) => {
  selectedFile.value = uploadFile.raw;
  isDetected.value = false;
  resultImageUrl.value = "";
  detections.value = [];
  previewUrl.value = URL.createObjectURL(uploadFile.raw);
};

const handleBatchFileChange = (uploadFile, fileList) => {
  // 获取当前已有的文件名集合
  const existingNames = new Set(batchFiles.value.map(f => f.name));
  
  // 找出新增的文件
  const newFiles = fileList.filter(f => !existingNames.has(f.name));
  
  // 为新增文件创建预览并添加到列表
  newFiles.forEach(f => {
    batchFiles.value.push({
      name: f.name,
      raw: f.raw,
      preview: URL.createObjectURL(f.raw),
      size: f.size
    });
  });
};

const triggerAddMore = () => {
  batchFileInput.value?.click();
};

const handleBatchFileInputChange = (event) => {
  const files = Array.from(event.target.files);
  const existingNames = new Set(batchFiles.value.map(f => f.name));
  
  files.forEach(f => {
    if (!existingNames.has(f.name)) {
      batchFiles.value.push({
        name: f.name,
        raw: f,
        preview: URL.createObjectURL(f),
        size: f.size
      });
    }
  });
  
  // 清空 input 以便下次选择
  event.target.value = "";
};

const removeBatchFile = (index) => {
  const file = batchFiles.value[index];
  URL.revokeObjectURL(file.preview);
  batchFiles.value.splice(index, 1);
};

const clearBatchFiles = () => {
  batchFiles.value.forEach(f => URL.revokeObjectURL(f.preview));
  batchFiles.value = [];
  batchResults.value = [];
};

const handleBatchInference = async () => {
  if (batchFiles.value.length === 0) {
    ElMessage.warning("请先上传图片");
    return;
  }
  
  batchLoading.value = true;
  batchResults.value = [];
  
  const formData = new FormData();
  batchFiles.value.forEach(f => {
    formData.append("files", f.raw);
  });
  formData.append("confidence_threshold", confidenceThreshold.value);
  
  const userId = getCurrentUserId();
  if (userId) {
    formData.append("user_id", userId);
  }
  
  try {
    const startTime = Date.now();
    const res = await axios.post(
      "http://localhost:8000/api/inference/batch",
      formData,
      { headers: { "Content-Type": "multipart/form-data" }, timeout: 120000 }
    );
    batchDuration.value = ((Date.now() - startTime) / 1000).toFixed(3);
    
    if (res.data.code === 200) {
      batchResults.value = res.data.data.results || [];
      batchTotalImages.value = res.data.data.total_images || 0;
      batchTotalTargets.value = res.data.data.total_targets || 0;
      ElMessage.success(`批量检测完成！共处理 ${batchTotalImages.value} 张图片，发现 ${batchTotalTargets.value} 个目标`);
    } else {
      ElMessage.error(res.data.message || "批量检测失败");
    }
  } catch (err) {
    ElMessage.error(`请求失败: ${err.message}`);
  } finally {
    batchLoading.value = false;
  }
};

const resetBatchDetection = () => {
  clearBatchFiles();
  batchTotalImages.value = 0;
  batchTotalTargets.value = 0;
  batchDuration.value = 0;
};

// 文件夹检测相关函数
const triggerFolderSelect = () => {
  folderInput.value?.click();
};

const handleFolderInputChange = (event) => {
  const files = Array.from(event.target.files);
  
  if (files.length > 0) {
    const existingNames = new Set(batchFiles.value.map(f => f.name));
    
    files.forEach(file => {
      if (file.type.startsWith('image/') && !existingNames.has(file.name)) {
        batchFiles.value.push({
          name: file.name,
          raw: file,
          preview: URL.createObjectURL(file),
          size: file.size
        });
      }
    });
    
    ElMessage.success(`已添加 ${files.filter(f => f.type.startsWith('image/')).length} 张图片`);
    
    event.target.value = "";
  }
};

// 视频检测相关函数
const triggerVideoSelect = () => {
  videoFileInput.value?.click();
};

const handleVideoFileChange = (e) => {
  const file = e.target.files && e.target.files[0];
  if (file) {
    if (videoPreviewUrl.value) {
      URL.revokeObjectURL(videoPreviewUrl.value);
    }
    videoFile.value = file;
    videoPreviewUrl.value = URL.createObjectURL(file);
    videoResults.value = [];
    videoTotalFrames.value = 0;
    videoTotalTargets.value = 0;
    videoDuration.value = 0;
  }
};

const handleVideoInference = async () => {
  if (!videoFile.value) {
    ElMessage.warning("请先上传视频");
    return;
  }
  
  videoLoading.value = true;
  videoResults.value = [];
  
  const formData = new FormData();
  formData.append("video", videoFile.value);
  formData.append("confidence_threshold", confidenceThreshold.value);
  
  const userId = getCurrentUserId();
  if (userId) {
    formData.append("user_id", userId);
  }
  
  try {
    const startTime = Date.now();
    const res = await axios.post(
      "http://localhost:8000/api/inference/video",
      formData,
      { headers: { "Content-Type": "multipart/form-data" }, timeout: 300000 }
    );
    videoDuration.value = ((Date.now() - startTime) / 1000).toFixed(3);
    
    if (res.data.code === 200) {
      videoOutputUrl.value = res.data.data.video_url;
      videoTotalFrames.value = res.data.data.total_frames || 0;
      videoTotalTargets.value = res.data.data.total_targets || 0;
      
      // 处理检测结果，按帧分组
      const detectionsData = res.data.data.detections || [];
      console.log("检测结果数量:", detectionsData.length);
      
      // 按帧索引分组
      const framesMap = new Map();
      detectionsData.forEach(det => {
        const frameIndex = det.frame_index || 0;
        if (!framesMap.has(frameIndex)) {
          framesMap.set(frameIndex, []);
        }
        framesMap.get(frameIndex).push(det);
      });
      
      // 转换为 videoResults 格式
      videoResults.value = Array.from(framesMap.entries()).map(([frameIndex, dets]) => ({
        frame_index: frameIndex,
        detections: dets
      }));
      
      console.log("视频检测结果分组完成，共", videoResults.value.length, "帧有检测结果");
      
      // 详细调试日志
      console.log("=== 视频检测完成 ===");
      console.log("响应数据:", res.data);
      console.log("视频URL:", videoOutputUrl.value);
      console.log("视频URL类型:", typeof videoOutputUrl.value);
      console.log("视频URL长度:", videoOutputUrl.value?.length);
      console.log("总帧数:", videoTotalFrames.value);
      console.log("总目标数:", videoTotalTargets.value);
      
      // 验证URL格式
      if (!videoOutputUrl.value) {
        console.error("错误：视频URL为空");
        ElMessage.error("视频URL为空");
        return;
      }
      
      if (!videoOutputUrl.value.startsWith("http")) {
        console.error("错误：视频URL格式不正确:", videoOutputUrl.value);
        ElMessage.error("视频URL格式不正确");
        return;
      }
      
      // 手动触发视频加载
      setTimeout(() => {
        const videoElement = document.querySelector('.result-video video');
        if (videoElement) {
          console.log("找到视频元素:", videoElement);
          console.log("视频元素src:", videoElement.src);
          videoElement.load();
        } else {
          console.error("未找到视频元素");
        }
      }, 100);
      
      ElMessage.success(`视频检测完成！共分析 ${videoTotalFrames.value} 帧，发现 ${videoTotalTargets.value} 个目标`);
    } else {
      ElMessage.error(res.data.message || "视频检测失败");
    }
  } catch (err) {
    ElMessage.error(`请求失败：${err.message}`);
  } finally {
    videoLoading.value = false;
  }
};

const resetVideoDetection = () => {
  if (videoPreviewUrl.value) {
    URL.revokeObjectURL(videoPreviewUrl.value);
  }
  videoFile.value = null;
  videoPreviewUrl.value = "";
  videoOutputUrl.value = "";
  videoResults.value = [];
  videoTotalFrames.value = 0;
  videoTotalTargets.value = 0;
  videoDuration.value = 0;
};

const handleVideoError = (e) => {
  console.error("视频加载失败:", e);
  console.error("视频URL:", videoOutputUrl.value);
  ElMessage.error(`视频加载失败，请检查网络连接或刷新页面重试`);
};

const handleVideoLoaded = () => {
  console.log("视频加载成功");
};

const clearFile = () => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
  selectedFile.value = null;
  previewUrl.value = "";
  resultImageUrl.value = "";
  detections.value = [];
  isDetected.value = false;
};

const getCurrentUserId = () => {
  return getUserId();
};

const handleInference = async () => {
  if (!selectedFile.value) {
    ElMessage.warning("请先上传图片");
    return;
  }
  loading.value = true;
  const formData = new FormData();
  formData.append("file", selectedFile.value);
  formData.append("confidence_threshold", confidenceThreshold.value);
  
  const userId = getCurrentUserId();
  if (userId) {
    formData.append("user_id", userId);
  }

  try {
    const startTime = Date.now();
    const res = await axios.post(
      "http://localhost:8000/api/inference/single",
      formData,
      { headers: { "Content-Type": "multipart/form-data" }, timeout: 60000 }
    );
    inferenceTime.value = ((Date.now() - startTime) / 1000).toFixed(3);

    if (res.data.code === 200) {
      resultImageUrl.value = res.data.data.image_url;
      detections.value = res.data.data.detections || [];
      isDetected.value = true;
      viewMode.value = "side";
      ElMessage.success(`检测完成！发现 ${detections.value.length} 个目标`);
    } else {
      ElMessage.error(res.data.message || "检测失败");
    }
  } catch (err) {
    ElMessage.error(`请求失败: ${err.message}`);
  } finally {
    loading.value = false;
  }
};

const resetDetection = () => {
  clearFile();
  inferenceTime.value = "0.000";
};
</script>

<style scoped>
.detection-page {
  max-width: 1400px;
  margin: 0 auto;
}

/* 顶部标题区 */
.page-header {
  text-align: center;
  padding: 20px 0 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  margin-bottom: 24px;
  color: #fff;
}

.page-header h1 {
  font-size: 24px;
  margin-bottom: 8px;
}

.page-header p {
  font-size: 14px;
  opacity: 0.9;
}

/* 模式选择区 */
.mode-section {
  margin-bottom: 16px;
}

.mode-label {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.mode-label::before {
  content: "";
  display: inline-block;
  width: 4px;
  height: 16px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 2px;
}

.mode-cards {
  display: flex;
  gap: 12px;
}

.mode-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #fff;
  border: 2px solid #e8ecf1;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
}

/* 置信度阈值设置区 */
.threshold-section {
  background: #fff;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.threshold-label {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.threshold-slider {
  max-width: 400px;
  margin-bottom: 8px;
}

.threshold-info {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: #666;
}

.threshold-value {
  font-weight: 600;
  color: #667eea;
  font-size: 15px;
}

.threshold-hint {
  color: #999;
  font-size: 12px;
}

.mode-card:hover {
  border-color: #667eea;
  color: #667eea;
}

.mode-card.active {
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.08));
  color: #667eea;
  font-weight: 600;
}

.mode-card.disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.mode-icon {
  font-size: 20px;
}

.mode-name {
  font-size: 14px;
}

/* 主内容区 */
.main-content {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 24px;
}

/* 左侧面板 */
.left-panel {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  min-height: 500px;
}

/* 上传区域 */
.upload-area {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}

.upload-box-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}

.batch-upload-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  height: 100%;
  justify-content: center;
}

.upload-divider {
  display: flex;
  align-items: center;
  gap: 16px;
  color: #999;
  font-size: 13px;
}

.upload-divider::before,
.upload-divider::after {
  content: "";
  flex: 1;
  height: 1px;
  background: #e8ecf1;
}

.folder-select-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  border: 2px dashed #d0d5dd;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.folder-select-area:hover {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
}

.folder-icon {
  font-size: 48px;
  color: #667eea;
  margin-bottom: 16px;
}

.folder-main {
  font-size: 16px;
  color: #333;
  margin-bottom: 8px;
}

.folder-sub {
  font-size: 13px;
  color: #999;
}

.upload-box {
  width: 100%;
  height: 100%;
}

.upload-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 10;
  cursor: pointer;
}

.upload-box :deep(.el-upload-dragger) {
  width: 100%;
  height: 100%;
  border: 2px dashed #d0d5dd;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.upload-box :deep(.el-upload-dragger:hover) {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
}

.folder-preview {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.video-preview {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.video-container {
  width: 100%;
  display: flex;
  justify-content: center;
  background: #f9fafb;
  border-radius: 10px;
  padding: 16px;
}

.video-player {
  width: 100%;
  max-width: 640px;
  border-radius: 8px;
}

.video-results {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.video-container.result-video {
  border: 2px solid #10b981;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
}

.video-player.result-player {
  box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3);
}

.video-info-panel {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.video-info-panel .info-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.video-info-panel .info-content {
  display: flex;
  gap: 32px;
  flex-wrap: wrap;
}

.video-info-panel .info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.video-info-panel .info-label {
  font-size: 13px;
  color: #6b7280;
}

.video-info-panel .info-value {
  font-size: 24px;
  font-weight: 700;
  color: #10b981;
}

.upload-content {
  text-align: center;
}

.upload-icon {
  font-size: 48px;
  color: #667eea;
  margin-bottom: 16px;
}

.upload-main {
  font-size: 16px;
  color: #333;
  margin-bottom: 8px;
}

.upload-sub {
  font-size: 13px;
  color: #999;
}

/* 预览区域 */
.preview-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-label {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 6px;
}

.image-container {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e8ecf1;
  background: #f5f7fa;
}

.image-container img {
  width: 100%;
  height: 320px;
  object-fit: contain;
  display: block;
}

.preview-info {
  display: flex;
  gap: 24px;
  font-size: 13px;
  color: #666;
}

.detect-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
}

.detect-btn:hover {
  background: linear-gradient(135deg, #5a6fd6, #6a4190);
}

/* 对比区域 */
.compare-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.compare-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.compare-label {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.view-toggle {
  display: flex;
  gap: 8px;
}

.toggle-btn {
  padding: 5px 14px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  background: #f5f7fa;
  color: #666;
  transition: all 0.3s;
}

.toggle-btn.active {
  background: #667eea;
  color: #fff;
}

.compare-images {
  display: grid;
  gap: 16px;
}

.compare-images.side {
  grid-template-columns: 1fr 1fr;
}

.compare-images.grid {
  grid-template-columns: 1fr;
}

.compare-item {
  background: #f9fafb;
  border-radius: 12px;
  padding: 12px;
}

.compare-item-label {
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e8ecf1;
  font-size: 13px;
  font-weight: 500;
  color: #666;
}

.compare-item-label.success {
  color: #67c23a;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.action-buttons .el-button {
  flex: 1;
  height: 44px;
  border-radius: 8px;
}

/* 右侧面板 */
.right-panel {
  position: sticky;
  top: 24px;
  height: fit-content;
}

.result-card {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.card-section {
  padding-bottom: 16px;
  margin-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.card-section:last-child {
  border-bottom: none;
  padding-bottom: 0;
  margin-bottom: 0;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  font-size: 13px;
  color: #999;
}

.info-value {
  font-size: 13px;
  color: #333;
  font-weight: 500;
}

.info-value.highlight {
  color: #667eea;
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: 24px 0;
  color: #999;
  font-size: 13px;
}

.empty-state p {
  margin-top: 8px;
}

.detection-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 300px;
  overflow-y: auto;
}

.detection-item {
  background: #f9fafb;
  border-radius: 8px;
  padding: 10px 12px;
}

.item-top {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.item-class {
  font-size: 13px;
  color: #333;
  font-weight: 500;
  text-transform: capitalize;
}

.item-conf {
  font-size: 12px;
  color: #667eea;
  font-weight: 600;
}

.progress-bar {
  height: 4px;
  background: #e8ecf1;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 2px;
  transition: width 0.5s ease;
}

.ai-advice {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  border-radius: 8px;
  padding: 14px;
}

.ai-advice p {
  font-size: 13px;
  color: #666;
  line-height: 1.8;
  margin: 0;
}

.ai-advice strong {
  color: #667eea;
}

/* 批量检测样式 */
.batch-preview {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.batch-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.batch-header-actions {
  display: flex;
  gap: 8px;
}

.batch-label {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 6px;
}

.batch-stats {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #666;
}

.stat-item {
  background: #f5f7fa;
  padding: 4px 12px;
  border-radius: 4px;
}

.batch-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.batch-item {
  background: #f9fafb;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #e8ecf1;
}

.batch-item img {
  width: 100%;
  height: 80px;
  object-fit: cover;
}

.batch-item-info {
  padding: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.batch-item-name {
  font-size: 12px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.batch-item-remove {
  color: #f56c6c;
  padding: 0;
  margin-left: 8px;
}

.batch-add-more {
  background: #f5f7fa;
  border-radius: 10px;
  border: 2px dashed #d9d9d9;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 120px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.batch-add-more:hover {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
}

.add-icon {
  font-size: 24px;
  color: #999;
  margin-bottom: 8px;
}

.add-text {
  font-size: 13px;
  color: #999;
}

.batch-add-more:hover .add-icon,
.batch-add-more:hover .add-text {
  color: #667eea;
}

.hidden-file-input {
  display: none;
}

.batch-results {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.batch-results-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-card {
  background: #f9fafb;
  border-radius: 12px;
  padding: 16px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.result-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.result-count {
  font-size: 13px;
  color: #67c23a;
  background: rgba(103, 194, 58, 0.1);
  padding: 2px 10px;
  border-radius: 4px;
}

.result-images {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}

.result-image-item {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e8ecf1;
}

.result-image-item img {
  width: 100%;
  height: 180px;
  object-fit: contain;
}

.image-label {
  display: block;
  padding: 6px 10px;
  font-size: 12px;
  color: #666;
  background: #f5f7fa;
  border-bottom: 1px solid #e8ecf1;
}

.image-label.success {
  color: #67c23a;
  background: rgba(103, 194, 58, 0.1);
}

.result-detections {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.mini-detection {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #fff;
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid #e8ecf1;
}

.mini-class {
  font-size: 12px;
  color: #333;
}

.mini-conf {
  font-size: 12px;
  color: #667eea;
  font-weight: 600;
}

.mini-more {
  font-size: 12px;
  color: #999;
  padding: 4px 10px;
}


</style>