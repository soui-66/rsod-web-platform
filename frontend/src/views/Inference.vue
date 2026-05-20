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
          <div class="upload-area">
            <el-upload
              class="upload-box"
              drag
              action="#"
              :auto-upload="false"
              :on-change="handleBatchFileChange"
              :show-file-list="true"
              multiple
              accept="image/*"
            >
              <div class="upload-content">
                <el-icon class="upload-icon"><Upload /></el-icon>
                <p class="upload-main">点击或拖拽多张图片到此处</p>
                <p class="upload-sub">支持同时上传多张 JPG / PNG 图片</p>
              </div>
            </el-upload>
          </div>
        </template>

        <!-- 文件夹模式 -->
        <template v-if="currentMode === 'folder'">
          <div class="upload-area">
            <el-upload
              class="upload-box"
              drag
              action="#"
              :auto-upload="false"
              :show-file-list="true"
              directory
            >
              <div class="upload-content">
                <el-icon class="upload-icon"><FolderOpened /></el-icon>
                <p class="upload-main">点击选择文件夹</p>
                <p class="upload-sub">自动识别文件夹中的所有图片</p>
              </div>
            </el-upload>
          </div>
        </template>

        <!-- 视频检测模式 -->
        <template v-if="currentMode === 'video'">
          <div class="upload-area">
            <el-upload
              class="upload-box"
              drag
              action="#"
              :auto-upload="false"
              :show-file-list="true"
              accept="video/*"
            >
              <div class="upload-content">
                <el-icon class="upload-icon"><VideoCamera /></el-icon>
                <p class="upload-main">点击或拖拽视频到此处</p>
                <p class="upload-sub">支持 MP4 / AVI / MOV 格式</p>
              </div>
            </el-upload>
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
                <span class="info-value highlight">{{ inferenceTime }}s</span>
              </div>
            </div>
          </div>

          <div class="card-section">
            <h3 class="section-title">
              <el-icon><Aim /></el-icon> 识别清单 ({{ detections.length }})
            </h3>
            <div v-if="detections.length === 0" class="empty-state">
              <el-icon :size="32" color="#ddd"><PictureFilled /></el-icon>
              <p>暂无检测结果</p>
            </div>
            <div v-else class="detection-list">
              <div
                v-for="(item, index) in detections"
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
              <template v-if="detections.length > 0">
                <p>检测到 <strong>{{ detections.length }}</strong> 个目标</p>
                <p>最高置信度：<strong>{{ maxConfidence }}%</strong></p>
                <p>最低置信度：<strong>{{ minConfidence }}%</strong></p>
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

const detectionModes = [
  { key: "single", icon: "Picture", name: "单图检测", disabled: false },
  { key: "batch", icon: "Upload", name: "批量检测", disabled: false },
  { key: "folder", icon: "FolderOpened", name: "文件夹", disabled: false },
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

const handleFileChange = (uploadFile) => {
  selectedFile.value = uploadFile.raw;
  isDetected.value = false;
  resultImageUrl.value = "";
  detections.value = [];
  previewUrl.value = URL.createObjectURL(uploadFile.raw);
};

const handleBatchFileChange = (uploadFile, fileList) => {
  console.log("批量文件:", fileList);
};

const clearFile = () => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
  selectedFile.value = null;
  previewUrl.value = "";
  resultImageUrl.value = "";
  detections.value = [];
  isDetected.value = false;
};

const handleInference = async () => {
  if (!selectedFile.value) {
    ElMessage.warning("请先上传图片");
    return;
  }
  loading.value = true;
  const formData = new FormData();
  formData.append("file", selectedFile.value);

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
  margin-bottom: 24px;
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
  font-size: 14px;
  color: #555;
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

.upload-box {
  width: 100%;
  height: 100%;
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
</style>