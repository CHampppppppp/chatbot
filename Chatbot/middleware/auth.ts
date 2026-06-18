import { useRuntimeConfig } from "nuxt/app";

const protectedPages = ["/", "/records", "/submit-task", "/authorization"];

export default defineNuxtRouteMiddleware(async (to: any, from: any) => {
  // 只在客户端执行
  if (typeof window === "undefined") {
    return;
  }

  const config = useRuntimeConfig();

  // 对于受保护的页面，检查登录状态
  if (protectedPages.includes(to.path)) {
    try {
      const { data, error } = await useFetch("/users/login-check", {
        baseURL: config.public.apiBase,
        server: false,
        credentials: "include",
        method: "GET",
      });

      // 检查是否有错误且状态码为 401
      if (error.value && error.value.statusCode === 401) {
        // 保存目标路径
        sessionStorage.setItem("sso_target_path", to.fullPath);

        // 未登录时统一跳转到本地登录页
        return navigateTo("/login");
      }
    } catch (error: any) {
      console.error("登录状态检查失败:", error);
      // 保存目标路径
      sessionStorage.setItem("sso_target_path", to.fullPath);

      // 网络或其他异常也跳转到本地登录页
      return navigateTo("/login");
    }
  }
});
