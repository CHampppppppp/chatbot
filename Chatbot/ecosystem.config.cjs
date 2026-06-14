module.exports = {
  apps: [
    {
      name: "chatbot-app1",
      script: "./.output/server/index.mjs", // Nuxt 3构建输出的服务器文件
      instances: process.env.PM2_INSTANCES || "max", // 或者具体数字，如 2
      exec_mode: "cluster",
      node_args: "--max-old-space-size=1024", // 单进程内存限制

      // 环境变量
      env: {
        NODE_ENV: "production",
        HOST: "0.0.0.0",
        PORT: 3001,
        UV_THREADPOOL_SIZE: process.env.UV_THREADPOOL_SIZE || "4", // 线程池 = CPU 核，提升 I/O
      },

      // 自动重启配置
      watch: false,
      max_memory_restart: "2G",
      min_uptime: "10s",
      max_restarts: 10,
      restart_delay: 6000,

      // 日志配置
      log_type: "none", // 设置为none，确保性能
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      error_file: "/Chatbot-App1/logs/err.log",
      out_file: "/Chatbot-App1/logs/out.log",
      log_file: "/Chatbot-App1/logs/combined.log",
      merge_logs: true,

      // 进程管理
      kill_timeout: 5000,
      listen_timeout: 8000,

      // 环境特定配置
      env_production: {
        NITRO_PRESET: "node_cluster",
        NODE_ENV: "production",
        PORT: 3001,
        UV_THREADPOOL_SIZE: "4",
      },
    },
  ],
};
