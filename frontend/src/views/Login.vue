<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <div class="logo-icon">🛰️</div>
        <h1>遥感目标识别平台</h1>
        <p>多场景影像·精准识别</p>
      </div>

      <el-form
        class="login-form"
        :model="form"
        :rules="rules"
        ref="formRef"
        @submit.prevent="handleLogin"
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

        <el-button
          type="primary"
          size="large"
          class="login-btn"
          :loading="loading"
          @click="handleLogin"
        >
          登 录
        </el-button>
      </el-form>

      <div class="login-footer">
        <p>默认账号：admin / admin123</p>
        <p class="register-link">还没有账号？<a href="/register">立即注册</a></p>
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
});

const rules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

const handleLogin = async () => {
  if (!formRef.value) return;

  await formRef.value.validate((valid) => {
    if (!valid) return;
  });

  loading.value = true;

  try {
    const response = await fetch("http://localhost:8000/api/auth/login", {
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
      localStorage.setItem("isLoggedIn", "true");
      localStorage.setItem("username", result.data.username);
      localStorage.setItem("userRole", result.data.role);
      localStorage.setItem("userInfo", JSON.stringify(result.data));
      ElMessage.success("登录成功！");
      router.push("/");
    } else {
      ElMessage.error(result.message || "用户名或密码错误！");
    }
  } catch (error) {
    ElMessage.error("登录失败，请稍后重试");
    console.error("Login error:", error);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

.login-container {
  width: 400px;
  background: #fff;
  border-radius: 16px;
  padding: 48px 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.logo-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.login-header h1 {
  font-size: 24px;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.login-header p {
  font-size: 13px;
  color: #999;
}

.login-form {
  margin-bottom: 24px;
}

.login-form :deep(.el-input__wrapper) {
  padding: 12px 16px;
  border-radius: 8px;
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  border-radius: 8px;
  background: linear-gradient(135deg, #00c9a7, #00b894);
  border: none;
  margin-top: 8px;
}

.login-btn:hover {
  background: linear-gradient(135deg, #00b894, #00a381);
}

.login-footer {
  text-align: center;
}

.login-footer p {
  font-size: 12px;
  color: #ccc;
}

.login-footer .register-link {
  margin-top: 8px;
}

.login-footer .register-link a {
  color: #00c9a7;
  text-decoration: none;
}

.login-footer .register-link a:hover {
  text-decoration: underline;
}
</style>