# 文件处理相关
import json
import logging
from typing import Optional

from dotenv import load_dotenv

# 请求相关
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Security, UploadFile
from fastapi.responses import StreamingResponse

# 模型相关
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from common.BaseResponse import BaseResponse
from common.processImage import generated_unique_filename
from common.security import TokenData, verify_jwt_token
from db import models
from db.database import SessionLocal, get_db
from utils.ali_chat import AliChat
from utils.dimension_scorer import (
    compute_knowledge_reserve,
    get_active_score,
    get_user_by_token_user_id,
    get_user_dimension_scores,
)
from utils.image_quota_manager import ImageQuotaManager, ImageServiceType
from utils.xunfei_image import XunfeiImageGenerator

load_dotenv()

router = APIRouter()

logger = logging.getLogger(__name__)


def get_redis_client():
    """
    动态获取 redis_client，避免循环导入
    在模块初始化时不导入，而是在运行时导入
    """
    from main import redis_client

    return redis_client


def require_admin(token_data: TokenData):
    if token_data.userType != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")


class Message(BaseModel):
    role: str
    content: str


class Messages(BaseModel):
    messages: list[Message]


class RAGRequest(BaseModel):
    messages: list[Message]
    role: str


# 通用的聊天处理函数
async def handle_chat_request(
    request: Messages,
    chat_method: str = "generate_response_stream",
    extra_params: dict = None,
    token_data: TokenData = None,
    db: Session = None,
    background_tasks: BackgroundTasks = None,
):
    """
    通用的聊天请求处理函数

    Args:
        request: 包含消息的请求对象
        chat_method: AliChat对象要调用的方法名
        extra_params: 额外的参数字典
        token_data: JWT 解码后的用户身份信息
        db: 数据库会话（用于查询用户画像）
        background_tasks: 后台任务（用于对话结束后异步评分）
    """
    profile_prompt = ""
    if token_data and token_data.userId and db:
        from utils.profile_builder import build_profile_prompt, get_user_profile

        profile = get_user_profile(db, token_data.userId)
        profile_prompt = build_profile_prompt(profile)

    if profile_prompt:
        logger.info(f"用户画像已注入 prompt: {token_data.userId}")

    ali_chat = AliChat()
    messages_dict_list = [
        {"role": msg.role, "content": msg.content} for msg in request.messages
    ]

    # 获取AliChat对象的指定方法
    chat_handler = getattr(ali_chat, chat_method)

    # 根据方法调用相应的处理逻辑
    if chat_method == "generate_image":
        extra_params = extra_params or {"time": 1}
        content = chat_handler(messages_dict_list, extra_params)
    else:
        content = chat_handler(
            messages_dict_list,
            rag=extra_params.get("rag") if extra_params else None,
            role=extra_params.get("role") if extra_params else None,
            profile_prompt=profile_prompt,
        )

    # 流式响应结束后异步评分
    if background_tasks and token_data and token_data.userId:
        background_tasks.add_task(
            _evaluate_after_chat,
            token_data.userId,
            messages_dict_list,
        )

    return StreamingResponse(content=content, media_type="text/event-stream")


def _evaluate_after_chat(token_user_id: str, messages: list[dict]):
    """对话结束后异步评估维度变化。"""
    from utils.dimension_scorer import evaluate_dimensions

    db = SessionLocal()
    try:
        user = get_user_by_token_user_id(db, token_user_id)
        if not user:
            logger.warning(f"异步评分未找到用户: {token_user_id}")
            return
        evaluate_dimensions(db, user.id, messages)
    except Exception as e:
        logger.error(f"异步评分失败: {e}")
    finally:
        db.close()


# 通用图像处理函数工厂函数
async def image_request_handler(
    messages: Messages,
    image: Optional[UploadFile] = File(None),
    chat_method: str = "handle_image",
    user_id: str = None,
    db: Session = None,
):
    """
    通用的图像处理请求工厂函数

    Args:
        messages: 包含消息的请求对象
        image: 上传的图片文件
        chat_method: AliChat对象要调用的方法名
        user_id: SSO 用户唯一标识（来自 JWT token 的 userId 字段，用于配额扣除）
        db: 数据库会话（用于记录日志）
    """

    ali_chat = AliChat()

    image_url = None
    if image:
        # 构造文件URL，使用绝对路径
        image_url = generated_unique_filename(image)

    image_handler = getattr(ali_chat, chat_method)

    messages_dict_list = [
        {"role": msg.role, "content": msg.content} for msg in messages.messages
    ]

    # 传递 user_id 和 db 给 handle_image 方法
    content = image_handler(
        messages_dict_list, image_url=image_url, user_id=user_id, db=db
    )

    return StreamingResponse(content=content, media_type="text/event-stream")


# 讯飞星火图像处理函数
async def xunfei_image_request_handler(
    messages: Messages,
    image: Optional[UploadFile] = File(None),
):
    """
    讯飞星火图像处理请求函数

    Args:
        messages: 包含消息的请求对象
        image: 上传的图片文件(暂不支持,保留用于兼容)
    """

    xunfei_chat = XunfeiImageGenerator()

    messages_dict_list = [
        {"role": msg.role, "content": msg.content} for msg in messages.messages
    ]
    content = xunfei_chat.handle_image(messages_dict_list, image_url=None)

    return StreamingResponse(content=content, media_type="text/event-stream")


@router.post("/chat", description="校园精灵")
async def chat(
    request: RAGRequest,
    background_tasks: BackgroundTasks,
    token_data: TokenData = Security(verify_jwt_token),
    db: Session = Depends(get_db),
):
    return await handle_chat_request(
        request,
        extra_params={"rag": True, "role": request.role},
        token_data=token_data,
        db=db,
        background_tasks=background_tasks,
    )


@router.post("/inspirationSuperman", description="灵感超人")
async def inspirationSuperman(
    request: Messages,
    background_tasks: BackgroundTasks,
    token_data: TokenData = Security(verify_jwt_token),
    db: Session = Depends(get_db),
):
    return await handle_chat_request(
        request,
        token_data=token_data,
        db=db,
        background_tasks=background_tasks,
    )


@router.post("/intelligentArtist", description="智能画家")
async def intelligentArtist(
    messages: str = Form(...),
    image: Optional[UploadFile] = File(None),
    token_data: TokenData = Security(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    智能画家 - 支持图像生成和编辑
    会进行配额预检查，配额不足时返回 429 错误
    """
    try:
        # 1. 配额预检查
        redis_client = get_redis_client()
        if not redis_client:
            raise HTTPException(status_code=500, detail="服务暂时不可用")

        quota_manager = ImageQuotaManager(redis_client)

        # 检查生成和编辑配额（至少有一个有余额才能继续）
        can_generate, gen_remaining = await quota_manager.check_quota_async(
            token_data.userId, ImageServiceType.GENERATE
        )
        can_edit, edit_remaining = await quota_manager.check_quota_async(
            token_data.userId, ImageServiceType.EDIT
        )

        if not can_generate and not can_edit:
            raise HTTPException(
                status_code=429,
                detail={
                    "msg": "今日图像服务次数已用尽",
                    "generate": {"limit": 10, "remaining": 0},
                    "edit": {"limit": 3, "remaining": 0},
                },
            )

        # 2. 解析消息
        messages_list = json.loads(messages)

        # 创建Message对象列表
        message_objects = []
        for msg in messages_list:
            message_objects.append(
                Message(role=msg.get("role"), content=msg.get("content"))
            )

        # 创建Messages对象
        messages_obj = Messages(messages=message_objects)

        # 3. 处理图像请求（会在内部根据LLM判断扣除对应配额）
        # 使用阿里通义处理图像（支持生成和编辑）
        return await image_request_handler(
            messages_obj,
            image,
            user_id=token_data.userId,  # 传递user_id用于配额扣除
            db=db,
        )
    except Exception as e:
        print(f"messages转换失败: {str(e)}")
        return BaseResponse("操作失败", code=400, err=f"消息格式不正确: {str(e)}")


@router.post("/computerDoctor", description="电脑博士")
async def computerDoctor(
    request: RAGRequest,
    background_tasks: BackgroundTasks,
    token_data: TokenData = Security(verify_jwt_token),
    db: Session = Depends(get_db),
):
    return await handle_chat_request(
        request,
        extra_params={"rag": True, "role": request.role},
        token_data=token_data,
        db=db,
        background_tasks=background_tasks,
    )


@router.post("/cultureMaster", description="文化达人")
async def cultureMaster(
    request: Messages,
    background_tasks: BackgroundTasks,
    token_data: TokenData = Security(verify_jwt_token),
    db: Session = Depends(get_db),
):
    return await handle_chat_request(
        request,
        token_data=token_data,
        db=db,
        background_tasks=background_tasks,
    )


@router.post("/eloquentWarrior", description="妙语奇兵")
async def eloquentWarrior(
    request: Messages,
    background_tasks: BackgroundTasks,
    token_data: TokenData = Security(verify_jwt_token),
    db: Session = Depends(get_db),
):
    return await handle_chat_request(
        request,
        token_data=token_data,
        db=db,
        background_tasks=background_tasks,
    )


# ==================== 图像服务配额管理接口 ====================


@router.get("/image-quota", description="获取用户图像服务配额信息")
async def get_user_image_quota(
    token_data: TokenData = Security(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    获取当前用户的图像服务配额信息

    使用 JWT token 中的 userId（SSO 用户唯一标识）查询配额

    Returns:
        {
            "image_generate": {"used": 3, "limit": 10, "remaining": 7},
            "image_edit": {"used": 1, "limit": 3, "remaining": 2}
        }
    """
    try:
        redis_client = get_redis_client()
        if not redis_client:
            raise HTTPException(
                status_code=500,
                detail={"msg": "服务暂时不可用", "error": "图像服务配额获取失败"},
            )

        quota_manager = ImageQuotaManager(redis_client)
        quotas = await quota_manager.get_all_quotas_async(token_data.userId)

        return BaseResponse(
            msg="图像服务配额查询成功",
            code=200,
            data={"generate": quotas["image_generate"], "edit": quotas["image_edit"]},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询配额失败: {str(e)}")
        raise HTTPException(
            status_code=500, detail={"msg": "图像服务配额查询失败", "error": str(e)}
        )


@router.get("/admin/image-quota/{user_id}", description="【管理员】查询指定用户配额")
async def admin_get_user_quota(
    user_id: str,
    token_data: TokenData = Security(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    管理员查询指定用户的图像服务配额

    Args:
        user_id: SSO 用户唯一标识（来自 JWT token 的 userId 字段，如工号、学号等）

    TODO: 添加管理员权限验证
    """
    try:
        require_admin(token_data)

        redis_client = get_redis_client()
        if not redis_client:
            raise HTTPException(status_code=500, detail="服务暂时不可用")

        quota_manager = ImageQuotaManager(redis_client)
        quotas = await quota_manager.get_all_quotas_async(user_id)

        return BaseResponse(
            msg="查询成功", code=200, data={"user_id": user_id, "quotas": quotas}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"管理员查询配额失败: {str(e)}")
        return BaseResponse(msg="查询失败", code=500, err=str(e))


@router.post(
    "/admin/image-quota/reset/{user_id}", description="【管理员】重置指定用户配额"
)
async def admin_reset_user_quota(
    user_id: str,
    token_data: TokenData = Security(verify_jwt_token),
):
    """
    管理员重置指定用户的今日图像服务配额

    Args:
        user_id: SSO 用户唯一标识（来自 JWT token 的 userId 字段，如工号、学号等）

    TODO: 添加管理员权限验证
    """
    try:
        require_admin(token_data)
        redis_client = get_redis_client()
        if not redis_client:
            raise HTTPException(status_code=500, detail="服务暂时不可用")

        quota_manager = ImageQuotaManager(redis_client)
        deleted_count = await quota_manager.reset_user_quota_async(user_id)

        return BaseResponse(
            msg="配额已重置",
            code=200,
            data={"user_id": user_id, "reset_keys": deleted_count},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"管理员重置配额失败: {str(e)}")
        return BaseResponse(msg="重置失败", code=500, err=str(e))


# ==================== 用户画像接口 ====================


def _get_user_by_token(db: Session, user_id: str):
    user = db.query(models.Users).filter(models.Users.sso_user_id == user_id).first()
    if not user:
        user = db.query(models.Users).filter(models.Users.user_id == user_id).first()
    if not user:
        user = db.query(models.Users).filter(models.Users.node_id == user_id).first()
    return user


class ProfileUpdate(BaseModel):
    real_name: str | None = None
    school: str | None = None
    grade: str | None = None
    Class: str | None = None
    interests: str | None = None


@router.get("/profile", description="获取当前用户画像")
async def get_profile(
    token_data: TokenData = Security(verify_jwt_token),
    db: Session = Depends(get_db),
):
    user = _get_user_by_token(db, token_data.userId)
    if not user:
        return BaseResponse(msg="用户画像不存在", code=404, data=None)
    return BaseResponse(
        msg="获取成功",
        code=200,
        data={
            "real_name": user.real_name,
            "school": user.school,
            "grade": user.grade,
            "class": user.Class,
            "interests": user.interests,
        },
    )


# ==================== 维度得分与反馈接口 ====================


class FeedbackRequest(BaseModel):
    message_id: str
    feedback: str = Field(..., pattern="^(like|dislike)$")


@router.post("/feedback", description="对 AI 回复点赞或点踩")
async def submit_feedback(
    request: FeedbackRequest,
    token_data: TokenData = Security(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    用户点赞/点踩 AI 回复，同步更新 AI_SATISFACTION 维度。
    - like: +1
    - dislike: -1
    最终值限制在 [0, 5]。
    """
    from utils.dimension_scorer import apply_feedback

    user = _get_user_by_token(db, token_data.userId)
    if not user:
        raise HTTPException(status_code=404, detail={"msg": "用户不存在"})

    delta = 1.0 if request.feedback == "like" else -1.0
    reason = "用户点赞" if request.feedback == "like" else "用户点踩"

    try:
        result = apply_feedback(
            db=db,
            user_id=user.id,
            dimension_key="AI_SATISFACTION",
            delta=delta,
            reason=reason,
            source_type="feedback",
            source_id=request.message_id,
        )
        return BaseResponse(
            msg="反馈已记录",
            code=200,
            data={
                "dimension_key": result["dimension_key"],
                "new_value": result["new_value"],
                "previous_value": result["previous_value"],
            },
        )
    except Exception as e:
        logger.error(f"记录反馈失败: {e}")
        raise HTTPException(status_code=500, detail={"msg": "反馈记录失败"})


@router.get("/dimensions", description="获取当前用户维度得分")
async def get_dimensions(
    token_data: TokenData = Security(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """返回当前用户所有维度最新得分，及计算出的知识储备。"""
    user = _get_user_by_token(db, token_data.userId)
    if not user:
        raise HTTPException(status_code=404, detail={"msg": "用户不存在"})

    scores = get_user_dimension_scores(db, user.id)
    knowledge_reserve = compute_knowledge_reserve(scores)
    active_score = get_active_score(scores)

    return BaseResponse(
        msg="获取成功",
        code=200,
        data={
            "scores": scores,
            "knowledge_reserve": knowledge_reserve,
            "active_score": active_score,
        },
    )


@router.get("/dimensions/history", description="获取指定维度更新历史")
async def get_dimension_history(
    dimension_key: str,
    token_data: TokenData = Security(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """返回指定维度的更新历史（含前/后对比和 reason）。"""
    user = _get_user_by_token(db, token_data.userId)
    if not user:
        raise HTTPException(status_code=404, detail={"msg": "用户不存在"})

    history = (
        db.query(models.StudentDimensionScoreHistory)
        .filter(
            models.StudentDimensionScoreHistory.user_id == user.id,
            models.StudentDimensionScoreHistory.dimension_key == dimension_key,
        )
        .order_by(models.StudentDimensionScoreHistory.created_at.desc())
        .all()
    )

    return BaseResponse(
        msg="获取成功",
        code=200,
        data=[
            {
                "dimension_key": h.dimension_key,
                "previous_value": float(h.previous_value) if h.previous_value is not None else None,
                "new_value": float(h.new_value),
                "change_delta": float(h.change_delta),
                "reason": h.reason,
                "source_type": h.source_type,
                "source_id": h.source_id,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in history
        ],
    )


class EvaluateRequest(BaseModel):
    messages: list[Message]


@router.post("/evaluate", description="手动触发一次维度评分")
async def manual_evaluate(
    request: EvaluateRequest,
    token_data: TokenData = Security(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """手动触发大模型评分（测试/补评用）。"""
    from utils.dimension_scorer import evaluate_dimensions

    user = _get_user_by_token(db, token_data.userId)
    if not user:
        raise HTTPException(status_code=404, detail={"msg": "用户不存在"})

    messages_dict_list = [
        {"role": msg.role, "content": msg.content} for msg in request.messages
    ]
    updated = evaluate_dimensions(db, user.id, messages_dict_list)

    return BaseResponse(
        msg="评分完成",
        code=200,
        data={"updated_dimensions": updated},
    )


@router.put("/profile", description="更新当前用户画像")
async def update_profile(
    profile_data: ProfileUpdate,
    token_data: TokenData = Security(verify_jwt_token),
    db: Session = Depends(get_db),
):
    user = _get_user_by_token(db, token_data.userId)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={"msg": "用户不存在"},
        )
    if profile_data.real_name is not None:
        user.real_name = profile_data.real_name
    if profile_data.school is not None:
        user.school = profile_data.school
    if profile_data.grade is not None:
        user.grade = profile_data.grade
    if profile_data.Class is not None:
        user.Class = profile_data.Class
    if profile_data.interests is not None:
        user.interests = profile_data.interests
    db.commit()
    db.refresh(user)
    return BaseResponse(
        msg="更新成功",
        code=200,
        data={
            "real_name": user.real_name,
            "school": user.school,
            "grade": user.grade,
            "class": user.Class,
            "interests": user.interests,
        },
    )
