<template>
  <div class="detection-page">
    <!-- 顶部操作栏 -->
    <div class="top-bar">
      <div class="mode-tabs">
        <el-button
          v-for="mode in modes"
          :key="mode.value"
          :type="currentMode === mode.value ? 'primary' : ''"
          @click="currentMode = mode.value"
        >
          {{ mode.label }}
        </el-button>
      </div>

      <!-- 模型选择 -->
      <div class="model-selector">
        <el-select v-model="selectedModelId" placeholder="选择模型" @change="onModelChange">
          <el-option v-for="model in modelList" :key="model.id" :label="model.name" :value="model.id" />
        </el-select>
        <el-button type="text" @click="showUploadModel = true">上传模型</el-button>
      </div>
    </div>

    <!-- 置信度设置 -->
    <div class="confidence-control">
      <span class="label">置信度阈值</span>
      <el-slider v-model="confidence" :min="0.1" :max="0.9" :step="0.05" />
      <span class="value">{{ (confidence * 100).toFixed(0) }}%</span>
    </div>

    <!-- 单图检测 -->
    <div v-if="currentMode === 'single'" class="detection-content">
      <div class="upload-area">
        <el-upload
          action="#"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleSingleFile"
          accept="image/*"
        >
          <div class="upload-box" v-if="!singleImage">
            <el-icon><Image /></el-icon>
            <p>点击或拖拽上传图片</p>
          </div>
          <img v-else :src="singleImage" class="preview-image" />
        </el-upload>
        <el-button type="primary" :loading="isDetecting" @click="detectSingle">开始检测</el-button>
      </div>

      <!-- 结果展示 -->
      <div v-if="singleResult" class="result-area">
        <div class="result-images">
          <div class="image-item">
            <h4>原图</h4>
            <img :src="singleResult.original_url" />
          </div>
          <div class="image-item">
            <h4>检测结果</h4>
            <img :src="singleResult.image_url" />
          </div>
        </div>
        <div class="result-info">
          <p>检测到 {{ singleResult.target_count }} 个目标</p>
          <p>耗时 {{ singleResult.duration.toFixed(2) }} 秒</p>
          <p>使用模型: {{ singleResult.model_name }}</p>
        </div>
      </div>
    </div>

    <!-- 批量检测 -->
    <div v-if="currentMode === 'batch'" class="batch-content">
      <el-upload
        action="#"
        :auto-upload="false"
        :show-file-list="true"
        :on-change="handleBatchFile"
        accept="image/*"
        multiple
      >
        <div class="batch-upload-box">
          <el-icon><Upload /></el-icon>
          <p>点击选择多张图片</p>
        </div>
      </el-upload>
      <el-button type="primary" :loading="isDetecting" @click="detectBatch">批量检测</el-button>
    </div>

    <!-- 摄像头检测 -->
    <div v-if="currentMode === 'camera'" class="camera-content">
      <CameraDetection />
    </div>

    <!-- 视频检测 -->
    <div v-if="currentMode === 'video'" class="video-content">
      <el-upload
        action="#"
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleVideoFile"
        accept="video/*"
      >
        <div class="video-upload-box">
          <el-icon><VideoCamera /></el-icon>
          <p>点击上传视频</p>
        </div>
      </el-upload>
      <el-button type="primary" :loading="isDetecting" @click="detectVideo">开始检测</el-button>
    </div>

    <!-- 模型上传弹窗 -->
    <el-dialog title="上传模型" :visible.sync="showUploadModel">
      <el-form :model="uploadForm">
        <el-form-item label="模型名称">
          <el-input v-model="uploadForm.name" />
        </el-form-item>
        <el-form-item label="模型文件">
          <el-upload
            action="/api/model/upload"
            :data="{ name: uploadForm.name, description: uploadForm.description }"
            :on-success="onUploadSuccess"
            :file-list="uploadFiles"
            accept=".pt"
          >
            <el-button type="primary">选择文件</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Image, Upload, VideoCamera } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import CameraDetection from '@/components/CameraDetection.vue'

const API_URL = 'http://localhost:8000/api'

// 模式列表
const modes = [
  { label: '单图检测', value: 'single' },
  { label: '批量检测', value: 'batch' },
  { label: '摄像头检测', value: 'camera' },
  { label: '视频检测', value: 'video' }
]

// 状态
const currentMode = ref('single')
const modelList = ref([])
const selectedModelId = ref(null)
const confidence = ref(0.25)
const isDetecting = ref(false)
const showUploadModel = ref(false)

// 单图检测
const singleImage = ref('')
const singleResult = ref(null)

// 批量检测
const batchFiles = ref([])

// 视频检测
const videoFile = ref('')

// 上传表单
const uploadForm = ref({ name: '', description: '' })
const uploadFiles = ref([])

// 加载模型列表
const loadModels = async () => {
  try {
    const res = await axios.get(`${API_URL}/model/list`)
    if (res.data.code === 200) {
      modelList.value = res.data.data
      if (modelList.value.length > 0) {
        selectedModelId.value = modelList.value[0].id
      }
    }
  } catch (err) {
    console.error('加载模型失败:', err)
  }
}

// 处理单图文件
const handleSingleFile = (file) => {
  singleImage.value = URL.createObjectURL(file.raw)
  singleResult.value = null
}

// 单图检测
const detectSingle = async () => {
  if (!singleImage.value) return

  isDetecting.value = true
  const form = new FormData()
  form.append('file', document.querySelector('.upload-area input[type=file]').files[0])
  form.append('confidence_threshold', confidence.value)
  if (selectedModelId.value) {
    form.append('model_id', selectedModelId.value)
  }

  try {
    const res = await axios.post(`${API_URL}/inference/single`, form)
    if (res.data.code === 200) {
      singleResult.value = {
        ...res.data.data,
        duration: parseFloat(res.data.data.duration) || 0
      }
    } else {
      ElMessage.error(res.data.message || '检测失败')
    }
  } catch (err) {
    ElMessage.error('检测失败')
  } finally {
    isDetecting.value = false
  }
}

// 处理批量文件
const handleBatchFile = (file) => {
  batchFiles.value.push(file)
}

// 批量检测
const detectBatch = async () => {
  if (batchFiles.value.length === 0) return

  isDetecting.value = true
  const form = new FormData()
  batchFiles.value.forEach(f => form.append('files', f.raw))
  form.append('confidence_threshold', confidence.value)
  if (selectedModelId.value) {
    form.append('model_id', selectedModelId.value)
  }

  try {
    const res = await axios.post(`${API_URL}/inference/batch`, form)
    if (res.data.code === 200) {
      ElMessage.success(`批量检测完成，处理 ${res.data.data.total_images} 张图片`)
    } else {
      ElMessage.error(res.data.message)
    }
  } catch (err) {
    ElMessage.error('批量检测失败')
  } finally {
    isDetecting.value = false
  }
}

// 处理视频文件
const handleVideoFile = (file) => {
  videoFile.value = URL.createObjectURL(file.raw)
}

// 视频检测
const detectVideo = async () => {
  if (!videoFile.value) return

  isDetecting.value = true
  const form = new FormData()
  form.append('video', document.querySelector('.video-content input[type=file]').files[0])
  form.append('confidence_threshold', confidence.value)
  if (selectedModelId.value) {
    form.append('model_id', selectedModelId.value)
  }

  try {
    const res = await axios.post(`${API_URL}/inference/video`, form)
    if (res.data.code === 200) {
      ElMessage.success('视频检测完成')
    } else {
      ElMessage.error(res.data.message)
    }
  } catch (err) {
    ElMessage.error('视频检测失败')
  } finally {
    isDetecting.value = false
  }
}

// 模型选择变化
const onModelChange = () => {
  console.log('选择模型:', selectedModelId.value)
}

// 模型上传成功
const onUploadSuccess = (res) => {
  if (res.code === 200) {
    ElMessage.success('模型上传成功')
    showUploadModel.value = false
    loadModels()
  }
}

onMounted(() => {
  loadModels()
})
</script>

<style scoped>
.detection-page { padding: 20px; }

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.mode-tabs { display: flex; gap: 8px; }

.model-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.confidence-control {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
}

.confidence-control .label { font-weight: 500; }
.confidence-control .value { color: #3b82f6; font-weight: 600; }

.detection-content { display: flex; gap: 20px; }

.upload-area { flex: 1; }

.upload-box {
  border: 2px dashed #ddd;
  padding: 40px;
  text-align: center;
  margin-bottom: 15px;
}

.preview-image { max-width: 100%; max-height: 400px; }

.result-area { flex: 1; }

.result-images { display: flex; gap: 15px; }

.image-item { flex: 1; }
.image-item img { width: 100%; max-height: 300px; }

.result-info { margin-top: 15px; }

.batch-content, .video-content { margin-top: 20px; }

.batch-upload-box, .video-upload-box {
  border: 2px dashed #ddd;
  padding: 40px;
  text-align: center;
  margin-bottom: 15px;
}

.camera-content { margin-top: 20px; }
</style>