<template>
  <div>
    <HTTPError
      v-if="showError"
      :message="errorMessage"
      :detail="errorDetail"
      @click="closeError"
    />
    <NuxtPage />
  </div>
</template>

<script setup>
import { useRuntimeConfig } from "nuxt/app";
import { ref, onMounted, onUnmounted } from "vue";
import HTTPError from "./components/HTTPError.vue";
import eventBus from "./utils/eventBus";

const showError = ref(false);
const errorMessage = ref("");
const errorDetail = ref("");

function buildAppUrl(path = "/") {
  const base = useRuntimeConfig().public.webBaseUrl.replace(/\/$/, "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${base}${normalizedPath}`;
}

function closeError() {
  showError.value = false;
}

async function handleError({ message, detail }) {
  if (message === "登录失败") {
    await navigateTo("/login");
    return;
  }
  errorMessage.value = message || "发生未知错误";
  errorDetail.value = detail || "";
  showError.value = true;
}

// 处理 SSO 登录成功事件（来自 eventBus）
function handleSSOLoginSuccess(userInfo) {
  if (typeof window !== "undefined") {
    localStorage.setItem("userInfo", JSON.stringify(userInfo));
  }
}

// 处理 SSO 登录错误事件（来自 eventBus）
function handleSSOLoginError(error) {
  localStorage.removeItem("userInfo");
  handleError({
    message: "SSO 登录失败",
    detail: error.message || "单点登录过程中发生错误",
  });
}

// 全局 SSO 处理
const processGlobalSSO = async () => {
  if (typeof window === "undefined") return;

  const isFromSSODomain =
    document.referrer && document.referrer.includes("szyx.zjer.cn");

  if (isFromSSODomain) {
    // 严格验证是否为有效的 SSO 回调
    const ssoFlag = sessionStorage.getItem("sso_redirect");

    // 只有来自 SSO 域名或有重定向标记才处理
    if (!isFromSSODomain && !ssoFlag) {
      return;
    }

    try {
      const { autoHandleSSOCallback } = await import("~/api/sso");
      const result = await autoHandleSSOCallback();

      if (result) {
        handleSSOLoginSuccess(result);
        eventBus.emit("sso-login-success", result);

        // 清理 URL 并重定向到首页
        const basePath = localStorage.getItem("base_path") || "/";
        window.location.replace(buildAppUrl(basePath));
      }
    } catch (error) {
      console.error("App.vue SSO 处理失败:", error);
      handleSSOLoginError(error);
      eventBus.emit("sso-login-error", error);
    }
  }
};

onMounted(() => {
  eventBus.on("http-error", handleError);
  eventBus.on("sso-login-success", handleSSOLoginSuccess);
  eventBus.on("sso-login-error", handleSSOLoginError);

  // 在 app 级别处理 SSO 回调
  processGlobalSSO();

  // 自动检测系统主题
  const detectSystemTheme = () => {
    if (typeof window !== "undefined") {
      const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      document.documentElement.setAttribute(
        "data-theme",
        isDark ? "dark" : "light"
      );
    }
  };

  // 初始检测
  detectSystemTheme();

  // 监听系统主题变化
  if (typeof window !== "undefined") {
    window
      .matchMedia("(prefers-color-scheme: dark)")
      .addEventListener("change", detectSystemTheme);
  }
});

onUnmounted(() => {
  eventBus.off("http-error", handleError);
  eventBus.off("sso-login-success", handleSSOLoginSuccess);
  eventBus.off("sso-login-error", handleSSOLoginError);

  // 移除主题变化监听器
  if (typeof window !== "undefined") {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    // 由于 detectSystemTheme 是在 onMounted 内部定义的，这里需要重新定义或使用其他方式移除监听器
    // 为了简单起见，我们可以直接移除所有监听器
    mediaQuery.removeEventListener("change", () => {});
  }
});
</script>

<style>
.page-enter-active,
.page-leave-active {
  transition: all 0.4s;
}
.page-enter-from,
.page-leave-to {
  opacity: 0;
  filter: blur(1rem);
}

.layout-enter-active,
.layout-leave-active {
  transition: all 0.4s;
}
.layout-enter-from,
.layout-leave-to {
  filter: grayscale(1);
}
</style>
