#!/bin/bash

# 使用 pm2 管理前后端 dev server
# 用法：
#   ./dev.sh start [--db=local|cloud]  # 启动服务
#   ./dev.sh stop                       # 停止所有服务
#   ./dev.sh restart [--db=local|cloud] # 重启服务
#   ./dev.sh status                     # 查看状态
#   ./dev.sh logs [backend|frontend]    # 查看日志（默认全部）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$SCRIPT_DIR/ChatbotApi"
FRONT_DIR="$SCRIPT_DIR/Chatbot"
VENV_PYTHON="$API_DIR/venv/bin/python"

PM2_APP_API="chatbot-api"
PM2_APP_FRONTEND="chatbot-frontend"

# ── 解析子命令 ──
CMD="${1:-start}"
shift 2>/dev/null || true

DB_PROFILE="local"
for arg in "$@"; do
    if [[ "$arg" =~ ^--db=(local|cloud)$ ]]; then
        DB_PROFILE="${BASH_REMATCH[1]}"
    fi
done

# ── 加载数据库配置 ──
load_env() {
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
}

# ── 启动 Redis ──
ensure_redis() {
    REDIS_PORT=$(echo "${REDIS_URL:-redis://localhost:6379}" | sed -n 's/.*:\([0-9]*\)$/\1/p')
    REDIS_PORT=${REDIS_PORT:-6379}
    if ! redis-cli -p "$REDIS_PORT" ping > /dev/null 2>&1; then
        echo "Redis (端口 $REDIS_PORT) 未启动，尝试启动..."
        if redis-server --port "$REDIS_PORT" --daemonize yes --save "" --appendonly no --dir /tmp 2>/dev/null; then
            sleep 1
            if redis-cli -p "$REDIS_PORT" ping > /dev/null 2>&1; then
                echo "Redis 已在端口 $REDIS_PORT 启动"
            else
                echo "Redis 启动失败，请手动启动"; exit 1
            fi
        elif command -v systemctl > /dev/null 2>&1; then
            sudo systemctl start redis 2>/dev/null || sudo systemctl start redis-server 2>/dev/null || { echo "Redis 启动失败，请手动启动"; exit 1; }
            sleep 2
        else
            echo "未找到 Redis 启动方式，请手动启动 Redis"; exit 1
        fi
    fi
}

# ── 检查 venv ──
ensure_venv() {
    if [ ! -f "$VENV_PYTHON" ]; then
        echo "错误：venv 不存在 ($VENV_PYTHON)，请先创建虚拟环境。"
        exit 1
    fi
}

# ── 子命令实现 ──
case "$CMD" in
    start)
        load_env
        ensure_redis
        ensure_venv

        # 后端
        echo "启动后端 (pm2: $PM2_APP_API)..."
        pm2 start \
            --name "$PM2_APP_API" \
            --cwd "$API_DIR" \
            bash -- -c "source venv/bin/activate && ENV=dev uvicorn main:app --host 0.0.0.0 --port 8001 --reload" \
            > /dev/null

        # 前端
        echo "启动前端 (pm2: $PM2_APP_FRONTEND)..."
        pm2 start \
            --name "$PM2_APP_FRONTEND" \
            --cwd "$FRONT_DIR" \
            pnpm -- dev \
            > /dev/null

        echo ""
        echo "========================================="
        echo "  后端: http://localhost:8001"
        echo "  前端: http://localhost:3005/app1"
        echo "  API文档: http://localhost:8001/docs"
        echo "========================================="
        echo ""
        echo "  pm2 logs          # 查看所有日志"
        echo "  pm2 status        # 查看状态"
        echo "  ./dev.sh stop     # 停止服务"
        echo ""
        ;;

    stop)
        echo "停止所有服务..."
        pm2 delete "$PM2_APP_API" 2>/dev/null || true
        pm2 delete "$PM2_APP_FRONTEND" 2>/dev/null || true
        echo "已停止"
        ;;

    restart)
        echo "重启所有服务..."
        pm2 delete "$PM2_APP_API" 2>/dev/null || true
        pm2 delete "$PM2_APP_FRONTEND" 2>/dev/null || true
        sleep 1
        exec "$0" start "$@"
        ;;

    status)
        pm2 status
        ;;

    logs)
        TARGET="${1:-}"
        case "$TARGET" in
            backend)  pm2 logs "$PM2_APP_API" ;;
            frontend) pm2 logs "$PM2_APP_FRONTEND" ;;
            *)        pm2 logs ;;
        esac
        ;;

    *)
        echo "用法: $0 {start|stop|restart|status|logs} [--db=local|cloud]"
        echo ""
        echo "  start   启动服务（可指定 --db=local|cloud）"
        echo "  stop    停止所有服务"
        echo "  restart 重启服务（可指定 --db=local|cloud）"
        echo "  status  查看 pm2 状态"
        echo "  logs    查看日志（可选 backend|frontend）"
        exit 1
        ;;
esac
