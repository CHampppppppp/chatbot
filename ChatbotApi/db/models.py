from sqlalchemy import (
    NVARCHAR,
    VARCHAR,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import backref, relationship

from db.database import Base


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, unique=True)
    real_name = Column(NVARCHAR)
    school = Column(NVARCHAR)
    grade = Column(NVARCHAR)
    Class = Column(NVARCHAR)
    role = Column(Integer)
    disable = Column(Boolean)


class Tasks(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    homework = Column(NVARCHAR)
    type = Column(NVARCHAR)
    status = Column(Integer)
    create_time = Column(DateTime)
    update_time = Column(DateTime)
    user = relationship("Users")
    course = relationship("Courses")


class Contents(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(NVARCHAR)
    grade = Column(NVARCHAR)
    level = Column(Integer)
    parent_id = Column(Integer, ForeignKey("contents.id"))
    rank = Column(Integer)
    course_id = Column(Integer, ForeignKey("courses.id"))
    create_time = Column(DateTime)
    update_time = Column(DateTime)
    disable = Column(Boolean)
    course = relationship("Courses")
    children = relationship(
        "Contents", cascade="all", backref=backref("parent", remote_side=[id])
    )


class Courses(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content = Column(NVARCHAR)
    describe = Column(NVARCHAR)
    checklist = Column(NVARCHAR)
    case = Column(NVARCHAR)
    create_time = Column(DateTime)
    update_time = Column(DateTime)
    disable = Column(Boolean)


class Homeworks(Base):
    __tablename__ = "homeworks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    homework = Column(NVARCHAR)
    type = Column(NVARCHAR)
    create_time = Column(DateTime)
    update_time = Column(DateTime)
    disable = Column(Boolean)
    user_id_str = Column(VARCHAR)
    user = relationship("Users")
    course = relationship("Courses")


class Records(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(Integer)
    meta = Column(NVARCHAR)
    create_time = Column(DateTime)
    user_id_str = Column(VARCHAR)
    user = relationship("Users")


class Classes(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    code = Column(NVARCHAR)
    time = Column(DateTime)
    disable = Column(Boolean)
    user = relationship("Users")


class PlatformRecords(Base):
    __tablename__ = "platform_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(VARCHAR)
    course_id = Column(VARCHAR)
    type = Column(Integer)
    meta = Column(NVARCHAR)
    create_time = Column(DateTime, server_default=func.getdate())


class AuthorizationCodes(Base):
    __tablename__ = "authorization_codes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(VARCHAR, unique=True)
    activated_time = Column(DateTime, server_default=func.getdate())
    expire_time = Column(DateTime)


class ImageServiceLog(Base):
    """
    图像服务调用日志表
    
    重要说明：
    - user_id 存储的是 SSO 系统的唯一用户标识（来自 JWT token 的 userId 字段）
    - 这个 userId 是用户在 SSO 系统中的唯一标识（如工号、学号等）
    - 不是本地 Users 表的 id 或 user_id 字段
    - 确保跨系统的唯一性和准确性
    """
    __tablename__ = "image_service_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(VARCHAR, index=True)  # SSO 用户唯一标识（来自JWT token的userId字段）
    service_type = Column(VARCHAR)  # image_generate 或 image_edit
    status = Column(VARCHAR)  # success 或 failed
    prompt = Column(NVARCHAR)  # 用户提示词（截断至500字符）
    call_time = Column(DateTime, server_default=func.getdate(), index=True)  # 调用时间
