"""
MethodD nasdaq-full v1 模拟数据验收脚本

验收：manifest hash、run_id 数量、分区完整性、IV spike 频率
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict

import pandas as pd
import yaml


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = BASE_DIR / "data" / "simulated" / "nasdaq_full" / "v1"
DEFAULT_UNIVERSE = BASE_DIR / "data" / "universe" / "nasdaq" / "universe.csv"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_manifest(data_dir: Path) -> Dict[str, object]:
    manifest_path = data_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"缺少 manifest.json: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _validate_hashes(data_dir: Path, manifest: Dict[str, object]) -> None:
    sha_map = manifest.get("sha256") or {}
    if not sha_map:
        raise ValueError("manifest.sha256 为空")
    for filename, expected in sha_map.items():
        path = data_dir / filename
        if not path.exists():
            path = BASE_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"缺少文件: {path}")
        actual = _sha256(path)
        if actual != expected:
            raise ValueError(f"hash 不一致: {filename}")


def _validate_run_id(universe_path: Path, calendar_days: int) -> int:
    tickers = pd.read_csv(universe_path)["ticker"].dropna()
    expected = int(len(tickers) * calendar_days)
    if expected <= 0:
        raise ValueError("run_id 期望值无效")
    return expected


def _validate_partitions(
    data_dir: Path, expected_tickers: int
) -> Dict[str, list[Path]]:
    partitions = {}
    for name in ("prices", "iv", "targets", "options"):
        part_dir = data_dir / name
        if not part_dir.exists():
            raise FileNotFoundError(f"缺少 {name} 分区目录")
        files = sorted(part_dir.glob("ticker=*.parquet"))
        if len(files) != expected_tickers:
            raise ValueError(f"{name} 分区数量异常: {len(files)} != {expected_tickers}")
        partitions[name] = files
    return partitions


def _validate_sample_run_id(sample_file: Path, calendar_days: int) -> None:
    df = pd.read_parquet(sample_file)
    if df.empty:
        raise ValueError("样本分区为空")
    if len(df) != calendar_days:
        raise ValueError(f"run_id 数量异常: {len(df)} != {calendar_days}")
    if df["run_id"].nunique() != calendar_days:
        raise ValueError("run_id 未唯一覆盖日历")


def _validate_iv_spike(data_dir: Path, lower: float, upper: float) -> None:
    iv_dir = data_dir / "iv"
    sample_files = sorted(iv_dir.glob("ticker=*.parquet"))
    if not sample_files:
        raise FileNotFoundError("iv 分区为空")
    sample_files = sample_files[: min(50, len(sample_files))]

    spike_rates = []
    for path in sample_files:
        df = pd.read_parquet(path)
        if df.empty:
            continue
        df = df.sort_values("date")
        rolling = df["iv"].rolling(10, min_periods=5).median()
        spike = (df["iv"] - rolling) / rolling
        spike_rates.append((spike > 0.15).mean())
    if not spike_rates:
        raise ValueError("无法计算 IV spike 频率")
    avg_rate = float(pd.Series(spike_rates).mean())
    if avg_rate < lower or avg_rate > upper:
        raise ValueError(f"IV spike 频率异常: {avg_rate:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="MethodD 模拟数据验收")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="模拟数据目录（包含 manifest.json）",
    )
    parser.add_argument(
        "--universe",
        type=Path,
        default=DEFAULT_UNIVERSE,
        help="Nasdaq universe.csv 路径",
    )
    parser.add_argument(
        "--spike-lower",
        type=float,
        default=0.02,
        help="IV spike 频率下限",
    )
    parser.add_argument(
        "--spike-upper",
        type=float,
        default=0.25,
        help="IV spike 频率上限",
    )
    args = parser.parse_args()
    data_dir = args.data_dir

    manifest = _load_manifest(data_dir)
    _validate_hashes(data_dir, manifest)

    config_path = data_dir / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError("缺少 config.yaml")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not config:
        raise ValueError("config.yaml 为空")

    calendar = pd.bdate_range(
        start=config["start_date"], end=config["end_date"], freq="B"
    )
    expected_runs = _validate_run_id(args.universe, len(calendar))
    expected_tickers = int(pd.read_csv(args.universe)["ticker"].dropna().shape[0])

    manifest_partitions = manifest.get("partitions") or {}
    for name in ("prices", "iv", "targets", "options"):
        count = int(manifest_partitions.get(name, 0))
        if count != expected_tickers:
            raise ValueError(f"manifest 分区数量异常: {name}={count}")

    partitions = _validate_partitions(data_dir, expected_tickers)
    _validate_sample_run_id(partitions["prices"][0], len(calendar))
    _validate_sample_run_id(partitions["options"][0], len(calendar))
    _validate_iv_spike(data_dir, args.spike_lower, args.spike_upper)

    print("✓ manifest hash 校验通过")
    print(f"✓ expected run_id: {expected_runs}")
    print("✓ 分区完整性校验通过")
    print("✓ IV spike 频率在允许区间内")


if __name__ == "__main__":
    main()
