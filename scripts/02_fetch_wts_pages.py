from __future__ import annotations

import json
import time
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]

MANIFEST_PATH = ROOT / "data" / "raw" / "fortune" / "wong_tai_sin_source_manifest.jsonl"

# 原始网页 HTML 放这里，不建议提交到 GitHub
OUT_DIR = ROOT / "data" / "raw_private" / "fortune" / "pages_91"

LOG_PATH = ROOT / "data" / "raw_private" / "fortune" / "fetch_log.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    rows = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            rows.append(json.loads(line))

    return rows


def fetch_html(url: str) -> tuple[int, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    # 避免中文乱码
    response.encoding = response.apparent_encoding or "utf-8"

    return response.status_code, response.text


def main() -> None:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest file not found: {MANIFEST_PATH}")

    rows = load_jsonl(MANIFEST_PATH)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    success_count = 0
    error_count = 0

    with LOG_PATH.open("w", encoding="utf-8") as log_file:
        for row in rows:
            sign_id = row["sign_id"]

            # 这里先使用 91 抽签网作为网页采集源
            url = row["fallback_91chouqian_url"]

            out_path = OUT_DIR / f"{sign_id}.html"

            log_item = {
                "sign_id": sign_id,
                "url": url,
                "output_path": str(out_path),
                "status": "pending",
            }

            # 如果已经下载过，跳过，避免重复请求
            if out_path.exists() and out_path.stat().st_size > 1000:
                log_item.update(
                    {
                        "status": "skipped_existing",
                        "html_size": out_path.stat().st_size,
                    }
                )
                success_count += 1
                print(f"[SKIP] {sign_id} already exists: {out_path.name}")
                log_file.write(json.dumps(log_item, ensure_ascii=False) + "\n")
                continue

            try:
                status_code, html = fetch_html(url)

                out_path.write_text(html, encoding="utf-8")

                log_item.update(
                    {
                        "status": "success",
                        "status_code": status_code,
                        "html_size": len(html),
                    }
                )

                success_count += 1
                print(f"[OK] {sign_id} -> {out_path.name}, size={len(html)}")

            except Exception as exc:
                log_item.update(
                    {
                        "status": "error",
                        "error": str(exc),
                    }
                )

                error_count += 1
                print(f"[ERROR] {sign_id}: {exc}")

            log_file.write(json.dumps(log_item, ensure_ascii=False) + "\n")

            # 不要请求太快
            time.sleep(0.8)

    print("=" * 80)
    print(f"Finished. Success/skipped: {success_count}, Errors: {error_count}")
    print(f"HTML pages saved to: {OUT_DIR}")
    print(f"Fetch log saved to: {LOG_PATH}")


if __name__ == "__main__":
    main()