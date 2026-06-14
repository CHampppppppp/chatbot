import { autoHandleSSOCallback } from "~/api/sso";
import eventBus from "~/utils/eventBus";

export default function useSSO() {
  const isProcessing = ref(false);
  const userInfo = ref(null);
  const error = ref(null);

  // 手动处理 SSO 回调（通常不需要调用，app.vue 会自动处理）
  const processSSO = async () => {
    if (isProcessing.value) return;

    try {
      isProcessing.value = true;
      error.value = null;

      console.log("useSSO: Processing SSO callback...");

      const result = await autoHandleSSOCallback();

      if (result) {
        userInfo.value = result;
        console.log("useSSO: SSO callback processed successfully:", result);
        eventBus.emit("sso-login-success", result);
        return true;
      }

      return false;
    } catch (err) {
      error.value = err;
      console.error("useSSO: SSO callback processing failed:", err);
      eventBus.emit("sso-login-error", err);
      throw err;
    } finally {
      isProcessing.value = false;
    }
  };

  // 监听全局 SSO 事件
  onMounted(() => {
    eventBus.on("sso-login-success", (result) => {
      userInfo.value = result;
    });

    eventBus.on("sso-login-error", (err) => {
      error.value = err;
    });
  });

  onUnmounted(() => {
    eventBus.off("sso-login-success");
    eventBus.off("sso-login-error");
  });

  return {
    isProcessing: readonly(isProcessing),
    userInfo: readonly(userInfo),
    error: readonly(error),
    processSSO,
    isSSOCallback,
  };
}
