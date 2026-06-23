from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import backref, relationship

from db.database import Base


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(100), unique=True)
    real_name = Column(String(100))
    school = Column(String(100))
    grade = Column(String(50))
    Class = Column(String(50))
    role = Column(Integer)
    disable = Column(Boolean)
    sso_user_id = Column(String(100), unique=True, nullable=True)
    node_id = Column(String(100), unique=True, nullable=True)
    gender = Column(String(10), nullable=True)
    interests = Column(Text, nullable=True)
    knowledge_reserve = Column(Integer, nullable=True)  # 知识储备 0-5 分
    active_score = Column(Integer, nullable=True)  # 活跃度分数


class Tasks(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    homework = Column(Text)
    type = Column(String(50))
    status = Column(Integer)
    create_time = Column(DateTime)
    update_time = Column(DateTime)
    user = relationship("Users")
    course = relationship("Courses")


class Contents(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200))
    grade = Column(String(50))
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
    content = Column(Text)
    describe = Column(Text)
    checklist = Column(Text)
    case = Column(Text)
    create_time = Column(DateTime)
    update_time = Column(DateTime)
    disable = Column(Boolean)


class Homeworks(Base):
    __tablename__ = "homeworks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    homework = Column(Text)
    type = Column(String(50))
    create_time = Column(DateTime)
    update_time = Column(DateTime)
    disable = Column(Boolean)
    user_id_str = Column(String(100))
    user = relationship("Users")
    course = relationship("Courses")


class Records(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(Integer)
    meta = Column(Text)
    create_time = Column(DateTime)
    user_id_str = Column(String(100))
    user = relationship("Users")


class Classes(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    code = Column(String(100))
    time = Column(DateTime)
    disable = Column(Boolean)
    user = relationship("Users")


class PlatformRecords(Base):
    __tablename__ = "platform_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(100))
    course_id = Column(String(100))
    type = Column(Integer)
    meta = Column(Text)
    create_time = Column(DateTime, server_default=func.now())


class AuthorizationCodes(Base):
    __tablename__ = "authorization_codes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(100), unique=True)
    activated_time = Column(DateTime, server_default=func.now())
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
    user_id = Column(String(100), index=True)  # SSO 用户唯一标识（来自JWT token的userId字段）
    service_type = Column(String(50))  # image_generate 或 image_edit
    status = Column(String(50))  # success 或 failed
    prompt = Column(String(500))  # 用户提示词（截断至500字符）
    call_time = Column(DateTime, server_default=func.now(), index=True)  # 调用时间


class StudentDimensionScore(Base):
    __tablename__ = "student_dimension_scores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dimension_key = Column(String(50), nullable=False)
    dimension_value = Column(Numeric(8, 2), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    user = relationship("Users")


class StudentDimensionScoreHistory(Base):
    __tablename__ = "student_dimension_score_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dimension_key = Column(String(50), nullable=False)
    previous_value = Column(Numeric(8, 2), nullable=True)
    new_value = Column(Numeric(8, 2), nullable=False)
    change_delta = Column(Numeric(8, 2), nullable=False)
    reason = Column(Text, nullable=False)
    source_type = Column(String(50), default="interaction")
    source_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    user = relationship("Users")
