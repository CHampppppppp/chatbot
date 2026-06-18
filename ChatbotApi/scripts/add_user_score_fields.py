"""
为 users 表新增知识储备和活跃度字段。

支持 MySQL 和 SQL Server，通过 DATABASE_URL 自动识别数据库类型。

用法：
    python scripts/add_user_score_fields.py
    python scripts/add_user_score_fields.py --env-file .env.local
    python scripts/add_user_score_fields.py --env-file .env.cloud
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


parser = argparse.ArgumentParser(description="为 users 表新增用户评分字段")
parser.add_argument(
    "--env-file",
    default=".env",
    help="要加载的环境变量文件，默认 .env",
)
args = parser.parse_args()

# 加载环境变量
load_dotenv(args.env_file)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("错误：未设置 DATABASE_URL 环境变量")
    sys.exit(1)


def is_sqlserver(url: str) -> bool:
    return url.startswith("mssql")


def add_columns():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    if is_sqlserver(DATABASE_URL):
        add_column_sql = "ALTER TABLE users ADD {column} INT NULL;"
    else:
        add_column_sql = "ALTER TABLE users ADD COLUMN {column} INT NULL;"

    columns = ["knowledge_reserve", "active_score"]

    print(f"正在连接: {DATABASE_URL.split('@')[-1]}")
    with engine.connect() as conn:
        for column in columns:
            sql = add_column_sql.format(column=column)
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"✅ 已添加字段: {column}")
            except Exception as e:
                error_msg = str(e).lower()
                if (
                    "duplicate" in error_msg
                    or "already exists" in error_msg
                    or "重复" in error_msg
                ):
                    print(f"⚠️ 字段已存在，跳过: {column}")
                else:
                    print(f"❌ 添加字段失败 {column}: {e}")
                    raise


if __name__ == "__main__":
    add_columns()
