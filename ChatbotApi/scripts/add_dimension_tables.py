"""
为 users 表新增 node_id、gender 字段，并创建学生维度得分表。

支持 MySQL 和 SQL Server，通过 DATABASE_URL 自动识别数据库类型。

用法：
    python scripts/add_dimension_tables.py
    python scripts/add_dimension_tables.py --env-file .env.local
    python scripts/add_dimension_tables.py --env-file .env.cloud
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text


parser = argparse.ArgumentParser(description="新增学生维度得分相关表和字段")
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


def column_exists(engine, table_name: str, column_name: str) -> bool:
    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns(table_name)}
    return column_name in columns


def table_exists(engine, table_name: str) -> bool:
    return inspect(engine).has_table(table_name)


def add_columns(engine):
    if is_sqlserver(DATABASE_URL):
        add_column_sql = "ALTER TABLE users ADD {column} {dtype} NULL;"
    else:
        add_column_sql = "ALTER TABLE users ADD COLUMN {column} {dtype} NULL;"

    columns = {
        "node_id": "VARCHAR(100)",
        "gender": "VARCHAR(10)",
    }

    with engine.connect() as conn:
        for column, dtype in columns.items():
            if column_exists(engine, "users", column):
                print(f"⚠️ 字段已存在，跳过: {column}")
                continue
            sql = add_column_sql.format(column=column, dtype=dtype)
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"✅ 已添加字段: {column}")
            except Exception as e:
                print(f"❌ 添加字段失败 {column}: {e}")
                raise

        # SQL Server 需要单独创建唯一索引（不支持在 ADD 时直接 UNIQUE）
        if is_sqlserver(DATABASE_URL):
            try:
                conn.execute(
                    text(
                        "CREATE UNIQUE INDEX ux_users_node_id ON users(node_id) WHERE node_id IS NOT NULL;"
                    )
                )
                conn.commit()
                print("✅ 已创建 users.node_id 唯一索引")
            except Exception as e:
                error_msg = str(e).lower()
                if "already exists" in error_msg or "重复" in error_msg:
                    print("⚠️ 索引已存在，跳过: ux_users_node_id")
                else:
                    raise


def create_dimension_tables(engine):
    if is_sqlserver(DATABASE_URL):
        scores_sql = """
        CREATE TABLE student_dimension_scores (
            id INT IDENTITY(1,1) PRIMARY KEY,
            user_id INT NOT NULL,
            dimension_key VARCHAR(50) NOT NULL,
            dimension_value DECIMAL(8, 2) NOT NULL,
            updated_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT uq_user_dimension UNIQUE (user_id, dimension_key),
            CONSTRAINT fk_sds_user_id FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE INDEX idx_dimension_key ON student_dimension_scores(dimension_key);
        """
        history_sql = """
        CREATE TABLE student_dimension_score_history (
            id INT IDENTITY(1,1) PRIMARY KEY,
            user_id INT NOT NULL,
            dimension_key VARCHAR(50) NOT NULL,
            previous_value DECIMAL(8, 2) NULL,
            new_value DECIMAL(8, 2) NOT NULL,
            change_delta DECIMAL(8, 2) NOT NULL,
            reason TEXT NOT NULL,
            source_type VARCHAR(50) DEFAULT 'interaction',
            source_id VARCHAR(100) NULL,
            created_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_sdsh_user_id FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE INDEX idx_user_dimension ON student_dimension_score_history(user_id, dimension_key);
        CREATE INDEX idx_created_at ON student_dimension_score_history(created_at);
        """
    else:
        scores_sql = """
        CREATE TABLE student_dimension_scores (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            dimension_key VARCHAR(50) NOT NULL,
            dimension_value DECIMAL(8, 2) NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY (user_id, dimension_key),
            KEY idx_dimension_key (dimension_key),
            CONSTRAINT fk_sds_user_id FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
        history_sql = """
        CREATE TABLE student_dimension_score_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            dimension_key VARCHAR(50) NOT NULL,
            previous_value DECIMAL(8, 2) NULL,
            new_value DECIMAL(8, 2) NOT NULL,
            change_delta DECIMAL(8, 2) NOT NULL,
            reason TEXT NOT NULL,
            source_type VARCHAR(50) DEFAULT 'interaction',
            source_id VARCHAR(100) NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            KEY idx_user_dimension (user_id, dimension_key),
            KEY idx_created_at (created_at),
            CONSTRAINT fk_sdsh_user_id FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """

    with engine.connect() as conn:
        if table_exists(engine, "student_dimension_scores"):
            print("⚠️ 表已存在，跳过: student_dimension_scores")
        else:
            conn.execute(text(scores_sql))
            conn.commit()
            print("✅ 已创建表: student_dimension_scores")

        if table_exists(engine, "student_dimension_score_history"):
            print("⚠️ 表已存在，跳过: student_dimension_score_history")
        else:
            conn.execute(text(history_sql))
            conn.commit()
            print("✅ 已创建表: student_dimension_score_history")


def main():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    print(f"正在连接: {DATABASE_URL.split('@')[-1]}")

    add_columns(engine)
    create_dimension_tables(engine)
    print("\n迁移完成。")


if __name__ == "__main__":
    main()
