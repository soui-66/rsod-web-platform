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
          <el-option
            :key="0"
            label="🔧 使用本地默认模型"
            :value="0"
          />
          <el-option v-for="model in modelList" :key="model.id" :label="model.name" :value="model.id" />
        </el-select>
        <el-button type="primary" size="small" @click="showUploadModel = true">
          <el-icon><Upload /></el-icon> 上传模型
        </el-button>
      </div>
    </div>

    <!-- 置信度设置 -->
    <div class="confidence-control">
      <span class="label">
        <el-icon><Aim /></el-icon> 置信度阈值
      </span>
      <el-slider v-model="confidence" :min="0.1" :max="0.9" :step="0.05" />
      <span class="value">{{ (confidence * 100).toFixed(0) }}%</span>
    </div>

    <!-- 单图检测 -->
    <div v-if="currentMode === 'single'" class="detection-content">
      <div class="upload-area">
        <el-upload
          class="upload-box"
          action="#"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleSingleFile"
          accept="image/*"
        >
          <div v-if="!singleImage" class="upload-placeholder">
            <el-icon><Image /></el-icon>
            <p>点击或拖拽上传图片</p>
          </div>
          <img v-else :src="singleImage" class="preview-image" />
        </el-upload>
        <el-button type="primary" size="large" :loading="isDetecting" @click="detectSingle">
          {{ isDetecting ? '检测中...' : '🚀 开始检测' }}
        </el-button>
      </div>

      <!-- 结果展示 -->
      <div v-if="singleResult" class="result-area">
        <div class="result-header">
          <span class="result-title">✅ 检测完成</span>
          <el-button @click="resetSingle" size="small">
            <el-icon><Refresh /></el-icon> 重新检测
          </el-button>
        </div>
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
      <div v-if="batchFiles.length === 0" class="batch-upload-area">
        <el-upload
          class="upload-box"
          action="#"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleBatchFile"
          accept="image/*"
          multiple
        >
          <div class="upload-placeholder">
            <el-icon><Upload /></el-icon>
            <p>点击选择多张图片</p>
          </div>
        </el-upload>
      </div>
      <div v-else>
        <div class="batch-header">
          <span>已选择 {{ batchFiles.length }} 张图片</span>
          <el-button type="danger" size="small" @click="clearBatch">清空</el-button>
        </div>
        <div class="batch-preview">
          <div v-for="(file, index) in batchFiles" :key="index" class="batch-item">
            <img :src="file.preview" :alt="file.name" />
            <span>{{ file.name }}</span>
          </div>
        </div>
      </div>
      <el-button type="primary" size="large" :loading="isDetecting" @click="detectBatch">
        {{ isDetecting ? '批量检测中...' : '🚀 批量检测' }}
      </el-button>
    </div>

    <!-- 摄像头检测 -->
    <div v-if="currentMode === 'camera'" class="camera-content">
      <CameraDetection />
    </div>

    <!-- 视频检测 -->
    <div v-if="currentMode === 'video'" class="video-content">
      <div v-if="!videoFile" class="video-upload-area">
        <el-upload
          class="upload-box"
          action="#"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleVideoFile"
          accept="video/*"
        >
          <div class="upload-placeholder">
            <el-icon><VideoCamera /></el-icon>
            <p>点击上传视频</p>
          </div>
        </el-upload>
      </div>
      <div v-else>
        <div class="video-preview">
          <video :src="videoFile" controls class="video-player"></video>
        </div>
      </div>
      <el-button type="primary" size="large" :loading="isDetecting" @click="detectVideo">
        {{ isDetecting ? '视频检测中...' : '🚀 开始检测' }}
      </el-button>
    </div>

    <!-- 模型上传弹窗 -->
    <el-dialog title="上传模型" v-model="showUploadModel" width="500px">
      <el-form :model="uploadForm" label-width="100px">
        <el-form-item label="模型名称">
          <el-input v-model="uploadForm.name" placeholder="请输入模型名称" />
        </el-form-item>
        <el-form-item label="模型描述">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入模型描述（可选）"
          />
        </el-form-item>
        <el-form-item label="模型文件">
          <el-upload
            ref="modelUploadRef"
            action="#"
            :auto-upload="false"
            :limit="1"
            :on-change="handleModelFileChange"
            :on-remove="handleModelFileRemove"
            accept=".pt"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon> 选择文件
            </el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadModel = false">取消</el-button>
        <el-button type="primary" :loading="uploadingModel" @click="handleUploadModel">
          上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Image, Upload, VideoCamera, Aim, Refresh } from '@element-plus/icons-vue'
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
const selectedModelId = ref(0)
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
const modelUploadRef = ref(null)
const uploadingModel = ref(false)

// 加载模型列表
const loadModels = async () => {
  try {
    const res = await axios.get(`${API_URL}/model/list`)
    if (res.data.code === 200) {
      modelList.value = res.data.data
      if (modelList.value.length > 0 && !selectedModelId.value) {
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
  if (!singleImage.value) {
    ElMessage.warning('请先上传图片')
    return
  }

  isDetecting.value = true
  const form = new FormData()
  form.append('file', document.querySelector('.upload-area input[type=file]').files[0])
  form.append('confidence_threshold', confidence.value)
  if (selectedModelId.value && selectedModelId.value !== 0) {
    form.append('selected_model_id', selectedModelId.value)
  }

  try {
    const res = await axios.post(`${API_URL}/inference/single`, form)
    if (res.data.code === 200) {
      singleResult.value = {
        ...res.data.data,
        duration: parseFloat(res.data.data.duration) || 0
      }
      ElMessage.success(`检测完成！发现 ${res.data.data.target_count} 个目标`)
    } else {
      ElMessage.error(res.data.message || '检测失败')
    }
  } catch (err) {
    ElMessage.error('检测失败: ' + err.message)
  } finally {
    isDetecting.value = false
  }
}

// 重置单图检测
const resetSingle = () => {
  if (singleImage.value) {
    URL.revokeObjectURL(singleImage.value)
  }
  singleImage.value = ''
  singleResult.value = null
}

// 处理批量文件
const handleBatchFile = (uploadFile, fileList) => {
  const existingNames = new Set(batchFiles.value.map(f => f.name))
  const newFiles = fileList.filter(f => !existingNames.has(f.name))
  
  newFiles.forEach(f => {
    batchFiles.value.push({
      name: f.name,
      raw: f.raw,
      preview: URL.createObjectURL(f.raw)
    })
  })
}

// 清空批量文件
const clearBatch = () => {
  batchFiles.value.forEach(f => URL.revokeObjectURL(f.preview))
  batchFiles.value = []
}

// 批量检测
const detectBatch = async () => {
  if (batchFiles.value.length === 0) {
    ElMessage.warning('请先选择图片')
    return
  }

  isDetecting.value = true
  const form = new FormData()
  batchFiles.value.forEach(f => form.append('files', f.raw))
  form.append('confidence_threshold', confidence.value)
  if (selectedModelId.value && selectedModelId.value !== 0) {
    form.append('selected_model_id', selectedModelId.value)
  }

  try {
    const res = await axios.post(`${API_URL}/inference/batch`, form, { timeout: 120000 })
    if (res.data.code === 200) {
      ElMessage.success(`批量检测完成，处理 ${res.data.data.total_images} 张图片，发现 ${res.data.data.total_targets} 个目标`)
      clearBatch()
    } else {
      ElMessage.error(res.data.message)
    }
  } catch (err) {
    ElMessage.error('批量检测失败: ' + err.message)
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
  if (!videoFile.value) {
    ElMessage.warning('请先上传视频')
    return
  }

  isDetecting.value = true
  const form = new FormData()
  form.append('video', document.querySelector('.video-content input[type=file]').files[0])
  form.append('confidence_threshold', confidence.value)
  if (selectedModelId.value && selectedModelId.value !== 0) {
    form.append('selected_model_id', selectedModelId.value)
  }

  try {
    const res = await axios.post(`${API_URL}/inference/video`, form, { timeout: 300000 })
    if (res.data.code === 200) {
      ElMessage.success(`视频检测完成！共分析 ${res.data.data.total_frames} 帧，发现 ${res.data.data.total_targets} 个目标`)
    } else {
      ElMessage.error(res.data.message)
    }
  } catch (err) {
    ElMessage.error('视频检测失败: ' + err.message)
  } finally {
    isDetecting.value = false
  }
}

// 模型选择变化
const onModelChange = () => {
  if (selectedModelId.value === 0) {
    ElMessage.info('已切换到本地默认模型')
  } else {
    const model = modelList.value.find(m => m.id === selectedModelId.value)
    if (model) {
      ElMessage.success(`已切换到模型: ${model.name}`)
    }
  }
}

// 模型文件选择
const handleModelFileChange = (file) => {
  uploadForm.value.modelFile = file.raw
}

// 模型文件移除
const handleModelFileRemove = () => {
  uploadForm.value.modelFile = null
}

// 上传模型
const handleUploadModel = async () => {
  if (!uploadForm.value.name) {
    ElMessage.warning('请输入模型名称')
    return
  }
  if (!uploadForm.value.modelFile) {
    ElMessage.warning('请选择模型文件')
    return
  }

  uploadingModel.value = true
  const formData = new FormData()
  formData.append('name', uploadForm.value.name)
  formData.append('description', uploadForm.value.description)
  formData.append('file', uploadForm.value.modelFile)

  try {
    const res = await axios.post(`${API_URL}/model/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    if (res.data.code === 200) {
      ElMessage.success('模型上传成功')
      showUploadModel.value = false
      uploadForm.value = { name: '', description: '', modelFile: null }
      loadModels()
    } else {
      ElMessage.error(res.data.message || '上传失败')
    }
  } catch (err) {
    ElMessage.error('上传失败: ' + err.message)
  } finally {
    uploadingModel.value = false
  }
}

onMounted(() => {
  loadModels()
})
</script>

<style scoped>
.detection-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.mode-tabs {
  display: flex;
  gap: 8px;
}

.mode-tabs .el-button {
  padding: 8px 20px;
  border-radius: 8px;
}

.model-selector {
  display: flex;
  align-items: center;
  gap: 12px;
}

.model-selector .el-select {
  width: 200px;
}

.confidence-control {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: #f8fafc;
  border-radius: 12px;
}

.confidence-control .label {
  font-weight: 600;
  color: #333;
}

.confidence-control .value {
  color: #667eea;
  font-weight: 700;
  font-size: 16px;
}

.confidence-control .el-slider {
  flex: 1;
  max-width: 400px;
}

.detection-content {
  display: flex;
  gap: 24px;
}

.upload-area {
  flex: 1;
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.upload-box {
  width: 100%;
  margin-bottom: 16px;
}

.upload-placeholder {
  border: 2px dashed #d0d5dd;
  border-radius: 12px;
  padding: 48px;
  text-align: center;
  transition: all 0.3s;
}

.upload-placeholder:hover {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
}

.upload-placeholder .el-icon {
  font-size: 48px;
  color: #667eea;
  margin-bottom: 12px;
}

.upload-placeholder p {
  color: #666;
  font-size: 15px;
}

.preview-image {
  width: 100%;
  max-height: 400px;
  object-fit: contain;
  border-radius: 12px;
  border: 1px solid #e8ecf1;
}

.upload-area .el-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  border-radius: 10px;
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.result-area {
  flex: 1;
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.result-title {
  font-size: 18px;
  font-weight: 600;
  color: #10b981;
}

.result-images {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.image-item {
  background: #f9fafb;
  border-radius: 12px;
  padding: 12px;
}

.image-item h4 {
  margin-bottom: 8px;
  font-size: 14px;
  color: #666;
}

.image-item img {
  width: 100%;
  max-height: 300px;
  object-fit: contain;
  border-radius: 8px;
}

.result-info {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(16, 185, 129, 0.05));
  border-radius: 10px;
  padding: 16px;
}

.result-info p {
  margin: 6px 0;
  color: #333;
}

.batch-content, .video-content {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.batch-upload-area, .video-upload-area {
  margin-bottom: 16px;
}

.batch-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e8ecf1;
}

.batch-preview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.batch-item {
  background: #f9fafb;
  border-radius: 10px;
  overflow: hidden;
}

.batch-item img {
  width: 100%;
  height: 80px;
  object-fit: cover;
}

.batch-item span {
  display: block;
  padding: 8px;
  font-size: 12px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-preview {
  margin-bottom: 16px;
}

.video-player {
  width: 100%;
  max-width: 640px;
  border-radius: 12px;
  margin: 0 auto;
  display: block;
}

.camera-content {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}
</style>