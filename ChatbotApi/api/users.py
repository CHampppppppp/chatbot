import base64
import hashlib
import json
from datetime import datetime, timedelta
from typing import Annotated
from urllib.parse import urlparse

import httpx
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    Security,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy import and_
from sqlalchemy.orm import Session
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from api.records import (
    add_platform_record_internal,
    add_record,
    add_record_legacy,
    set_course_id,
)
from common import config
from common.BaseResponse import BaseResponse
from common.security import (
    TokenData,
    create_id_token,
    get_user,
    verify_jwt_token,
)
from db import models
from db.database import get_db

router = APIRouter()


def generate_sso_token(
    app_key: str, secret_key: str, relative_url: str, request_body: str | None = None
) -> str:
    """
    生成SSO认证的Authorization token
    """
    # 获取当前时间戳（毫秒）
    timestamp = str(int(datetime.now().timestamp() * 1000))

    # 构建参数
    parameters = {"alg": "MD5", "appKey": app_key, "timestamp": timestamp}

    # 将参数转为JSON字符串并进行base64编码
    parameters_json = json.dumps(parameters)
    base64_parameters = base64.b64encode(parameters_json.encode("utf-8")).decode(
        "utf-8"
    )

    # 生成签名
    signature = sign_sso_data(secret_key, base64_parameters, relative_url, body=None)

    return f"{base64_parameters}.{signature}"


def sign_sso_data(
    sign_key: str, base64_parameters: str, relative_url: str, body: str | None = None
) -> str:
    """
    生成SSO签名
    """
    # 解析URL获取相对路径
    parsed_url = urlparse(relative_url)
    relative_url = parsed_url.path
    if parsed_url.query:
        relative_url += "?" + parsed_url.query

    # 构建要签名的数据
    data = base64_parameters + relative_url + (body or "")

    # 生成MD5签名
    signature_data = data + sign_key
    md5_hash = hashlib.md5(signature_data.encode("utf-8")).hexdigest()

    return md5_hash.upper()


class Token(BaseModel):
    id_token: str
    token_type: str


class StudentRegister(BaseModel):
    real_name: str  # 学生真实姓名
    username: str  # 学生姓名拼音
    class_code: str  # 课程码


def set_id_token_cookie(
    response: Response,
    id_token: str,
    max_age: int,
    prod_samesite: str = "strict",
):
    response.set_cookie(
        key="id_token",
        value=id_token,
        httponly=True,
        secure=config.COOKIE_SECURE,
        samesite=config.get_cookie_samesite(),
        max_age=max_age,
    )


def delete_id_token_cookie(response: Response):
    response.delete_cookie(
        key="id_token",
        path="/",
        secure=config.COOKIE_SECURE,
        samesite=config.get_cookie_samesite(),
    )


def set_session_cookie(response: Response, key: str, value: str):
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=config.COOKIE_SECURE,
        samesite=config.get_cookie_samesite(),
    )


async def login_permit(
    user,
    code,
    response: Response,
    db: Session = None,
):
    id_token_expires = timedelta(minutes=config.ID_TOKEN_EXPIRE_MINUTES)
    id_token = create_id_token(
        data={
            "sub": str(user.user_id),
            "userId": str(user.user_id),
            "userType": "teacher" if user.role == 2 else "student",
        },
        expires_delta=id_token_expires,
    )

    # 数据埋点
    meta = {
        "code": code,
        "time": datetime.now().isoformat(timespec="milliseconds"),
    }
    # 使用内部函数记录登录行为，传递用户 ID
    await add_record_legacy(
        type=1,
        meta=json.dumps(meta, ensure_ascii=False),
        db=db,
    )

    set_id_token_cookie(
        response,
        id_token,
        int(id_token_expires.total_seconds()),
        prod_samesite="none",
    )

    data = {
        "user": user.user_id,
    }
    return BaseResponse(
        "登录成功", code=status.HTTP_200_OK, data=data, response=response
    )


@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
    response: Response = None,
):
    # user = authenticate_user(db, form_data.username, form_data.password) # 规范验证流程，暂时弃用
    # 只需要验证账号
    user = get_user(db, username=form_data.username)
    if not user:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="账号不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    print(f"[DEBUG] 登录用户角色: {'教师' if user.role == 2 else '学生'}")
    print(f"[DEBUG] 登录用户ID: {user.user_id}")
    if user.role == 2:
        # 教师登录
        return await login_permit(user, form_data.password, response, db)
    else:
        # 学生登录
        if form_data.password == "123456":
            return await login_permit(
                user, form_data.password, response, db
            )  # 允许课程码 123456 直接登录，测试用

        current_time = datetime.now()
        permission = (
            db.query(models.Classes)
            .filter(
                and_(
                    models.Classes.disable == 0,
                    models.Classes.code == form_data.password,
                    models.Classes.time >= current_time,
                )
            )
            .first()
        )
        if permission is not None:
            return await login_permit(user, form_data.password, response, db)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账号或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )


@router.get("/login-check")
async def login_check(
    token_data: Annotated[TokenData, Security(verify_jwt_token)], response: Response
):
    if not token_data or not token_data.username:
        delete_id_token_cookie(response)
        return BaseResponse(
            msg="登录状态验证失败",
            code=status.HTTP_401_UNAUTHORIZED,
            response=response,
        )
    return BaseResponse(
        msg="登录状态验证成功",
        code=status.HTTP_200_OK,
        data={"username": token_data.username},
        response=response,
    )


@router.post("/register")
async def register(
    student_data: StudentRegister,
    payload: Annotated[TokenData, Security(verify_jwt_token)],
    db: Session = Depends(get_db),
):
    # 验证请求者是否为教师
    teacher = get_user(db, username=payload.username)
    print(f"[DEBUG] 注册请求者角色: {'教师' if teacher.role == 2 else '学生'}")
    print(f"[DEBUG] 注册请求者ID: {teacher.user_id}")
    if not teacher or teacher.role != 2:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="只有教师可以注册学生账号",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # # 验证课程码是否有效
    # current_time = datetime.now()
    # course = (
    #     db.query(models.Classes)
    #     .filter(
    #         and_(
    #             models.Classes.disable == 0,
    #             models.Classes.code == student_data.class_code,
    #             models.Classes.time >= current_time,
    #             models.Classes.teacher_id == teacher.user_id,
    #         )
    #     )
    #     .first()
    # )

    # if not course:
    #     raise HTTPException(
    #         status_code=HTTP_401_UNAUTHORIZED,
    #         detail="无效的课程码或课程码已过期",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )

    # 根据真实姓名和姓名拼音查找学生记录
    existing_student = (
        db.query(models.Users)
        .filter(
            (models.Users.user_id == student_data.username)
            | (models.Users.real_name == student_data.real_name)
        )
        .first()
    )

    if existing_student:
        # 更新现有学生信息
        existing_student.user_id = student_data.username
        existing_student.real_name = student_data.real_name
        existing_student.Class = student_data.class_code
        existing_student.disable = False
        db.commit()
        db.refresh(existing_student)

        return BaseResponse(
            "学生账号信息已更新", code=200, data={"user_id": existing_student.user_id}
        )
    else:
        # 创建新的学生用户
        new_student = models.Users(
            user_id=student_data.username,
            real_name=student_data.real_name,
            Class=student_data.class_code,
            role=1,  # 学生角色
            disable=False,
        )

        db.add(new_student)
        db.commit()
        db.refresh(new_student)

        return BaseResponse(
            "学生账号注册成功", code=200, data={"user_id": new_student.user_id}
        )


@router.post("/logout")
async def logout(response: Response):
    # 清除Cookie，指定path确保正确删除
    delete_id_token_cookie(response)
    return BaseResponse("登出成功", code=200, response=response)


# 消费code获取用户基本信息
@router.get("/user_info", description="消费前端传入的CODE来获取用户基本信息")
async def get_user_info_by_code(
    code: str,
    fromBusiness: str,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        # 准备请求参数
        url = "https://szyx.zjer.cn/yunzhi-api/openapi/third/auth/tob/getuserinfo"
        relative_url = "/third/auth/tob/getuserinfo"
        request_body = json.dumps({"code": code, "clientId": "chatbot"})

        # 生成Authorization token
        authorization_token = generate_sso_token(
            config.SSO_APP_KEY,
            config.SSO_SECRET_KEY,
            relative_url,
            request_body,
        )
        # 发起网络请求获取用户信息
        async with httpx.AsyncClient() as client:
            http_response = await client.post(
                url,
                json=json.loads(request_body),  # 将 requestBody 作为载荷发送
                headers={
                    "Content-Type": "application/json",
                    "version": "2.0.0",
                    "Authorization": authorization_token,
                },
                timeout=30.0,  # 设置超时时间
            )

            # 检查响应状态
            print(f"【SSO】获取用户信息响应: {http_response.json()}")
            if http_response.json().get("code") == 200:
                http_data = {
                    "sub": str(http_response.json().get("name")),
                    "userId": str(http_response.json().get("userId")),
                    "orgId": str(http_response.json().get("orgId")),
                    "orgName": str(http_response.json().get("orgName")),
                    "userType": str(http_response.json().get("userType")),
                }
                id_token_expires = timedelta(minutes=config.ID_TOKEN_EXPIRE_MINUTES)
                id_token = create_id_token(
                    data=http_data,
                    expires_delta=id_token_expires,
                )

                set_id_token_cookie(
                    response,
                    id_token,
                    int(id_token_expires.total_seconds()),
                    prod_samesite="strict",
                )

                # 记录SSO登录行为
                record_meta = {
                    "username": http_data.get("sub"),
                    "userId": http_data.get("userId"),
                    "orgId": http_data.get("orgId"),
                    "orgName": http_data.get("orgName"),
                    "userType": http_data.get("userType"),
                    "code": code,
                    "fromBusiness": fromBusiness,
                }

                await add_platform_record_internal(
                    db=db,
                    user_id=http_data.get("userId"),
                    type=1,
                    meta=record_meta,
                )

                # SSO 登录时自动创建/更新 Users 表映射
                sso_user_id = http_data.get("userId")
                existing_user = (
                    db.query(models.Users)
                    .filter(models.Users.sso_user_id == sso_user_id)
                    .first()
                )
                if not existing_user:
                    new_user = models.Users(
                        sso_user_id=sso_user_id,
                        real_name=http_data.get("sub"),
                        school=http_data.get("orgName"),
                        disable=False,
                        role=1,
                    )
                    db.add(new_user)
                    db.commit()

                return BaseResponse(
                    msg="获取用户信息成功", code=200, data=http_data, response=response
                )
            else:
                # SSO服务返回非200状态，抛出HTTP异常
                sso_error_code = http_response.json().get("code", 500)
                sso_error_message = http_response.json().get(
                    "message", "获取用户信息失败"
                )

                # 根据SSO返回的错误码映射到合适的HTTP状态码
                if sso_error_code == 401:
                    http_status = status.HTTP_401_UNAUTHORIZED
                elif sso_error_code == 403:
                    http_status = status.HTTP_403_FORBIDDEN
                elif sso_error_code == 404:
                    http_status = status.HTTP_404_NOT_FOUND
                else:
                    http_status = status.HTTP_500_INTERNAL_SERVER_ERROR

                raise HTTPException(
                    status_code=http_status,
                    detail={
                        "error": "sso_service_error",
                        "message": f"获取用户信息失败: {sso_error_message}",
                        "sso_error_code": sso_error_code,
                    },
                )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail={"msg": "请检查网络后重试", "error": "请求超时"},
        )
    except httpx.RequestError as e:
        print(f"【SSO】网络请求错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "msg": "请求错误",
                "error": "网络请求失败",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"【SSO】未知错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "msg": "获取用户信息时发生未知错误",
                "error": "服务器错误，请联系管理员",
            },
        )


@router.get("/authorization", description="使用授权码登录平台", status_code=200)
async def platform_authorization(
    code: str,
    course_id: str,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        # 根据授权码查询是否被授权
        authorization_record = (
            db.query(models.AuthorizationCodes)
            .filter(models.AuthorizationCodes.code == code)
            .first()
        )

        if not authorization_record:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "msg": "授权失败",
                    "error": "授权码无效或已过期",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 检查授权码是否过期
        current_time = datetime.now()
        if (
            authorization_record.expire_time
            and authorization_record.activated_time
            and (
                authorization_record.activated_time >= current_time
                or authorization_record.expire_time <= current_time
            )
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "msg": "授权失败",
                    "error": "授权码未生效或已过期",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # record_data = {"authorization_code": code}
        set_session_cookie(response, "authorization_code", code)
        set_session_cookie(response, "course_id", course_id)

        set_course_id(course_id)
        # await add_platform_record_internal(db=db, user_id=None, type=8, meta=json.dumps(record_data))

        return BaseResponse("授权登录成功", code=status.HTTP_200_OK, response=response)
    except HTTPException:
        raise
    except Exception as e:
        print(f"【授权登录失败】{str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "msg": "授权登录失败",
                "error": "服务器错误，请联系管理员",
            },
        )


@router.get("/authorization/status", description="检查授权码登录状态", status_code=200)
async def check_authorization_status(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    检查用户的授权码登录状态
    从 cookie 中获取授权码，验证其有效性
    """
    try:
        # 从 cookie 中获取授权码
        authorization_code = request.cookies.get("authorization_code")

        if not authorization_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "msg": "无权访问",
                    "error": "请先进行授权登录",
                },
            )

        # 查询授权码是否存在且有效
        authorization_record = (
            db.query(models.AuthorizationCodes)
            .filter(models.AuthorizationCodes.code == authorization_code)
            .first()
        )

        if not authorization_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "msg": "授权码无效",
                    "error": "请先进行授权登录",
                },
            )

        # 检查授权码是否过期
        current_time = datetime.now()
        if (
            authorization_record.expire_time
            and authorization_record.expire_time < current_time
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "msg": "授权码已过期",
                    "error": "请重新授权登录",
                },
            )

        # 授权码有效
        return BaseResponse(
            msg="授权有效",
            code=status.HTTP_200_OK,
            data={
                "authorized": True,
                "activated_time": authorization_record.activated_time.isoformat()
                if authorization_record.activated_time
                else None,
                "expire_time": authorization_record.expire_time.isoformat()
                if authorization_record.expire_time
                else None,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"【检查授权状态失败】{str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "msg": "检查授权状态失败",
                "error": "服务器错误，请联系管理员",
            },
        )


# ==================== 用户画像接口 ====================


def get_user_by_token(db: Session, user_id: str):
    """根据 token 中的 userId 查找用户，兼容 SSO 和本地登录。"""
    user = db.query(models.Users).filter(models.Users.sso_user_id == user_id).first()
    if not user:
        user = db.query(models.Users).filter(models.Users.user_id == user_id).first()
    return user


class ProfileUpdate(BaseModel):
    real_name: str | None = None
    school: str | None = None
    grade: str | None = None
    Class: str | None = None


@router.get("/profile", description="获取当前用户画像")
async def get_profile(
    token_data: Annotated[TokenData, Security(verify_jwt_token)],
    db: Session = Depends(get_db),
):
    if not token_data.userId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"msg": "缺少用户标识"},
        )
    user = get_user_by_token(db, token_data.userId)
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
        },
    )


@router.put("/profile", description="更新当前用户画像")
async def update_profile(
    profile_data: ProfileUpdate,
    token_data: Annotated[TokenData, Security(verify_jwt_token)],
    db: Session = Depends(get_db),
):
    if not token_data.userId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"msg": "缺少用户标识"},
        )
    user = get_user_by_token(db, token_data.userId)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
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
        },
    )
