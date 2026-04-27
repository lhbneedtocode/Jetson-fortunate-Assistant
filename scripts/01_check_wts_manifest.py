from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MANIFEST_PATH = ROOT / "data" / "raw" / "fortune" / "wong_tai_sin_source_manifest.jsonl"
OUT_CSV = ROOT / "data" / "processed" / "fortune" / "wts_manifest_checked.csv"

REQUIRED_FIELDS = [
    "oracle_system",
    "sign_id",
    "official_taonet_url_zh_tw",
    "fallback_91chouqian_url",
    "recommended_use",
    "extraction_status",
]


def load_jsonl(path: Path) -> list[dict]:
    rows = []

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Line {line_no} is not valid JSON: {exc}") from exc

            rows.append(item)

    return rows


def main() -> None:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest file not found: {MANIFEST_PATH}")

    rows = load_jsonl(MANIFEST_PATH)

    print(f"Loaded rows: {len(rows)}")

    if len(rows) != 100:
        print(f"[WARNING] Expected 100 rows, but got {len(rows)}")

    sign_ids = []

    for idx, row in enumerate(rows, start=1):
        for field in REQUIRED_FIELDS:
            if field not in row:
                raise ValueError(f"Row {idx} missing field: {field}")

        sign_id = str(row["sign_id"])
        sign_ids.append(sign_id)

        if not sign_id.isdigit() or len(sign_id) != 3:
            raise ValueError(f"Row {idx} has invalid sign_id: {sign_id}")

        if row["oracle_system"] != "wong_tai_sin_100":
            raise ValueError(f"Row {idx} has unexpected oracle_system: {row['oracle_system']}")

        if not str(row["official_taonet_url_zh_tw"]).startswith("https://"):
            raise ValueError(f"Row {idx} official URL is invalid")

        if not str(row["fallback_91chouqian_url"]).startswith("https://"):
            raise ValueError(f"Row {idx} fallback URL is invalid")

    expected_ids = [f"{i:03d}" for i in range(1, 101)]

    missing = sorted(set(expected_ids) - set(sign_ids))
    duplicated = sorted({x for x in sign_ids if sign_ids.count(x) > 1})

    if missing:
        print("[WARNING] Missing sign ids:", missing)

    if duplicated:
        print("[WARNING] Duplicated sign ids:", duplicated)

    if not missing and not duplicated and len(rows) == 100:
        print("[OK] Manifest contains 100 unique sign IDs from 001 to 100.")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "oracle_system",
                "sign_id",
                "official_taonet_url_zh_tw",
                "fallback_91chouqian_url",
                "extraction_status",
            ],
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    "oracle_system": row["oracle_system"],
                    "sign_id": row["sign_id"],
                    "official_taonet_url_zh_tw": row["official_taonet_url_zh_tw"],
                    "fallback_91chouqian_url": row["fallback_91chouqian_url"],
                    "extraction_status": row["extraction_status"],
                }
            )

    print(f"Saved checked CSV to: {OUT_CSV}")


if __name__ == "__main__":
    main()