from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]

HTML_DIR = ROOT / "data" / "raw_private" / "fortune" / "pages_91"
OUT_JSONL = ROOT / "data" / "processed" / "fortune" / "signs_wong_tai_sin_100.jsonl"
OUT_REPORT = ROOT / "data" / "processed" / "fortune" / "parse_report.json"


ASPECT_ALIASES = {
    "流年": "year",
    "事业": "career",
    "谋事": "career",
    "工作": "career",
    "求职": "career",
    "交易": "business",
    "生意": "business",
    "财富": "wealth",
    "财运": "wealth",
    "自身": "self",
    "家庭": "family",
    "家宅": "family",
    "姻缘": "love",
    "感情": "love",
    "婚姻": "love",
    "移居": "move",
    "名誉": "reputation",
    "健康": "health",
    "病情": "health",
    "友谊": "friendship",
    "学业": "study",
    "考试": "study",
    "子女": "children",
    "六甲": "children",
    "出行": "travel",
    "行人": "travel",
    "遗失": "lost_item",
    "失物": "lost_item",
    "天时": "weather",
    "风水": "fengshui",
}


LEVEL_PATTERNS = [
    "上上",
    "上吉",
    "中吉",
    "中平",
    "下下",
    "下吉",
    "大吉",
    "吉",
    "凶",
]


def clean_text(text: str) -> str:
    """Normalize whitespace inside one text segment."""
    return re.sub(r"\s+", " ", text.strip())


def clean_lines(text: str) -> list[str]:
    """Split text into non-empty normalized lines."""
    return [clean_text(line) for line in text.splitlines() if clean_text(line)]


def normalize_section_markers(text: str) -> str:
    """
    Normalize website section markers.

    The 91chouqian pages often use:
    【签词】 【典故】 【释义】 【签解】

    We normalize them to:
    〖签词〗 〖典故〗 〖释义〗 〖签解〗
    """
    replacements = {
        "【签词】": "〖签词〗",
        "【签诗】": "〖签词〗",
        "【签文】": "〖签词〗",
        "【典故】": "〖典故〗",
        "【释义】": "〖释义〗",
        "【签解】": "〖签解〗",
        "〔签词〕": "〖签词〗",
        "〔签诗〕": "〖签词〗",
        "〔签文〕": "〖签词〗",
        "〔典故〕": "〖典故〗",
        "〔释义〕": "〖释义〗",
        "〔签解〕": "〖签解〗",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def normalize_sign_id(value: int | str) -> str:
    return f"{int(value):03d}"


def normalize_level(level: str) -> str:
    level = clean_text(level)
    level = level.replace("签", "")

    for pattern in LEVEL_PATTERNS:
        if pattern in level:
            return pattern

    return level


def normalize_story_title(story_title: str) -> str:
    story_title = clean_text(story_title)

    # 去掉网页标题后缀
    story_title = re.sub(r"\s*-\s*91抽签网.*$", "", story_title)
    story_title = re.sub(r"\s*_.*$", "", story_title)

    # 防止把后面正文吃进去
    story_title = re.split(r"〖|【|签词|签诗|签文|典故|释义|签解", story_title)[0]

    return clean_text(story_title)


def section_between(text: str, start_marker: str, end_markers: list[str]) -> str:
    """
    Extract text between one start marker and the earliest following end marker.
    """
    start = text.find(start_marker)

    if start == -1:
        return ""

    start += len(start_marker)
    end = len(text)

    for marker in end_markers:
        idx = text.find(marker, start)
        if idx != -1:
            end = min(end, idx)

    return text[start:end].strip()


def section_between_any(text: str, start_markers: list[str], end_markers: list[str]) -> str:
    """
    Extract section with multiple possible start markers.
    """
    best_start = -1
    best_marker = ""

    for marker in start_markers:
        idx = text.find(marker)
        if idx != -1 and (best_start == -1 or idx < best_start):
            best_start = idx
            best_marker = marker

    if best_start == -1:
        return ""

    start = best_start + len(best_marker)
    end = len(text)

    for marker in end_markers:
        idx = text.find(marker, start)
        if idx != -1:
            end = min(end, idx)

    return text[start:end].strip()


def extract_level_and_story(sign_id: int, h1_text: str, full_text: str) -> tuple[str, str]:
    """
    Extract level and story title from h1 or first part of page text.

    Example:
    黄大仙灵签 第23签：中平 卢生梦 - 91抽签网
    """
    candidates = [
        h1_text,
        full_text[:800],
    ]

    patterns = [
        rf"黄大仙灵签\s*第\s*{sign_id}\s*签[：:]\s*(?P<level>上上|上吉|中吉|中平|下下|下吉|大吉|吉|凶|中平签)\s*(?P<story>.+)",
        rf"第\s*{sign_id}\s*签[：:]\s*(?P<level>上上|上吉|中吉|中平|下下|下吉|大吉|吉|凶|中平签)\s*(?P<story>.+)",
        rf"第\s*{sign_id}\s*签\s*(?P<level>上上|上吉|中吉|中平|下下|下吉|大吉|吉|凶|中平签)\s*(?P<story>.+)",
        rf"第\s*[一二三四五六七八九十百卅廿〇零]+签[：:]\s*(?P<level>上上|上吉|中吉|中平|下下|下吉|大吉|吉|凶|中平签)\s*(?P<story>.+)",
    ]

    for text in candidates:
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                level = normalize_level(match.group("level"))
                story_title = normalize_story_title(match.group("story"))
                return level, story_title

    return "", ""


def extract_poem(full_text: str) -> list[str]:
    """
    Extract sign poem / sign text.

    Main expected structure:
    〖签词〗
    ...
    〖典故〗
    """
    block = section_between_any(
        full_text,
        start_markers=[
            "〖签词〗",
            "〖签诗〗",
            "〖签文〗",
            "黄大仙灵签签文",
            "黄大仙灵签签诗",
            "黄大仙灵签诗",
        ],
        end_markers=[
            "〖典故〗",
            "〖释义〗",
            "〖签解〗",
            "黄大仙灵签典故",
            "黄大仙灵签释义",
            "黄大仙灵签解签",
        ],
    )

    lines = clean_lines(block)

    cleaned: list[str] = []

    for line in lines:
        # 去掉栏目标题或网页噪声
        if line in {
            "签词",
            "签诗",
            "签文",
            "黄大仙灵签签文",
            "黄大仙灵签签诗",
            "黄大仙灵签诗",
        }:
            continue

        if line.startswith("黄大仙灵签") and "第" in line and "签" in line:
            continue

        if line.startswith("上一篇") or line.startswith("下一篇"):
            continue

        if line.startswith("91抽签网"):
            continue

        if len(line) <= 1:
            continue

        cleaned.append(line)

    # 签词通常不长，避免误吃后面解释
    return cleaned[:8]


def extract_story(full_text: str) -> str:
    block = section_between(
        full_text,
        "〖典故〗",
        ["〖释义〗", "〖签解〗", "热门推荐", "上一篇", "下一篇"],
    )

    lines = clean_lines(block)
    cleaned: list[str] = []

    for line in lines:
        if line in {"典故", "黄大仙灵签典故"}:
            continue

        if line.startswith("黄大仙灵签") and "第" in line and "签" in line:
            continue

        if line.startswith("上一篇") or line.startswith("下一篇"):
            continue

        cleaned.append(line)

    return clean_text(" ".join(cleaned))


def parse_aspect_lines(block: str) -> tuple[dict[str, str], list[str]]:
    """
    Parse lines like:
    事业：xxxx
    财富：xxxx
    姻缘：xxxx
    """
    aspects: dict[str, list[str]] = {}
    remaining: list[str] = []

    for line in clean_lines(block):
        # 支持：事业：xxxx 或 事业: xxxx
        match = re.match(r"^([^：:]{1,12})[：:]\s*(.+)$", line)

        if not match:
            remaining.append(line)
            continue

        raw_key = clean_text(match.group(1))
        value = clean_text(match.group(2))

        aspect = ASPECT_ALIASES.get(raw_key)

        if aspect:
            aspects.setdefault(aspect, []).append(value)
        else:
            remaining.append(line)

    merged = {key: " ".join(values) for key, values in aspects.items()}
    return merged, remaining


def merge_aspects(*items: dict[str, str]) -> dict[str, str]:
    merged: dict[str, list[str]] = {}

    for item in items:
        for key, value in item.items():
            if value:
                merged.setdefault(key, []).append(value)

    return {key: " ".join(values) for key, values in merged.items()}


def extract_meaning_block(full_text: str) -> str:
    return section_between(
        full_text,
        "〖释义〗",
        ["〖签解〗", "热门推荐", "上一篇", "下一篇"],
    )


def extract_explanation_block(full_text: str) -> str:
    return section_between(
        full_text,
        "〖签解〗",
        ["##### 热门推荐", "热门推荐", "上一篇", "下一篇", "相关阅读"],
    )


def infer_keywords(level: str, story_title: str, overall: str, aspects: dict[str, str]) -> list[str]:
    text = " ".join([level, story_title, overall, " ".join(aspects.values())])

    candidates = [
        "贵人",
        "谨慎",
        "等待",
        "转机",
        "努力",
        "坚持",
        "守成",
        "进取",
        "姻缘",
        "财富",
        "健康",
        "事业",
        "学业",
        "家庭",
        "风险",
        "机会",
        "沟通",
        "保守",
        "顺利",
        "阻滞",
        "平稳",
        "变动",
        "小心",
        "求职",
        "考试",
        "投资",
        "疾病",
        "平安",
        "成功",
        "失败",
        "虚幻",
        "务实",
    ]

    keywords = [kw for kw in candidates if kw in text]

    # 去重，保持顺序
    seen = set()
    unique_keywords = []

    for kw in keywords:
        if kw not in seen:
            unique_keywords.append(kw)
            seen.add(kw)

    return unique_keywords[:8]


def parse_html_file(path: Path) -> dict[str, object]:
    sign_id = int(path.stem)

    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    # h1 用于提取签级和典故标题
    h1 = soup.find("h1")
    h1_text = clean_text(h1.get_text(" ")) if h1 else ""

    # 保留换行结构，便于按栏目切分
    full_text = "\n".join(clean_lines(soup.get_text("\n")))
    full_text = normalize_section_markers(full_text)

    level, story_title = extract_level_and_story(sign_id, h1_text, full_text)

    poem_lines = extract_poem(full_text)
    story = extract_story(full_text)

    meaning_block = extract_meaning_block(full_text)
    explanation_block = extract_explanation_block(full_text)

    meaning_aspects, meaning_remaining = parse_aspect_lines(meaning_block)
    explanation_aspects, explanation_remaining = parse_aspect_lines(explanation_block)

    aspects = merge_aspects(meaning_aspects, explanation_aspects)

    overall_parts: list[str] = []

    # 典故也可以作为综合解释的一部分，但不要替代 story 字段
    if story:
        overall_parts.append(story)

    if meaning_remaining:
        overall_parts.append(" ".join(meaning_remaining))

    if explanation_remaining:
        # 防止太长，只取前面几句作为综合解释
        overall_parts.append(" ".join(explanation_remaining[:6]))

    overall_interpretation = clean_text(" ".join(overall_parts))

    normalized_id = normalize_sign_id(sign_id)

    item = {
        "oracle_system": "wong_tai_sin_100",
        "sign_id": normalized_id,
        "sign_key": f"wong_tai_sin_100_{normalized_id}",
        "title": f"第{sign_id}签",
        "level": level,
        "story_title": story_title,
        "poem": poem_lines,
        "story": story,
        "overall_interpretation": overall_interpretation,
        "aspects": aspects,
        "keywords": infer_keywords(level, story_title, overall_interpretation, aspects),
        "source_urls": [
            f"https://91chouqian.com/huangdaxianlingqian/{sign_id}.html",
            f"https://taonet.siksikyuen.org.hk/StickEnquiry/{sign_id}/zh-TW",
        ],
    }

    return item


def main() -> None:
    if not HTML_DIR.exists():
        raise FileNotFoundError(f"HTML directory not found: {HTML_DIR}")

    html_files = sorted(HTML_DIR.glob("*.html"))

    if len(html_files) != 100:
        print(f"[WARNING] Expected 100 HTML files, got {len(html_files)}")

    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    items: list[dict[str, object]] = []
    warnings: list[str] = []

    for path in html_files:
        item = parse_html_file(path)
        items.append(item)

        sign_id = str(item["sign_id"])

        if not item["level"]:
            warnings.append(f"{sign_id}: missing level")

        if not item["story_title"]:
            warnings.append(f"{sign_id}: missing story_title")

        if not item["poem"]:
            warnings.append(f"{sign_id}: missing poem")

        if not item["story"]:
            warnings.append(f"{sign_id}: missing story")

        if not item["overall_interpretation"]:
            warnings.append(f"{sign_id}: missing overall_interpretation")

        if not item["aspects"]:
            warnings.append(f"{sign_id}: missing aspects")

    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    report = {
        "html_files": len(html_files),
        "parsed_items": len(items),
        "output_jsonl": str(OUT_JSONL),
        "warnings_count": len(warnings),
        "warnings": warnings[:200],
    }

    OUT_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 80)
    print(f"Parsed items: {len(items)}")
    print(f"Saved JSONL to: {OUT_JSONL}")
    print(f"Saved report to: {OUT_REPORT}")
    print(f"Warnings: {len(warnings)}")

    if warnings:
        print("First warnings:")
        for warning in warnings[:30]:
            print(" -", warning)

    print("=" * 80)
    print("Example item 001:")
    print(json.dumps(items[0], ensure_ascii=False, indent=2)[:2000])

    item_023 = next((item for item in items if item.get("sign_id") == "023"), None)
    if item_023:
        print("=" * 80)
        print("Example item 023:")
        print(json.dumps(item_023, ensure_ascii=False, indent=2)[:2000])


if __name__ == "__main__":
    main()