<template>
  <div class="chat-container">
    <div class="chat-header">
      <div class="header-left">
        <el-icon class="ai-icon"><Aim /></el-icon>
        <div>
          <h3>AI 助手</h3>
          <span>遥感目标检测专家</span>
        </div>
      </div>
      <el-button type="danger" size="small" @click="clearHistory">清空历史</el-button>
    </div>

    <div class="chat-content" ref="chatContainer">
      <div v-if="messages.length === 0" class="welcome-container">
        <div class="welcome-icon">
          <el-icon><Message /></el-icon>
        </div>
        <h2>欢迎使用 AI 助手</h2>
        <p>我可以帮您解答关于遥感目标检测的问题</p>

        <div class="quick-questions">
          <div
            class="question-item"
            v-for="(q, index) in quickQuestions"
            :key="index"
            @click="sendQuickMessage(q)"
          >
            {{ q }}
          </div>
        </div>
      </div>

      <div v-else class="messages-list">
        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="['message-item', msg.type]"
        >
          <div class="message-avatar">
            <el-icon v-if="msg.type === 'ai'"><Aim /></el-icon>
            <el-icon v-else><User /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-header">
              <span>{{ msg.type === 'ai' ? 'AI 助手' : '您' }}</span>
              <span class="message-time">{{ msg.time }}</span>
            </div>
            <div class="message-text">{{ msg.content }}</div>
          </div>
        </div>

        <div v-if="loading" class="message-item ai">
          <div class="message-avatar">
            <el-icon><Aim /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-header">
              <span>AI 助手</span>
            </div>
            <div class="message-text">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-input-area">
      <div class="input-wrapper">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          placeholder="输入您的问题..."
          @keydown.enter.ctrl="sendMessage"
          class="chat-input"
        />
        <div class="input-actions">
          <el-button @click="clearMessages" circle>
            <el-icon><Delete /></el-icon>
          </el-button>
          <el-button type="primary" @click="sendMessage" :loading="loading" circle size="large">
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
      <div class="input-tip">按 Ctrl+Enter 发送</div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue';
import { Message, Delete, Aim, User, ArrowRight } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const quickQuestions = [
  '什么是遥感目标检测？',
  '支持检测哪些目标？',
  '如何提高检测准确率？',
  '如何导出检测结果？'
];

const messages = ref([]);
const inputMessage = ref('');
const loading = ref(false);
const chatContainer = ref(null);

const getCurrentUserId = () => {
  const userInfo = localStorage.getItem('userInfo');
  if (userInfo) {
    try {
      return JSON.parse(userInfo).id || 1;
    } catch {
      return 1;
    }
  }
  return 1;
};

const loadHistory = async () => {
  try {
    const userId = getCurrentUserId();
    const response = await axios.get(`${API_URL}/chat/history`, {
      params: { user_id: userId }
    });
    if (response.data.code === 200) {
      const history = response.data.data;
      messages.value = history.map((msg, index) => ({
        type: msg.role === 'assistant' ? 'ai' : 'user',
        content: msg.content,
        time: ''
      }));
    }
  } catch (err) {
    console.error('加载历史记录失败:', err);
  }
};

const clearHistory = async () => {
  try {
    const userId = getCurrentUserId();
    await axios.delete(`${API_URL}/chat/history`, {
      params: { user_id: userId }
    });
    messages.value = [];
    ElMessage.success('历史记录已清空');
  } catch (err) {
    console.error('清空历史记录失败:', err);
    ElMessage.error('清空历史记录失败');
  }
};

const clearMessages = () => {
  messages.value = [];
};

const sendQuickMessage = (text) => {
  inputMessage.value = text;
  sendMessage();
};

const sendMessage = async () => {
  const text = inputMessage.value.trim();
  if (!text || loading.value) {
    return;
  }

  messages.value.push({
    type: 'user',
    content: text,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  });

  inputMessage.value = '';

  await nextTick();
  scrollToBottom();

  loading.value = true;

  try {
    const userId = getCurrentUserId();
    const apiMessages = messages.value.map(msg => ({
      role: msg.type === 'user' ? 'user' : 'assistant',
      content: msg.content
    }));

    const response = await axios.post(`${API_URL}/chat/completion`, {
      messages: apiMessages,
      user_id: userId
    });

    if (response && response.data) {
      const res = response.data;

      if (res.code === 200 && res.data && res.data.content) {
        messages.value.push({
          type: 'ai',
          content: res.data.content,
          time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
        });
      } else {
        ElMessage.error(res.message || 'AI 回复失败');
      }
    } else {
      ElMessage.error('API 响应为空');
    }
  } catch (err) {
    console.error('Chat error:', err);
    ElMessage.error('网络错误，请稍后重试');
  } finally {
    loading.value = false;
    nextTick(() => {
      scrollToBottom();
    });
  }
};

const scrollToBottom = () => {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
  }
};

onMounted(() => {
  loadHistory();
  nextTick(() => {
    scrollToBottom();
  });
});

onUnmounted(() => {
});
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
}

.chat-header {
  padding: 20px 30px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.ai-icon {
  font-size: 32px;
  color: #3b82f6;
}

.chat-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.chat-header span {
  display: block;
  font-size: 13px;
  color: #6b7280;
}

.chat-content {
  flex: 1;
  overflow-y: auto;
  padding: 30px;
}

.welcome-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
}

.welcome-icon {
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  box-shadow: 0 10px 40px rgba(59, 130, 246, 0.3);
}

.welcome-icon .el-icon {
  font-size: 48px;
  color: white;
}

.welcome-container h2 {
  margin: 0 0 10px 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.welcome-container p {
  margin: 0 0 30px 0;
  font-size: 14px;
  color: #6b7280;
}

.quick-questions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  max-width: 500px;
}

.question-item {
  padding: 14px 20px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  color: #374151;
  text-align: left;
}

.question-item:hover {
  border-color: #3b82f6;
  background: #eff6ff;
  color: #1d4ed8;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message-item {
  display: flex;
  gap: 12px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 20px;
}

.message-item.ai .message-avatar {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}

.message-item.user .message-avatar {
  background: #10b981;
  color: white;
}

.message-content {
  max-width: 70%;
}

.message-item.user .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.message-header span:first-child {
  font-weight: 600;
  font-size: 14px;
  color: #374151;
}

.message-time {
  font-size: 12px;
  color: #9ca3af;
}

.message-text {
  padding: 14px 18px;
  border-radius: 14px;
  font-size: 15px;
  line-height: 1.6;
  word-wrap: break-word;
}

.message-item.ai .message-text {
  background: white;
  color: #1f2937;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.message-item.user .message-text {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #9ca3af;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-8px);
  }
}

.chat-input-area {
  padding: 20px 30px;
  background: white;
  border-top: 1px solid #e5e7eb;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.chat-input {
  flex: 1;
}

.chat-input :deep(.el-textarea__inner) {
  border-radius: 12px;
  border-color: #d1d5db;
  resize: none;
  font-size: 15px;
}

.chat-input :deep(.el-textarea__inner:focus) {
  border-color: #3b82f6;
}

.input-actions {
  display: flex;
  gap: 10px;
}

.input-tip {
  text-align: center;
  margin-top: 10px;
  font-size: 12px;
  color: #9ca3af;
}
</style>