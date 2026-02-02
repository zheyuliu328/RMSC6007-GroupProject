"""
NVDA 覆盖式卖 call 演示：离线真实快照复算 + 严格抓取
"""

import sys
import os
import argparse
from datetime import datetime
from typing import Dict, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd

from src.data.real_data_loader import fetch_nvda_option_chain, load_snapshot
from src.data.snapshot_store import (
    write_snapshot,
    write_manifest,
    load_manifest,
    resolve_snapshot_path,
    write_checksum,
    load_checksum,
    verify_checksum,
)


def _ensure_snapshot_dir() -> str:
    base_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "snapshots"
    )
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


REQUIRED_MANIFEST_FIELDS = [
    "mode",
    "ticker",
    "created_at",
    "timezone",
    "data_source",
    "pricing_rule",
    "contract_key",
    "snapshots",
]

REQUIRED_CONTRACT_FIELDS = ["optionType", "expiry", "strike", "contractSymbol"]

REQUIRED_CHAIN_COLUMNS = [
    "contractSymbol",
    "expiry",
    "strike",
    "bid",
    "ask",
    "last",
    "iv",
    "optionType",
]


def _select_contract(chain_df: pd.DataFrame, spot: float) -> Dict[str, object]:
    """选择合约：最近到期 + ATM"""
    calls = chain_df[chain_df["optionType"] == "call"]
    if calls.empty:
        raise ValueError("期权链为空，无法选合约")

    calls = calls.copy()
    calls["expiry_dt"] = pd.to_datetime(calls["expiry"])
    calls["strike_diff"] = (calls["strike"] - spot).abs()
    calls = calls.sort_values(["expiry_dt", "strike_diff"])
    selected = calls.iloc[0]

    return {
        "optionType": "call",
        "expiry": selected["expiry"],
        "strike": float(selected["strike"]),
        "contractSymbol": selected.get("contractSymbol"),
    }


def _match_contract(
    chain_df: pd.DataFrame, key: Dict[str, object], relax_strike: bool
) -> Dict[str, object]:
    """严格匹配 contractSymbol + expiry + strike + type"""
    target = chain_df[
        (chain_df["optionType"] == key["optionType"])
        & (chain_df["expiry"] == key["expiry"])
        & (chain_df["strike"] == key["strike"])
        & (chain_df["contractSymbol"] == key["contractSymbol"])
    ]
    substituted = False
    substitute_info = None

    if target.empty:
        if not relax_strike:
            raise ValueError("缺少同 contractSymbol + expiry + strike + type 合约")
        candidates = chain_df[
            (chain_df["optionType"] == key["optionType"])
            & (chain_df["expiry"] == key["expiry"])
        ].copy()
        if candidates.empty:
            raise ValueError("t5 快照同到期合约缺失，无法替代")
        candidates["strike_diff"] = (candidates["strike"] - key["strike"]).abs()
        candidates = candidates.sort_values("strike_diff")
        target = candidates.iloc[[0]]
        substituted = True
        substitute_info = {
            "original_strike": key["strike"],
            "substitute_strike": float(target["strike"].iloc[0]),
            "strike_distance": float(target["strike_diff"].iloc[0]),
            "substitute_contract_symbol": target["contractSymbol"].iloc[0],
        }

    row = target.iloc[0].to_dict()
    row["substituted"] = substituted
    row["substitute_info"] = substitute_info
    return row


def _resolve_price(row: Dict[str, object]) -> Tuple[float, int, str]:
    """价格口径：优先 bid/ask 中间价，失败 fallback last"""
    bid = row.get("bid")
    ask = row.get("ask")
    last = row.get("last")

    if pd.notna(bid) and pd.notna(ask) and bid > 0 and ask > 0:
        return float((bid + ask) / 2), 1, "mid"
    if pd.notna(last) and last > 0:
        return float(last), 0, "last"
    raise ValueError("bid/ask/last 均缺失或为 0，无法定价")


def _validate_manifest(manifest: Dict[str, object], require_t5: bool) -> None:
    if not manifest:
        raise ValueError("缺少 manifest，禁止运行离线复算")
    missing_fields = [
        field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest
    ]
    if missing_fields:
        raise ValueError(f"manifest 字段缺失: {missing_fields}")
    contract_key = manifest.get("contract_key")
    if not isinstance(contract_key, dict):
        raise ValueError("manifest.contract_key 缺失")
    missing_contract = [
        field for field in REQUIRED_CONTRACT_FIELDS if not contract_key.get(field)
    ]
    if missing_contract:
        raise ValueError(f"contract_key 字段缺失: {missing_contract}")
    snapshots = manifest.get("snapshots")
    if not isinstance(snapshots, dict):
        raise ValueError("manifest.snapshots 缺失")
    if "t0" not in snapshots:
        raise ValueError("manifest 缺少 t0 快照")
    if require_t5 and "t5" not in snapshots:
        raise ValueError("manifest 缺少 t5 快照")


def _manifest_path() -> str:
    return resolve_snapshot_path("manifest.json")


def _verify_manifest_checksum() -> None:
    manifest_path = _manifest_path()
    verify_checksum(manifest_path)


def _validate_snapshot(snapshot: Dict[str, object], label: str) -> None:
    if snapshot.get("spot") is None:
        raise ValueError(f"{label} 快照缺少 spot")
    if not snapshot.get("timestamp"):
        raise ValueError(f"{label} 快照缺少 timestamp")
    chain_df = snapshot.get("chain")
    if chain_df is None or not isinstance(chain_df, pd.DataFrame) or chain_df.empty:
        raise ValueError(f"{label} 快照缺少期权链数据")
    missing_cols = [
        col for col in REQUIRED_CHAIN_COLUMNS if col not in chain_df.columns
    ]
    if missing_cols:
        raise ValueError(f"{label} 快照字段缺失: {missing_cols}")


def _load_snapshot_from_manifest(
    manifest: Dict[str, object], key: str
) -> Dict[str, object]:
    snapshot_info = manifest.get("snapshots", {}).get(key)
    if not isinstance(snapshot_info, dict):
        raise ValueError(f"manifest 缺少 {key} 快照信息")
    filename = snapshot_info.get("file")
    checksum = snapshot_info.get("checksum")
    if not filename or not checksum:
        raise ValueError(f"manifest 缺少 {key} 文件或 checksum")
    path = resolve_snapshot_path(filename)
    verify_checksum(path)
    actual_checksum = load_checksum(path)
    if actual_checksum != checksum:
        raise ValueError(f"{key} checksum 与 manifest 不一致")
    snapshot = load_snapshot(path)
    _validate_snapshot(snapshot, key)
    return snapshot


def _save_outputs(rows: list) -> str:
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "nvda_covered_call_demo.csv")
    output_df = pd.DataFrame(rows)
    output_df.to_csv(output_path, index=False)
    return output_path


def run_strict_capture(ticker: str) -> None:
    """严格模式：t0 抓取并落盘"""
    print("【严格模式】开始抓取 t0 快照...")
    snapshot = fetch_nvda_option_chain(ticker)
    _validate_snapshot(snapshot, "t0")
    contract_key = _select_contract(snapshot["chain"], snapshot["spot"])
    snapshot_path = write_snapshot(snapshot, "t0")
    write_checksum(snapshot_path)

    t0_date = snapshot["timestamp"].split(" ")[0]
    target_date = pd.bdate_range(t0_date, periods=6)[-1].strftime("%Y-%m-%d")
    timezone = datetime.now().astimezone().tzname()
    manifest = {
        "mode": "strict",
        "ticker": ticker,
        "created_at": snapshot["timestamp"],
        "t0_date": t0_date,
        "t5_target_date": target_date,
        "timezone": timezone,
        "data_source": "Yahoo Finance",
        "pricing_rule": "mid_else_last",
        "contract_key": contract_key,
        "snapshots": {
            "t0": {
                "file": os.path.basename(snapshot_path),
                "checksum": load_checksum(snapshot_path),
            }
        },
    }
    manifest_path = write_manifest(manifest)
    write_checksum(manifest_path)

    print(f"✓ t0 快照已落盘: {snapshot_path}")
    print(f"✓ manifest 已更新: {manifest_path}")
    print(
        f"提示：t5 目标交易日为 {target_date}，请在该日期或之后执行 --strict-t5 生成 t5 并复算。"
    )


def run_t5_strict(manifest: Dict[str, object], relax_strike: bool) -> Dict[str, object]:
    """严格模式：抓取 t5 并复算"""
    print("【严格模式】开始抓取 t5 快照...")
    snapshot = fetch_nvda_option_chain(manifest["ticker"])
    _validate_snapshot(snapshot, "t5")
    snapshot_path = write_snapshot(snapshot, "t5")
    write_checksum(snapshot_path)
    manifest["snapshots"]["t5"] = {
        "file": os.path.basename(snapshot_path),
        "checksum": load_checksum(snapshot_path),
    }
    manifest["t5_timestamp"] = snapshot["timestamp"]
    manifest_path = write_manifest(manifest)
    write_checksum(manifest_path)

    t0_snapshot = _load_snapshot_from_manifest(manifest, "t0")
    t5_snapshot = snapshot
    return _run_analysis(
        t0_snapshot, t5_snapshot, manifest, relax_strike, data_mode="STRICT_CAPTURE"
    )


def _run_analysis(
    t0_snapshot: Dict[str, object],
    t5_snapshot: Dict[str, object],
    manifest: Dict[str, object],
    relax_strike: bool,
    data_mode: str,
) -> Dict[str, object]:
    contract_key = manifest["contract_key"]
    t0_chain = t0_snapshot["chain"]
    t5_chain = t5_snapshot["chain"]

    try:
        t0_row = _match_contract(t0_chain, contract_key, relax_strike=False)
        t5_row = _match_contract(t5_chain, contract_key, relax_strike=relax_strike)

        entry_price = float(t0_snapshot["spot"])
        exit_price = float(t5_snapshot["spot"])
        strike_price = float(contract_key["strike"])
        option_open, mid_used_t0, price_source_t0 = _resolve_price(t0_row)
        option_close, mid_used_t5, price_source_t5 = _resolve_price(t5_row)

        iv_entry = t0_row.get("iv")
        iv_exit = t5_row.get("iv")
        if pd.isna(iv_entry) or pd.isna(iv_exit):
            raise ValueError("IV 缺失")

        shares = 100
        stock_pnl = (exit_price - entry_price) * shares
        option_pnl = (option_open - option_close) * shares
        total_pnl = stock_pnl + option_pnl

        row = {
            "data_mode": data_mode,
            "match_status": "OK" if not t5_row["substituted"] else "RELAXED",
            "match_failure_reason": "",
            "STRICT_MATCH": 0 if t5_row["substituted"] else 1,
            "SUBSTITUTED_STRIKE": int(t5_row["substituted"]),
            "ticker": manifest["ticker"],
            "t0_timestamp": t0_snapshot.get("timestamp"),
            "t5_timestamp": t5_snapshot.get("timestamp"),
            "spot_t0": entry_price,
            "spot_t5": exit_price,
            "expiry": contract_key["expiry"],
            "strike": strike_price,
            "option_type": contract_key["optionType"],
            "contract_symbol_manifest": contract_key.get("contractSymbol"),
            "contract_symbol_t0": t0_row.get("contractSymbol"),
            "contract_symbol_t5": t5_row.get("contractSymbol"),
            "premium_open": option_open,
            "premium_close": option_close,
            "bid_t0": t0_row.get("bid"),
            "ask_t0": t0_row.get("ask"),
            "last_t0": t0_row.get("last"),
            "bid_t5": t5_row.get("bid"),
            "ask_t5": t5_row.get("ask"),
            "last_t5": t5_row.get("last"),
            "mid_used_t0": mid_used_t0,
            "mid_used_t5": mid_used_t5,
            "price_used_t0": option_open,
            "price_used_t5": option_close,
            "price_source_t0": price_source_t0,
            "price_source_t5": price_source_t5,
            "iv_t0": iv_entry,
            "iv_t5": iv_exit,
            "stock_pnl": stock_pnl,
            "option_pnl": option_pnl,
            "total_pnl": total_pnl,
            "shares": shares,
            "pricing_rule": manifest["pricing_rule"],
            "data_source": manifest["data_source"],
        }

        if t5_row["substituted"]:
            substitute_info = t5_row.get("substitute_info") or {}
            row.update(
                {
                    "original_strike": substitute_info.get("original_strike"),
                    "substitute_strike": substitute_info.get("substitute_strike"),
                    "strike_distance": substitute_info.get("strike_distance"),
                    "substitute_contract_symbol": substitute_info.get(
                        "substitute_contract_symbol"
                    ),
                }
            )

        output_path = _save_outputs([row])

        print("=" * 80)
        print(f"DATA_MODE={data_mode}")
        print(f"t0={t0_snapshot.get('timestamp')} t5={t5_snapshot.get('timestamp')}")
        print(f"输出文件: {output_path}")
        print("=" * 80)
        return row
    except Exception as exc:
        failure_reason = str(exc)
        row = {
            "data_mode": data_mode,
            "match_status": "FAIL",
            "match_failure_reason": failure_reason,
            "STRICT_MATCH": 0,
            "SUBSTITUTED_STRIKE": 0,
            "ticker": manifest.get("ticker"),
            "t0_timestamp": t0_snapshot.get("timestamp"),
            "t5_timestamp": t5_snapshot.get("timestamp"),
        }
        output_path = _save_outputs([row])
        print("=" * 80)
        print(f"DATA_MODE={data_mode}")
        print(f"复算失败: {failure_reason}")
        print(f"输出文件: {output_path}")
        print("=" * 80)
        raise


def run_demo_offline(relax_strike: bool) -> None:
    """离线 demo：读取 manifest 和快照"""
    _verify_manifest_checksum()
    manifest = load_manifest()
    _validate_manifest(manifest, require_t5=True)
    t0_snapshot = _load_snapshot_from_manifest(manifest, "t0")
    t5_snapshot = _load_snapshot_from_manifest(manifest, "t5")
    _run_analysis(
        t0_snapshot,
        t5_snapshot,
        manifest,
        relax_strike=relax_strike,
        data_mode="OFFLINE_SNAPSHOT_REAL",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="NVDA 覆盖式卖 call 离线真实快照复算")
    parser.add_argument("--ticker", default="NVDA", help="标的代码")
    parser.add_argument(
        "--relax-strike", action="store_true", help="允许 t5 替代 strike"
    )
    parser.add_argument(
        "--strict-t0", action="store_true", help="严格模式：抓取 t0 快照并落盘"
    )
    parser.add_argument(
        "--strict-t5", action="store_true", help="严格模式：抓取 t5 快照并复算"
    )
    args = parser.parse_args()

    _ensure_snapshot_dir()
    manifest = load_manifest()

    if args.strict_t0:
        run_strict_capture(args.ticker)
        return

    if args.strict_t5:
        _verify_manifest_checksum()
        _validate_manifest(manifest, require_t5=False)
        run_t5_strict(manifest, args.relax_strike)
        return

    run_demo_offline(args.relax_strike)


if __name__ == "__main__":
    main()
