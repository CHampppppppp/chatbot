#!/bin/bash
set -e

# 等待Redis服务就绪
if [ "\$WAIT_FOR_REDIS" = "true" ]; then
    echo "等待Redis服务启动..."
    while ! redis-cli -h \${REDIS_HOST:-redis} -p \${REDIS_PORT:-6379} ping > /dev/null 2>&1; do
        echo "Redis未就绪，等待中..."
        sleep 2
    done
    echo "Redis服务已就绪！"
fi

echo "🚀 启动生产模式..."
exec python3 main.py