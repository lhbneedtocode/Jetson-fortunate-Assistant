from __future__ import annotations

from typing import Any

from app.services.fortune_retriever import FortuneChunk


ASPECT_ZH = {
    "general": "综合",
    "career": "事业/求职",
    "study": "学业/考试",
    "love": "感情/姻缘",
    "wealth": "财富/投资",
    "health": "健康",
    "family": "家庭",
    "self": "自身",
    "travel": "出行",
    "business": "交易/生意",
}

STYLE_ZH = {
    "modern": "现代口语",
    "traditional": "传统古风",
    "healing": "温柔治愈",
    "sharp": "犀利吐槽",
    "rational": "理性分析",
}

STYLE_INSTRUCTIONS = {
    "modern": "现代口语：表达自然、清楚、少玄学词，像日常建议。",
    "traditional": "传统古风：语言庄重含蓄，可适度使用‘宜守不宜躁’等表达，但必须易懂。",
    "healing": "温柔治愈：先接住焦虑，再给小步骤建议，语气温和支持。",
    "sharp": "犀利吐槽：可以直接幽默，但不能攻击用户，最后必须给可执行建议。",
    "rational": "理性分析：少情绪化安慰，多拆解现实变量、风险点、可控因素和下一步动作。",
}


def classify_aspect(question: str) -> str:
    q = question.lower()
    keyword_map = {
        "career": ["工作", "事业", "求职", "实习", "面试", "offer", "升职", "跳槽", "就业"],
        "study": ["考试", "学业", "课程", "论文", "研究生", "申请", "成绩", "毕业", "升学"],
        "love": ["感情", "恋爱", "对象", "复合", "分手", "婚姻", "姻缘", "喜欢", "表白"],
        "wealth": ["钱", "财", "投资", "股票", "收入", "财富", "赚钱", "理财", "基金"],
        "health": ["健康", "病", "身体", "焦虑", "失眠", "医院", "疼", "康复"],
        "family": ["家庭", "父母", "家人", "孩子", "亲戚"],
        "travel": ["出行", "旅游", "搬家", "移民", "外地"],
        "business": ["交易", "生意", "合作", "创业", "客户"],
    }

    for aspect, keywords in keyword_map.items():
        if any(word.lower() in q for word in keywords):
            return aspect

    return "general"


def build_fortune_retrieval_query(question: str, aspect: str, sign_id: str) -> str:
    aspect_label = ASPECT_ZH.get(aspect, aspect)
    return f"签号：{sign_id}。问题方向：{aspect_label}。用户问题：{question}"


STRUCTURED_SYSTEM_PROMPT = """
你是“灵签智解”系统的中文解签助手。
你的任务是基于给定签文资料，生成结构化 JSON 解签报告。

重要边界：
1. 只能依据给定签文资料解释，不要编造签号、签诗或典故。
2. 这是传统文化娱乐和自我反思参考，不代表现实预测。
3. 不能替代医学、法律、投资、职业等专业建议。
4. 必须只输出一个合法 JSON 对象，不要输出 Markdown，不要输出代码块，不要输出额外解释。
""".strip()


def _shorten(text: str, limit: int = 520) -> str:
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def _build_evidence_text(chunks: list[FortuneChunk]) -> str:
    evidence_blocks = []
    for idx, chunk in enumerate(chunks[:6], start=1):
        meta = chunk.metadata or {}
        evidence_blocks.append(
            "\n".join([
                f"资料{idx}：",
                f"- 签号：{meta.get('sign_id')}",
                f"- 吉凶等级：{meta.get('level')}",
                f"- 典故标题：{meta.get('story_title')}",
                f"- 资料方向：{meta.get('aspect_label', meta.get('aspect'))}",
                f"- 资料类型：{meta.get('chunk_type')}",
                f"- 内容：{_shorten(chunk.text, 520)}",
            ])
        )
    return "\n\n".join(evidence_blocks)


def build_structured_fortune_prompt(
    question: str,
    aspect: str,
    sign_id: str,
    chunks: list[FortuneChunk],
    style: str = "modern",
    question_analysis: dict[str, Any] | None = None,
) -> tuple[str, str]:
    aspect_label = ASPECT_ZH.get(aspect, aspect)
    style_label = STYLE_ZH.get(style, STYLE_ZH["modern"])
    style_instruction = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["modern"])
    qa = question_analysis or {}
    evidence_text = _build_evidence_text(chunks)

    user_prompt = f"""
用户问题：{question}
问题方向：{aspect_label}
抽到签号：{sign_id}
用户情绪识别：{qa.get('emotion', '未识别')}
问题类型识别：{qa.get('question_type', '建议型')}
问题关键词：{', '.join(qa.get('keywords', [])) or '无'}
用户选择的解签风格：{style_label}
风格要求：{style_instruction}

签文资料：
{evidence_text}

请严格输出下面 JSON 结构，所有字段都必须填写，不能留空，不能只写标题：
{{
  "plain_summary": "用2-3句话给出最重要的白话总结，必须直接说清楚这支签的大意。",
  "traditional_explanation": "用2-3句话解释签诗/典故在传统语境下的含义。",
  "answer_to_question": "用3-5句话直接回应用户问题，必须结合问题方向、情绪和签文资料。",
  "action_suggestions": [
    "第一条现实可执行建议",
    "第二条现实可执行建议",
    "第三条现实可执行建议"
  ],
  "risk_warning": "用1-2句话说明需要谨慎的地方，避免让用户误以为这是现实预测。",
  "comfort_message": "用1-2句话给出情绪安抚或积极提醒。",
  "fortune_attitude": "用一句短语概括本签态度，例如：宜守不宜躁 / 先稳后进 / 谨慎等待 / 主动求变",
  "short_conclusion": "用一句话概括结论，适合显示在卡片顶部"
}}

输出要求：
1. 只输出 JSON 对象，不要写 ```json。
2. 不要输出“以下是”等前置语。
3. action_suggestions 必须是数组，恰好 3 条。
4. 内容要符合用户选择的解签风格：{style_label}。
5. 不要使用绝对化预测词，如“一定会”“必然会”“保证”。
""".strip()

    return STRUCTURED_SYSTEM_PROMPT, user_prompt


# Backward-compatible wrapper. Some older code may still import build_fortune_prompt.
def build_fortune_prompt(
    question: str,
    aspect: str,
    sign_id: str,
    chunks: list[FortuneChunk],
) -> tuple[str, str]:
    return build_structured_fortune_prompt(
        question=question,
        aspect=aspect,
        sign_id=sign_id,
        chunks=chunks,
        style="modern",
        question_analysis=None,
    )
