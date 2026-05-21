<template>
  <div class="profile-page">
    <!-- 顶部用户卡片 -->
    <div class="user-card">
      <div class="user-avatar">
        <span class="avatar-text">{{ username.charAt(0).toUpperCase() }}</span>
        <div class="avatar-badge">
          <el-icon><User /></el-icon>
        </div>
      </div>
      <div class="user-info">
        <h2>{{ username }}</h2>
        <div class="user-meta">
          <span class="role-tag">{{ userRole === 'admin' ? '管理员' : '普通用户' }}</span>
          <span class="join-date">注册于 {{ joinDate }}</span>
        </div>
      </div>
      <div class="user-stats">
        <div class="stat-item">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">总检测</div>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.today }}</div>
          <div class="stat-label">今日检测</div>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.targets }}</div>
          <div class="stat-label">识别目标</div>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧导航 -->
      <div class="sidebar">
        <div
          v-for="item in menuItems"
          :key="item.key"
          class="menu-item"
          :class="{ active: activeTab === item.key }"
          @click="activeTab = item.key"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </div>
      </div>

      <!-- 右侧内容 -->
      <div class="content-area">
        <!-- 基本信息 -->
        <div v-if="activeTab === 'info'" class="tab-content">
          <div class="section-header">
            <h3>基本信息</h3>
            <el-button type="text" @click="editInfo = !editInfo">
              {{ editInfo ? '取消' : '编辑' }}
            </el-button>
          </div>
          
          <el-form :model="userForm" class="info-form">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="用户名">
                  <el-input
                    v-model="userForm.username"
                    :disabled="!editInfo"
                    placeholder="请输入用户名"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="角色">
                  <el-input
                    v-model="userForm.role"
                    disabled
                    placeholder="用户角色"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="注册时间">
                  <el-input
                    v-model="userForm.joinDate"
                    disabled
                    placeholder="注册时间"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="最后登录">
                  <el-input
                    v-model="userForm.lastLogin"
                    disabled
                    placeholder="最后登录时间"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="简介">
              <el-input
                v-model="userForm.bio"
                :disabled="!editInfo"
                placeholder="简单介绍一下自己..."
                type="textarea"
                :rows="3"
              />
            </el-form-item>
            <el-form-item v-if="editInfo">
              <el-button type="primary" @click="saveInfo">保存修改</el-button>
              <el-button @click="editInfo = false">取消</el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 修改密码 -->
        <div v-if="activeTab === 'password'" class="tab-content">
          <div class="section-header">
            <h3>修改密码</h3>
          </div>
          
          <el-form
            :model="passwordForm"
            :rules="passwordRules"
            ref="passwordFormRef"
            class="password-form"
          >
            <el-form-item prop="oldPassword">
              <el-input
                v-model="passwordForm.oldPassword"
                type="password"
                placeholder="请输入当前密码"
                prefix-icon="Lock"
              />
            </el-form-item>
            <el-form-item prop="newPassword">
              <el-input
                v-model="passwordForm.newPassword"
                type="password"
                placeholder="请输入新密码"
                prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            <el-form-item prop="confirmPassword">
              <el-input
                v-model="passwordForm.confirmPassword"
                type="password"
                placeholder="请确认新密码"
                prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :loading="passwordLoading"
                @click="changePassword"
              >
                确认修改
              </el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 检测记录 -->
        <div v-if="activeTab === 'history'" class="tab-content">
          <div class="section-header">
            <h3>最近检测记录</h3>
            <el-button type="primary" plain @click="$router.push('/history')">
              查看全部
            </el-button>
          </div>
          
          <div v-if="recentRecords.length > 0" class="history-list">
            <div
              v-for="record in recentRecords"
              :key="record.id"
              class="history-item"
              @click="$router.push('/history')"
            >
              <div class="history-image">
                <img :src="record.image_url" :alt="record.file_name" />
              </div>
              <div class="history-info">
                <div class="history-name">{{ record.file_name }}</div>
                <div class="history-meta">
                  <span>{{ record.target_count }} 个目标</span>
                  <span>{{ record.max_confidence }}%</span>
                </div>
              </div>
              <div class="history-time">{{ record.time_ago }}</div>
            </div>
          </div>
          <div v-else class="empty-state">
            <div class="empty-icon">📭</div>
            <p>暂无检测记录</p>
            <el-button type="primary" @click="$router.push('/')">去检测</el-button>
          </div>
        </div>

        <!-- 安全设置 -->
        <div v-if="activeTab === 'security'" class="tab-content">
          <div class="section-header">
            <h3>安全设置</h3>
          </div>
          
          <div class="security-list">
            <div class="security-item">
              <div class="security-info">
                <div class="security-icon">🔐</div>
                <div>
                  <div class="security-title">登录密码</div>
                  <div class="security-desc">保护您的账户安全</div>
                </div>
              </div>
              <el-button type="text" @click="activeTab = 'password'">修改</el-button>
            </div>
            <div class="security-item">
              <div class="security-info">
                <div class="security-icon">📧</div>
                <div>
                  <div class="security-title">绑定邮箱</div>
                  <div class="security-desc">用于找回密码和接收通知</div>
                </div>
              </div>
              <span class="security-status">未绑定</span>
            </div>
            <div class="security-item">
              <div class="security-info">
                <div class="security-icon">📱</div>
                <div>
                  <div class="security-title">绑定手机</div>
                  <div class="security-desc">用于身份验证和安全提醒</div>
                </div>
              </div>
              <span class="security-status">未绑定</span>
            </div>
          </div>
        </div>

        <!-- 系统设置 -->
        <div v-if="activeTab === 'settings'" class="tab-content">
          <div class="section-header">
            <h3>系统设置</h3>
          </div>
          
          <el-form :model="settingsForm" class="settings-form">
            <el-form-item label="语言">
              <el-select v-model="settingsForm.language" placeholder="请选择语言">
                <el-option label="简体中文" value="zh-CN" />
                <el-option label="English" value="en" />
              </el-select>
            </el-form-item>
            <el-form-item label="主题">
              <el-select v-model="settingsForm.theme" placeholder="请选择主题">
                <el-option label="明亮模式" value="light" />
                <el-option label="暗色模式" value="dark" />
                <el-option label="跟随系统" value="auto" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-switch v-model="settingsForm.notification" />
              <span class="switch-label">接收通知</span>
            </el-form-item>
            <el-form-item>
              <el-switch v-model="settingsForm.emailNotify" />
              <span class="switch-label">邮件通知</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveSettings">保存设置</el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { useRouter } from "vue-router";
import { User, Lock, Aim, Bell, View, Download } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";

const router = useRouter();
const activeTab = ref("info");
const editInfo = ref(false);
const passwordLoading = ref(false);
const passwordFormRef = ref(null);

// 用户信息
const username = ref(localStorage.getItem("username") || "");
const userRole = ref(localStorage.getItem("userRole") || "user");
const joinDate = ref("2024-01-15");

// 用户表单
const userForm = reactive({
  username: username.value,
  role: userRole.value === "admin" ? "管理员" : "普通用户",
  joinDate: joinDate.value,
  lastLogin: "2024-01-20 14:30",
  bio: ""
});

// 密码表单
const passwordForm = reactive({
  oldPassword: "",
  newPassword: "",
  confirmPassword: ""
});

// 密码验证规则
const passwordRules = {
  oldPassword: [
    { required: true, message: "请输入当前密码", trigger: "blur" }
  ],
  newPassword: [
    { required: true, message: "请输入新密码", trigger: "blur" },
    { min: 6, max: 30, message: "密码长度在6到30个字符之间", trigger: "blur" }
  ],
  confirmPassword: [
    { required: true, message: "请确认新密码", trigger: "blur" },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error("两次输入的密码不一致"));
        } else {
          callback();
        }
      },
      trigger: "blur"
    }
  ]
};

// 设置表单
const settingsForm = reactive({
  language: "zh-CN",
  theme: "light",
  notification: true,
  emailNotify: false
});

// 统计数据
const stats = reactive({
  total: 156,
  today: 8,
  targets: 423
});

// 最近记录
const recentRecords = ref([
  {
    id: 1,
    file_name: "aircraft_001.jpg",
    image_url: "https://via.placeholder.com/80x80",
    target_count: 3,
    max_confidence: 95.6,
    time_ago: "10分钟前"
  },
  {
    id: 2,
    file_name: "tank_002.jpg",
    image_url: "https://via.placeholder.com/80x80",
    target_count: 5,
    max_confidence: 89.2,
    time_ago: "1小时前"
  },
  {
    id: 3,
    file_name: "building_003.jpg",
    image_url: "https://via.placeholder.com/80x80",
    target_count: 12,
    max_confidence: 92.8,
    time_ago: "3小时前"
  }
]);

// 菜单列表
const menuItems = [
  { key: "info", label: "基本信息", icon: User },
  { key: "password", label: "修改密码", icon: Lock },
  { key: "history", label: "检测记录", icon: View },
  { key: "security", label: "安全设置", icon: Aim },
  { key: "settings", label: "系统设置", icon: Bell }
];

// 保存信息
const saveInfo = () => {
  username.value = userForm.username;
  localStorage.setItem("username", userForm.username);
  editInfo.value = false;
  ElMessage.success("信息修改成功");
};

// 修改密码
const changePassword = async () => {
  if (!passwordFormRef.value) return;
  
  passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      passwordLoading.value = true;
      // 模拟API请求
      await new Promise(resolve => setTimeout(resolve, 1500));
      passwordLoading.value = false;
      ElMessage.success("密码修改成功，请重新登录");
      // 清空表单
      passwordForm.oldPassword = "";
      passwordForm.newPassword = "";
      passwordForm.confirmPassword = "";
    }
  });
};

// 保存设置
const saveSettings = () => {
  ElMessage.success("设置保存成功");
};

onMounted(() => {
  // 可以在这里获取用户真实数据
});
</script>

<style scoped>
.profile-page {
  min-height: 100%;
  padding: 20px;
  background: #f5f7fa;
}

/* 用户卡片 */
.user-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 30px;
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 20px;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
}

.user-avatar {
  position: relative;
}

.avatar-text {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 32px;
  font-weight: 600;
}

.avatar-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #00c9a7;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
}

.user-info h2 {
  margin: 0;
  color: #fff;
  font-size: 24px;
  font-weight: 600;
}

.user-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
}

.role-tag {
  padding: 4px 12px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  color: #fff;
  font-size: 12px;
}

.join-date {
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}

.user-stats {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 24px;
  background: rgba(255, 255, 255, 0.1);
  padding: 16px 24px;
  border-radius: 12px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #fff;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 4px;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
}

/* 主内容区 */
.main-content {
  display: flex;
  gap: 20px;
}

/* 左侧导航 */
.sidebar {
  width: 200px;
  background: #fff;
  border-radius: 12px;
  padding: 12px;
  flex-shrink: 0;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  color: #666;
  font-size: 14px;
}

.menu-item:hover {
  background: #f5f7fa;
  color: #667eea;
}

.menu-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

/* 右侧内容 */
.content-area {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  padding: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

/* 表单样式 */
.info-form, .password-form, .settings-form {
  max-width: 600px;
}

.info-form .el-form-item,
.password-form .el-form-item,
.settings-form .el-form-item {
  margin-bottom: 20px;
}

.switch-label {
  margin-left: 8px;
  color: #666;
}

/* 历史记录列表 */
.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.history-item:hover {
  background: #f0f2f5;
  transform: translateX(4px);
}

.history-image img {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  object-fit: cover;
}

.history-info {
  flex: 1;
}

.history-name {
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.history-meta {
  display: flex;
  gap: 16px;
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}

.history-time {
  font-size: 12px;
  color: #999;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 40px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state p {
  color: #999;
  margin-bottom: 16px;
}

/* 安全设置列表 */
.security-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.security-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.security-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.security-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.security-title {
  font-weight: 500;
  color: #333;
}

.security-desc {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.security-status {
  padding: 4px 12px;
  background: #fff3e0;
  border-radius: 20px;
  color: #fa8c16;
  font-size: 12px;
}
</style>