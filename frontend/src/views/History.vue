<template>
  <div class="history-page">
    <!-- 顶部标题区 -->
    <div class="page-header">
      <h1>📋 检测历史记录</h1>
      <p>查看和管理您的所有检测记录</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon blue">📊</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_count }}</div>
          <div class="stat-label">总检测次数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green">🖼️</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.today_count }}</div>
          <div class="stat-label">今日检测</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon purple">🎯</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_targets }}</div>
          <div class="stat-label">识别目标总数</div>
        </div>
      </div>
    </div>

    <!-- 筛选工具栏 -->
    <div class="toolbar">
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

      <el-select v-model="filterMode" placeholder="检测模式" clearable style="width: 130px">
        <el-option label="单图检测" value="single" />
        <el-option label="批量检测" value="batch" />
        <el-option label="视频检测" value="video" />
      </el-select>

      <el-button type="danger" plain @click="clearAllHistory" :disabled="records.length === 0">
        <el-icon><Delete /></el-icon> 清空记录
      </el-button>
    </div>

    <!-- 历史记录列表 -->
    <div class="history-list">
      <el-empty v-if="filteredRecords.length === 0" description="暂无检测记录" />

      <div
        v-for="record in paginatedRecords"
        :key="record.id"
        class="history-item"
      >
        <div class="item-images">
          <div class="image-box">
            <span class="box-label">原图</span>
            <img :src="record.file_path" alt="原图" />
          </div>
          <div class="image-arrow">→</div>
          <div class="image-box">
            <span class="box-label success">结果</span>
            <img :src="record.result_path" alt="结果图" />
          </div>
        </div>

        <div class="item-info">
          <div class="info-header">
            <h4 class="file-name">{{ record.file_name }}</h4>
            <span class="detect-time">{{ record.created_at }}</span>
          </div>

          <div class="detect-stats">
            <span class="stat-item">
              <el-icon><Aim /></el-icon>
              {{ record.target_count }} 个目标
            </span>
            <span class="stat-item">
              <el-icon><Timer /></el-icon>
              {{ record.duration.toFixed(3) }}s
            </span>
            <span class="stat-item">
              <el-icon><TrendCharts /></el-icon>
              最高 {{ (record.max_confidence * 100).toFixed(1) }}%
            </span>
          </div>

          <div class="target-tags">
            <el-tag
              v-for="(target, idx) in record.detections.slice(0, 4)"
              :key="idx"
              size="small"
              type="info"
            >
              {{ target.class }} {{ (target.confidence * 100).toFixed(0) }}%
            </el-tag>
            <el-tag v-if="record.detections.length > 4" size="small">
              +{{ record.detections.length - 4 }}
            </el-tag>
          </div>
        </div>

        <div class="item-actions">
          <el-button type="primary" @click="viewDetail(record)">
            <el-icon><View /></el-icon> 详情
          </el-button>
          <el-button type="danger" @click="deleteRecord(record.id)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="filteredRecords.length > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="filteredRecords.length"
        layout="total, sizes, prev, pager, next"
      />
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="检测详情" width="900px">
      <div v-if="selectedRecord" class="detail-content">
        <div class="detail-images">
          <div class="image-box">
            <span class="box-label">原始图片</span>
            <img :src="selectedRecord.file_path" alt="原图" />
          </div>
          <div class="image-box">
            <span class="box-label success">检测结果</span>
            <img :src="selectedRecord.result_path" alt="结果" />
          </div>
        </div>

        <div class="detail-info">
          <h4>📋 检测信息</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="文件名">{{ selectedRecord.file_name }}</el-descriptions-item>
            <el-descriptions-item label="检测时间">{{ selectedRecord.created_at }}</el-descriptions-item>
            <el-descriptions-item label="检测耗时">{{ selectedRecord.duration.toFixed(3) }}s</el-descriptions-item>
            <el-descriptions-item label="识别目标数">{{ selectedRecord.target_count }}</el-descriptions-item>
            <el-descriptions-item label="检测模型">{{ selectedRecord.model_name }}</el-descriptions-item>
            <el-descriptions-item label="最高置信度">{{ (selectedRecord.max_confidence * 100).toFixed(1) }}%</el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="detail-targets">
          <h4>🎯 识别清单</h4>
          <el-table :data="selectedRecord.detections" style="width: 100%" stripe>
            <el-table-column prop="class" label="类别" width="120" />
            <el-table-column label="置信度">
              <template #default="{ row }">
                <el-progress
                  :percentage="(row.confidence * 100)"
                  :color="getProgressColor(row.confidence * 100)"
                />
              </template>
            </el-table-column>
            <el-table-column label="数值" width="100">
              <template #default="{ row }">
                {{ (row.confidence * 100).toFixed(1) }}%
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import axios from "axios";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Search,
  Delete,
  Aim,
  Timer,
  TrendCharts,
  View,
} from "@element-plus/icons-vue";

const records = ref([]);
const stats = ref({ total_count: 0, today_count: 0, total_targets: 0 });
const searchKeyword = ref("");
const filterMode = ref("");
const currentPage = ref(1);
const pageSize = ref(10);
const detailVisible = ref(false);
const selectedRecord = ref(null);

const filteredRecords = computed(() => {
  let list = records.value;

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    list = list.filter((item) =>
      item.file_name.toLowerCase().includes(keyword)
    );
  }

  if (filterMode.value) {
    list = list.filter((item) => item.mode === filterMode.value);
  }

  return list;
});

const paginatedRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredRecords.value.slice(start, start + pageSize.value);
});

const getProgressColor = (percentage) => {
  if (percentage >= 80) return "#67c23a";
  if (percentage >= 60) return "#e6a23c";
  return "#f56c6c";
};

const fetchHistoryList = async () => {
  try {
    const userId = localStorage.getItem("user_id");
    const res = await axios.get("http://localhost:8000/api/history/list", {
      params: { user_id: userId || null, page: 1, page_size: 100 }
    });
    if (res.data.code === 200) {
      records.value = res.data.data.records;
    }
  } catch (err) {
    console.error("获取历史记录失败:", err);
  }
};

const fetchStats = async () => {
  try {
    const userId = localStorage.getItem("user_id");
    const res = await axios.get("http://localhost:8000/api/history/stats", {
      params: { user_id: userId || null }
    });
    if (res.data.code === 200) {
      stats.value = res.data.data;
    }
  } catch (err) {
    console.error("获取统计数据失败:", err);
  }
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
  } catch (err) {
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
    });

    for (const record of records.value) {
      await axios.delete(`http://localhost:8000/api/history/${record.id}`);
    }

    ElMessage.success("清空成功");
    fetchHistoryList();
    fetchStats();
  } catch (err) {
    if (err !== "cancel") {
      ElMessage.error("清空失败");
    }
  }
};

onMounted(() => {
  fetchHistoryList();
  fetchStats();
});
</script>

<style scoped>
.history-page {
  max-width: 1200px;
  margin: 0 auto;
}

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
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.blue {
  background: rgba(102, 126, 234, 0.1);
}
.stat-icon.green {
  background: rgba(103, 194, 58, 0.1);
}
.stat-icon.purple {
  background: rgba(118, 75, 162, 0.1);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #333;
}

.stat-label {
  font-size: 13px;
  color: #999;
}

.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-item {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  gap: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.item-images {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.image-box {
  width: 140px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #eee;
}

.image-box img {
  width: 100%;
  height: 100px;
  object-fit: cover;
}

.box-label {
  display: block;
  padding: 6px 8px;
  font-size: 12px;
  background: #f5f7fa;
  color: #666;
  text-align: center;
}

.box-label.success {
  background: rgba(103, 194, 58, 0.1);
  color: #67c23a;
}

.image-arrow {
  font-size: 20px;
  color: #999;
}

.item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-name {
  font-size: 15px;
  color: #333;
  font-weight: 600;
}

.detect-time {
  font-size: 12px;
  color: #999;
}

.detect-stats {
  display: flex;
  gap: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #666;
}

.target-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.item-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: center;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-images {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.detail-images .image-box {
  width: 350px;
}

.detail-images .image-box img {
  width: 100%;
  height: auto;
  max-height: 300px;
  object-fit: contain;
}

.detail-info h4,
.detail-targets h4 {
  margin-bottom: 12px;
  color: #333;
}
</style>