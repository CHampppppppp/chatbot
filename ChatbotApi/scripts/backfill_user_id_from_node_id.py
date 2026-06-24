#!/usr/bin/env python3
"""
将 users 表中 user_id 为空的记录，用 node_id 回填。

用法：
    cd ChatbotApi
    source venv/bin/activate
    python scripts/backfill_user_id_from_node_id.py

处理逻辑：
    1. 找到所有 user_id IS NULL AND node_id IS NOT NULL 的用户
    2. 优先设置 user_id = node_id
    3. 若 node_id 已被他人占用为 user_id，则生成 fallback（如 node_id_1）
    4. 全程在一个事务中执行，失败自动回滚
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 必须先加载 .env，再导入 db.models（db.database 会在导入时读取 DATABASE_URL 创建 engine）
load_dotenv(dotenv_path=os.getenv("ENV_FILE", ".env"))

from db.models import Users

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("错误：未设置 DATABASE_URL 环境变量")
    sys.exit(1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def _find_unique_user_id(
    db: Session, node_id: str, assigned: set[str]
) -> str:
    """确保生成的 user_id 不与现有记录冲突，也不与本次已分配冲突。"""
    if len(node_id) > 100:
        print(f"    [WARN] node_id 长度超过 100，将被截断: {node_id[:50]}...")

    candidate = node_id[:100]
    if candidate not in assigned:
        existing = db.query(Users).filter(Users.user_id == candidate).first()
        if existing is None:
            return candidate

    counter = 1
    max_attempts = 1000
    while counter <= max_attempts:
        candidate = f"{node_id[:95]}_{counter}"
        if candidate not in assigned:
            existing = db.query(Users).filter(Users.user_id == candidate).first()
            if existing is None:
                return candidate
        counter += 1

    raise RuntimeError(f"无法为 node_id={node_id} 生成唯一 user_id")


def main(dry_run: bool = False):
    db = SessionLocal()
    try:
        users = (
            db.query(Users)
            .filter(Users.user_id.is_(None), Users.node_id.isnot(None))
            .all()
        )

        if not users:
            print("没有需要回填的 user_id（user_id 为空且 node_id 不为空的记录不存在）")
            return

        mode = "【模拟运行】" if dry_run else ""
        print(f"{mode} 发现 {len(users)} 条需要回填 user_id 的记录\n")

        assigned: set[str] = set()
        for user in users:
            old_user_id = user.user_id
            new_user_id = _find_unique_user_id(db, user.node_id, assigned)
            assigned.add(new_user_id)
            if not dry_run:
                user.user_id = new_user_id
            print(
                f"  {'将回填' if dry_run else '回填'}: id={user.id}, real_name={user.real_name}, "
                f"node_id={user.node_id}, user_id {old_user_id} -> {new_user_id}"
            )

        if dry_run:
            print(f"\n✅ 模拟完成，共 {len(users)} 条记录会被修改（未提交）")
        else:
            db.commit()
            print(f"\n✅ 成功回填 {len(users)} 条记录的 user_id")
    except Exception as e:
        db.rollback()
        print(f"\n❌ 回填失败，已回滚: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将 users.user_id 用 node_id 回填")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅预览会修改哪些记录，不实际写入数据库",
    )
    args = parser.parse_args()
    main(dry_run=args.dry_run)
