<template>
  <div class="history-page">
    <!-- 顶部标题区 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">📋</div>
        <div class="header-text">
          <h1>检测历史记录</h1>
          <p>查看和管理您的所有检测记录</p>
        </div>
      </div>
      <el-button
        type="primary"
        plain
        @click="refreshData"
        :loading="loading"
        class="refresh-btn"
      >
        <el-icon><Refresh :spin="loading" /></el-icon> 刷新
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card" @mouseenter="hoverCard($event)" @mouseleave="leaveCard($event)">
        <div class="stat-icon blue">📊</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_count }}</div>
          <div class="stat-label">总检测次数</div>
        </div>
        <div class="stat-trend up">↑ 12%</div>
      </div>
      <div class="stat-card" @mouseenter="hoverCard($event)" @mouseleave="leaveCard($event)">
        <div class="stat-icon green">🖼️</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.today_count }}</div>
          <div class="stat-label">今日检测</div>
        </div>
        <div class="stat-trend up">↑ 8%</div>
      </div>
      <div class="stat-card" @mouseenter="hoverCard($event)" @mouseleave="leaveCard($event)">
        <div class="stat-icon purple">🎯</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_targets }}</div>
          <div class="stat-label">识别目标总数</div>
        </div>
        <div class="stat-trend down">↓ 3%</div>
      </div>
    </div>

    <!-- 筛选工具栏 -->
    <div class="toolbar">
      <div class="search-wrapper">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索文件名..."
          clearable
          style="width: 260px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <div class="filter-group">
        <el-select v-model="filterMode" placeholder="检测模式" clearable style="width: 130px">
          <el-option label="全部模式" value="" />
          <el-option label="单图检测" value="single" />
          <el-option label="批量检测" value="batch" />
          <el-option label="视频检测" value="video" />
        </el-select>

        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 280px"
        />
      </div>

      <div class="action-group">
        <el-button type="primary" plain @click="exportRecords">
          <el-icon><Download /></el-icon> 导出记录
        </el-button>
        <el-button
          type="danger"
          plain
          @click="clearAllHistory"
          :disabled="records.length === 0"
        >
          <el-icon><Delete /></el-icon> 清空记录
        </el-button>
      </div>
    </div>

    <!-- 历史记录列表 -->
    <div class="history-list">
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <span class="loading-text">加载中...</span>
      </div>

      <div v-else-if="filteredRecords.length === 0" class="empty-container">
        <div class="empty-icon">📭</div>
        <p class="empty-text">暂无检测记录</p>
        <el-button type="primary" @click="$router.push('/')">去检测</el-button>
      </div>

      <transition-group name="list" v-else>
        <div
          v-for="record in paginatedRecords"
          :key="record.id"
          class="history-item"
          @mouseenter="hoverItem($event)"
          @mouseleave="leaveItem($event)"
        >
          <div class="item-images">
            <div class="image-box">
              <span class="box-label">原图</span>
              <img
                :src="record.file_path"
                alt="原图"
                class="preview-img"
                @click="previewImage(record.file_path)"
              />
              <div class="image-overlay">
                <el-icon class="zoom-icon"><ZoomIn /></el-icon>
              </div>
            </div>
            <div class="image-arrow">→</div>
            <div class="image-box">
              <span class="box-label success">结果</span>
              <img
                :src="record.result_path"
                alt="结果图"
                class="preview-img"
                @click="previewImage(record.result_path)"
              />
              <div class="image-overlay">
                <el-icon class="zoom-icon"><ZoomIn /></el-icon>
              </div>
            </div>
          </div>

          <div class="item-info">
            <div class="info-header">
              <h4 class="file-name" :title="record.file_name">{{ record.file_name }}</h4>
              <span class="detect-time">{{ formatTime(record.created_at) }}</span>
            </div>

            <div class="detect-stats">
              <span class="stat-item">
                <el-icon><Aim /></el-icon>
                <span class="stat-num">{{ record.target_count }}</span> 个目标
              </span>
              <span class="stat-item">
                <el-icon><Timer /></el-icon>
                <span class="stat-num">{{ record.duration.toFixed(3) }}s</span>
              </span>
              <span class="stat-item">
                <el-icon><TrendCharts /></el-icon>
                最高 <span class="stat-num">{{ (record.max_confidence * 100).toFixed(1) }}%</span>
              </span>
            </div>

            <div class="target-tags">
              <el-tag
                v-for="(target, idx) in record.detections.slice(0, 4)"
                :key="idx"
                size="small"
                type="info"
                class="target-tag"
              >
                {{ target.class }} {{ (target.confidence * 100).toFixed(0) }}%
              </el-tag>
              <el-tag v-if="record.detections.length > 4" size="small" class="more-tag">
                +{{ record.detections.length - 4 }} 更多
              </el-tag>
            </div>
          </div>

          <div class="item-actions">
            <el-button type="primary" size="small" @click="viewDetail(record)">
              <el-icon><View /></el-icon> 详情
            </el-button>
            <el-button type="danger" size="small" @click="deleteRecord(record.id)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </div>
        </div>
      </transition-group>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="!loading && filteredRecords.length > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="filteredRecords.length"
        layout="total, sizes, prev, pager, next, jumper"
        background
      />
    </div>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="检测详情"
      width="900px"
      top="10vh"
      :close-on-click-modal="false"
    >
      <div v-if="selectedRecord" class="detail-content">
        <div class="detail-images">
          <div class="image-box">
            <span class="box-label">原始图片</span>
            <img :src="selectedRecord.file_path" alt="原图" class="detail-img" />
          </div>
          <div class="image-box">
            <span class="box-label success">检测结果</span>
            <img :src="selectedRecord.result_path" alt="结果" class="detail-img" />
          </div>
        </div>

        <div class="detail-info">
          <h4 class="section-title">📋 检测信息</h4>
          <el-descriptions :column="2" border :size="small">
            <el-descriptions-item label="文件名" label-width="100px">
              <span class="text-ellipsis">{{ selectedRecord.file_name }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="检测时间" label-width="100px">
              {{ selectedRecord.created_at }}
            </el-descriptions-item>
            <el-descriptions-item label="检测耗时" label-width="100px">
              <span class="highlight">{{ selectedRecord.duration.toFixed(3) }}s</span>
            </el-descriptions-item>
            <el-descriptions-item label="识别目标数" label-width="100px">
              <span class="highlight">{{ selectedRecord.target_count }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="检测模型" label-width="100px">
              {{ selectedRecord.model_name || "YOLO11n" }}
            </el-descriptions-item>
            <el-descriptions-item label="最高置信度" label-width="100px">
              <span class="highlight">{{ (selectedRecord.max_confidence * 100).toFixed(1) }}%</span>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="detail-targets">
          <h4 class="section-title">🎯 识别清单</h4>
          <el-table :data="selectedRecord.detections" style="width: 100%" stripe :border="false">
            <el-table-column prop="class" label="类别" width="120" />
            <el-table-column label="置信度" width="200">
              <template #default="{ row }">
                <el-progress
                  :percentage="(row.confidence * 100)"
                  :color="getProgressColor(row.confidence * 100)"
                  :show-text="false"
                />
              </template>
            </el-table-column>
            <el-table-column label="置信度值" width="100">
              <template #default="{ row }">
                <span :class="getConfidenceClass(row.confidence * 100)">
                  {{ (row.confidence * 100).toFixed(1) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column label="位置" width="200">
              <template #default="{ row }">
                <span class="bbox-text">{{ formatBbox(row.bbox) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>

    <!-- 图片预览弹窗 -->
    <el-dialog
      v-model="previewVisible"
      title="图片预览"
      width="800px"
      :close-on-click-modal="true"
    >
      <img :src="previewImageUrl" alt="预览" class="preview-modal-img" />
    </el-dialog>
  </div>
</template>

<script setup>import { ref, computed, onMounted } from "vue";
import axios from "axios";
import { ElMessage, ElMessageBox } from "element-plus";
import { Search, Delete, Aim, Timer, TrendCharts, View, Refresh, Download, ZoomIn } from "@element-plus/icons-vue";
const records = ref([]);
const stats = ref({ total_count: 0, today_count: 0, total_targets: 0 });
const searchKeyword = ref("");
const filterMode = ref("");
const dateRange = ref([]);
const currentPage = ref(1);
const pageSize = ref(10);
const detailVisible = ref(false);
const selectedRecord = ref(null);
const previewVisible = ref(false);
const previewImageUrl = ref("");
const loading = ref(false);
const filteredRecords = computed(() => {
 let list = records.value;
 if (searchKeyword.value) {
 const keyword = searchKeyword.value.toLowerCase();
 list = list.filter((item) => item.file_name.toLowerCase().includes(keyword));
 }
 if (filterMode.value) {
 list = list.filter((item) => item.mode === filterMode.value);
 }
 if (dateRange.value && dateRange.value.length === 2) {
 const startDate = new Date(dateRange.value[0]).toISOString().split("T")[0];
 const endDate = new Date(dateRange.value[1]).toISOString().split("T")[0];
 list = list.filter((item) => {
 const itemDate = item.created_at.split(" ")[0];
 return itemDate >= startDate && itemDate <= endDate;
 });
 }
 return list;
});
const paginatedRecords = computed(() => {
 const start = (currentPage.value - 1) * pageSize.value;
 return filteredRecords.value.slice(start, start + pageSize.value);
});
const getProgressColor = (percentage) => {
 if (percentage >= 80)
 return "#67c23a";
 if (percentage >= 60)
 return "#e6a23c";
 return "#f56c6c";
};
const getConfidenceClass = (percentage) => {
 if (percentage >= 80)
 return "confidence-high";
 if (percentage >= 60)
 return "confidence-medium";
 return "confidence-low";
};
const formatTime = (timeStr) => {
 const date = new Date(timeStr);
 const now = new Date();
 const diff = now - date;
 const days = Math.floor(diff / (1000 * 60 * 60 * 24));
 const hours = Math.floor(diff / (1000 * 60 * 60));
 const minutes = Math.floor(diff / (1000 * 60));
 if (days > 0)
 return `${days}天前`;
 if (hours > 0)
 return `${hours}小时前`;
 if (minutes > 0)
 return `${minutes}分钟前`;
 return "刚刚";
};
const formatBbox = (bbox) => {
 if (!bbox)
 return "-";
 return `(${bbox[0].toFixed(0)}, ${bbox[1].toFixed(0)}) - (${bbox[2].toFixed(0)}, ${bbox[3].toFixed(0)})`;
};
const hoverCard = (e) => {
 e.currentTarget.classList.add("hover");
};
const leaveCard = (e) => {
 e.currentTarget.classList.remove("hover");
};
const hoverItem = (e) => {
 e.currentTarget.classList.add("hover");
};
const leaveItem = (e) => {
 e.currentTarget.classList.remove("hover");
};
const previewImage = (url) => {
 previewImageUrl.value = url;
 previewVisible.value = true;
};
const fetchHistoryList = async () => {
 loading.value = true;
 try {
 const res = await axios.get("http://localhost:8000/api/history/list", {
 params: { page: 1, page_size: 100 }
 });
 if (res.data.code === 200) {
 records.value = res.data.data.records;
 }
 }
 catch (err) {
 console.error("获取历史记录失败:", err);
 ElMessage.error("获取历史记录失败");
 }
 finally {
 loading.value = false;
 fetchStats();
 }
};
const fetchStats = () => {
 const today = new Date().toISOString().split('T')[0];
 let total_count = records.value.length;
 let today_count = 0;
 let total_targets = 0;
 
 records.value.forEach(record => {
 total_targets += record.target_count || 0;
 if (record.created_at && record.created_at.startsWith(today)) {
 today_count++;
 }
 });
 
 stats.value = { total_count, today_count, total_targets };
};
const refreshData = () => {
 currentPage.value = 1;
 fetchHistoryList();
};
const viewDetail = (record) => {
 selectedRecord.value = record;
 detailVisible.value = true;
};
const deleteRecord = async (id) => {
 try {
 await ElMessageBox.confirm("确定要删除这条记录吗？", "提示", {
 confirmButtonText: "确定",
 cancelButtonText: "取消",
 type: "warning",
 });
 const res = await axios.delete(`http://localhost:8000/api/history/${id}`);
 if (res.data.code === 200) {
 ElMessage.success("删除成功");
 fetchHistoryList();
 fetchStats();
 }
 }
 catch (err) {
 if (err !== "cancel") {
 ElMessage.error("删除失败");
 }
 }
};
const clearAllHistory = async () => {
 try {
 await ElMessageBox.confirm("确定要清空所有历史记录吗？此操作不可恢复！", "警告", {
 confirmButtonText: "确定清空",
 cancelButtonText: "取消",
 type: "warning",
 confirmButtonClass: "el-button--danger",
 });
 for (const record of records.value) {
 await axios.delete(`http://localhost:8000/api/history/${record.id}`);
 }
 ElMessage.success("清空成功");
 fetchHistoryList();
 fetchStats();
 }
 catch (err) {
 if (err !== "cancel") {
 ElMessage.error("清空失败");
 }
 }
};
const exportRecords = () => {
 if (filteredRecords.value.length === 0) {
 ElMessage.warning("没有可导出的记录");
 return;
 }
 const exportData = filteredRecords.value.map((record) => ({
 id: record.id,
 file_name: record.file_name,
 target_count: record.target_count,
 duration: record.duration.toFixed(3),
 max_confidence: (record.max_confidence * 100).toFixed(1),
 created_at: record.created_at,
 }));
 const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
 const url = URL.createObjectURL(blob);
 const a = document.createElement("a");
 a.href = url;
 a.download = `检测记录_${new Date().toISOString().split("T")[0]}.json`;
 document.body.appendChild(a);
 a.click();
 document.body.removeChild(a);
 URL.revokeObjectURL(url);
 ElMessage.success("导出成功");
};
onMounted(() => {
 fetchHistoryList();
 fetchStats();
});
</script>

<style scoped>
.history-page {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  margin-bottom: 24px;
  color: #fff;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  font-size: 36px;
}

.header-text h1 {
  font-size: 24px;
  margin-bottom: 4px;
  font-weight: 600;
}

.header-text p {
  font-size: 14px;
  opacity: 0.85;
}

.refresh-btn {
  color: #fff;
  border-color: rgba(255, 255, 255, 0.3);
}

.refresh-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  position: relative;
}

.stat-card:hover,
.stat-card.hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
}

.stat-icon.blue {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(102, 126, 234, 0.2));
}

.stat-icon.green {
  background: linear-gradient(135deg, rgba(103, 194, 58, 0.1), rgba(103, 194, 58, 0.2));
}

.stat-icon.purple {
  background: linear-gradient(135deg, rgba(118, 75, 162, 0.1), rgba(118, 75, 162, 0.2));
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a2e;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #888;
  margin-top: 4px;
}

.stat-trend {
  position: absolute;
  right: 20px;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 12px;
}

.stat-trend.up {
  background: rgba(103, 194, 58, 0.1);
  color: #67c23a;
}

.stat-trend.down {
  background: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  border-radius: 12px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.filter-group {
  display: flex;
  gap: 12px;
}

.action-group {
  display: flex;
  gap: 10px;
}

.history-list {
  min-height: 400px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 80px;
  gap: 16px;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  color: #999;
  font-size: 14px;
}

.empty-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 80px;
  gap: 12px;
}

.empty-icon {
  font-size: 64px;
  opacity: 0.5;
}

.empty-text {
  color: #999;
  font-size: 14px;
  margin: 0;
}

.history-item {
  background: #fff;
  border-radius: 14px;
  padding: 20px;
  display: flex;
  gap: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  border-left: 4px solid transparent;
}

.history-item:hover,
.history-item.hover {
  transform: translateX(4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border-left-color: #667eea;
}

.item-images {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.image-box {
  width: 140px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #e8ecf1;
  position: relative;
}

.image-box img {
  width: 100%;
  height: 100px;
  object-fit: cover;
  cursor: pointer;
}

.box-label {
  display: block;
  padding: 6px 8px;
  font-size: 12px;
  background: #f5f7fa;
  color: #666;
  text-align: center;
  font-weight: 500;
}

.box-label.success {
  background: rgba(103, 194, 58, 0.1);
  color: #67c23a;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.image-box:hover .image-overlay {
  opacity: 1;
}

.zoom-icon {
  color: #fff;
  font-size: 24px;
}

.image-arrow {
  font-size: 24px;
  color: #ddd;
  font-weight: bold;
}

.item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-name {
  font-size: 15px;
  color: #1a1a2e;
  font-weight: 600;
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detect-time {
  font-size: 12px;
  color: #999;
  background: #f5f7fa;
  padding: 4px 10px;
  border-radius: 12px;
}

.detect-stats {
  display: flex;
  gap: 24px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #666;
}

.stat-num {
  font-weight: 600;
  color: #333;
}

.target-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.target-tag {
  background: rgba(102, 126, 234, 0.1);
  border-color: rgba(102, 126, 234, 0.2);
  color: #667eea;
}

.more-tag {
  background: #f5f7fa;
  color: #999;
}

.item-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: center;
}

.pagination {
  margin-top: 28px;
  display: flex;
  justify-content: center;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-images {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.detail-images .image-box {
  width: 380px;
}

.detail-images .image-box img {
  width: 100%;
  height: auto;
  max-height: 320px;
  object-fit: contain;
}

.section-title {
  margin-bottom: 14px;
  color: #1a1a2e;
  font-size: 15px;
  font-weight: 600;
}

.text-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}

.highlight {
  color: #667eea;
  font-weight: 600;
}

.confidence-high {
  color: #67c23a;
  font-weight: 600;
}

.confidence-medium {
  color: #e6a23c;
  font-weight: 600;
}

.confidence-low {
  color: #f56c6c;
  font-weight: 600;
}

.bbox-text {
  font-size: 12px;
  color: #888;
  font-family: monospace;
}

.preview-modal-img {
  width: 100%;
  max-height: 600px;
  object-fit: contain;
}

.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.list-move {
  transition: transform 0.3s ease;
}
</style>