<template>
  <div class="chat-page">
    <!-- 顶部标题区 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">🤖</div>
        <div class="header-text">
          <h1>AI 智能助手</h1>
          <p>有什么问题可以问我，我来帮您解答</p>
        </div>
      </div>
      <el-button
        type="primary"
        plain
        @click="clearChat"
        :disabled="messages.length === 0"
        class="clear-btn"
      >
        <el-icon><Delete /></el-icon> 清空对话
      </el-button>
    </div>

    <!-- 聊天内容区 -->
    <div class="chat-container" ref="chatContainer">
      <!-- 欢迎消息 -->
      <div v-if="messages.length === 0" class="welcome-message">
        <div class="welcome-icon">👋</div>
        <h3>您好！我是您的AI助手</h3>
        <p>我可以帮助您解答关于遥感目标检测的问题</p>
        <div class="quick-questions">
          <span class="quick-btn" @click="sendQuickMessage('什么是遥感目标检测？')">什么是遥感目标检测？</span>
          <span class="quick-btn" @click="sendQuickMessage('支持检测哪些目标类型？')">支持检测哪些目标类型？</span>
          <span class="quick-btn" @click="sendQuickMessage('如何提高检测准确率？')">如何提高检测准确率？</span>
          <span class="quick-btn" @click="sendQuickMessage('检测结果如何导出？')">检测结果如何导出？</span>
        </div>
      </div>

      <!-- 消息列表 -->
      <div v-else class="message-list">
        <div
          v-for="(message, index) in messages"
          :key="index"
          class="message-item"
          :class="message.type"
        >
          <div class="message-avatar">
            {{ message.type === 'user' ? '👤' : '🤖' }}
          </div>
          <div class="message-content">
            <div class="message-header">
              <span class="message-name">{{ message.type === 'user' ? '我' : 'AI助手' }}</span>
              <span class="message-time">{{ message.time }}</span>
            </div>
            <div class="message-body">
              <p v-html="formatMessage(message.content)"></p>
            </div>
          </div>
        </div>
        
        <!-- 加载状态 -->
        <div v-if="loading" class="message-item ai">
          <div class="message-avatar">🤖</div>
          <div class="message-content">
            <div class="typing-indicator">
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="input-area">
      <div class="input-wrapper">
        <el-input
          v-model="inputMessage"
          placeholder="输入您的问题..."
          class="chat-input"
          :disabled="loading"
          @keyup.enter="sendMessage"
        >
          <template #suffix>
            <el-button
              type="primary"
              :loading="loading"
              :disabled="!inputMessage.trim() || loading"
              @click="sendMessage"
              class="send-btn"
            >
              <el-icon><Message /></el-icon>
            </el-button>
          </template>
        </el-input>
      </div>
      <div class="input-tips">
        <span class="tip-item"><el-icon><Aim /></el-icon> 支持 Markdown 格式</span>
        <span class="tip-item">按 Enter 发送</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue';
import { Message, Delete, Aim } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

// 消息列表
const messages = ref([]);

// 输入消息
const inputMessage = ref('');

// 加载状态
const loading = ref(false);

// 聊天容器引用
const chatContainer = ref(null);

// 格式化消息内容（支持简单的 Markdown）
const formatMessage = (content) => {
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
    .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>');
};

// 发送快速消息
const sendQuickMessage = (text) => {
  inputMessage.value = text;
  sendMessage();
};

// 发送消息
const sendMessage = async () => {
  const text = inputMessage.value.trim();
  if (!text || loading.value) return;

  // 添加用户消息
  messages.value.push({
    type: 'user',
    content: text,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  });

  // 清空输入
  inputMessage.value = '';

  // 滚动到底部
  await nextTick();
  scrollToBottom();

  // 模拟AI回复
  loading.value = true;
  
  // 模拟网络延迟
  setTimeout(() => {
    const replies = [
      '遥感目标检测是利用计算机视觉技术从遥感影像中自动识别和定位感兴趣目标的过程。它在城市规划、环境保护、灾害监测等领域有广泛应用。',
      '我们的系统支持检测多种目标类型，包括：飞机、油罐、操场、建筑物、船舶、农业虫害等。',
      '提高检测准确率的方法包括：1) 使用更高分辨率的影像；2) 增加训练数据量；3) 调整模型参数；4) 使用数据增强技术。',
      '检测结果可以通过历史记录页面导出为 JSON 格式文件，方便进行后续分析和处理。',
      '当前系统采用 YOLO11 模型进行目标检测，具有较高的检测速度和准确率。',
      '遥感影像的分辨率会直接影响检测效果，建议使用分辨率不低于 640x640 的影像进行检测。',
      '批量检测功能支持一次上传多张图片进行检测，提高工作效率。',
      '检测完成后，您可以查看目标的位置信息、置信度等详细数据，并支持图片预览和对比查看。'
    ];

    const randomReply = replies[Math.floor(Math.random() * replies.length)];

    messages.value.push({
      type: 'ai',
      content: randomReply,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    });

    loading.value = false;

    // 滚动到底部
    nextTick(() => {
      scrollToBottom();
    });
  }, 1500 + Math.random() * 1000);
};

// 滚动到底部
const scrollToBottom = () => {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
  }
};

// 清空对话
const clearChat = () => {
  messages.value = [];
  ElMessage.success('对话已清空');
};

// 组件挂载时滚动到底部
onMounted(() => {
  scrollToBottom();
});
</script>

<style scoped>
.chat-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.page-header {
  padding: 20px 30px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  font-size: 40px;
}

.header-text h1 {
  margin: 0;
  color: #fff;
  font-size: 24px;
  font-weight: 600;
}

.header-text p {
  margin: 4px 0 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}

.clear-btn {
  color: #fff;
  border-color: rgba(255, 255, 255, 0.3);
}

.clear-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
}

.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px 30px;
  scroll-behavior: smooth;
}

.welcome-message {
  text-align: center;
  padding: 60px 20px;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.welcome-message h3 {
  color: #fff;
  font-size: 24px;
  margin: 0 0 10px;
}

.welcome-message p {
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 30px;
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
}

.quick-btn {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.quick-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message-item {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.message-item.user {
  margin-left: auto;
  flex-direction: row-reverse;
}

.message-item.user .message-content {
  background: #fff;
  border-radius: 16px 16px 4px 16px;
}

.message-item.ai {
  margin-right: auto;
}

.message-item.ai .message-content {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px 16px 16px 4px;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.message-content {
  flex: 1;
  padding: 12px 16px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.message-name {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.message-time {
  font-size: 12px;
  color: #999;
}

.message-body p {
  margin: 0;
  color: #333;
  line-height: 1.6;
  font-size: 14px;
}

.message-body pre {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-body code {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.message-body strong {
  font-weight: 600;
}

.message-body em {
  font-style: italic;
}

/* 输入状态指示器 */
.typing-indicator {
  display: flex;
  gap: 6px;
  padding: 8px 0;
}

.typing-dot {
  width: 8px;
  height: 8px;
  background: #667eea;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-dot:nth-child(1) {
  animation-delay: 0s;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 80%, 100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  40% {
    opacity: 1;
    transform: scale(1);
  }
}

.input-area {
  padding: 20px 30px;
  background: rgba(255, 255, 255, 0.95);
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.input-wrapper {
  display: flex;
  gap: 12px;
}

.chat-input {
  flex: 1;
  border-radius: 24px;
  padding: 12px 20px;
  font-size: 14px;
}

.send-btn {
  border-radius: 50%;
  width: 44px;
  height: 44px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.input-tips {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 12px;
}

.tip-item {
  font-size: 12px;
  color: #999;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 滚动条样式 */
.chat-container::-webkit-scrollbar {
  width: 6px;
}

.chat-container::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.chat-container::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
}

.chat-container::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}
</style>