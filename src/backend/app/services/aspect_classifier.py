from __future__ import annotations

from pathlib import Path
from typing import Any
import joblib


ASPECT_LABELS = {
    "career": "事业/求职",
    "study": "学业/考试",
    "relationship": "感情/人际",
    "wealth": "财运/投资",
    "health": "健康/状态",
    "general": "综合",
    "love": "感情/人际",
}


ASPECT_ALIAS = {
    "love": "relationship",
    "emotion": "relationship",
    "relationship": "relationship",
    "career": "career",
    "job": "career",
    "work": "career",
    "study": "study",
    "exam": "study",
    "wealth": "wealth",
    "money": "wealth",
    "health": "health",
    "general": "general",
}


KEYWORD_RULES = [
    ("relationship", [
        "爱情", "恋爱", "感情", "桃花", "对象", "喜欢", "暗恋", "暧昧",
        "复合", "分手", "前任", "男朋友", "女朋友", "伴侣", "婚姻",
        "结婚", "脱单", "缘分", "关系", "人际", "朋友", "友情",
    ]),
    ("career", [
        "工作", "实习", "求职", "面试", "公司", "岗位", "offer", "转正",
        "加薪", "升职", "职场", "职业", "简历", "老板", "领导", "同事",
        "项目", "创业", "事业",
    ]),
    ("study", [
        "学习", "学业", "考试", "考研", "期末", "成绩", "论文", "课程",
        "作业", "毕业", "复习", "上岸", "录取", "读研", "学校",
    ]),
    ("wealth", [
        "财运", "钱", "赚钱", "收入", "投资", "理财", "股票", "基金",
        "亏损", "消费", "买房", "财富", "奖金", "薪资",
    ]),
    ("health", [
        "健康", "身体", "状态", "生病", "失眠", "焦虑", "压力", "疲惫",
        "休息", "情绪", "抑郁", "不舒服", "恢复", "医院",
    ]),
]


_MODEL = None


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _model_path() -> Path:
    return _project_root() / "models" / "aspect_classifier" / "aspect_classifier.joblib"


def _normalize_aspect(aspect: str | None) -> str:
    key = str(aspect or "general").strip().lower()
    return ASPECT_ALIAS.get(key, key if key in ASPECT_LABELS else "general")


def _label(aspect: str) -> str:
    return ASPECT_LABELS.get(aspect, "综合")


def _load_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    path = _model_path()
    if not path.exists():
        _MODEL = False
        return None

    try:
        _MODEL = joblib.load(path)
        return _MODEL
    except Exception:
        _MODEL = False
        return None


def _keyword_rule(question: str) -> dict[str, Any] | None:
    q = str(question or "").strip()
    if not q:
        return None

    matched = []
    for aspect, words in KEYWORD_RULES:
        hits = [w for w in words if w and w in q]
        if hits:
            matched.append((aspect, hits))

    if not matched:
        return None

    matched.sort(key=lambda x: len(x[1]), reverse=True)
    aspect, hits = matched[0]
    aspect = _normalize_aspect(aspect)

    return {
        "aspect": aspect,
        "label": _label(aspect),
        "confidence": 0.99,
        "source": "keyword_rule",
        "matched_keywords": hits,
        "scores": {aspect: 0.99},
    }


def predict_question_aspect(question: str) -> dict[str, Any]:
    q = str(question or "").strip()

    rule = _keyword_rule(q)
    if rule:
        return rule

    model = _load_model()
    if model is None:
        return {
            "aspect": "general",
            "label": "综合",
            "confidence": 0.0,
            "source": "fallback",
            "matched_keywords": [],
            "scores": {},
        }

    try:
        pred = model.predict([q])[0]
        aspect = _normalize_aspect(pred)

        scores = {}
        confidence = 0.0

        if hasattr(model, "predict_proba"):
            proba = model.predict_proba([q])[0]
            classes = list(getattr(model, "classes_", []))
            for cls, score in zip(classes, proba):
                norm_cls = _normalize_aspect(cls)
                scores[norm_cls] = max(scores.get(norm_cls, 0.0), float(score))
            confidence = float(max(proba)) if len(proba) else 0.0
        else:
            confidence = 1.0
            scores = {aspect: confidence}

        return {
            "aspect": aspect,
            "label": _label(aspect),
            "confidence": confidence,
            "source": "trained_classifier",
            "matched_keywords": [],
            "scores": scores,
        }
    except Exception:
        return {
            "aspect": "general",
            "label": "综合",
            "confidence": 0.0,
            "source": "model_error",
            "matched_keywords": [],
            "scores": {},
        }


def should_auto_use_aspect(aspect: str | None) -> bool:
    if aspect is None:
        return True
    value = str(aspect).strip().lower()
    return value in {"", "auto", "none", "null", "智能识别", "自动识别"}
