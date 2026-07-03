import logging

from db.models import Users
from sqlalchemy.orm import Session

from utils.dimension_scorer import (
    compute_knowledge_reserve,
    get_active_score,
    get_user_dimension_scores,
)

logger = logging.getLogger(__name__)


def get_user_profile(db: Session, user_id: str) -> dict | None:
    # 优先按 SSO 用户 ID 查询；本地登录用户没有 sso_user_id，则按 user_id 查询
    user = db.query(Users).filter(Users.sso_user_id == user_id).first()
    if not user:
        user = db.query(Users).filter(Users.user_id == user_id).first()
    if not user:
        user = db.query(Users).filter(Users.node_id == user_id).first()
    if not user:
        return None

    dimension_scores = get_user_dimension_scores(db, user.id)

    return {
        "real_name": user.real_name,
        "school": user.school,
        "grade": user.grade,
        "class": user.Class,
        "gender": user.gender,
        "knowledge_reserve": compute_knowledge_reserve(dimension_scores),
        "active_score": get_active_score(dimension_scores),
        "dimension_scores": dimension_scores,
    }


def _build_recommendation_rules(profile: dict) -> list[str]:
    """根据学生画像生成资源推荐选择规则。"""
    rules = []
    knowledge_reserve = profile.get("knowledge_reserve")
    if knowledge_reserve is not None:
        if knowledge_reserve <= 1.5:
            rules.append(
                f"知识储备为 {knowledge_reserve}/5 分，属于初学水平，优先推荐难度为“简单/入门”的资源，避免复杂概念和过多步骤。"
            )
        elif knowledge_reserve <= 3.5:
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


def build_profile_prompt(profile: dict, role: str = "") -> str:
    """构建用户画像 prompt。仅当 role 为 computerDoctor 时才拼接资源推荐规则和推荐理由要求。"""
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
    if profile.get("gender"):
        parts.append(f"性别：{profile['gender']}")
    if profile.get("knowledge_reserve") is not None:
        parts.append(f"知识储备：{profile['knowledge_reserve']}/5 分")
    if profile.get("active_score") is not None:
        parts.append(f"活跃度：{profile['active_score']} 分")

    sections = []
    if parts:
        sections.append("当前对话的学生画像：" + "，".join(parts) + "。")

    # 仅电脑博士角色需要资源推荐规则和推荐理由要求
    if role == "computerDoctor":
        rules = _build_recommendation_rules(profile)
        if rules:
            sections.append(
                "请根据上述画像，严格按以下规则从知识库中选择并推荐资源：\n"
                + "\n".join(f"{i + 1}. {rule}" for i, rule in enumerate(rules))
            )

    if not sections:
        return ""

    # 非电脑博士角色只返回画像信息，不拼接推荐规则
    if role != "computerDoctor":
        return "\n\n".join(sections)

    return (
        "\n\n".join(sections)
        + "\n\n"
        + "资源筛选补充说明：\n"
        "1. 知识库返回的每条资源都包含 difficulty 字段（取值为 LOW / MEDIUM / HIGH）和 resourceType 字段（取值为 VIDEO / DOCUMENT / GAME / PRACTICE / ARTICLE）。"
        "请直接根据这两个字段进行筛选，不要仅依赖标题猜测。\n"
        "2. 请严格按照上述画像规则选择资源：知识储备低优先选择 difficulty=LOW，中等选择 MEDIUM，高选择 HIGH；"
        "活跃度低优先选择 resourceType=DOCUMENT 或 ARTICLE，中等优先选择 VIDEO 或 PRACTICE，高优先选择 GAME、VIDEO 或 PRACTICE。\n"
        "3. 如果多个资源都符合条件，按相关度从高到低排序；如果完全不符合画像的资源，不要推荐。\n"
        "4. 推荐时必须输出资源链接，使用 Markdown 链接格式 `[资源标题](URL)`，并用中文标注难度和类型，附上推荐理由。"
        "难度映射：LOW→入门，MEDIUM→中等，HIGH→进阶；类型映射：VIDEO→视频，DOCUMENT→文档，GAME→游戏，PRACTICE→互动练习，ARTICLE→文章。只写中文，不要输出英文枚举值。"
        "不要直接复制提示词中的示例链接或格式，必须根据用户查询和知识库动态生成真实匹配的内容。\n\n"
        "【必须遵守】推荐理由格式：\n"
        "每个推荐资源必须附上推荐理由，说明为什么根据该学生的知识储备和活跃度推荐。"
        "格式：「推荐理由：因为你的知识储备为X/5分，属于[水平]，所以选择了[难度中文]的资源；因为你的活跃度为X分，属于[水平]，所以选择了[类型中文]的资源。」\n\n"
        "示例（根据实际画像调整，不要照搬分数）：\n"
        "示例1：推荐理由：因为你的知识储备为1/5分，属于初学水平，所以选择了入门难度；同时活跃度为25分，属于较低水平，所以推荐你可以自主阅读的文章类资源。\n"
        "[Word插入图片入门教程](https://example.com/word-image-basic)（难度：入门，类型：文章）\n\n"
        "示例2：推荐理由：因为你的知识储备为3/5分，属于中等水平，所以选择了中等难度；同时活跃度为55分，属于中等水平，适合互动练习类资源。\n"
        "[PPT动画设置互动练习](https://example.com/ppt-animation-practice)（难度：中等，类型：互动练习）\n\n"
        "示例3：推荐理由：因为你的知识储备为4/5分，属于较高水平，所以选择了进阶难度；同时活跃度为85分，属于较高水平，适合高互动的游戏类资源。\n"
        "[PPT综合设计挑战](https://example.com/ppt-design-challenge)（难度：进阶，类型：游戏）"
    )
