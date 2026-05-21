import { createRouter, createWebHistory } from "vue-router";
import Inference from "../views/Inference.vue";
import Login from "../views/Login.vue";
import Register from "../views/Register.vue";
import History from "../views/History.vue";

const routes = [
  {
    path: "/login",
    name: "login",
    component: Login,
    meta: { requiresAuth: false },
  },
  {
    path: "/register",
    name: "register",
    component: Register,
    meta: { requiresAuth: false },
  },
  {
    path: "/",
    name: "inference",
    component: Inference,
    meta: { requiresAuth: true },
  },
  {
    path: "/history",
    name: "history",
    component: History,
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// 路由守卫：登录验证
router.beforeEach((to, from, next) => {
  const isLoggedIn = localStorage.getItem("isLoggedIn") === "true";

  if (to.meta.requiresAuth && !isLoggedIn) {
    // 需要登录但未登录，跳转到登录页
    next("/login");
  } else if (to.path === "/login" && isLoggedIn) {
    // 已登录访问登录页，跳转到首页
    next("/");
  } else {
    next();
  }
});

export default router;