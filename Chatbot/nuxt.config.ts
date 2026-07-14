// https://nuxt.com/docs/api/configuration/nuxt-config
const isProduction = process.env.NODE_ENV === "production";
const getProductionEnv = (name: string) => {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} must be configured for a production build`);
  }
  return value;
};

const publicApiBase = isProduction
  ? getProductionEnv("NUXT_PUBLIC_API_BASE")
  : "http://localhost:8001";
const apiBase = isProduction
  ? process.env.NUXT_API_BASE || publicApiBase
  : "http://localhost:8001";
const webBaseUrl = isProduction
  ? getProductionEnv("NUXT_PUBLIC_WEB_BASE_URL")
  : "http://localhost:3005";
const appBase = process.env.NUXT_PUBLIC_APP_BASE || "/app1";
const ssoLoginUrl =
  process.env.NUXT_PUBLIC_SSO_LOGIN_URL ||
  "https://szyx.zjer.cn/micro/web/internetSchool/login";

export default defineNuxtConfig({
  app: {
    baseURL: appBase,
    head: {
      title: "校园精灵智能体",
      titleTemplate: "%s | 校园精灵智能体",
      meta: [
        { name: "viewport", content: "width=device-width, initial-scale=1" },
      ],
      link: [{ rel: "icon", type: "image/x-icon", href: "/favicon.ico" }],
    },
    pageTransition: { name: "page", mode: "out-in" },
    layoutTransition: { name: "layout", mode: "out-in" },
  },

  runtimeConfig: {
    apiBase,
    public: {
      apiBase: publicApiBase,
      appBase,
      webBaseUrl,
      ssoLoginUrl,
      isDev: !isProduction,
    },
  },

  routeRules: {
    "/": {}, // ssr
    "/letter": { prerender: true },
    "/login": { ssr: false },
    "/submit-task": {}, // ssr
    "/authorization": { prerender: true },
    "/records": { prerender: true },
    "/stu-register": { ssr: false },
  },

  sourcemap: process.env.NODE_ENV === "development",
  ssr: true,
  devtools: { enabled: process.env.NODE_ENV === "development" },
  compatibilityDate: "2025-05-15",

  css: ["~/assets/css/app.css"],
  modules: ["@nuxtjs/tailwindcss"],

  devServer: {
    port: 3005,
  },
});
