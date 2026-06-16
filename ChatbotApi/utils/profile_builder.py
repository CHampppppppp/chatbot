import json
import logging

from db.models import Users
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_user_profile(db: Session, sso_user_id: str) -> dict | None:
    user = db.query(Users).filter(Users.sso_user_id == sso_user_id).first()
    if not user:
        return None
    return {
        "real_name": user.real_name,
        "school": user.school,
        "grade": user.grade,
        "class": user.Class,
        "interests": user.interests,
    }


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
    if not parts:
        return ""
    return "当前对话的学生画像：" + "，".join(parts) + "。请根据学生画像进行个性化推荐。"
