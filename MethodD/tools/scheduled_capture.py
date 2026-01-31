#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""定时采集编排脚本：t0 批次采集 + t5 回填 + index 日志"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from capture_snapshots import capture_t0, capture_t5


RUNS_DIR = Path("data/snapshots/runs")
INDEX_PATH = RUNS_DIR / "index.csv"
INDEX_COLUMNS = [
    "run_id",
    "ticker",
    "captured_at_t0_utc",
    "t5_due_date",
    "captured_at_t5_utc",
    "t5_status",
    "note",
    "last_checked_utc",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_runs_dir() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)


def _load_manifest(path: Path) -> Optional[Dict[str, object]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _calc_t5_due_date(t0_iso: str) -> Optional[str]:
    if not t0_iso:
        return None
    t0_date = pd.to_datetime(t0_iso).date().isoformat()
    return pd.bdate_range(t0_date, periods=6)[-1].strftime("%Y-%m-%d")


def _is_t5_done(manifest: Dict[str, object]) -> bool:
    snapshots = manifest.get("snapshots") or {}
    t5_map = snapshots.get("t5")
    if not isinstance(t5_map, dict) or not t5_map:
        return False
    return all(value for value in t5_map.values())


def _load_index() -> pd.DataFrame:
    if not INDEX_PATH.exists():
        return pd.DataFrame(columns=INDEX_COLUMNS)
    df = pd.read_csv(INDEX_PATH)
    for col in INDEX_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    return df[INDEX_COLUMNS]


def _save_index(df: pd.DataFrame) -> None:
    df.to_csv(INDEX_PATH, index=False)


def _upsert_index(df: pd.DataFrame, record: Dict[str, object]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame([record], columns=INDEX_COLUMNS)
    run_id = record.get("run_id")
    if run_id in df["run_id"].values:
        df.loc[df["run_id"] == run_id, INDEX_COLUMNS] = [record.get(col) for col in INDEX_COLUMNS]
        return df
    return pd.concat([df, pd.DataFrame([record], columns=INDEX_COLUMNS)], ignore_index=True)


def _scan_manifests() -> List[Dict[str, object]]:
    manifests = []
    if not RUNS_DIR.exists():
        return manifests
    for run_dir in RUNS_DIR.iterdir():
        manifest_path = run_dir / "manifest.json"
        if not manifest_path.exists():
            continue
        manifest = _load_manifest(manifest_path)
        if not manifest:
            continue
        manifest["run_id"] = manifest.get("run_id") or run_dir.name
        manifests.append(manifest)
    return manifests


def run_t0_capture(tickers: List[str], dry_run: bool) -> List[Dict[str, object]]:
    records = []
    for ticker in tickers:
        if dry_run:
            print(f"[DRY-RUN] t0 capture {ticker}")
            continue
        run_id = capture_t0(ticker)
        manifest_path = RUNS_DIR / run_id / "manifest.json"
        manifest = _load_manifest(manifest_path) or {}
        due_date = _calc_t5_due_date(manifest.get("captured_at_t0_utc", ""))
        record = {
            "run_id": run_id,
            "ticker": manifest.get("ticker", ticker).upper(),
            "captured_at_t0_utc": manifest.get("captured_at_t0_utc"),
            "t5_due_date": due_date,
            "captured_at_t5_utc": manifest.get("captured_at_t5_utc"),
            "t5_status": "pending",
            "note": "",
            "last_checked_utc": _utc_now_iso(),
        }
        records.append(record)
    return records


def run_t5_backfill(dry_run: bool) -> List[Dict[str, object]]:
    records = []
    today = datetime.now().date()
    for manifest in _scan_manifests():
        run_id = manifest.get("run_id")
        t0_iso = manifest.get("captured_at_t0_utc") or ""
        due_date = _calc_t5_due_date(t0_iso)
        if not due_date:
            continue
        due = pd.to_datetime(due_date).date() <= today
        done = _is_t5_done(manifest)
        if not due or done:
            status = "done" if done else "pending"
            record = {
                "run_id": run_id,
                "ticker": manifest.get("ticker"),
                "captured_at_t0_utc": t0_iso,
                "t5_due_date": due_date,
                "captured_at_t5_utc": manifest.get("captured_at_t5_utc"),
                "t5_status": status,
                "note": "",
                "last_checked_utc": _utc_now_iso(),
            }
            records.append(record)
            continue

        if dry_run:
            print(f"[DRY-RUN] t5 backfill {run_id}")
            continue
        try:
            capture_t5(run_id)
            refreshed = _load_manifest(RUNS_DIR / run_id / "manifest.json") or manifest
            record = {
                "run_id": run_id,
                "ticker": refreshed.get("ticker"),
                "captured_at_t0_utc": refreshed.get("captured_at_t0_utc"),
                "t5_due_date": due_date,
                "captured_at_t5_utc": refreshed.get("captured_at_t5_utc"),
                "t5_status": "done",
                "note": "",
                "last_checked_utc": _utc_now_iso(),
            }
        except Exception as exc:
            record = {
                "run_id": run_id,
                "ticker": manifest.get("ticker"),
                "captured_at_t0_utc": t0_iso,
                "t5_due_date": due_date,
                "captured_at_t5_utc": manifest.get("captured_at_t5_utc"),
                "t5_status": "failed",
                "note": str(exc),
                "last_checked_utc": _utc_now_iso(),
            }
        records.append(record)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="定时采集编排脚本")
    parser.add_argument("--tickers", default="NVDA", help="逗号分隔标的")
    parser.add_argument("--mode", choices=["t0", "t5", "both"], default="both")
    parser.add_argument("--dry-run", action="store_true", help="只打印不执行")
    args = parser.parse_args()

    _ensure_runs_dir()
    index_df = _load_index()

    if args.mode in ("t5", "both"):
        for record in run_t5_backfill(args.dry_run):
            index_df = _upsert_index(index_df, record)

    if args.mode in ("t0", "both"):
        tickers = [item.strip().upper() for item in args.tickers.split(",") if item.strip()]
        for record in run_t0_capture(tickers, args.dry_run):
            index_df = _upsert_index(index_df, record)

    _save_index(index_df)
    print(f"index updated: {INDEX_PATH}")


if __name__ == "__main__":
    main()