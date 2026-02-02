"""
下载并固化 Nasdaq universe 快照
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
UNIVERSE_DIR = BASE_DIR / "data" / "universe" / "nasdaq"
SNAPSHOT_URL = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt"
SNAPSHOT_PATH = UNIVERSE_DIR / "nasdaqlisted_snapshot.txt"
UNIVERSE_PATH = UNIVERSE_DIR / "universe.csv"


def _parse_universe(lines: List[str]) -> pd.DataFrame:
    records = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("File Creation Time"):
            continue
        if line.startswith("Symbol|"):
            continue
        if line.startswith("|" * 3):
            continue
        if line.startswith("Market Category"):
            continue
        if "|" not in line:
            continue
        parts = line.split("|")
        symbol = parts[0].strip()
        test_issue = parts[3].strip() if len(parts) > 3 else ""
        if not symbol or test_issue.upper() == "Y":
            continue
        records.append({"ticker": symbol})
    df = pd.DataFrame(records).drop_duplicates().sort_values("ticker")
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="下载 Nasdaq universe 快照")
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=SNAPSHOT_PATH,
        help="nasdaqlisted.txt 快照路径",
    )
    args = parser.parse_args()

    snapshot_path = args.snapshot
    if not snapshot_path.exists():
        raise FileNotFoundError(f"缺少快照文件: {snapshot_path}")

    lines = snapshot_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    df = _parse_universe(lines)

    UNIVERSE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(UNIVERSE_PATH, index=False)
    print(f"✓ universe 已生成: {UNIVERSE_PATH} (n={len(df)})")


if __name__ == "__main__":
    main()
