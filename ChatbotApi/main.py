import logging
import os
import pickle
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from router.router import api_router

class NoHeadFilter(logging.Filter):
    """
    自定义过滤器：排除 HEAD 方法的访问日志。
    """
    def filter(self, record: logging.LogRecord) -> bool:
        # Uvicorn access 日志的 record.args 结构：
        # args[0]: 客户端 IP 和端口 (e.g., "127.0.0.1:12345")
        # args[1]: HTTP 方法 (e.g., "HEAD", "GET")
        # args[2]: 请求路径 + 查询字符串 (e.g., "/api/users")
        # args[3]: HTTP 版本 (e.g., "HTTP/1.1")
        # args[4]: 状态码 (e.g., 200)
        if record.args and len(record.args) >= 2:
            # 如果方法是 HEAD，过滤掉（返回 False）
            return record.args[1] != "HEAD"
        # 其他日志通过
        return True

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 获取 Uvicorn 的 access logger 并添加过滤器
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.addFilter(NoHeadFilter())

# Redis配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client: Optional[redis.Redis] = None

# 调度器（全局变量）
scheduler: Optional[AsyncIOScheduler] = None


async def reset_daily_quota():
    """每日凌晨0点清空所有用户的昨日配额缓存（异步版本）"""
    try:
        if not redis_client:
            logger.error("[定时任务] Redis客户端未初始化")
            return
        
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        
        # 使用异步扫描避免阻塞
        patterns = [
            f"user:*:image_generate:{yesterday}",
            f"user:*:image_edit:{yesterday}"
        ]
        
        keys_to_delete = []
        for pattern in patterns:
            async for key in redis_client.scan_iter(match=pattern, count=100):
                keys_to_delete.append(key)
        
        if keys_to_delete:
            await redis_client.delete(*keys_to_delete)
            logger.info(f"[定时任务] 每日配额重置完成，删除 {len(keys_to_delete)} 个昨日配额键")
        else:
            logger.info("[定时任务] 无过期配额键需要清理")
            
    except Exception as e:
        logger.error(f"[定时任务] 配额重置失败: {str(e)}")


class SessionData:
    """会话数据类，用于管理会话状态"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[Dict[str, Any]] = [
            {
                "role": "system",
                "content": "You are a helpful assistant. If the user requests an image, call the 'generate_image' function.",
            }
        ]
        self.last_activity = time.time()
        self.max_messages = 50

    def add_message(self, role: str, content: str):
        """添加消息并维护消息数量限制"""
        self.messages.append({"role": role, "content": content})
        self.last_activity = time.time()

        if len(self.messages) > self.max_messages:
            system_msg = self.messages[0]
            self.messages = [system_msg] + self.messages[-(self.max_messages - 1) :]

    def is_expired(self, timeout: int = 3600) -> bool:
        """检查会话是否过期（默认1小时）"""
        return time.time() - self.last_activity > timeout

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "session_id": self.session_id,
            "messages": self.messages,
            "last_activity": self.last_activity,
            "max_messages": self.max_messages,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionData":
        """从字典反序列化"""
        instance = cls(data["session_id"])
        instance.messages = data["messages"]
        instance.last_activity = data["last_activity"]
        instance.max_messages = data["max_messages"]
        return instance


# Redis会话管理器
class RedisSessionManager:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.session_prefix = "websocket_session:"
        self.session_ttl = 3600

    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """获取会话数据"""
        try:
            key = f"{self.session_prefix}{session_id}"
            data = await self.redis.get(key)
            if data:
                session_dict = pickle.loads(data)
                return SessionData.from_dict(session_dict)
            return None
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None

    async def save_session(self, session_data: SessionData):
        """保存会话数据"""
        try:
            key = f"{self.session_prefix}{session_data.session_id}"
            data = pickle.dumps(session_data.to_dict())
            await self.redis.setex(key, self.session_ttl, data)
        except Exception as e:
            logger.error(f"Error saving session {session_data.session_id}: {e}")


session_manager: Optional[RedisSessionManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global redis_client, session_manager, scheduler

    try:
        # 1. 初始化 Redis
        redis_client = redis.from_url(
            REDIS_URL, decode_responses=False, max_connections=20
        )
        await redis_client.ping()
        session_manager = RedisSessionManager(redis_client)
        logger.info("✅ Redis 连接成功")

        # 2. 初始化并启动调度器
        scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
        
        # 添加每日0点重置任务
        scheduler.add_job(
            reset_daily_quota,
            trigger="cron",
            hour=0,
            minute=0,
            second=0,
            id="reset_daily_quota",
            name="每日配额重置",
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("✅ 定时任务调度器启动成功（每日0点重置配额）")

        yield  # 应用运行期间

        # 3. 关闭调度器
        if scheduler:
            scheduler.shutdown(wait=True)
            logger.info("调度器已关闭")

        # 4. 关闭 Redis
        if redis_client:
            await redis_client.close()
        logger.info("应用关闭完成")

    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise


app = FastAPI(lifespan=lifespan)


# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://nginx",
        "http://127.0.0.1:3005",
        "http://localhost:3005",
        "https://chatbot.mgsai.cn",
        "https://szyx.zjer.cn",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加所有API路由
app.include_router(api_router, prefix="")


@app.get("/")
async def index():
    return {
        "status": "running",
        "mode": "production",
        "services": ["websocket-chatbot", "rest-api", "database"],
        "websocket": "/ws/{session_id}",
        "api_docs": "/docs",
    }


@app.head("/health")
async def health_check():
    """健康检查端点"""
    try:
        redis_status = "disconnected"
        if redis_client:
            await redis_client.ping()
            redis_status = "connected"
        
        scheduler_status = "running" if scheduler and scheduler.running else "stopped"
        next_reset = None
        if scheduler and scheduler.running:
            job = scheduler.get_job("reset_daily_quota")
            if job and job.next_run_time:
                next_reset = job.next_run_time.isoformat()
        
        return {
            "status": "healthy",
            "redis": redis_status,
            "scheduler": scheduler_status,
            "next_quota_reset": next_reset
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


if __name__ == "__main__":
    import multiprocessing

    import uvicorn

    cpu_count = multiprocessing.cpu_count()

    try:
        import uvloop
        loop_type = "uvloop"
    except ImportError:
        loop_type = "asyncio"

    print("🚀 启动生产模式")
    print(f"💻 CPU核心: {cpu_count}")
    print(f"🔄 事件循环: {loop_type}")
    print("🌐 监听地址: 0.0.0.0:8001")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        workers=cpu_count,
        timeout_graceful_shutdown=120,
        limit_max_requests=1000,
        loop=loop_type,
        log_level="info",
        reload=False,
    )
