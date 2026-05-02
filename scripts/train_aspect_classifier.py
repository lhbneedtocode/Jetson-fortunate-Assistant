#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Train a lightweight Question Aspect Classifier for QianWu.

Model:
  Chinese character n-gram TF-IDF + Logistic Regression

Outputs:
  models/aspect_classifier/aspect_classifier.joblib
  outputs/aspect_classifier/metrics.json
  outputs/aspect_classifier/class_distribution.png
  outputs/aspect_classifier/confusion_matrix.png
  data/aspect_classifier/training_data.csv
"""

from __future__ import annotations

import csv
import json
import random
import re
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


ASPECT_LABELS = {
    "career": "事业/求职",
    "study": "学业/考试",
    "relationship": "感情/人际",
    "wealth": "财运/投资",
    "health": "健康/状态",
    "general": "综合/其他",
}


def clean_text(text: str) -> str:
    text = str(text or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[，。！？、；：,.!?;:\[\]（）()《》\"'“”‘’]", " ", text)
    return text.strip()


def build_template_dataset() -> List[Tuple[str, str]]:
    """Generate a compact but useful labeled dataset from templates.

    You can later extend data/aspect_classifier/training_data.csv with real user questions.
    """
    data: List[Tuple[str, str]] = []

    templates: Dict[str, List[str]] = {
        "career": [
            "我这个月能找到实习吗",
            "最近工作运势如何",
            "我应该继续现在的工作方向吗",
            "面试会顺利吗",
            "找工作有没有机会",
            "我适合跳槽吗",
            "这个岗位值得投递吗",
            "实习转正机会大吗",
            "最近项目推进不顺怎么办",
            "我和领导沟通会顺利吗",
            "职业发展应该怎么选择",
            "现在适合换方向吗",
            "我的求职状态怎么样",
            "这份 offer 要不要接受",
            "我能不能拿到实习 offer",
            "最近适合主动联系 HR 吗",
            "科研项目和实习应该怎么取舍",
            "我现在的工作会有突破吗",
            "创业项目是否适合继续",
            "当前团队合作会不会顺利",
        ],
        "study": [
            "期末考试能不能过",
            "最近学习状态如何",
            "论文能不能顺利完成",
            "这个课程项目能拿高分吗",
            "考研复习是否顺利",
            "我适合继续读博吗",
            "这门课怎么准备比较好",
            "我的学习计划要不要调整",
            "毕业论文能否按时完成",
            "最近科研进展是否会变好",
            "考试前应该怎么复习",
            "导师会认可我的研究方向吗",
            "这个实验能不能成功",
            "我需要换研究题目吗",
            "答辩能不能顺利通过",
            "我最近写报告是否顺利",
            "论文投稿有希望吗",
            "这个模型复现能成功吗",
            "课程作业会不会出问题",
            "学习压力很大怎么办",
        ],
        "relationship": [
            "我和他还有机会吗",
            "最近感情运势如何",
            "对方是否还在意我",
            "我该不该主动联系对方",
            "这段关系值得继续吗",
            "朋友之间最近会不会有矛盾",
            "人际关系怎么改善",
            "我和同学合作会顺利吗",
            "最近适合表白吗",
            "这段感情会有结果吗",
            "我应该放下这段关系吗",
            "和家人沟通会不会顺利",
            "最近容易和别人发生冲突吗",
            "我该怎么处理暧昧关系",
            "团队关系是否稳定",
            "我的桃花运怎么样",
            "我们之间的误会能解开吗",
            "这段关系是不是该冷静一下",
            "和室友相处会不会好转",
            "我在人际关系中需要注意什么",
        ],
        "wealth": [
            "最近财运如何",
            "适合投资吗",
            "这个月会不会破财",
            "股票基金要不要买",
            "兼职收入会增加吗",
            "最近能不能存下钱",
            "这笔钱能不能收回来",
            "现在适合做副业吗",
            "这个项目能赚钱吗",
            "我适合创业投资吗",
            "最近消费要注意什么",
            "会不会有意外支出",
            "财务压力能缓解吗",
            "奖学金有没有希望",
            "是否适合购买设备",
            "这次合作收益如何",
            "能不能拿到奖金",
            "收入会不会增长",
            "资金周转是否顺利",
            "理财计划要不要调整",
        ],
        "health": [
            "最近身体状态如何",
            "最近总是很累怎么办",
            "压力大睡不好会改善吗",
            "健康方面需要注意什么",
            "最近情绪很焦虑怎么办",
            "身体恢复会顺利吗",
            "运动计划是否适合继续",
            "最近精神状态不好",
            "会不会因为熬夜影响健康",
            "我需要休息一段时间吗",
            "焦虑状态能不能缓解",
            "最近适合减肥吗",
            "作息要不要调整",
            "身体不舒服需要注意什么",
            "心理压力很大怎么办",
            "最近精力不足怎么改善",
            "适不适合高强度工作",
            "需要减少熬夜吗",
            "健康运势如何",
            "恢复状态怎么样",
        ],
        "general": [
            "今天整体运势如何",
            "最近会不会顺利",
            "这个选择应该怎么做",
            "我现在需要注意什么",
            "未来一段时间会变好吗",
            "这件事有没有转机",
            "我该坚持还是放弃",
            "最近整体状态如何",
            "这件事能不能成功",
            "目前应该主动还是等待",
            "我该如何面对这个问题",
            "最近有什么需要避开的事",
            "这件事有没有贵人帮助",
            "我应该保守一点还是积极一点",
            "现在时机成熟了吗",
            "这段时间会有好消息吗",
            "我应该如何调整方向",
            "接下来一个月运势如何",
            "现在做决定合适吗",
            "我该怎么让事情变顺",
        ],
    }

    prefixes = ["", "请问", "想问一下", "帮我看看", "我想知道", "最近"]
    suffixes = ["", "谢谢", "麻烦分析一下", "给我一点建议", "会有好结果吗", "应该怎么办"]

    for aspect, questions in templates.items():
        for q in questions:
            data.append((q, aspect))
            for prefix in random.sample(prefixes, k=2):
                for suffix in random.sample(suffixes, k=2):
                    text = f"{prefix}{q}{suffix}".strip()
                    data.append((text, aspect))

    # Deduplicate
    seen = set()
    unique = []
    for text, label in data:
        key = (clean_text(text), label)
        if key not in seen:
            seen.add(key)
            unique.append((text, label))
    return unique


def load_or_create_dataset(csv_path: Path) -> List[Tuple[str, str]]:
    if csv_path.exists():
        rows = []
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                text = (row.get("text") or row.get("question") or "").strip()
                label = (row.get("label") or row.get("aspect") or "").strip()
                if text and label in ASPECT_LABELS:
                    rows.append((text, label))
        if rows:
            return rows

    rows = build_template_dataset()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "label_name"])
        writer.writeheader()
        for text, label in rows:
            writer.writerow({"text": text, "label": label, "label_name": ASPECT_LABELS[label]})
    return rows


def plot_class_distribution(labels: List[str], output_path: Path) -> None:
    counts = {label: labels.count(label) for label in ASPECT_LABELS}
    names = [ASPECT_LABELS[k] for k in counts.keys()]
    values = list(counts.values())

    plt.figure(figsize=(9, 4.8))
    plt.bar(names, values)
    plt.title("Question Aspect Dataset Distribution")
    plt.xlabel("Aspect")
    plt.ylabel("Number of samples")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def plot_confusion_matrix(cm: np.ndarray, output_path: Path) -> None:
    labels = list(ASPECT_LABELS.keys())
    names = [ASPECT_LABELS[k] for k in labels]

    plt.figure(figsize=(7.6, 6.8))
    plt.imshow(cm, interpolation="nearest")
    plt.title("Question Aspect Classifier Confusion Matrix")
    plt.xticks(range(len(names)), names, rotation=35, ha="right")
    plt.yticks(range(len(names)), names)
    plt.xlabel("Predicted label")
    plt.ylabel("True label")

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, str(cm[i, j]), ha="center", va="center")

    plt.colorbar(fraction=0.046, pad=0.04)
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def main() -> None:
    random.seed(42)

    project_root = Path(__file__).resolve().parents[1]
    data_path = project_root / "data" / "aspect_classifier" / "training_data.csv"
    model_dir = project_root / "models" / "aspect_classifier"
    output_dir = project_root / "outputs" / "aspect_classifier"
    model_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = load_or_create_dataset(data_path)
    texts = [clean_text(t) for t, _ in rows]
    labels = [label for _, label in rows]

    X_train, X_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=0.22,
        random_state=42,
        stratify=labels,
    )

    clf = Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="char",
                    ngram_range=(1, 4),
                    min_df=1,
                    max_df=0.95,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1200,
                    class_weight="balanced",
                    C=4.0,
                    solver="lbfgs",
                    random_state=42,
                ),
            ),
        ]
    )

    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    labels_order = list(ASPECT_LABELS.keys())
    report = classification_report(
        y_test,
        y_pred,
        labels=labels_order,
        target_names=[ASPECT_LABELS[k] for k in labels_order],
        output_dict=True,
        zero_division=0,
    )
    cm = confusion_matrix(y_test, y_pred, labels=labels_order)

    metrics = {
        "model": "TF-IDF character n-gram + Logistic Regression",
        "num_samples": len(rows),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "accuracy": accuracy_score(y_test, y_pred),
        "macro_f1": f1_score(y_test, y_pred, average="macro"),
        "labels": ASPECT_LABELS,
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
    }

    model_payload = {
        "pipeline": clf,
        "labels": ASPECT_LABELS,
        "version": "qianwu_aspect_classifier_v1",
    }

    joblib.dump(model_payload, model_dir / "aspect_classifier.joblib")

    with (output_dir / "metrics.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    plot_class_distribution(labels, output_dir / "class_distribution.png")
    plot_confusion_matrix(cm, output_dir / "confusion_matrix.png")

    print("Training finished.")
    print(f"Dataset: {data_path}")
    print(f"Model:   {model_dir / 'aspect_classifier.joblib'}")
    print(f"Metrics: {output_dir / 'metrics.json'}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Macro-F1: {metrics['macro_f1']:.4f}")


if __name__ == "__main__":
    main()
