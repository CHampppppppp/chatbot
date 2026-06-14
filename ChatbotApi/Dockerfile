# Multi-stage build: 第一阶段用于构建依赖，第二阶段运行时镜像（减小最终大小 ~30MB）
FROM python:3.11.14-slim-bookworm as builder

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ENV=production \
    REDIS_URL=redis://redis:6379 \
    TZ=Asia/Shanghai

WORKDIR /ChatbotApi

# 配置清华大学Debian镜像源并解决GPG问题
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|http://security.debian.org/debian-security|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' /etc/apt/sources.list.d/debian.sources

# 更新GPG密钥并安装系统依赖
RUN apt-get update --allow-unauthenticated && \
    apt-get install -y --allow-unauthenticated \
        tzdata \
        gcc \
        g++ \
        curl \
        redis-tools \
        gnupg \
        ca-certificates \
        poppler-utils && \
    apt-get update && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# 复制依赖文件（利用Docker缓存）
COPY requirements.txt .

# 配置pip使用阿里云镜像源
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com

# 安装Python依赖（--user 安装到用户目录，优化复制）
RUN pip install --no-cache-dir -r requirements.txt

# 创建非root用户（提前创建，提高安全性）
RUN useradd -m -u 1000 chatbot && \
    mkdir -p /ChatbotApi/logs /ChatbotApi/uploads /ChatbotApi/homeworks && \
    chown -R chatbot:chatbot /ChatbotApi /home/chatbot

# 复制应用代码（顺序优化：先 mkdir/chown，后 COPY）
COPY --chown=chatbot:chatbot . .

# --- 第二阶段：运行时镜像 ---
FROM python:3.11-slim

# 复制系统依赖（poppler-utils 等，从 builder 复制最小依赖）
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/include /usr/local/include
COPY --from=builder /etc/apt/sources.list.d /etc/apt/sources.list.d

# 安装运行时系统依赖（最小化，添加 update 以应用清华源）
RUN apt-get update --allow-unauthenticated && \
    apt-get install -y --allow-unauthenticated \
        curl \
        redis-tools \
        ca-certificates \
        poppler-utils && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# 设置环境变量（同 builder）
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ENV=production \
    REDIS_URL=redis://redis:6379 \
    PATH="/home/chatbot/.local/bin:${PATH}"

WORKDIR /ChatbotApi

# 从 builder 复制用户安装的依赖和代码（用户 ID 1000 已匹配，无需重新 useradd）
COPY --from=builder --chown=1000:1000 /home/chatbot /home/chatbot
COPY --from=builder --chown=1000:1000 /ChatbotApi /ChatbotApi

# 切换到非root用户
USER 1000

# 健康检查（优化：使用 /health 端点，interval 30s 匹配 SLB，timeout 5s）
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -I -f http://localhost:8001/health || exit 1

# 暴露端口
EXPOSE 8001

# 复制启动脚本（作为主机文件 COPY，--chown 生效）
COPY --chown=1000:1000 entrypoint.sh /ChatbotApi/entrypoint.sh

# 设置脚本权限（作为 root 执行）
USER root
RUN chmod +x /ChatbotApi/entrypoint.sh
USER 1000

# 使用启动脚本作为入口点
ENTRYPOINT ["/ChatbotApi/entrypoint.sh"]