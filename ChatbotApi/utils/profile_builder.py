import json
import logging

from db.models import Users
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_user_profile(db: Session, user_id: str) -> dict | None:
    # 优先按 SSO 用户 ID 查询；本地登录用户没有 sso_user_id，则按 user_id 查询
    user = db.query(Users).filter(Users.sso_user_id == user_id).first()
    if not user:
        user = db.query(Users).filter(Users.user_id == user_id).first()
    if not user:
        return None
    return {
        "real_name": user.real_name,
        "school": user.school,
        "grade": user.grade,
        "class": user.Class,
        "interests": user.interests,
        "knowledge_reserve": user.knowledge_reserve,
        "active_score": user.active_score,
    }


def _build_recommendation_rules(profile: dict) -> list[str]:
    """根据学生画像生成资源推荐选择规则。"""
    rules = []
    knowledge_reserve = profile.get("knowledge_reserve")
    if knowledge_reserve is not None:
        if knowledge_reserve <= 1:
            rules.append(
                f"知识储备为 {knowledge_reserve}/5 分，属于初学水平，优先推荐难度为“简单/入门”的资源，避免复杂概念和过多步骤。"
            )
        elif knowledge_reserve <= 3:
            rules.append(
                f"知识储备为 {knowledge_reserve}/5 分，属于中等水平，推荐难度为“中等”的资源，可适当搭配简单资源帮助巩固。"
            )
        else:
            rules.append(
                f"知识储备为 {knowledge_reserve}/5 分，属于较高水平，可推荐难度为“困难/进阶”的资源，适当增加综合性和挑战性。"
            )
    active_score = profile.get("active_score")
    if active_score is not None:
        if active_score < 40:
            rules.append(
                f"活跃度为 {active_score} 分，属于较低水平，优先推荐“文章”“图文教程”等低交互门槛、可自主阅读的资源，减少操作步骤和游戏化任务。"
            )
        elif active_score < 75:
            rules.append(
                f"活跃度为 {active_score} 分，属于中等水平，可推荐“视频”“互动练习”等具有适度参与感的资源，避免任务过重。"
            )
        else:
            rules.append(
                f"活跃度为 {active_score} 分，属于较高水平，优先推荐“游戏”“挑战任务”“项目式资源”“视频”等高互动、高参与感形式。"
            )
    return rules


def build_profile_prompt(profile: dict) -> str:
    if not profile:
        return ""
    parts = []
    if profile.get("real_name"):
        parts.append(f"姓名：{profile['real_name']}")
    if profile.get("school"):
        parts.append(f"学校：{profile['school']}")
    if profile.get("grade"):
        parts.append(f"年级：{profile['grade']}")
    if profile.get("class"):
        parts.append(f"班级：{profile['class']}")
    if profile.get("interests"):
        try:
            tags = json.loads(profile["interests"])
            if isinstance(tags, list) and tags:
                parts.append(f"兴趣标签：{'、'.join(tags)}")
        except (json.JSONDecodeError, TypeError):
            if profile["interests"].strip():
                parts.append(f"兴趣标签：{profile['interests']}")
    if profile.get("knowledge_reserve") is not None:
        parts.append(f"知识储备：{profile['knowledge_reserve']}/5 分")
    if profile.get("active_score") is not None:
        parts.append(f"活跃度：{profile['active_score']} 分")

    rules = _build_recommendation_rules(profile)

    sections = []
    if parts:
        sections.append("当前对话的学生画像：" + "，".join(parts) + "。")
    if rules:
        sections.append(
            "请根据上述画像，严格按以下规则从知识库中选择并推荐资源：\n"
            + "\n".join(f"{i + 1}. {rule}" for i, rule in enumerate(rules))
        )

    if not sections:
        return ""
    return "\n\n".join(sections) + "\n\n推荐时优先选择符合以上规则的资源，并简要说明推荐理由。"
