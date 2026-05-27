<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-header">
        <div class="logo-icon">🛰️</div>
        <h1>遥感目标识别平台</h1>
        <p>多场景影像·精准识别</p>
      </div>

      <el-form
        class="register-form"
        :model="form"
        :rules="rules"
        ref="formRef"
        @submit.prevent="handleRegister"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            size="large"
            prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="请确认密码"
            size="large"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          class="register-btn"
          :loading="loading"
          @click="handleRegister"
        >
          注 册
        </el-button>
      </el-form>

      <div class="register-footer">
        <span>已有账号？</span>
        <a href="/login" class="link">立即登录</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

const router = useRouter();
const formRef = ref(null);
const loading = ref(false);

const form = reactive({
  username: "",
  password: "",
  confirmPassword: "",
});

const rules = {
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { min: 3, max: 20, message: "用户名长度在3到20个字符之间", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, max: 30, message: "密码长度在6到30个字符之间", trigger: "blur" },
  ],
  confirmPassword: [
    { required: true, message: "请确认密码", trigger: "blur" },
    {
      validator: (rule, value, callback) => {
        if (value !== form.password) {
          callback(new Error("两次输入的密码不一致"));
        } else {
          callback();
        }
      },
      trigger: "blur",
    },
  ],
};

const handleRegister = async () => {
  if (!formRef.value) return;

  // 修复：使用 Promise 模式进行表单校验
  try {
    await formRef.value.validate();
  } catch (error) {
    // 校验失败，直接返回，不继续执行注册逻辑
    ElMessage.warning("请检查表单填写是否正确");
    return;
  }

  loading.value = true;

  try {
    const response = await fetch("http://localhost:8000/api/auth/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: form.username,
        password: form.password,
      }),
    });

    const result = await response.json();

    if (result.code === 200) {
      ElMessage.success("注册成功！即将跳转至首页");
      
      localStorage.setItem("isLoggedIn", "true");
      localStorage.setItem("username", result.data.username);
      localStorage.setItem("userRole", result.data.role);
      localStorage.setItem("userInfo", JSON.stringify(result.data));

      setTimeout(() => {
        router.push("/");
      }, 1500);
    } else {
      ElMessage.error(result.message || "注册失败");
    }
  } catch (error) {
    ElMessage.error("注册失败，请稍后重试");
    console.error("Registration error:", error);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

.register-container {
  width: 400px;
  background: #fff;
  border-radius: 16px;
  padding: 48px 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.register-header {
  text-align: center;
  margin-bottom: 36px;
}

.logo-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.register-header h1 {
  font-size: 24px;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.register-header p {
  font-size: 13px;
  color: #999;
}

.register-form {
  margin-bottom: 24px;
}

.register-form :deep(.el-input__wrapper) {
  padding: 12px 16px;
  border-radius: 8px;
}

.register-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  border-radius: 8px;
  background: linear-gradient(135deg, #00c9a7, #00b894);
  border: none;
  margin-top: 8px;
}

.register-btn:hover {
  background: linear-gradient(135deg, #00b894, #00a381);
}

.register-footer {
  text-align: center;
  font-size: 13px;
  color: #999;
}

.register-footer .link {
  color: #00c9a7;
  margin-left: 4px;
  text-decoration: none;
}

.register-footer .link:hover {
  text-decoration: underline;
}
</style>