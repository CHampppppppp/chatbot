import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

# 导入配置文件
from common import config
from db import models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
SECRET_KEY = config.SECRET_KEY


class Token(BaseModel):
    id_token: str
    token_type: str


class TokenData(BaseModel):
    userId: str | None = None
    username: str | None = None
    orgId: str | None = None
    orgName: str | None = None
    userType: str | None = None


class User(BaseModel):
    username: str


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 用于从Cookie中获取 JWT token
def get_token_from_cookie(request: Request) -> str | None:
    token = request.cookies.get("id_token")
    if not token and not config.DEV_MODE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"msg": "用户未登录", "error": ""},
        )
    return token


def get_user(db: Session, username: str = None):
    if not username:
        return None

    query = db.query(models.Users).filter(models.Users.disable == 0)

    if username:
        query = query.filter(models.Users.user_id == username)

    user = query.first()
    return user if user else None


def create_id_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=config.ID_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_jwt_token(
    request: Request,
    token: Annotated[str | None, Depends(get_token_from_cookie)] = None,
):
    # dev 模式：没有 token 时直接使用默认用户
    if not token and config.DEV_MODE:
        token_data = TokenData(**config.DEV_DEFAULT_USER)
        token_data.username = config.DEV_DEFAULT_USER["username"]
        return token_data

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"msg": "用户未登录", "error": ""},
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        userId = payload.get("userId")
        orgId = payload.get("orgId")
        orgName = payload.get("orgName")
        userType = payload.get("userType")

        if username is None:
            logger.warning("Token中缺少用户名信息")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"msg": "身份校验失败", "error": "用户名缺失"},
            )

        token_data = TokenData()
        token_data.userId = userId
        token_data.username = username
        token_data.orgId = orgId
        token_data.orgName = orgName
        token_data.userType = userType
        logger.info(f"认证成功: {token_data.username}")
        return token_data
    except jwt.InvalidTokenError as e:
        logger.error(f"令牌处理错误: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"msg": "身份校验失败", "error": "无效的身份认证"},
        )
    except HTTPException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail,
        )
    except Exception as e:
        logger.error(f"意外错误: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"msg": "身份校验失败", "error": "服务器错误，请联系管理员"},
        )
