import json
import logging
import os
from typing import Any

import dashscope
from dashscope import Generation
from sqlalchemy.orm import Session

from db.models import (
    StudentDimensionScore,
    StudentDimensionScoreHistory,
    Users,
)

logger = logging.getLogger(__name__)

# 16 个核心维度
CORE_DIMENSIONS = {
    # 认知类
    "COG_READING": "阅读理解",
    "COG_LANGUAGE": "语言表达",
    "COG_SCIENCE_KNOWLEDGE": "科学知识",
    "COG_SCIENCE_INQUIRY": "科学探究",
    "COG_COMPUTATIONAL": "计算思维",
    "COG_TECH_LITERACY": "技术素养",
    # 心理类
    "PSY_ANXIETY": "焦虑倾向",
    "PSY_DEPRESSION": "抑郁倾向",
    "PSY_PRESSURE": "学业压力",
    "PSY_RESILIENCE": "心理韧性",
    "PSY_INTEREST_STABILITY": "兴趣稳定性",
    "PSY_LIFE_SATISFACTION": "生活满意度",
    # 实践类
    "PRAC_INNOVATION": "创新能力",
    "PRAC_PROBLEM_SOLVING": "问题解决能力",
    "PRAC_COLLABORATION": "协作能力",
    "PRAC_PRACTICE": "实践能力",
}

# 所有维度（含 AI 满意度）
ALL_DIMENSIONS = {**CORE_DIMENSIONS, "AI_SATISFACTION": "对 AI 的满意度"}


def get_user_dimension_scores(db: Session, user_id: int) -> dict[str, float]:
    """获取用户所有维度最新得分。"""
    scores = (
        db.query(StudentDimensionScore)
        .filter(StudentDimensionScore.user_id == user_id)
        .all()
    )
    result = {s.dimension_key: float(s.dimension_value) for s in scores}
    logger.info(
        f"[dimension_scores] user_id={user_id} 查到 {len(result)} 个维度得分: {result}"
    )
    return result


def get_user_by_token_user_id(db: Session, token_user_id: str) -> Users | None:
    """根据 token 中的 userId 查找本地用户。"""
    user = db.query(Users).filter(Users.sso_user_id == token_user_id).first()
    if not user:
        user = db.query(Users).filter(Users.user_id == token_user_id).first()
    if not user:
        user = db.query(Users).filter(Users.node_id == token_user_id).first()
    return user


def compute_knowledge_reserve(scores: dict[str, float]) -> float | None:
    """知识储备 = (阅读理解 + 语言表达 + 科学知识) / 3 * 0.5"""
    keys = ["COG_READING", "COG_LANGUAGE", "COG_SCIENCE_KNOWLEDGE"]
    values = [scores.get(k) for k in keys]
    if any(v is None for v in values):
        return None
    return round(sum(values) / 3 * 0.5, 2)


def get_active_score(scores: dict[str, float]) -> float | None:
    """从维度表中获取活跃度。"""
    value = scores.get("active_score")
    return round(value, 2) if value is not None else None


def _clamp(value: float, min_val: float = 0, max_val: float = 5) -> float:
    return max(min_val, min(max_val, value))


def apply_dimension_update(
    db: Session,
    user_id: int,
    dimension_key: str,
    new_value: float,
    reason: str,
    source_type: str = "interaction",
    source_id: str | None = None,
) -> dict[str, Any]:
    """应用维度更新，并记录历史。"""
    if dimension_key not in ALL_DIMENSIONS and dimension_key != "active_score":
        raise ValueError(f"未知维度: {dimension_key}")

    existing = (
        db.query(StudentDimensionScore)
        .filter(
            StudentDimensionScore.user_id == user_id,
            StudentDimensionScore.dimension_key == dimension_key,
        )
        .first()
    )

    previous_value = float(existing.dimension_value) if existing else None
    new_value = round(float(new_value), 2)

    # 写历史
    history = StudentDimensionScoreHistory(
        user_id=user_id,
        dimension_key=dimension_key,
        previous_value=previous_value,
        new_value=new_value,
        change_delta=round(
            new_value - previous_value if previous_value is not None else 0, 2
        ),
        reason=reason,
        source_type=source_type,
        source_id=source_id,
    )
    db.add(history)

    if existing:
        existing.dimension_value = new_value
    else:
        score = StudentDimensionScore(
            user_id=user_id,
            dimension_key=dimension_key,
            dimension_value=new_value,
        )
        db.add(score)

    db.commit()

    logger.info(
        f"[dimension_update] user_id={user_id} dimension={dimension_key} "
        f"previous={previous_value} new={new_value} delta={history.change_delta} "
        f"source_type={source_type} source_id={source_id} reason={reason!r}"
    )

    return {
        "dimension_key": dimension_key,
        "previous_value": previous_value,
        "new_value": new_value,
        "reason": reason,
    }


def apply_feedback(
    db: Session,
    user_id: int,
    dimension_key: str,
    delta: float,
    reason: str,
    source_type: str = "feedback",
    source_id: str | None = None,
) -> dict[str, Any]:
    """处理用户反馈（如点赞/点踩），在当前值基础上增减并截断。"""
    existing = (
        db.query(StudentDimensionScore)
        .filter(
            StudentDimensionScore.user_id == user_id,
            StudentDimensionScore.dimension_key == dimension_key,
        )
        .first()
    )

    current_value = float(existing.dimension_value) if existing else 0.0
    new_value = _clamp(current_value + delta)

    return apply_dimension_update(
        db=db,
        user_id=user_id,
        dimension_key=dimension_key,
        new_value=new_value,
        reason=reason,
        source_type=source_type,
        source_id=source_id,
    )


def _build_evaluation_prompt(scores: dict[str, float], messages: list[dict]) -> str:
    """构建给大模型的评分 prompt。"""
    # 只把核心维度给模型，active_score 和 AI_SATISFACTION 不动
    core_scores = {k: scores.get(k) for k in CORE_DIMENSIONS.keys()}
    score_lines = "\n".join(
        f"  {k} ({CORE_DIMENSIONS[k]}): {v}" for k, v in core_scores.items()
    )

    conversation = "\n".join(
        f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in messages
    )

    prompt = f"""你是一位教育评估专家。请根据学生与 AI 助手的对话，判断学生的哪些能力/心理维度发生了变化，并给出变化后的得分和依据。

当前学生各维度得分（0-5 分）：
{score_lines}

对话内容：
{conversation}

请只返回 JSON，格式如下。只输出确实有变化的维度，没有变化的不需要输出：
{{
  "PRAC_COLLABORATION": {{
    "new_value": 5.5,
    "reason": "学生在讨论海报分工时主动提出了同伴的角色建议，体现出协作能力有所提升。"
  }}
}}

注意：
- 每个维度变化幅度建议控制在 -1 到 +1 之间。
- new_value 必须在 0-5 之间。
- reason 必须具体说明依据，引用对话中的具体表现。
- 只输出 JSON，不要任何其他文字。"""

    return prompt


def evaluate_dimensions(
    db: Session,
    user_id: int,
    messages: list[dict],
) -> list[dict[str, Any]]:
    """调用大模型评估维度变化，并应用到数据库。"""
    logger.info(f"[evaluate_dimensions] 开始评分 user_id={user_id} 消息数={len(messages)}")
    scores = get_user_dimension_scores(db, user_id)
    if not scores:
        logger.warning(f"[evaluate_dimensions] 用户 {user_id} 没有维度基线，跳过评分")
        return []

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        logger.error("[evaluate_dimensions] DASHSCOPE_API_KEY 未设置，无法评分")
        return []

    try:
        prompt = _build_evaluation_prompt(scores, messages)
        logger.debug(f"[evaluate_dimensions] 评分 prompt:\n{prompt}")

        response = Generation.call(
            api_key=api_key,
            model=Generation.Models.qwen_turbo,
            messages=[{"role": "user", "content": prompt}],
            result_format="message",
            stream=False,
        )

        if not response or not response.output or not response.output.choices:
            logger.error("[evaluate_dimensions] 大模型评分返回为空")
            return []

        content = response.output.choices[0].message.content
        logger.info(f"[evaluate_dimensions] 大模型原始返回: {content!r}")

        # 清理可能的 markdown 代码块
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        result = json.loads(content)
        if not isinstance(result, dict):
            logger.error(f"[evaluate_dimensions] 大模型评分返回格式错误: {content}")
            return []

        logger.info(f"[evaluate_dimensions] 解析后变化维度数: {len(result)}")

        updated = []
        for dimension_key, item in result.items():
            if dimension_key not in CORE_DIMENSIONS:
                logger.warning(
                    f"[evaluate_dimensions] 忽略未知维度: {dimension_key}"
                )
                continue
            new_value = item.get("new_value")
            reason = item.get("reason", "")
            if new_value is None or not reason:
                logger.warning(
                    f"[evaluate_dimensions] 维度 {dimension_key} 缺少 new_value 或 reason，跳过"
                )
                continue

            updated.append(
                apply_dimension_update(
                    db=db,
                    user_id=user_id,
                    dimension_key=dimension_key,
                    new_value=new_value,
                    reason=reason,
                    source_type="interaction",
                    source_id=None,
                )
            )

        logger.info(
            f"[evaluate_dimensions] 评分完成 user_id={user_id} 实际更新 {len(updated)} 个维度: "
            f"{[u['dimension_key'] for u in updated]}"
        )
        return updated

    except json.JSONDecodeError as e:
        logger.error(f"[evaluate_dimensions] 大模型评分 JSON 解析失败: {e}")
        return []
    except Exception as e:
        logger.error(f"[evaluate_dimensions] 大模型评分失败: {e}")
        return []
