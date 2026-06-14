#!/bin/bash

# 一键启动前后端 dev server

set -e

API_DIR="/Users/champ/Documents/chatbot/ChatbotApi"
FRONT_DIR="/Users/champ/Documents/chatbot/Chatbot"
VENV_PATH="$API_DIR/venv/bin/activate"

# 检查 Redis
if ! redis-cli ping > /dev/null 2>&1; then
  echo "Redis 未启动，尝试启动..."
  brew services start redis 2>/dev/null || { echo "Redis 启动失败，请手动启动"; exit 1; }
  sleep 2
fi

# 检查端口占用，先清理
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null

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
