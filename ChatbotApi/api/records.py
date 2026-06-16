import datetime
import json
from typing import Annotated, Dict, Optional

from fastapi import APIRouter, Body, Depends, Request, Security, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from common.BaseResponse import BaseResponse
from common.security import TokenData, get_user, verify_jwt_token
from db import models
from db.database import get_db

router = APIRouter()

course_id = "1"  # 默认为1


def set_course_id(new_course_id: str) -> None:
    """
    设置全局course_id变量
    :param new_course_id: 新的课程ID
    """
    global course_id
    course_id = new_course_id


async def add_platform_record_internal(
    db: Session,
    user_id: str,
    type: int,
    meta: Dict,
) -> None:
    """
    内部辅助函数：直接添加平台记录，不需要token验证
    用于SSO登录等场景
    :param db: 数据库会话
    :param user_id: 用户ID
    :param type: 记录类型
    :param meta: 记录元数据
    """
    global course_id
    try:
        record = models.PlatformRecords(
            course_id=course_id,
            user_id=user_id,
            type=type,
            meta=json.dumps(meta, ensure_ascii=False) if meta else None,
        )
        db.add(record)
        db.commit()
    except Exception as e:
        print(f"【添加平台记录失败】{str(e)}")
        db.rollback()
        pass  # 后台记录不应该影响主流程


class RecordParams(BaseModel):
    type: int
    meta: Optional[str] = None


async def add_record_legacy(
    type: int,
    meta: Dict,
    db: Session = Depends(get_db),
):
    """
    旧平台记录入口(内部辅助函数)
    :params type: 记录类型
    :params meta: 记录元数据
    :params token_data: 令牌数据
    :params db: 数据库会话
    :return BaseResponse
    """
    try:
        record = models.Records(
            type=type,
            meta=json.dumps(meta) if meta else None,
        )
        db.add(record)
        db.flush()
        db.commit()
        return BaseResponse(msg="操作成功", code=200)
    except Exception as e:
        print(f"【添加数据失败】{str(e)}")
        pass  # 后台记录不应该影响主流程


@router.post(
    "/add",
    description="添加学生行为记录",
    status_code=status.HTTP_200_OK,
)
async def add_record(
    type: Annotated[int, Body()],
    meta: Annotated[Dict, Body(...)],
    request: Request,
    token_data: TokenData = Security(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    行为类型:
        1：login（学生登录的学号, 课程码, 登录时间)
        2：button-click（点击每个按钮的时间, 点击按钮的名称）
        3：role-chat（与每个角色的对话内容, 时间）
        4：chat（与校园精灵的对话内容, 时间）
        5：homework-submit（提交作业的时间）
        6：task-judge（评价作品的内容和时间）
        7: resource-rate（推荐满意度）
        8: authorization（授权码授权）
        9: image-rate(图片生成满意度)
    :params type: 记录类型
    :params meta: 记录元数据
    :return BaseResponse
    """
    global course_id
    try:
        if isinstance(meta, str):
            meta = json.loads(meta)
        meta.update(
            {
                "username": token_data.username,
                "orgId": token_data.orgId,
                "orgName": token_data.orgName,
                "userType": token_data.userType,
            }
        )

        if request.cookies.get("course_id"):
            course_id = request.cookies.get("course_id")
        print(f"course_id = {course_id}")
        record = models.PlatformRecords(
            course_id=course_id,  # 向世界介绍我的学校场景，course_id统一为1
            user_id=token_data.userId,
            type=type,
            meta=json.dumps(meta) if meta else None,
        )
        db.add(record)
        db.flush()
        db.commit()
        return BaseResponse(msg="操作成功", code=200)
    except Exception as e:
        print(f"【添加数据失败】{str(e)}")
        pass  # 后台记录不应该影响主流程


@router.get(
    "/get",
    description="获取学生行为记录",
)
async def get_records(
    token_data: Annotated[TokenData, Security(verify_jwt_token)],
    db: Session = Depends(get_db),
):
    user_id = token_data.username
    user = get_user(db, user_id)
    # 查询所有Records及对应的Users账号
    # 只导出2025-08-12当天的所有记录
    start_time = datetime.datetime(2025, 8, 12, 0, 0, 0)
    end_time = datetime.datetime(2025, 8, 13, 0, 0, 0)
    records = (
        db.query(
            models.Records.id,
            models.Users.user_id,
            models.Records.type,
            models.Records.meta,
            models.Records.create_time,
        )
        .outerjoin(models.Users, models.Records.user_id == models.Users.id)
        .filter(models.Records.create_time >= start_time)
        .filter(models.Records.create_time < end_time)
        .order_by(models.Records.create_time.desc())
        .limit(20000)
        .all()
    )
    records_dict = [
        {
            "id": r.id,
            "user_id": r.user_id if r.user_id is not None else None,
            "type": r.type,
            "create_time": r.create_time.isoformat() if r.create_time else None,
            "meta": r.meta,
        }
        for r in records
    ]
    return BaseResponse(msg="操作成功", code=200, data=records_dict)
