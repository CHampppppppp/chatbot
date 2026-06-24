"""
把 users 表中的 active_score 和 knowledge_reserve 迁移到 student_dimension_scores。

用法：
    cd ChatbotApi
    source venv/bin/activate
    python scripts/migrate_user_scores_to_dimensions.py
    python scripts/migrate_user_scores_to_dimensions.py --env-file .env.local
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import StudentDimensionScore, StudentDimensionScoreHistory, Users


def upsert_dimension(db, user_id, dimension_key, value, source_type="migration"):
    if value is None:
        return False

    existing = (
        db.query(StudentDimensionScore)
        .filter(
            StudentDimensionScore.user_id == user_id,
            StudentDimensionScore.dimension_key == dimension_key,
        )
        .first()
    )

    if existing:
        print(f"    维度 {dimension_key} 已存在，跳过")
        return False

    score = StudentDimensionScore(
        user_id=user_id,
        dimension_key=dimension_key,
        dimension_value=value,
    )
    db.add(score)

    history = StudentDimensionScoreHistory(
        user_id=user_id,
        dimension_key=dimension_key,
        previous_value=None,
        new_value=value,
        change_delta=0,
        reason="从 users 表迁移",
        source_type=source_type,
        source_id=None,
    )
    db.add(history)
    return True


def migrate(db):
    users = (
        db.query(Users)
        .filter(
            (Users.active_score.isnot(None)) | (Users.knowledge_reserve.isnot(None))
        )
        .all()
    )

    print(f"共发现 {len(users)} 位用户有旧字段数据，开始迁移...\n")

    migrated_users = 0
    for user in users:
        print(f"用户 {user.id} ({user.real_name or user.user_id or user.node_id}):")
        has_migrated = False

        if user.active_score is not None:
            if upsert_dimension(db, user.id, "active_score", float(user.active_score)):
                print(f"    迁移 active_score: {user.active_score}")
                has_migrated = True

        if user.knowledge_reserve is not None:
            if upsert_dimension(
                db, user.id, "knowledge_reserve", float(user.knowledge_reserve)
            ):
                print(f"    迁移 knowledge_reserve: {user.knowledge_reserve}")
                has_migrated = True

        if has_migrated:
            migrated_users += 1

        db.commit()

    print(f"\n✅ 迁移完成，共迁移 {migrated_users} 位用户")


def main():
    parser = argparse.ArgumentParser(description="迁移 users 旧字段到维度表")
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
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        migrate(db)
    except Exception as e:
        db.rollback()
        print(f"\n❌ 迁移失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
