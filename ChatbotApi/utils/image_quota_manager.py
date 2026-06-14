"""
图像服务配额管理器（完全异步）
支持图像生成和图像编辑的每日配额限制

重要说明：
- user_id 使用 SSO 系统的 userId（来自 JWT token）
- 这是用户在 SSO 系统中的唯一标识（如工号、学号等）
- 确保跨系统的唯一性和准确性
"""

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from typing import Tuple

import redis as sync_redis
import redis.asyncio as redis
from sqlalchemy.orm import Session

from db.models import ImageServiceLog

# 创建线程池用于执行同步数据库操作
_db_thread_pool = ThreadPoolExecutor(max_workers=10)

logger = logging.getLogger(__name__)


class ImageServiceType(str, Enum):
    """图像服务类型枚举"""

    GENERATE = "image_generate"  # 图像生成（每日10次）
    EDIT = "image_edit"  # 图像编辑（每日3次）


class ImageQuotaManager:
    """图像服务配额管理器"""

    # 配额限制配置
    QUOTA_LIMITS = {ImageServiceType.GENERATE: 10, ImageServiceType.EDIT: 3}

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    @staticmethod
    def _get_redis_key(user_id: str, service_type: ImageServiceType) -> str:
        """
        生成Redis键: user:{sso_userId}:{service_type}:{YYYYMMDD}

        Args:
            user_id: SSO 用户唯一标识（来自 JWT token 的 userId 字段）
            service_type: 服务类型（image_generate 或 image_edit）
        """
        today = datetime.now().strftime("%Y%m%d")
        return f"user:{user_id}:{service_type.value}:{today}"

    @staticmethod
    def _get_quota_limit(service_type: ImageServiceType) -> int:
        """获取指定服务的配额限制"""
        return ImageQuotaManager.QUOTA_LIMITS.get(service_type, 0)

    @staticmethod
    def _seconds_until_midnight() -> int:
        """计算距离今日23:59:59还有多少秒"""
        now = datetime.now()
        end_of_day = datetime(now.year, now.month, now.day, 23, 59, 59)
        return int((end_of_day - now).total_seconds()) + 1

    async def check_quota_async(
        self, user_id: str, service_type: ImageServiceType
    ) -> Tuple[bool, int]:
        """
        异步检查配额（不扣除）

        Args:
            user_id: SSO 用户唯一标识（来自 JWT token 的 userId 字段）
            service_type: 服务类型

        Returns:
            (是否有余额, 剩余次数)
        """
        try:
            redis_key = self._get_redis_key(user_id, service_type)
            limit = self._get_quota_limit(service_type)

            # 从Redis获取已使用次数
            used_bytes = await self.redis.get(redis_key)
            used = int(used_bytes) if used_bytes else 0

            remaining = limit - used
            has_quota = remaining > 0

            logger.debug(
                f"配额检查: user={user_id}, type={service_type.value}, used={used}/{limit}, remaining={remaining}"
            )

            return has_quota, max(0, remaining)

        except Exception as e:
            logger.error(f"检查配额失败: {str(e)}")
            # 出错时保守处理：假设没有配额
            return False, 0

    def consume_quota_sync(
        self,
        user_id: str,
        service_type: ImageServiceType,
        db: Session,
        prompt: str = "",
        status: str = "success",
    ) -> int:
        """
        同步方式扣除配额并记录日志（先数据库后Redis）

        适用于同步上下文（如生成器函数）中调用

        Args:
            user_id: SSO 用户唯一标识（来自 JWT token 的 userId 字段）
            service_type: 服务类型
            db: 数据库会话（必须在当前线程创建）
            prompt: 用户提示词
            status: 调用状态（success/failed）

        Returns:
            扣除后的剩余次数
        """
        try:
            # 1. 先在当前线程同步写入数据库（避免跨线程使用Session）
            try:
                log = ImageServiceLog(
                    user_id=user_id,
                    service_type=service_type.value,
                    status=status,
                    prompt=prompt[:500] if prompt else "",
                )
                db.add(log)
                db.commit()
                logger.debug(
                    f"配额日志已记录: user={user_id}, type={service_type.value}"
                )
            except Exception as db_error:
                logger.error(f"写入配额日志失败: {str(db_error)}")
                db.rollback()
                # 日志写入失败不影响配额扣除

            # 2. 同步扣除Redis配额（创建同步连接避免事件循环冲突）
            def _deduct_redis_quota_sync():
                """在新线程中使用同步Redis客户端扣除配额"""
                # 从异步客户端的连接信息创建同步客户端
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                sync_client = sync_redis.from_url(
                    redis_url,
                    decode_responses=False,  # 保持与异步客户端一致
                )

                try:
                    redis_key = self._get_redis_key(user_id, service_type)
                    limit = self._get_quota_limit(service_type)

                    # Redis原子递增
                    new_count = sync_client.incr(redis_key)

                    # 第一次使用时设置过期时间（到今天23:59:59）
                    if new_count == 1:
                        ttl = self._seconds_until_midnight()
                        sync_client.expire(redis_key, ttl)
                        logger.debug(f"设置配额键过期时间: {redis_key}, TTL={ttl}秒")

                    remaining = max(0, limit - new_count)
                    logger.info(
                        f"配额已扣除: user={user_id}, type={service_type.value}, used={new_count}/{limit}, remaining={remaining}"
                    )
                    return remaining
                finally:
                    sync_client.close()

            # 在线程池中执行同步Redis操作
            future = _db_thread_pool.submit(_deduct_redis_quota_sync)
            return future.result()  # 等待Redis操作完成

        except Exception as e:
            logger.error(f"扣除配额失败: {str(e)}")
            return 0

    async def consume_quota_async(
        self,
        user_id: str,
        service_type: ImageServiceType,
        db: Session,
        prompt: str = "",
        status: str = "success",
    ) -> int:
        """
        异步扣除配额并记录日志（仅用于纯异步上下文）

        ⚠️ 警告：db Session 必须是异步的或在同一线程创建

        Args:
            user_id: SSO 用户唯一标识（来自 JWT token 的 userId 字段）
            service_type: 服务类型
            db: 数据库会话
            prompt: 用户提示词
            status: 调用状态（success/failed）

        Returns:
            扣除后的剩余次数
        """
        try:
            redis_key = self._get_redis_key(user_id, service_type)
            limit = self._get_quota_limit(service_type)

            # Redis原子递增
            new_count = await self.redis.incr(redis_key)

            # 第一次使用时设置过期时间（到今天23:59:59）
            if new_count == 1:
                ttl = self._seconds_until_midnight()
                await self.redis.expire(redis_key, ttl)
                logger.debug(f"设置配额键过期时间: {redis_key}, TTL={ttl}秒")

            remaining = max(0, limit - new_count)

            # 在线程池中执行同步数据库操作（避免事件循环冲突）
            def _write_db_log():
                try:
                    log = ImageServiceLog(
                        user_id=user_id,
                        service_type=service_type.value,
                        status=status,
                        prompt=prompt[:500] if prompt else "",  # 限制长度
                    )
                    db.add(log)
                    db.commit()
                except Exception as db_error:
                    logger.error(f"写入配额日志失败: {str(db_error)}")
                    db.rollback()
                    # 日志写入失败不影响配额扣除

            # 异步提交到线程池（不等待完成，避免阻塞）
            _db_thread_pool.submit(_write_db_log)

            logger.info(
                f"配额已扣除: user={user_id}, type={service_type.value}, used={new_count}/{limit}, remaining={remaining}"
            )

            return remaining

        except Exception as e:
            logger.error(f"扣除配额失败: {str(e)}")
            return 0

    async def get_all_quotas_async(self, user_id: str) -> dict:
        """
        异步获取用户所有服务的配额信息

        Args:
            user_id: SSO 用户唯一标识（来自 JWT token 的 userId 字段）

        Returns:
            {
                "image_generate": {"used": 3, "limit": 10, "remaining": 7},
                "image_edit": {"used": 1, "limit": 3, "remaining": 2}
            }
        """
        result = {}

        for service_type in ImageServiceType:
            redis_key = self._get_redis_key(user_id, service_type)
            limit = self._get_quota_limit(service_type)

            used_bytes = await self.redis.get(redis_key)
            used = int(used_bytes) if used_bytes else 0
            remaining = max(0, limit - used)

            result[service_type.value] = {
                "used": used,
                "limit": limit,
                "remaining": remaining,
            }

        return result

    async def reset_user_quota_async(self, user_id: str):
        """
        异步重置指定用户的所有配额（管理员功能）

        Args:
            user_id: SSO 用户唯一标识（来自 JWT token 的 userId 字段）
        """
        today = datetime.now().strftime("%Y%m%d")

        keys_to_delete = [
            f"user:{user_id}:image_generate:{today}",
            f"user:{user_id}:image_edit:{today}",
        ]

        deleted = await self.redis.delete(*keys_to_delete)
        logger.info(f"管理员重置配额: user={user_id}, deleted_keys={deleted}")

        return deleted
