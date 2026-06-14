/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./components/**/*.{js,vue,ts}",
    "./layouts/**/*.vue",
    "./pages/**/*.vue",
    "./plugins/**/*.{js,ts}",
    "./app.vue",
    "./error.vue",
  ],
  theme: {
    extend: {},
  },
  daisyui: {
    themes: [
      {
        // 适度调整浅色主题，实现更和谐的UI
        light: {
          // 基础背景色 - 保持白色基调
          "base-100": "#ffffff",
          "base-200": "#f9fafb",
          "base-300": "#f3f4f6",
          "base-content": "#111827",
          
          // 功能色 - 统一调整为更和谐的色调
          primary: "#3b82f6",
          secondary: "#8b5cf6",
          accent: "#ec4899",
          neutral: "#6b7280",
          info: "#3b82f6",
          success: "#10b981",
          warning: "#f59e0b",
          error: "#ef4444",
        }
      },
      {
        // 添加统一的暗色主题配置
        dark: {
          // 基础背景色
          "base-100": "#111827",
          "base-200": "#1f2937",
          "base-300": "#374151",
          "base-content": "#f3f4f6",
          
          // 与浅色主题统一的功能色
          primary: "#3b82f6",
          secondary: "#8b5cf6",
          accent: "#ec4899",
          neutral: "#9ca3af",
          info: "#3b82f6",
          success: "#10b981",
          warning: "#f59e0b",
          error: "#ef4444",
        }
      },
      "cupcake"
    ],
    darkTheme: "dark", // 默认暗色主题
    base: true, // 使用基础主题（light/dark）
    styled: true, // 使用 DaisyUI 样式
    utils: true, // 使用 DaisyUI 工具类
    prefix: "", // 无前缀
    logs: false, // 禁用日志
  },
  plugins: [require("daisyui")],
};
