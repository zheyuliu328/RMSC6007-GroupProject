#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 伪代码（先展示，后为可执行脚本）
#
# capture_t0(ticker)
# - 拉 Yahoo Finance option chain 的所有 expirations
# - 拉 spot 与 exchangeTimezoneName, regularMarketTime
# - 选 expiry：优先 20 到 40 DTE 内最接近 30 DTE，否则选最近到期
# - 选 ATM strike：最小化 abs(strike-spot)
# - 从 calls 里找到该 strike 的合约，取 contractSymbol 作为主键
# - 把整条 option chain 或至少该 expiry 的 calls/puts 全量落盘为 snapshot json
# - 写 manifest.json，包含 data_source, captured_at, timezone, pricing_rule, contract_key, t0_snapshot_path
# - 对 snapshot 与 manifest 写 sha256 文件
#
# capture_t5()
# - 读 manifest.json，拿 contract_key 与 expiry
# - 再抓一次同 expiry 的 option chain 作为 t5 快照落盘
# - 在 t5 快照中按 contractSymbol 精确匹配 calls 记录
# - 匹配不到直接失败并打印原因
# - 更新 manifest 写入 t5_snapshot_path 与 captured_at_t5
# - 对 t5 snapshot 与更新后的 manifest 写 sha256 文件

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
import yfinance as yf

BASE_URL = "https://query2.finance.yahoo.com/v7/finance/options/{ticker}"
SNAP_DIR = Path("data/snapshots")
RUNS_DIR = SNAP_DIR / "runs"

PRICING_RULE = "mid_else_last"
DATA_SOURCE = "yfinance option_chain (Yahoo Finance)"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _write_sha256(path: Path) -> Path:
    digest = _sha256_file(path)
    out = path.with_suffix(path.suffix + ".sha256")
    out.write_text(digest + "\n", encoding="utf-8")
    return out


def _verify_sha256(path: Path) -> None:
    sha_path = path.with_suffix(path.suffix + ".sha256")
    if not sha_path.exists():
        raise FileNotFoundError(f"缺少 checksum 文件: {sha_path}")
    expected = sha_path.read_text(encoding="utf-8").strip()
    actual = _sha256_file(path)
    if expected != actual:
        raise ValueError(f"checksum 不匹配: {path} expected={expected} actual={actual}")


def _http_get_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 20,
) -> Dict[str, Any]:
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }
    resp = requests.get(url, params=params, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _fetch_option_chain(ticker: str, expiry: Optional[int] = None) -> Dict[str, Any]:
    url = BASE_URL.format(ticker=ticker)
    params: Dict[str, Any] = {}
    if expiry is not None:
        params["date"] = expiry
    return _http_get_json(url, params=params)


def _fetch_chain_yf(ticker: str, expiry: str) -> Dict[str, Any]:
    ticker_obj = yf.Ticker(ticker)
    chain = ticker_obj.option_chain(expiry)
    return {
        "calls": chain.calls,
        "puts": chain.puts,
    }


def _extract_chain_result(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        results = payload["optionChain"]["result"]
        if not results:
            raise KeyError("empty result")
        return results[0]
    except Exception as exc:
        raise ValueError(f"无法解析 optionChain JSON: {exc}") from exc


def _dte_days(now_epoch: int, expiry_epoch: int) -> float:
    return (expiry_epoch - now_epoch) / (24 * 3600)


def _pick_expiries(now_epoch: int, expirations: List[int], count: int = 3) -> List[int]:
    candidates = [(exp, _dte_days(now_epoch, exp)) for exp in expirations]
    in_band = [(exp, dte) for exp, dte in candidates if 20 <= dte <= 40]
    selected: List[int] = []
    if in_band:
        in_band = sorted(in_band, key=lambda item: abs(item[1] - 30.0))
        selected.extend([exp for exp, _ in in_band[:count]])
    if len(selected) < count:
        future = [(exp, dte) for exp, dte in candidates if dte > 0]
        future = sorted(future, key=lambda item: item[1])
        for exp, _ in future:
            if exp in selected:
                continue
            selected.append(exp)
            if len(selected) >= count:
                break
    return selected


def _find_atm_call(option_chain: Dict[str, Any], spot: float) -> Tuple[float, Dict[str, Any]]:
    calls = option_chain.get("calls") or []
    if not calls:
        raise ValueError("该 expiry 下 calls 为空")
    strikes = sorted({float(c["strike"]) for c in calls if "strike" in c})
    if not strikes:
        raise ValueError("calls 中没有 strike 字段")
    atm_strike = min(strikes, key=lambda strike: abs(strike - spot))
    for call in calls:
        if float(call.get("strike", -1)) == float(atm_strike):
            return atm_strike, call
    raise ValueError("找不到 ATM strike 对应的 call 记录")


def _find_atm_call_df(calls_df: pd.DataFrame, spot: float) -> Tuple[float, Dict[str, Any]]:
    if calls_df is None or calls_df.empty:
        raise ValueError("该 expiry 下 calls 为空")
    calls_df = calls_df.copy()
    calls_df['strike_diff'] = (calls_df['strike'] - spot).abs()
    atm_call = calls_df.loc[calls_df['strike_diff'].idxmin()]
    return float(atm_call['strike']), atm_call.to_dict()


def _normalize_chain(df: pd.DataFrame, expiry: str, option_type: str) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=['expiry', 'strike', 'bid', 'ask', 'last', 'iv', 'contractSymbol', 'optionType', 'openInterest'])

    normalized = df.copy()
    normalized['expiry'] = expiry
    normalized['optionType'] = option_type
    rename_map = {
        'lastPrice': 'last',
        'impliedVolatility': 'iv'
    }
    normalized = normalized.rename(columns=rename_map)
    columns = ['expiry', 'strike', 'bid', 'ask', 'last', 'iv', 'contractSymbol', 'optionType', 'openInterest']
    for col in columns:
        if col not in normalized.columns:
            normalized[col] = pd.NA
    return normalized[columns]


def _ensure_snapshot_dir() -> None:
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)


def _run_dir(run_id: str) -> Path:
    _ensure_snapshot_dir()
    return RUNS_DIR / run_id


def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def capture_t0(ticker: str, run_id: Optional[str] = None) -> str:
    _ensure_snapshot_dir()
    if run_id is None:
        run_id = f"{ticker.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir = _run_dir(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    ticker_obj = yf.Ticker(ticker)
    spot_df = ticker_obj.history(period='1d', interval='1d')
    if spot_df.empty:
        raise ValueError(f"无法获取 {ticker} 现价")
    spot = float(spot_df['Close'].iloc[-1])
    tz_name = datetime.now().astimezone().tzname() or "UTC"
    now_epoch = int(time.time())

    expirations = ticker_obj.options
    if not expirations:
        raise ValueError("expirationDates 为空")
    expiry_map = {exp: int(pd.to_datetime(exp).timestamp()) for exp in expirations}
    expiries = _pick_expiries(now_epoch, list(expiry_map.values()), count=3)
    expiries = [exp for exp, epoch in expiry_map.items() if epoch in expiries]

    snapshots: Dict[str, str] = {}
    contract_symbol = None
    atm_strike = None
    primary_expiry = expiries[0]

    for expiry in expiries:
        chain_data = _fetch_chain_yf(ticker, expiry)
        calls_df = chain_data.get("calls")
        puts_df = chain_data.get("puts")
        if calls_df is None or calls_df.empty:
            continue

        if expiry == primary_expiry:
            atm_strike, call_rec = _find_atm_call_df(calls_df, spot)
            contract_symbol = call_rec.get("contractSymbol")
            if not contract_symbol:
                raise ValueError("ATM call 缺少 contractSymbol")

        chain_df = pd.concat([
            _normalize_chain(calls_df, expiry, 'call'),
            _normalize_chain(puts_df, expiry, 'put')
        ], ignore_index=True)

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snap_name = f"{ticker.lower()}_chain_t0_{expiry}_{stamp}.json"
        snap_path = run_dir / snap_name

        snapshot = {
            "meta": {
                "ticker": ticker.upper(),
                "data_source": DATA_SOURCE,
                "captured_at_utc": _utc_now_iso(),
                "exchange_timezone": tz_name,
                "regularMarketTime_epoch": now_epoch,
                "pricing_rule": PRICING_RULE,
            },
            "expiry_epoch": int(pd.to_datetime(expiry).timestamp()),
            "spot": spot,
            "chain": chain_df.to_dict(orient='records'),
        }
        _write_json(snap_path, snapshot)
        _write_sha256(snap_path)
        snapshots[str(expiry)] = snap_name

    if not snapshots:
        raise ValueError("t0 未能落盘任何 expiry 快照")

    manifest = {
        "run_id": run_id,
        "data_mode_default": "OFFLINE_SNAPSHOT_REAL",
        "data_source": DATA_SOURCE,
        "pricing_rule": PRICING_RULE,
        "ticker": ticker.upper(),
        "timezone": tz_name,
        "captured_at_t0_utc": _utc_now_iso(),
        "t5_target_rule": "t0_plus_5_trading_days",
        "expiries": [str(expiry) for expiry in expiries],
        "contract_key": {
            "ticker": ticker.upper(),
            "type": "call",
            "expiry_epoch": int(pd.to_datetime(primary_expiry).timestamp()),
            "strike": float(atm_strike) if atm_strike is not None else None,
            "contractSymbol": contract_symbol,
        },
        "snapshots": {
            "t0": snapshots,
            "t5": {str(expiry): None for expiry in expiries},
        },
    }
    manifest_path = run_dir / "manifest.json"
    _write_json(manifest_path, manifest)
    _write_sha256(manifest_path)

    print("OK t0 captured")
    print(
        "spot={spot} expiry_epoch={expiry} strike={strike} contractSymbol={symbol}".format(
            spot=spot,
            expiry=primary_expiry,
            strike=atm_strike,
            symbol=contract_symbol,
        )
    )
    print(f"snapshots={snapshots}")
    print(f"run_id={run_id}")
    print("next: run t5 on the 5th trading day to capture t5")
    return run_id


def capture_t5(run_id: str) -> None:
    run_dir = _run_dir(run_id)
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"缺少 manifest: {manifest_path}")

    _verify_sha256(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    contract_key = manifest.get("contract_key") or {}
    ticker = contract_key.get("ticker")
    expiries = manifest.get("expiries") or []
    if not expiries:
        expiry = contract_key.get("expiry_epoch")
        if expiry is not None:
            expiries = [expiry]
    if not ticker or not expiries:
        raise ValueError("manifest 缺少 ticker 或 expiries")

    ticker_obj = yf.Ticker(ticker)
    spot_df = ticker_obj.history(period='1d', interval='1d')
    if spot_df.empty:
        raise ValueError(f"无法获取 {ticker} 现价")
    spot = float(spot_df['Close'].iloc[-1])
    tz_name = datetime.now().astimezone().tzname() or manifest.get("timezone") or "UTC"
    now_epoch = int(time.time())

    snapshots: Dict[str, str] = {}
    for expiry in expiries:
        chain_data = _fetch_chain_yf(ticker, str(expiry))
        calls_df = chain_data.get("calls")
        puts_df = chain_data.get("puts")
        if calls_df is None or calls_df.empty:
            continue

        chain_df = pd.concat([
            _normalize_chain(calls_df, str(expiry), 'call'),
            _normalize_chain(puts_df, str(expiry), 'put')
        ], ignore_index=True)

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snap_name = f"{ticker.lower()}_chain_t5_{expiry}_{stamp}.json"
        snap_path = run_dir / snap_name

        snapshot = {
            "meta": {
                "ticker": ticker.upper(),
                "data_source": DATA_SOURCE,
                "captured_at_utc": _utc_now_iso(),
                "exchange_timezone": tz_name,
                "regularMarketTime_epoch": now_epoch,
                "pricing_rule": PRICING_RULE,
            },
            "expiry_epoch": int(pd.to_datetime(expiry).timestamp()),
            "spot": spot,
            "chain": chain_df.to_dict(orient='records'),
        }
        _write_json(snap_path, snapshot)
        _write_sha256(snap_path)
        snapshots[str(expiry)] = snap_name

    if not snapshots:
        raise ValueError("t5 未能落盘任何 expiry 快照")

    manifest["captured_at_t5_utc"] = _utc_now_iso()
    manifest["snapshots"]["t5"] = snapshots
    _write_json(manifest_path, manifest)
    _write_sha256(manifest_path)

    print("OK t5 captured")
    print(f"snapshots={snapshots}")
    print("offline mode now has t0+t5 snapshots")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="NVDA")
    parser.add_argument("--run-id", default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("t0")
    sub.add_parser("t5")
    args = parser.parse_args()

    if args.cmd == "t0":
        capture_t0(args.ticker, args.run_id)
    elif args.cmd == "t5":
        if not args.run_id:
            raise ValueError("t5 必须指定 --run-id")
        capture_t5(args.run_id)
    else:
        raise ValueError("unknown cmd")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("aborted", file=sys.stderr)
        sys.exit(130)