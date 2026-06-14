<template>
  <div class="p-6 max-w-2xl mx-auto">
    <h1 class="text-2xl font-bold mb-6">SSO 测试页面</h1>

    <!-- SSO 状态显示 -->
    <div class="bg-base-200 p-4 rounded-lg mb-6">
      <h2 class="text-lg font-semibold mb-2">SSO 状态</h2>
      <div v-if="isProcessing" class="text-primary">
        🔄 正在处理 SSO 回调...
      </div>
      <div v-else-if="userInfo" class="text-success">
        ✅ SSO 登录成功
        <pre class="mt-2 text-sm bg-base-100 p-2 rounded">{{
          JSON.stringify(userInfo, null, 2)
        }}</pre>
      </div>
      <div v-else-if="error" class="text-error">
        ❌ SSO 登录失败
        <pre class="mt-2 text-sm bg-base-100 p-2 rounded">{{ error.message }}</pre>
      </div>
      <div v-else class="text-base-content">
        ⏳ 等待 SSO 回调或未检测到 SSO 参数
      </div>
    </div>

    <!-- URL 参数检查 -->
    <div class="bg-base-200 p-4 rounded-lg mb-6">
      <h2 class="text-lg font-semibold mb-2">当前 URL 参数</h2>
      <div v-if="urlParams.code || urlParams.fromBusiness">
        <p><strong>Code:</strong> {{ urlParams.code || "无" }}</p>
        <p><strong>State:</strong> {{ urlParams.fromBusiness || "无" }}</p>
        <p class="mt-2">
          <span v-if="isSSOCallback" class="text-success"
            >✅ 检测到 SSO 回调参数</span
          >
          <span v-else class="text-warning">⚠️ SSO 参数不完整</span>
        </p>
      </div>
      <div v-else class="text-base-content">无查询参数</div>
    </div>

    <!-- 手动触发 -->
    <div class="bg-base-200 p-4 rounded-lg mb-6">
      <h2 class="text-lg font-semibold mb-2">手动测试</h2>
      <button
        @click="manualProcess"
        :disabled="isProcessing"
        class="bg-primary text-primary-content px-4 py-2 rounded hover:bg-primary/90 disabled:opacity-50"
      >
        手动处理 SSO 回调
      </button>
    </div>

    <!-- 模拟测试 -->
    <div class="bg-base-200 p-4 rounded-lg">
      <h2 class="text-lg font-semibold mb-2">模拟测试</h2>
      <p class="text-sm text-base-content/80 mb-2">
        点击下面的链接模拟 SSO 重定向（会添加测试参数到当前页面）
      </p>
      <button
        @click="simulateSSO"
        class="bg-success text-success-content px-4 py-2 rounded hover:bg-success/90"
      >
        模拟 SSO 重定向
      </button>
    </div>
  </div>
</template>

<script setup>
const { isProcessing, userInfo, error, processSSO, isSSOCallback } = useSSO();

// 获取当前 URL 参数
const urlParams = ref({});

// 手动处理 SSO
const manualProcess = async () => {
  try {
    await processSSO();
  } catch (err) {
    console.error("手动处理失败:", err);
  }
};

// 模拟 SSO 重定向
const simulateSSO = () => {
  const currentUrl = new URL(window.location);
  currentUrl.searchParams.set("code", "test_code_" + Date.now());
  currentUrl.searchParams.set(
    "fromBusiness",
    "test_fromBusiness_" + Date.now()
  );
  window.location.href = currentUrl.toString();
};

// 更新 URL 参数显示
const updateUrlParams = () => {
  if (typeof window !== "undefined") {
    const urlSearchParams = new URLSearchParams(window.location.search);
    urlParams.value = {
      code: urlSearchParams.get("code"),
      fromBusiness: urlSearchParams.get("fromBusiness"),
    };
  }
};

onMounted(() => {
  updateUrlParams();

  // 监听 SSO 事件
  const handleSSOSuccess = (result) => {
    console.log("页面监听到 SSO 成功:", result);
  };

  const handleSSOError = (err) => {
    console.error("页面监听到 SSO 失败:", err);
  };

  eventBus.on("sso-login-success", handleSSOSuccess);
  eventBus.on("sso-login-error", handleSSOError);

  onUnmounted(() => {
    eventBus.off("sso-login-success", handleSSOSuccess);
    eventBus.off("sso-login-error", handleSSOError);
  });
});
</script>
