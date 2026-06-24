"""
删除 users 表的 active_score 和 knowledge_reserve 字段。

用法：
    cd ChatbotApi
    source venv/bin/activate
    python scripts/drop_user_score_columns.py
    python scripts/drop_user_score_columns.py --env-file .env.local
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text


def is_sqlserver(url) -> bool:
    return str(url).startswith("mssql")


def column_exists(engine, table_name: str, column_name: str) -> bool:
    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns(table_name)}
    return column_name in columns


def drop_columns(engine):
    columns = ["active_score", "knowledge_reserve"]

    with engine.connect() as conn:
        for column in columns:
            if not column_exists(engine, "users", column):
                print(f"⚠️ 字段已不存在，跳过: {column}")
                continue

            if is_sqlserver(engine.url):
                sql = f"ALTER TABLE users DROP COLUMN {column};"
            else:
                sql = f"ALTER TABLE users DROP COLUMN {column};"

            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"✅ 已删除字段: {column}")
            except Exception as e:
                print(f"❌ 删除字段失败 {column}: {e}")
                raise


def main():
    parser = argparse.ArgumentParser(description="删除 users 表的旧评分字段")
    parser.add_argument(
        "--env-file",
        default=".env",
        help="要加载的环境变量文件，默认 .env",
    )
    args = parser.parse_args()

    load_dotenv(args.env_file)

    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("错误：未设置 DATABASE_URL 环境变量")
        sys.exit(1)

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    print(f"正在连接: {DATABASE_URL.split('@')[-1]}")
    drop_columns(engine)
    print("\n清理完成。")


if __name__ == "__main__":
    main()
