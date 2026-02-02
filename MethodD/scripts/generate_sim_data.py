"""
MethodD 模拟数据生成器（v1）

目标：统一输入、可复现、多 run、可追踪可回滚
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import yaml

from src.pricing.bs_pricer import BlackScholesOption


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = BASE_DIR / "data" / "simulated" / "nasdaq_full" / "v1" / "config.yaml"
DEFAULT_UNIVERSE = BASE_DIR / "data" / "universe" / "nasdaq" / "universe.csv"


@dataclass
class Regime:
    """市场状态参数"""

    name: str
    drift: float
    vol: float
    iv_level: float


def _load_config(path: Path) -> Dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(f"缺少 config.yaml: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _load_universe(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"缺少 universe.csv: {path}")
    df = pd.read_csv(path)
    if "ticker" not in df.columns:
        raise ValueError("universe.csv 缺少 ticker 列")
    df = df.dropna(subset=["ticker"]).copy()
    df["ticker"] = df["ticker"].astype(str)
    if df.empty:
        raise ValueError("universe 为空")
    return df


def _ticker_seed(global_seed: int, ticker: str) -> int:
    digest = hashlib.sha256(f"{global_seed}:{ticker}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _make_calendar(start_date: str, end_date: str) -> pd.DatetimeIndex:
    return pd.bdate_range(start=start_date, end=end_date, freq="B")


def _sample_regimes(
    n_days: int,
    regimes: List[Regime],
    rng: np.random.Generator,
    min_block: int,
    max_block: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[str]]:
    """生成 regime 路径（分段切换）"""

    drifts = np.zeros(n_days)
    vols = np.zeros(n_days)
    iv_levels = np.zeros(n_days)
    names: List[str] = []

    idx = 0
    while idx < n_days:
        regime = rng.choice(regimes)
        block = int(rng.integers(min_block, max_block + 1))
        end = min(idx + block, n_days)
        drifts[idx:end] = regime.drift
        vols[idx:end] = regime.vol
        iv_levels[idx:end] = regime.iv_level
        names.extend([regime.name] * (end - idx))
        idx = end

    return drifts, vols, iv_levels, names


def _simulate_iv(
    n_days: int,
    iv_levels: np.ndarray,
    rng: np.random.Generator,
    iv_base: float,
    iv_vol: float,
    iv_floor: float,
    iv_mean_revert: float,
    jump_prob: float,
    jump_scale: float,
    baseline_window: int,
    spike_reversion_boost: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """均值回归 + 脉冲跳跃的 IV 序列"""

    iv = np.zeros(n_days)
    iv_eps = np.zeros(n_days)
    spike_strength = np.zeros(n_days)
    iv[0] = iv_base

    for t in range(1, n_days):
        start = max(0, t - baseline_window)
        baseline = np.median(iv[start:t]) if t > 0 else iv_base
        ratio = (iv[t - 1] - baseline) / baseline if baseline > 0 else 0.0
        spike_strength[t] = max(0.0, ratio)

        kappa = iv_mean_revert * (1 + spike_reversion_boost * spike_strength[t])
        jump = rng.normal(0.0, jump_scale) if rng.random() < jump_prob else 0.0
        eps = rng.normal(0.0, 1.0)
        iv_eps[t] = eps
        shock = iv_vol * eps + jump
        target = iv_levels[t] if iv_levels[t] > 0 else iv_base

        iv[t] = iv[t - 1] + kappa * (target - iv[t - 1]) + shock
        iv[t] = max(iv[t], iv_floor)

    return iv, iv_eps, spike_strength


def _simulate_returns(
    drifts: np.ndarray,
    vols: np.ndarray,
    iv_eps: np.ndarray,
    spike_strength: np.ndarray,
    rng: np.random.Generator,
    corr_ret_iv: float,
    spike_vol_boost: float,
) -> np.ndarray:
    """收益率与 IV 变化负相关，并在 IV spike 时放大波动"""

    n_days = len(drifts)
    rets = np.zeros(n_days)
    corr = float(np.clip(corr_ret_iv, -0.95, 0.95))
    mix_scale = np.sqrt(1 - corr ** 2)

    for t in range(1, n_days):
        z_ret = rng.normal(0.0, 1.0)
        z_iv = iv_eps[t]
        vol = vols[t] * (1 + spike_vol_boost * spike_strength[t])
        rets[t] = drifts[t] + vol * (corr * z_iv + mix_scale * z_ret)

    return rets


def _build_prices(init_price: float, log_returns: np.ndarray) -> np.ndarray:
    prices = init_price * np.exp(np.cumsum(log_returns))
    return prices


def _build_universe_meta(universe_df: pd.DataFrame, seed: int) -> pd.DataFrame:
    meta = universe_df.copy()
    if "mcap" not in meta.columns or "beta" not in meta.columns:
        mcap_values = []
        beta_values = []
        for ticker in meta["ticker"].tolist():
            ticker_seed = _ticker_seed(seed, ticker)
            rng = np.random.default_rng(ticker_seed)
            mcap_values.append(10 ** rng.uniform(9.0, 12.0))
            beta = float(np.clip(rng.normal(1.1, 0.35), 0.3, 2.8))
            beta_values.append(beta)
        meta["mcap"] = mcap_values
        meta["beta"] = beta_values
    return meta[["ticker", "mcap", "beta"]]


def _build_pool_membership(meta_df: pd.DataFrame, mcap_q: float, beta_q: float) -> pd.DataFrame:
    mcap_thr = float(meta_df["mcap"].quantile(mcap_q))
    beta_thr = float(meta_df["beta"].quantile(beta_q))
    membership = meta_df.copy()
    membership["mcap_thr"] = mcap_thr
    membership["beta_thr"] = beta_thr
    membership["mcap_pass"] = membership["mcap"] >= mcap_thr
    membership["beta_pass"] = membership["beta"] >= beta_thr
    membership["in_pool"] = (membership["mcap_pass"] & membership["beta_pass"]).astype(int)
    return membership


def _compute_targets(df_prices: pd.DataFrame, df_iv: pd.DataFrame) -> pd.DataFrame:
    merged = df_prices.merge(df_iv, on=["date", "ticker", "run_id"], how="left")
    merged = merged.sort_values(["ticker", "date"])
    merged["spot_return_5d"] = (
        merged.groupby("ticker")["close"].shift(-5) / merged["close"] - 1
    )
    merged["iv_change_5d"] = (
        merged.groupby("ticker")["iv"].shift(-5) - merged["iv"]
    )
    return merged[["date", "ticker", "run_id", "spot_return_5d", "iv_change_5d"]]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_manifest(
    output_dir: Path,
    dataset_version: str,
    files: List[Path],
    universe_files: List[Path],
    partitions: Dict[str, int],
    ticker_count: int,
) -> None:
    sha_map = {path.name: _sha256(path) for path in files}
    for path in universe_files:
        resolved = path.resolve()
        try:
            rel_path = resolved.relative_to(BASE_DIR)
        except ValueError:
            rel_path = Path(path)
        sha_map[str(rel_path)] = _sha256(resolved)

    manifest = {
        "dataset_version": dataset_version,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "sha256": sha_map,
        "partitions": partitions,
        "ticker_count": ticker_count,
    }

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def generate_dataset(config_path: Path, dataset_version: str | None, universe_path: Path) -> Path:
    config = _load_config(config_path)
    version = dataset_version or str(config.get("dataset_version") or "v1")
    output_dir = BASE_DIR / "data" / "simulated" / "nasdaq_full" / version
    output_dir.mkdir(parents=True, exist_ok=True)

    seed = int(config.get("seed", 42))
    rng = np.random.default_rng(seed)
    init_price = float(config.get("init_price", 100.0))
    calendar = _make_calendar(config["start_date"], config["end_date"])

    regimes = [Regime(**item) for item in config.get("regimes", [])]
    if not regimes:
        raise ValueError("regimes 不能为空")

    min_block = int(config.get("regime_min_days", 20))
    max_block = int(config.get("regime_max_days", 60))

    iv_params = config.get("iv_params", {})
    iv_base = float(iv_params.get("iv_base", 0.20))
    iv_vol = float(iv_params.get("iv_vol", 0.02))
    iv_floor = float(iv_params.get("iv_floor", 0.05))
    iv_mean_revert = float(iv_params.get("iv_mean_revert", 0.15))
    jump_prob = float(iv_params.get("jump_prob", 0.05))
    jump_scale = float(iv_params.get("jump_scale", 0.08))
    baseline_window = int(iv_params.get("baseline_window", 10))
    spike_reversion_boost = float(iv_params.get("spike_reversion_boost", 2.5))
    spike_vol_boost = float(iv_params.get("spike_vol_boost", 0.8))
    corr_ret_iv = float(iv_params.get("corr_ret_iv", -0.4))

    universe_df = _load_universe(universe_path)
    tickers = universe_df["ticker"].dropna().astype(str).tolist()
    ticker_count = len(tickers)

    pool_params = config.get("pool_params", {})
    mcap_quantile = float(pool_params.get("mcap_top_quantile", 0.7))
    beta_quantile = float(pool_params.get("beta_top_quantile", 0.7))

    options_params = config.get("options_params", {})
    tenor_days = options_params.get("tenor_days", [7])
    if isinstance(tenor_days, (int, float)):
        tenor_days = [int(tenor_days)]
    tenor_days = [int(item) for item in tenor_days]
    risk_free_rate = float(options_params.get("risk_free_rate", 0.02))
    strike_type = str(options_params.get("strike_type", "ATM"))
    prices_dir = output_dir / "prices"
    iv_dir = output_dir / "iv"
    targets_dir = output_dir / "targets"
    options_dir = output_dir / "options"
    prices_dir.mkdir(parents=True, exist_ok=True)
    iv_dir.mkdir(parents=True, exist_ok=True)
    targets_dir.mkdir(parents=True, exist_ok=True)
    options_dir.mkdir(parents=True, exist_ok=True)
    partitions = {
        "prices": 0,
        "iv": 0,
        "targets": 0,
        "options": 0,
    }

    meta_df = _build_universe_meta(universe_df, seed)
    meta_path = output_dir / "universe_meta.csv"
    meta_df.to_csv(meta_path, index=False)

    pool_df = _build_pool_membership(meta_df, mcap_quantile, beta_quantile)
    pool_path = output_dir / "pool_membership.csv"
    pool_df.to_csv(pool_path, index=False)

    for ticker in tickers:
        ticker_seed = _ticker_seed(seed, ticker)
        local_rng = np.random.default_rng(ticker_seed)

        drifts, vols, iv_levels, _ = _sample_regimes(
            len(calendar), regimes, local_rng, min_block, max_block
        )
        iv_series, iv_eps, spike_strength = _simulate_iv(
            len(calendar),
            iv_levels,
            local_rng,
            iv_base,
            iv_vol,
            iv_floor,
            iv_mean_revert,
            jump_prob,
            jump_scale,
            baseline_window,
            spike_reversion_boost,
        )

        log_returns = _simulate_returns(
            drifts, vols, iv_eps, spike_strength, local_rng, corr_ret_iv, spike_vol_boost
        )
        prices = _build_prices(init_price, log_returns)

        price_rows = []
        iv_rows = []
        option_rows = []
        for date, close, iv in zip(calendar, prices, iv_series):
            date_str = date.strftime("%Y-%m-%d")
            run_id = f"{date_str}|{ticker}"
            price_rows.append(
                {"date": date_str, "ticker": ticker, "run_id": run_id, "close": close}
            )
            iv_rows.append(
                {"date": date_str, "ticker": ticker, "run_id": run_id, "iv": iv}
            )
            for tenor in tenor_days:
                t_year = max(float(tenor) / 252.0, 1e-6)
                strike = close
                call_premium = BlackScholesOption.call_price(
                    S=float(close),
                    K=float(strike),
                    T=t_year,
                    r=risk_free_rate,
                    sigma=float(iv),
                )
                put_premium = BlackScholesOption.put_price(
                    S=float(close),
                    K=float(strike),
                    T=t_year,
                    r=risk_free_rate,
                    sigma=float(iv),
                )
                option_rows.append(
                    {
                        "date": date_str,
                        "ticker": ticker,
                        "run_id": run_id,
                        "tenor_days": tenor,
                        "strike_type": strike_type,
                        "call_premium": float(call_premium),
                        "put_premium": float(put_premium),
                    }
                )

        prices_df = pd.DataFrame(price_rows)
        iv_df = pd.DataFrame(iv_rows)
        options_df = pd.DataFrame(option_rows)
        targets_df = _compute_targets(prices_df, iv_df)

        prices_path = prices_dir / f"ticker={ticker}.parquet"
        iv_path = iv_dir / f"ticker={ticker}.parquet"
        targets_path = targets_dir / f"ticker={ticker}.parquet"
        options_path = options_dir / f"ticker={ticker}.parquet"

        prices_df.to_parquet(prices_path, index=False)
        iv_df.to_parquet(iv_path, index=False)
        targets_df.to_parquet(targets_path, index=False)
        options_df.to_parquet(options_path, index=False)
        partitions["prices"] += 1
        partitions["iv"] += 1
        partitions["targets"] += 1
        partitions["options"] += 1

    config_out = output_dir / "config.yaml"
    config_out.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    _write_manifest(
        output_dir,
        version,
        [config_out, meta_path, pool_path],
        [universe_path, universe_path.parent / "nasdaqlisted_snapshot.txt"],
        partitions,
        ticker_count,
    )
    return output_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="MethodD 模拟数据生成器")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="config.yaml 路径",
    )
    parser.add_argument(
        "--dataset-version",
        type=str,
        default=None,
        help="数据版本（默认取 config.yaml 里的 dataset_version）",
    )
    parser.add_argument(
        "--universe",
        type=Path,
        default=DEFAULT_UNIVERSE,
        help="Nasdaq universe.csv 路径",
    )
    args = parser.parse_args()

    output_dir = generate_dataset(args.config, args.dataset_version, args.universe)
    print(f"✓ 已生成模拟数据: {output_dir}")


if __name__ == "__main__":
    main()