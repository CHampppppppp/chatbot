module.exports = {
  apps: [
    {
      // 后端：FastAPI（端口 8001）
      name: "chatbot-backend",
      cwd: "./ChatbotApi",
      script: "pnpm",
      args: "run dev",
      watch: false,
      max_restarts: 10,
      min_uptime: "10s",
      restart_delay: 3000,
      max_memory_restart: "1G",
      env: {
        PYTHONUNBUFFERED: "1",
      },
      error_file: "../logs/backend-error.log",
      out_file: "../logs/backend-out.log",
      merge_logs: true,
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
    },
    {
      // 前端：Nuxt 3 开发服务器（端口 3005）
      name: "chatbot-frontend",
      cwd: "./Chatbot",
      script: "pnpm",
      args: "run dev",
      watch: false,
      max_restarts: 10,
      min_uptime: "10s",
      restart_delay: 3000,
      max_memory_restart: "500M",
      env: {
        NODE_ENV: "development",
      },
      error_file: "../logs/frontend-error.log",
      out_file: "../logs/frontend-out.log",
      merge_logs: true,
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
    },
  ],
};
