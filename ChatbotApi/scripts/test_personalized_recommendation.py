#!/usr/bin/env python3
"""
测试个性化推荐：为两个临时用户构造不同画像，问同一个问题，对比 LLM 输出。

用法：
    cd ChatbotApi
    source venv/bin/activate
    ENV_FILE=.env.local python scripts/test_personalized_recommendation.py
    ENV_FILE=.env.local python scripts/test_personalized_recommendation.py --scenario active
    ENV_FILE=.env.local python scripts/test_personalized_recommendation.py --question "怎么制作PPT"

要求：
    - 后端已启动并连接正确的数据库（默认 http://localhost:8001）
    - .env.local 里配置了 DATABASE_URL、SECRET_KEY、DASHSCOPE_API_KEY 等
"""

import argparse
import os
import sys
import time
import uuid
from datetime import timedelta

import pandas as pd
import requests
from dotenv import load_dotenv

# 必须先加载 .env，再导入项目模块（db.database 导入时会读取 DATABASE_URL）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(dotenv_path=os.getenv("ENV_FILE", ".env"))

from common.security import create_id_token
from db.database import SessionLocal
from db.models import StudentDimensionScore, StudentDimensionScoreHistory, Users
from utils.dimension_scorer import compute_knowledge_reserve, get_active_score
from utils.profile_builder import build_profile_prompt, get_user_profile


BASE_URL = os.getenv("TEST_BACKEND_URL", "http://localhost:8001")

# 知识库资源清单（相对 ChatbotApi 的上级目录）
RESOURCES_XLSX = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "resources_export.xlsx",
)


def load_resources() -> pd.DataFrame | None:
    if not os.path.exists(RESOURCES_XLSX):
        return None
    try:
        return pd.read_excel(RESOURCES_XLSX)
    except Exception as e:
        print(f"⚠️ 无法读取知识库清单 {RESOURCES_XLSX}: {e}")
        return None


def parse_sse(response) -> str:
    """把 text/event-stream 聚合成一段纯文本。"""
    chunks = []
    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue
        if line.startswith("data: "):
            payload = line[6:]
            if payload == "[DONE]":
                break
            chunks.append(payload)
    text = "".join(chunks)
    # 后端把 \n 替换成了 <br/>，这里还原方便阅读
    return text.replace("<br/>", "\n").strip()


def create_token(user_id: str) -> str:
    return create_id_token(
        {
            "sub": user_id,
            "userId": user_id,
            "userType": "student",
        },
        expires_delta=timedelta(hours=1),
    )


def upsert_score(db, user_id: int, dimension_key: str, value: float):
    """写入或更新维度得分。"""
    existing = (
        db.query(StudentDimensionScore)
        .filter(
            StudentDimensionScore.user_id == user_id,
            StudentDimensionScore.dimension_key == dimension_key,
        )
        .first()
    )
    if existing:
        existing.dimension_value = value
    else:
        db.add(
            StudentDimensionScore(
                user_id=user_id,
                dimension_key=dimension_key,
                dimension_value=value,
            )
        )


def build_user(
    db, suffix: str, reading: float, language: float, science: float, active: float
) -> Users:
    """创建一个临时用户并写入画像维度。"""
    user_id = f"test_persona_{suffix}_{uuid.uuid4().hex[:8]}"
    user = Users(
        user_id=user_id,
        real_name=f"测试用户-{suffix}",
        Class="test",
        role=1,
        disable=False,
    )
    db.add(user)
    db.flush()  # 拿到 user.id

    upsert_score(db, user.id, "COG_READING", reading)
    upsert_score(db, user.id, "COG_LANGUAGE", language)
    upsert_score(db, user.id, "COG_SCIENCE_KNOWLEDGE", science)
    upsert_score(db, user.id, "active_score", active)

    db.commit()
    db.refresh(user)
    return user


def ask_computer_doctor(base_url: str, token: str, question: str) -> str:
    """调用 /platform/computerDoctor，返回完整回复文本。"""
    url = f"{base_url}/platform/computerDoctor"
    resp = requests.post(
        url,
        json={
            "messages": [{"role": "user", "content": question}],
            "role": "computerDoctor",
        },
        cookies={"id_token": token},
        stream=True,
        timeout=120,
    )
    resp.raise_for_status()
    return parse_sse(resp)


def find_matched_resources(answer: str, resources: pd.DataFrame) -> list[dict]:
    """根据回答文本匹配知识库中的资源（按 URL 或标题子串）。"""
    matched = []
    for _, row in resources.iterrows():
        title = str(row.get("title") or "")
        url = str(row.get("url") or "")
        if not title and not url:
            continue
        # 优先用 URL 匹配，再用标题子串
        if url and url in answer:
            matched.append({"title": title, "url": url, "type": row.get("resourceType"), "difficulty": row.get("difficulty")})
        elif title and len(title) > 4 and title in answer:
            matched.append({"title": title, "url": url, "type": row.get("resourceType"), "difficulty": row.get("difficulty")})
    # 按标题去重
    seen = set()
    unique = []
    for m in matched:
        if m["title"] not in seen:
            seen.add(m["title"])
            unique.append(m)
    return unique


def main():
    parser = argparse.ArgumentParser(description="测试个性化推荐差异")
    parser.add_argument(
        "--backend", default=BASE_URL, help="后端地址，默认 http://localhost:8001"
    )
    parser.add_argument(
        "--scenario",
        choices=["knowledge", "active"],
        default="knowledge",
        help="测试维度：knowledge（对比知识储备高低）或 active（对比活跃度高低）",
    )
    parser.add_argument(
        "--question",
        default=None,
        help="统一询问的问题，不指定则使用场景默认问题",
    )
    args = parser.parse_args()

    # 场景默认问题
    default_questions = {
        "knowledge": "我想做一个关于动物的PPT，帮我推荐合适的学习资源",
        "active": "怎么给幻灯片添加切换效果？",
    }
    question = args.question or default_questions[args.scenario]

    resources = load_resources()
    if resources is not None:
        print(f"📚 已加载知识库清单：{len(resources)} 条资源\n")

    # 先简单探测后端是否活着
    try:
        r = requests.head(f"{args.backend}/health", timeout=5)
        if r.status_code not in (200, 405):
            print(f"⚠️ 后端 /health 返回状态码 {r.status_code}")
    except Exception as e:
        print(f"❌ 无法连接后端 {args.backend}: {e}")
        print("请先启动后端：ENV_FILE=.env.local ./venv/bin/python main.py")
        return

    db = SessionLocal()
    users = []
    try:
        if args.scenario == "knowledge":
            # A：低知识储备 + 低活跃度
            user_a = build_user(db, "low", reading=1.0, language=1.0, science=0.5, active=20.0)
            # B：高知识储备 + 高活跃度
            user_b = build_user(db, "high", reading=8.0, language=8.0, science=7.0, active=90.0)
        else:
            # A：中等知识储备 + 低活跃度
            user_a = build_user(db, "low_active", reading=4.0, language=4.0, science=4.0, active=20.0)
            # B：同等中等知识储备 + 高活跃度
            user_b = build_user(db, "high_active", reading=4.0, language=4.0, science=4.0, active=90.0)
        users = [user_a, user_b]

        profiles = []
        for user in users:
            profile = get_user_profile(db, user.user_id)
            prompt = build_profile_prompt(profile)
            profiles.append((user, profile, prompt))
            print(f"\n👤 {user.real_name} ({user.user_id})")
            print(f"   知识储备: {profile['knowledge_reserve']}")
            print(f"   活跃度:   {profile['active_score']}")
            print("   注入 prompt:\n" + "-" * 40)
            print(prompt)
            print("-" * 40)

        print(f"\n📝 统一问题：{question}\n")

        results = []
        for user, profile, prompt in profiles:
            token = create_token(user.user_id)
            print(f"⏳ 正在请求 {user.real_name} 的回复...")
            start = time.time()
            answer = ask_computer_doctor(args.backend, token, question)
            elapsed = time.time() - start
            results.append((user, answer, elapsed))
            print(f"✅ {user.real_name} 耗时 {elapsed:.1f}s\n")

        print("=" * 60)
        print("🆚 结果对比")
        print("=" * 60)
        for user, answer, elapsed in results:
            print(f"\n>>> {user.real_name} (user_id={user.user_id})")
            print(answer)
            if resources is not None:
                matched = find_matched_resources(answer, resources)
                print(f"\n🔍 匹配到的知识库资源（{len(matched)} 条）：")
                for m in matched:
                    print(f"   [{m['difficulty']}/{m['type']}] {m['title']} ({m['url']})")
            print(f"\n[耗时 {elapsed:.1f}s]")

    finally:
        print("\n🧹 清理临时测试用户...")
        for user in users:
            try:
                # 先删历史记录，再删维度得分，最后删用户
                db.query(StudentDimensionScoreHistory).filter(
                    StudentDimensionScoreHistory.user_id == user.id
                ).delete()
                db.query(StudentDimensionScore).filter(
                    StudentDimensionScore.user_id == user.id
                ).delete()
                db.query(Users).filter(Users.id == user.id).delete()
                db.commit()
                print(f"   已删除 {user.user_id}")
            except Exception as e:
                print(f"   删除 {user.user_id} 失败: {e}")
                db.rollback()
        db.close()


if __name__ == "__main__":
    main()
