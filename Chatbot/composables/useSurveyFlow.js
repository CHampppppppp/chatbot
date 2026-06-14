import { ref, computed, onMounted, onUnmounted } from "vue";

export const useSurveyFlow = () => {
  // 状态管理
  const surveyStatus = ref(
    localStorage.getItem("surveyStatus") || "not-started"
  );
  const surveyReturnTime = ref(
    localStorage.getItem("surveyReturnTime") || null
  );
  const autoCheckInterval = ref(null);

  // 计算属性
  const isCompleted = computed(() => surveyStatus.value === "completed");
  const isPending = computed(() => surveyStatus.value === "pending");
  const isNotStarted = computed(() => surveyStatus.value === "not-started");

  // 页面焦点监听
  const handleVisibilityChange = () => {
    if (!document.hidden && isPending.value) {
      checkSurveyCompletion();
    }
  };

  const handleWindowFocus = () => {
    if (isPending.value) {
      checkSurveyCompletion();
    }
  };

  // 检查问卷完成状态
  const checkSurveyCompletion = () => {
    const completed = confirm("您是否已完成问卷调查？");
    if (completed) {
      markCompleted();
    }
  };

  // 标记完成
  const markCompleted = () => {
    surveyStatus.value = "completed";
    surveyReturnTime.value = new Date().toLocaleString();

    stopAutoCheck();

    localStorage.setItem("surveyStatus", "completed");
    localStorage.setItem("surveyReturnTime", surveyReturnTime.value);
  };

  // 启动问卷流程
  const startSurvey = (surveyUrl = "https://www.wjx.cn/vm/wmP3uLo.aspx#") => {
    surveyStatus.value = "pending";
    localStorage.setItem("surveyStatus", "pending");

    startAutoCheck();

    const callbackUrl = encodeURIComponent(window.location.href);
    const fullUrl = `${surveyUrl}?callback=${callbackUrl}&source=chatbot`;

    return navigateTo(fullUrl, { external: true });
  };

  // 重置状态
  const reset = () => {
    surveyStatus.value = "not-started";
    surveyReturnTime.value = null;
    stopAutoCheck();
    localStorage.removeItem("surveyStatus");
    localStorage.removeItem("surveyReturnTime");
  };

  // 自动检测
  const startAutoCheck = () => {
    autoCheckInterval.value = setInterval(() => {
      if (isPending.value && !document.hidden) {
        console.log("自动检测问卷状态中...");
      }
    }, 30000);
  };

  const stopAutoCheck = () => {
    if (autoCheckInterval.value) {
      clearInterval(autoCheckInterval.value);
      autoCheckInterval.value = null;
    }
  };

  // 生命周期
  onMounted(() => {
    // 检查URL参数
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("survey") === "completed") {
      markCompleted();
    }

    // 添加监听器
    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("focus", handleWindowFocus);
  });

  onUnmounted(() => {
    document.removeEventListener("visibilitychange", handleVisibilityChange);
    window.removeEventListener("focus", handleWindowFocus);
    stopAutoCheck();
  });

  return {
    surveyStatus,
    surveyReturnTime,
    isCompleted,
    isPending,
    isNotStarted,
    checkSurveyCompletion,
    markCompleted,
    startSurvey,
    reset,
  };
};
