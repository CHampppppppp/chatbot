from datetime import timedelta
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from db import models
from db.database import get_db
from common.BaseResponse import BaseResponse
from datetime import datetime
from pydantic import BaseModel
import random
from common.security import get_user

router = APIRouter()


class CreateContentRequest(BaseModel):
    teacher_id: str
    code: str
    time: str


@router.get("/create")
async def create_code(user_id: str, db: Session = Depends(get_db)):
    user = get_user(db, username=user_id)
    if user is not None:
        if user.role == 2:
            new_code = models.Classes(
                teacher_id=user.id,
                code=str(random.randint(10**5, (10**6) - 1)),
                time=datetime.now() + timedelta(minutes=60),
                disable=0,
            )

            # 将新内容添加到数据库
            db.add(new_code)
            db.commit()
            db.refresh(new_code)

            return BaseResponse("创建课程码成功！", code=200, data=str(new_code.code))
        else:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="用户没有权限执行此操作！"
            )
    else:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="账号或密码错误")
