import { useRuntimeConfig } from "nuxt/app";

const protectedPages = ["/", "/records", "/submit-task", "/authorization"];

function buildSsoUrl(config: any) {
  const params = new URLSearchParams({
    response_type: "code",
    client_id: "chatbot",
    scope: "org_user",
    redirect_uri: config.public.webBaseUrl,
  });

  return `${config.public.ssoLoginUrl}?${params.toString()}`;
}

export default defineNuxtRouteMiddleware(async (to: any, from: any) => {
  // 只在客户端执行
  if (typeof window === "undefined") {
    return;
  }

  const config = useRuntimeConfig();

  // dev 模式跳过 SSO 登录检查，并提供默认课程路径，避免本地开发被授权页劫持
  if (config.public.isDev) {
    if (!localStorage.getItem("base_path")) {
      localStorage.setItem("base_path", "app1");
    }
    return;
  }

  // 获取根路径
  const basePath = localStorage.getItem("base_path") || "";
  if (!basePath) {
    return navigateTo("/authorization");
  }

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
        // 设置 SSO 重定向标记，用于后续验证
        sessionStorage.setItem("sso_redirect_initiated", "true");

        // 重定向到 SSO 登录
        return navigateTo(buildSsoUrl(config), { external: true });
      }
    } catch (error: any) {
      console.error("登录状态检查失败:", error);
      // 保存目标路径
      sessionStorage.setItem("sso_target_path", to.fullPath);
      // 设置 SSO 重定向标记，用于后续验证
      sessionStorage.setItem("sso_redirect_initiated", "true");

      // 如果是网络错误或其他异常，也重定向到登录页
      return navigateTo(buildSsoUrl(config), { external: true });
    }
  }
});
