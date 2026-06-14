import base64
import datetime
import os
import shutil
from typing import Annotated, Any, List, Union

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import and_
from sqlalchemy.orm import Session

from api.records import add_record
from common.BaseResponse import BaseResponse
from common.processImage import generated_unique_filename
from common.security import verify_jwt_token
from db import models
from db.database import get_db
from utils.ali_chat import AliChat

router = APIRouter()


class TaskRequest(BaseModel):
    course_id: int
    homework: str
    type: str


@router.get("/get", description="获取作业代码，当前暂时不用，获取目录时已自动获取")
async def get_task(
    course_id: int,
    token_data: Union[str, Any] = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    if token_data is not None:
        user_id = int(token_data["sub"])
        task = (
            db.query(models.Tasks)
            .filter(
                and_(
                    models.Tasks.user_id == user_id, models.Tasks.course_id == course_id
                )
            )
            .first()
        )
        return BaseResponse(msg="操作成功", code=200, data=task)
    else:
        return BaseResponse("操作失败", code=401, err="用户身份认证失败！")


@router.post("/submit", description="提交作业至服务器")
async def add_task(
    homework: List[UploadFile] = File(...),
    token_data: Union[str, Any] = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    提交作业至服务器
    文件保存路径在服务器/ChatbotApi/homeworks/
    作业类型自动提取文件扩展名
    :param homework: 作业文件
    :param token_data: JWT令牌数据
    :param db: 数据库会话
    :return: BaseResponse对象，包含操作结果

    """
    # 使用绝对路径并确保目录存在且权限正确
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../homeworks/")
    os.makedirs(save_dir, exist_ok=True)
    # 确保当前用户有写入权限
    if not os.access(save_dir, os.W_OK):
        print(f"【作业提交】目录无写入权限: {save_dir}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "msg": "作品提交失败",
                "error": "服务器错误，请联系管理员",
            },
        )

    file_info_list = []
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    allowed_types = [".jpg", ".png", ".jpeg"]
    for idx, file in enumerate(homework):
        # 安全性检查：验证文件名
        if not file.filename or ".." in file.filename or "/" in file.filename:
            raise HTTPException(
                code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "msg": "文件名不合法",
                    "error": "文件名包含非法字符",
                },
            )

        # 自动提取文档类型（文件扩展名）
        extracted_type = os.path.splitext(file.filename)[1].lower()
        if extracted_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "msg": "文件格式错误",
                    "error": f"不支持的文件类型：{extracted_type}",
                },
            )

        unique_filename = f"{timestamp}_{idx}_{file.filename}"
        file_location = os.path.join(save_dir, unique_filename)
        try:
            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            print(f"【作业提交】文件保存失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "msg": "作品保存失败",
                    "error": "服务器错误，请联系管理员",
                },
            )

        file_info_list.append(
            {
                "original": file.filename,
                "saved_as": unique_filename,
                "type": extracted_type,
            }
        )

        # 数据库存储所有文件名和类型（JSON字符串）
        # homework_json = json.dumps(
        #     [f["saved_as"] for f in file_info_list], ensure_ascii=False
        # )
        # type_json = json.dumps([f["type"] for f in file_info_list], ensure_ascii=False)

        # if task is None:
        #     db_data = models.Tasks(
        #         homework=homework_json,  # 存储所有文件名
        #         type=type_json,  # 存储所有类型
        #         status=1,
        #         create_time=datetime.datetime.now().isoformat(timespec="milliseconds"),
        #     )
        #     db.add(db_data)
        #     db.flush()
        #     db.commit()
        # else:
        #     db.query(models.Tasks).filter(and_(models.Tasks.user_id == user_id)).update(
        #         {
        #             "homework": homework_json,
        #             "type": type_json,
        #             "status": 1,
        #             "update_time": datetime.datetime.now().isoformat(
        #                 timespec="milliseconds"
        #             ),
        #         }
        #     )
        #     db.flush()
        #     db.commit()
        meta = {
            "files": file_info_list,
            "time": datetime.datetime.now().isoformat(timespec="milliseconds"),
        }
        await add_record(5, meta, token_data, db)
        return BaseResponse(msg="文件上传成功", code=200)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "msg": "作品提交失败",
                "error": "用户身份认证失败！",
            },
        )


@router.get("/save", description="下载作业，暂不使用")
async def save_task(
    course_id: int = Query(...),
    token_data: Union[str, Any] = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    if token_data is not None:
        user_id = int(token_data["sub"])
        task = (
            db.query(models.Tasks)
            .filter(
                and_(
                    models.Tasks.user_id == user_id, models.Tasks.course_id == course_id
                )
            )
            .first()
        )

        if task is None:
            return BaseResponse("操作失败", code=403, err="你还没有提交作业！")
        else:
            # 使用与保存时相同的路径
            file_location = f"/Chatbot-files/homeworks/{task.homework}"
            try:
                if not os.path.exists(file_location):
                    return BaseResponse("操作失败", code=404, err="文件不存在！")

                with open(file_location, "rb") as file:
                    encoded_string = base64.b64encode(file.read()).decode()
                return BaseResponse(msg="操作成功", code=200, data=encoded_string)
            except Exception as e:
                return BaseResponse("操作失败", code=500, err=f"文件读取失败：{str(e)}")
    else:
        return BaseResponse("操作失败", code=401, err="用户身份认证失败！")


@router.post("/judge", description="对作业进行评分")
async def judge_task(
    prompt: Annotated[str, Form(description="评分标准提示词")],
    files: List[UploadFile] = File(..., description="作业图片文件"),
):
    params_list = []
    messages = []
    # 上传的文件存在本地
    try:
        # 上传的文件保存到本地
        for file in files:
            file_path = generated_unique_filename(file)  # 得到唯一文件路径
            params_list.append({"image": file_path})

        # 添加评分标准
        params_list.append({"text": prompt})

        ali_chat = AliChat()

        messages.append({"role": "user", "content": params_list})
        content = ali_chat.image_input(messages)

        return StreamingResponse(content=content, media_type="text/event-stream")
    except Exception as e:
        print(f"评分失败, error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="评分失败"
        )
