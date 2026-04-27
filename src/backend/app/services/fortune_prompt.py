from __future__ import annotations

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


SYSTEM_PROMPT = """
你是“灵签智解”系统的中文解签助手。
你只能依据给定签文资料回答，不要编造签号、签诗或典故。
这是传统文化娱乐和自我反思参考，不能替代医学、法律或投资建议。
必须完整输出所有栏目，不要只写第一段。
""".strip()


def _shorten(text: str, limit: int = 240) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def build_fortune_prompt(
    question: str,
    aspect: str,
    sign_id: str,
    chunks: list[FortuneChunk],
) -> tuple[str, str]:
    aspect_label = ASPECT_ZH.get(aspect, aspect)

    evidence_blocks = []
    for idx, chunk in enumerate(chunks[:3], start=1):
        meta = chunk.metadata
        evidence_blocks.append(
            f"资料{idx}：签号{meta.get('sign_id')}，吉凶{meta.get('level')}，典故{meta.get('story_title')}，方向{meta.get('aspect_label', meta.get('aspect'))}。内容：{_shorten(chunk.text, 240)}"
        )

    evidence_text = "\n".join(evidence_blocks)

    user_prompt = f"""
用户问题：{question}
问题方向：{aspect_label}
抽到签号：{sign_id}

签文资料：
{evidence_text}

请严格按下面 5 个栏目完整回答，每个栏目 1-3 句话，不要中途停止：

【抽签结果】
写签号、吉凶、典故和一句核心含义。

【白话解释】
解释签诗/典故的大意。

【针对问题的解读】
结合“{aspect_label}”说明对用户问题的启示。

【行动建议】
用 1、2、3 列出三条现实建议。

【提醒】
说明仅供传统文化娱乐和自我反思参考。
""".strip()

    return SYSTEM_PROMPT, user_prompt