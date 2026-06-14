import axios from "axios";
import eventBus from "~/utils/eventBus";

function getErrorPayload(data: any, fallbackMessage: string) {
  const detail = data?.detail;

  if (typeof detail === "string") {
    return {
      message: detail || fallbackMessage,
      detail: "",
    };
  }

  return {
    message: detail?.msg || data?.msg || fallbackMessage,
    detail: detail?.error || data?.error || "",
  };
}

export default defineNuxtPlugin((nuxtApp) => {
  const config = useRuntimeConfig();

  // 根据环境选择正确的 baseURL
  const baseURL = process.server ? config.apiBase : config.public.apiBase;

  const api = axios.create({
    baseURL,
    timeout: 5000,
    withCredentials: true,
  });

  api.interceptors.response.use(
    (response) => {
      return response;
    },
    (error) => {
      if (error.response) {
        const { data } = error.response;
        switch (error.response.status) {
          case 401: {
            eventBus.emit("http-error", getErrorPayload(data, "请重新登录"));
            return Promise.reject(error);
          }
          case 403: {
            eventBus.emit("http-error", getErrorPayload(data, "权限不足"));
            return Promise.reject(error);
          }
          default:
            eventBus.emit("http-error", getErrorPayload(data, "请求错误"));
            return Promise.reject(error);
        }
      } else if (error.request) {
        eventBus.emit("http-error", {
          message: "无法连接至服务器",
          detail: error.request.responseText || "服务器不可用",
        });
      } else {
        eventBus.emit("http-error", {
          message: "无法连接至服务器，请稍后重试",
          detail: error.message || "服务器不可用",
        });
      }
      return Promise.reject(error);
    }
  );

  // 将 axios 实例注入到 Nuxt 应用中
  return {
    provide: {
      axios: api,
    },
  };
});
