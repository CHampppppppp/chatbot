"""
导入 副本SHOW_CASE_801_students.csv 中的学生画像与维度得分。

用法：
    cd ChatbotApi
    source venv/bin/activate
    python scripts/import_student_dimensions.py
    python scripts/import_student_dimensions.py --csv /path/to/副本SHOW_CASE_801_students.csv
"""

import argparse
import csv
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 让项目根目录可导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import (
    StudentDimensionScore,
    StudentDimensionScoreHistory,
    Users,
)

load_dotenv(dotenv_path=os.getenv("ENV_FILE", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("错误：未设置 DATABASE_URL 环境变量")
    sys.exit(1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

# CSV 列名 → dimension_key
DIMENSION_COLUMNS = {
    "阅读理解": "COG_READING",
    "语言表达": "COG_LANGUAGE",
    "科学知识": "COG_SCIENCE_KNOWLEDGE",
    "科学探究": "COG_SCIENCE_INQUIRY",
    "计算思维": "COG_COMPUTATIONAL",
    "技术素养": "COG_TECH_LITERACY",
    "焦虑倾向": "PSY_ANXIETY",
    "抑郁倾向": "PSY_DEPRESSION",
    "坚毅品格": "PSY_RESILIENCE",
    "学业压力": "PSY_PRESSURE",
    "兴趣稳定性": "PSY_INTEREST_STABILITY",
    "生活满意度": "PSY_LIFE_SATISFACTION",
    "创新能力": "PRAC_INNOVATION",
    "问题解决能力": "PRAC_PROBLEM_SOLVING",
    "实践能力": "PRAC_PRACTICE",
    "协作能力": "PRAC_COLLABORATION",
}


def parse_float(value):
    if value is None:
        return None
    value = str(value).strip()
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def get_or_create_user(db, row):
    node_id = row.get("Node ID", "").strip()

    user = None
    if node_id:
        user = db.query(Users).filter(Users.node_id == node_id).first()

    if not user:
        user = Users(
            node_id=node_id or None,
            real_name=row.get("学生姓名", "").strip() or None,
            Class=row.get("班级", "").strip() or None,
            school=row.get("学校", "").strip() or None,
            grade=row.get("年级", "").strip() or None,
            gender=row.get("性别", "").strip() or None,
            role=1,
            disable=False,
        )
        db.add(user)
        db.flush()
        print(f"  新建用户: {user.real_name} (id={user.id}, node_id={user.node_id})")
    else:
        # 更新画像字段
        user.real_name = row.get("学生姓名", "").strip() or user.real_name
        user.Class = row.get("班级", "").strip() or user.Class
        user.school = row.get("学校", "").strip() or user.school
        user.grade = row.get("年级", "").strip() or user.grade
        user.gender = row.get("性别", "").strip() or user.gender
        print(f"  更新用户: {user.real_name} (id={user.id}, node_id={user.node_id})")

    return user


def upsert_dimension(db, user_id, dimension_key, value, source_type="csv_import"):
    if value is None:
        return

    existing = (
        db.query(StudentDimensionScore)
        .filter(
            StudentDimensionScore.user_id == user_id,
            StudentDimensionScore.dimension_key == dimension_key,
        )
        .first()
    )

    previous_value = existing.dimension_value if existing else None

    # 写历史
    history = StudentDimensionScoreHistory(
        user_id=user_id,
        dimension_key=dimension_key,
        previous_value=previous_value,
        new_value=value,
        change_delta=(value - previous_value) if previous_value is not None else 0,
        reason="CSV 初始导入",
        source_type=source_type,
        source_id=None,
        created_at=datetime.utcnow(),
    )
    db.add(history)

    if existing:
        existing.dimension_value = value
        existing.updated_at = datetime.utcnow()
    else:
        score = StudentDimensionScore(
            user_id=user_id,
            dimension_key=dimension_key,
            dimension_value=value,
            updated_at=datetime.utcnow(),
        )
        db.add(score)


def import_csv(csv_path: str):
    db = SessionLocal()
    try:
        with open(csv_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        print(f"共读取 {len(rows)} 行，开始导入...\n")

        for idx, row in enumerate(rows, 1):
            print(f"[{idx}/{len(rows)}] 处理: {row.get('学生姓名', '')}")
            user = get_or_create_user(db, row)

            # 16 核心维度
            for csv_col, dimension_key in DIMENSION_COLUMNS.items():
                value = parse_float(row.get(csv_col))
                upsert_dimension(db, user.id, dimension_key, value)

            # active_score
            active_score = parse_float(row.get("Active score"))
            upsert_dimension(db, user.id, "active_score", active_score)

            # AI_SATISFACTION 初始值 = CSV 满意度
            satisfaction = parse_float(row.get("满意度（对AI的满意度）"))
            upsert_dimension(db, user.id, "AI_SATISFACTION", satisfaction)

            db.commit()

        print("\n✅ 导入完成")
    except Exception as e:
        db.rollback()
        print(f"\n❌ 导入失败: {e}")
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="导入学生维度得分 CSV")
    parser.add_argument(
        "--env-file",
        default=None,
        help="要加载的环境变量文件，默认使用当前目录的 .env",
    )
    parser.add_argument(
        "--csv",
        default=None,
        help="CSV 文件路径",
    )
    args = parser.parse_args()

    if args.env_file:
        load_dotenv(args.env_file, override=True)
        global DATABASE_URL, engine, SessionLocal
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            print("错误：未设置 DATABASE_URL 环境变量")
            sys.exit(1)
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=engine)

    csv_path = args.csv
    if not csv_path:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [
            os.path.join(project_root, "副本SHOW_CASE_801_students.csv"),
            os.path.join(os.path.dirname(project_root), "副本SHOW_CASE_801_students.csv"),
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                csv_path = candidate
                break

    if not csv_path or not os.path.exists(csv_path):
        print(f"错误：找不到 CSV 文件: {csv_path}")
        sys.exit(1)

    print(f"导入文件: {csv_path}")
    import_csv(csv_path)


if __name__ == "__main__":
    main()
