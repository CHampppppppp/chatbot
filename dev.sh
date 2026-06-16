#!/bin/bash

# 一键启动前后端 dev server
# 用法：
#   ./dev.sh           # 使用默认 .env（python-dotenv 自动加载）
#   ./dev.sh --db=local # 使用 .env.local（本地 MySQL）
#   ./dev.sh --db=cloud # 使用 .env.cloud（云 SQL Server）

set -e

API_DIR="/Users/champ/Documents/chatbot/ChatbotApi"
FRONT_DIR="/Users/champ/Documents/chatbot/Chatbot"
VENV_PATH="$API_DIR/venv/bin/activate"

DB_PROFILE=""
if [[ "$1" =~ ^--db=(local|cloud)$ ]]; then
    DB_PROFILE="${BASH_REMATCH[1]}"
fi

if [ -n "$DB_PROFILE" ]; then
    ENV_FILE="$API_DIR/.env.$DB_PROFILE"
    if [ -f "$ENV_FILE" ]; then
        echo "使用数据库配置: $ENV_FILE"
        set -a
        source "$ENV_FILE"
        set +a
    else
        echo "错误：$ENV_FILE 不存在，请先复制对应 .env.*.example 文件。"
        exit 1
    fi
fi

# 检查 Redis
if ! redis-cli ping > /dev/null 2>&1; then
  echo "Redis 未启动，尝试启动..."
  brew services start redis 2>/dev/null || { echo "Redis 启动失败，请手动启动"; exit 1; }
  sleep 2
fi

# 检查端口占用，先清理
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# 启动后端
echo "启动后端..."
cd "$API_DIR"
source "$VENV_PATH"
ENV=dev uvicorn main:app --host 0.0.0.0 --port 8001 --reload &
BACK_PID=$!

# 启动前端
echo "启动前端..."
cd "$FRONT_DIR"
pnpm dev &
FRONT_PID=$!

echo ""
echo "========================================="
echo "  后端: http://localhost:8001"
echo "  前端: http://localhost:3000/app1"
echo "  API文档: http://localhost:8001/docs"
echo "========================================="
echo ""
echo "按 Ctrl+C 关闭所有服务"

# 等待任一进程退出
wait $BACK_PID $FRONT_PID
