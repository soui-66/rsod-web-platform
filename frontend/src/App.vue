<template>
  <div>
    <!-- 登录页不需要布局 -->
    <router-view v-if="!isLoggedIn" />

    <!-- 已登录显示工作台布局 -->
    <div v-else class="layout">
      <!-- 左侧导航栏 -->
      <div class="sidebar">
        <div class="sidebar-logo">
          <div class="logo-icon">🛰️</div>
          <div class="logo-text">
            <h2>遥感目标识别平台</h2>
            <p>多场景影像·精准识别</p>
          </div>
        </div>
        <div class="sidebar-menu">
          <div
            v-for="item in menuItems"
            :key="item.path"
            class="menu-item"
            :class="{ active: currentRoute === item.path }"
            @click="$router.push(item.path)"
          >
            <span class="menu-icon">{{ item.icon }}</span>
            <span class="menu-label">{{ item.label }}</span>
          </div>
        </div>
      </div>

      <!-- 右侧主区域 -->
      <div class="main-area">
        <!-- 顶部栏 -->
        <div class="header">
          <div class="breadcrumb">
            <span>工作台</span>
            <span class="separator">></span>
            <span>{{ currentPageName }}</span>
          </div>
          <div class="user-info">
            <div class="avatar">{{ username.charAt(0).toUpperCase() }}</div>
            <div class="user-detail">
              <span class="username">{{ username }}</span>
              <span class="user-role">{{ userRole }}</span>
            </div>
            <el-button type="danger" size="small" @click="handleLogout">
              退出
            </el-button>
          </div>
        </div>

        <!-- 内容区域 -->
        <div class="content">
          <router-view />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();
const isLoggedIn = ref(false);
const username = ref("");
const userRole = ref("");

const currentRoute = computed(() => route.path);

const menuItems = ref([
  { path: "/", icon: "🎯", label: "智能检测" },
  { path: "/history", icon: "📋", label: "历史记录" },
  { path: "/ai-chat", icon: "💬", label: "AI 问答" },
  { path: "/targets", icon: "📊", label: "目标库" },
  { path: "/profile", icon: "👤", label: "个人中心" },
]);

const currentPageName = computed(() => {
  const item = menuItems.value.find((m) => m.path === currentRoute.value);
  return item ? item.label : "智能检测";
});

const handleLogout = () => {
  localStorage.removeItem("isLoggedIn");
  localStorage.removeItem("username");
  localStorage.removeItem("userRole");
  router.push("/login");
};

onMounted(() => {
  isLoggedIn.value = localStorage.getItem("isLoggedIn") === "true";
  username.value = localStorage.getItem("username") || "";
  userRole.value = localStorage.getItem("userRole") || "";
});
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial,
    sans-serif;
  background-color: #f5f7fa;
}

.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* 左侧导航栏 */
.sidebar {
  width: 220px;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-logo {
  padding: 24px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo-icon {
  font-size: 32px;
}

.logo-text h2 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.logo-text p {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
}

.sidebar-menu {
  padding: 16px 12px;
  flex: 1;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 4px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.menu-item.active {
  background: linear-gradient(135deg, #00c9a7, #00b894);
  color: #fff;
  font-weight: 500;
}

.menu-icon {
  font-size: 18px;
}

/* 右侧主区域 */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部栏 */
.header {
  height: 60px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid #e8ecf1;
  flex-shrink: 0;
}

.breadcrumb {
  font-size: 14px;
  color: #666;
}

.breadcrumb .separator {
  margin: 0 8px;
  color: #ccc;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #00c9a7, #00b894);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.user-detail {
  display: flex;
  flex-direction: column;
  margin-right: 8px;
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.user-role {
  font-size: 11px;
  color: #999;
}

/* 内容区域 */
.content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
</style>