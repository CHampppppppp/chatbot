#!/usr/bin/env python3
"""
Migrate data from cloud SQL Server to local MySQL.

Usage:
    # 1. Source = cloud SQL Server, target = local MySQL
    export SOURCE_DATABASE_URL="mssql+pymssql://..."
    export TARGET_DATABASE_URL="mysql+pymysql://chatbot:chatbot@localhost:3306/chatbot_local?charset=utf8mb4"

    # 2. Create the target database manually first:
    mysql -uroot -e "CREATE DATABASE chatbot_local CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

    # 3. Run migration
    cd ChatbotApi
    source venv/bin/activate
    python scripts/migrate_sqlserver_to_mysql.py
"""

import os
import sys
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# Make project root importable so we can reuse db.models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import Base
from db.models import (
    AuthorizationCodes,
    Classes,
    Contents,
    Courses,
    Homeworks,
    ImageServiceLog,
    PlatformRecords,
    Records,
    Tasks,
    Users,
)

load_dotenv()

SOURCE_URL = os.getenv("SOURCE_DATABASE_URL")
TARGET_URL = os.getenv("TARGET_DATABASE_URL")

if not SOURCE_URL or not TARGET_URL:
    print("Error: SOURCE_DATABASE_URL and TARGET_DATABASE_URL must be set.")
    sys.exit(1)

source_engine = create_engine(SOURCE_URL, pool_pre_ping=True)
target_engine = create_engine(TARGET_URL, pool_pre_ping=True)

SourceSession = sessionmaker(bind=source_engine)
TargetSession = sessionmaker(bind=target_engine)

source_metadata = MetaData()

# Maps duplicate user PKs to the kept PK so child records stay consistent.
USER_ID_REMAP: dict[int, int] = {}

# Tables are ordered by FK dependency (parents first, children after).
TABLES = [
    Users,
    Courses,
    Contents,
    Tasks,
    Homeworks,
    Records,
    Classes,
    PlatformRecords,
    AuthorizationCodes,
    ImageServiceLog,
]


@contextmanager
def session_scope(SessionCls):
    session = SessionCls()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def table_exists(engine, table_name: str) -> bool:
    return inspect(engine).has_table(table_name)


def copy_table(source_session, target_session, model_cls):
    table_name = model_cls.__tablename__
    global USER_ID_REMAP

    if not table_exists(source_engine, table_name):
        print(f"  [SKIP] Source table '{table_name}' does not exist.")
        return

    # Reflect the source table so we read exactly the columns that exist there.
    source_table = Table(table_name, source_metadata, autoload_with=source_engine)
    result = source_session.execute(source_table.select())
    rows = [dict(row._mapping) for row in result]
    total = len(rows)

    if total == 0:
        print(f"  [OK] {table_name}: 0 rows")
        return

    # Sort self-referential tables so parents are inserted before children.
    if table_name == "contents":
        rows = sorted(rows, key=lambda r: (r.get("parent_id") is not None, r.get("id") or 0))

    # Deduplicate users by user_id and remap child FKs.
    if table_name == "users":
        seen: dict[str, dict] = {}
        skipped = 0
        for row in rows:
            uid = row.get("user_id")
            if uid is not None and uid in seen:
                USER_ID_REMAP[row["id"]] = seen[uid]["id"]
                skipped += 1
            else:
                seen[uid] = row
        rows = list(seen.values())
        if skipped:
            print(f"  [WARN] users: skipped {skipped} duplicate user_id(s)")

    # Remap FK references for tables that point to users.id.
    if table_name in ("tasks", "homeworks", "records", "classes"):
        fk_col = "teacher_id" if table_name == "classes" else "user_id"
        for row in rows:
            old_id = row.get(fk_col)
            if old_id in USER_ID_REMAP:
                row[fk_col] = USER_ID_REMAP[old_id]

    # Insert into target; missing columns in source (e.g. newly added fields) become NULL.
    target_session.execute(model_cls.__table__.insert(), rows)
    target_session.commit()
    print(f"  [OK] {table_name}: {len(rows)} rows migrated")


def main():
    print("Source:", SOURCE_URL.split("@")[-1].split("/")[0])
    print("Target:", TARGET_URL.split("@")[-1].split("?")[0])

    # Create target schema
    print("\nCreating target tables...")
    Base.metadata.create_all(bind=target_engine)
    print("Target tables ready.")

    print("\nMigrating data...")
    with session_scope(SourceSession) as source_session, session_scope(
        TargetSession
    ) as target_session:
        # Allow explicit 0 in AUTO_INCREMENT primary keys (source SQL Server may use 0).
        target_session.execute(text("SET SESSION sql_mode = 'NO_AUTO_VALUE_ON_ZERO'"))
        # Disable FK checks during bulk load to avoid ordering edge cases.
        target_session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

        for model_cls in TABLES:
            copy_table(source_session, target_session, model_cls)

        target_session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

    print("\nMigration complete.")


if __name__ == "__main__":
    main()
