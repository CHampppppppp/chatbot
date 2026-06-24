import { fetchEventSource } from "@microsoft/fetch-event-source";

export const records = async (type, meta) => {
  const { $axios } = useNuxtApp();
  await $axios.post("/records/add", { type, meta });
};

export const getProfile = async () => {
  const { $axios } = useNuxtApp();
  const res = await $axios.get("/platform/profile");
  return res.data;
};

export const updateProfile = async (profileData) => {
  const { $axios } = useNuxtApp();
  const res = await $axios.put("/platform/profile", profileData);
  return res.data;
};

export const sendFeedback = async (messageId, feedback) => {
  const { $axios } = useNuxtApp();
  const res = await $axios.post("/platform/feedback", {
    message_id: messageId,
    feedback,
  });
  return res.data;
};

export const startEvalSession = async () => {
  const { $axios } = useNuxtApp();
  const res = await $axios.post("/platform/session/start");
  return res.data;
};

export const appendEvalSessionMessage = async (sessionId, messages) => {
  const { $axios } = useNuxtApp();
  const res = await $axios.post(`/platform/session/${sessionId}/message`, {
    messages,
  });
  return res.data;
};

export const endEvalSession = async (sessionId) => {
  const { $axios } = useNuxtApp();
  const res = await $axios.post(`/platform/session/${sessionId}/end`);
  return res.data;
};

export const getDimensions = async () => {
  const { $axios } = useNuxtApp();
  const res = await $axios.get("/platform/dimensions");
  return res.data;
};

export const fetchChatStream = (url, data, onMessage) => {
  const controller = new AbortController();
  const { signal } = controller;

  const isFormData =
    typeof FormData !== "undefined" && data instanceof FormData;

  fetchEventSource(url, {
    method: "POST",
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
    },
    cache: "no-store",
    credentials: "include",
    body: isFormData ? data : JSON.stringify(data),

    onmessage(event) {
      onMessage(event, controller);
    },

    onclose() {
      console.log("Connection closed by the server.");
    },

    onerror(error) {
      console.error("fetchEventSource error:", error);

      // 处理HTTP错误状态码
      if (error.status) {
        switch (error.status) {
          case 401:
            console.error("认证失败，跳转到登录页");
            // navigateTo("/login");
            break;
          case 403:
            console.error("权限不足");
            alert("权限不足，请联系管理员");
            break;
          case 500:
            console.error("服务器内部错误");
            alert("服务器内部错误，请稍后再试");
            break;
          default:
            console.error(`HTTP错误: ${error.status}`);
        }
      }

      // 对于 content-type 错误，不要重试
      if (error.message && error.message.includes("content-type")) {
        console.error("服务器返回的Content-Type不正确，请检查服务器端配置");
        controller.abort();
        return;
      }

      // 可以抛出错误让调用方处理
      throw error;
    },

    async onopen(response) {
      // 检查响应状态和Content-Type
      const contentType = response.headers.get("content-type") || "";
      if (
        response.ok &&
        (contentType.includes("text/event-stream") ||
          contentType.includes("application/json"))
      ) {
        return; // 一切正常
      } else if (response.status >= 400 && response.status < 500) {
        // 客户端错误，不要重试
        throw new Error(`客户端错误: ${response.status}`);
      } else if (response.status >= 500) {
        // 服务器错误，可以重试
        throw new RetriableError(`服务器错误: ${response.status}`);
      } else {
        // Content-Type 不正确
        throw new Error(
          `服务器返回的Content-Type不正确。期望: text/event-stream 或 application/json, 实际: ${contentType}`
        );
      }
    },

    signal,
  });

  return controller;
};
