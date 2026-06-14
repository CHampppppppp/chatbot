import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv

load_dotenv()

# 数据库连接配置 - 支持环境变量
DATABASE_URL = os.getenv("DATABASE_URL")

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL, pool_size=20, pool_pre_ping=True, pool_recycle=3600
)
# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# 声明基类
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
