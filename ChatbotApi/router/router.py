from fastapi import APIRouter, Security
from api import platform, users, records, tasks, classes
from common.security import verify_jwt_token

# 需要 JWT 校验的路由
api_router = APIRouter()
# api_router = APIRouter()


# 分组路由（除 users、classes 外）
api_router.include_router(
    platform.router,
    prefix="/platform",
    tags=["platform"],
    dependencies=[Security(verify_jwt_token)],
)

api_router.include_router(
    records.router,
    prefix="/records",
    tags=["records"],
    dependencies=[Security(verify_jwt_token)],
)
api_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Security(verify_jwt_token)],
)


# users、classes 路由不需要 JWT 校验，单独处理
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(classes.router, prefix="/classes", tags=["classes"])
