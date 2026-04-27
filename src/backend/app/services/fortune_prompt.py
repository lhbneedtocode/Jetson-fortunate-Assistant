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
    """
    A simple rule-based classifier.
    Later you can replace it with BERT / MacBERT classifier for report scoring.
    """
    q = question.lower()

    keyword_map = {
        "career": ["工作", "事业", "求职", "实习", "面试", "offer", "升职", "跳槽", "转工", "就业"],
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

    return f"""
签号：{sign_id}
用户问题方向：{aspect_label}
用户问题：{question}
请检索该签在这个问题方向下的签诗、典故、综合解释、方向解释和行动建议。
""".strip()


SYSTEM_PROMPT = """
你是“灵签智解”系统中的传统签文解释助手。

你的任务：
把黄大仙灵签的签诗、典故、释义和分项解释，转化成现代中文解释。

必须遵守：
1. 只能基于提供的签文资料和检索证据解读，不要编造新的签号、签诗、典故。
2. 本系统定位为传统文化文本解释、文化娱乐和自我反思参考，不要声称可以准确预测未来。
3. 遇到健康、法律、投资等高风险问题时，只能给一般性提醒，不能替代医生、律师或专业投资建议。
4. 不输出隐藏推理过程。
5. 语气温和、清晰、具体，避免恐吓式表达。
""".strip()


def build_fortune_prompt(
    question: str,
    aspect: str,
    sign_id: str,
    chunks: list[FortuneChunk],
) -> tuple[str, str]:
    aspect_label = ASPECT_ZH.get(aspect, aspect)

    evidence_blocks = []

    for idx, chunk in enumerate(chunks, start=1):
        meta = chunk.metadata

        evidence_blocks.append(
            f"""
[资料 {idx}]
签号：{meta.get("sign_id")}
吉凶等级：{meta.get("level")}
典故标题：{meta.get("story_title")}
资料类型：{meta.get("chunk_type")}
问题方向：{meta.get("aspect_label", meta.get("aspect"))}
内容：
{chunk.text}
""".strip()
        )

    evidence_text = "\n\n".join(evidence_blocks)

    user_prompt = f"""
用户问题：
{question}

系统判断的问题方向：
{aspect_label}

抽到的签号：
{sign_id}

检索到的签文资料：
{evidence_text}

请按以下结构输出：

【抽签结果】
说明签号、吉凶等级、典故标题和核心含义。

【签文白话解释】
用现代中文解释签诗和典故表达的意思。

【针对用户问题的解读】
结合用户的问题方向“{aspect_label}”解释，不要泛泛而谈。

【行动建议】
给出 3 条现实中可以执行的建议。

【提醒】
说明结果仅供传统文化娱乐和自我反思参考。
""".strip()

    return SYSTEM_PROMPT, user_prompt