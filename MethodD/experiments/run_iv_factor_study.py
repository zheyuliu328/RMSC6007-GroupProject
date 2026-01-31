"""
IV 收敛因子研究：前向样本累积 + 可复算统计输出
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data.snapshot_store import (
    resolve_snapshot_path,
    verify_checksum,
    list_run_manifests,
)
from src.data.real_data_loader import load_snapshot
from src.factor.factor_definition import IVFactorDefinition
from src.eval.metrics import FactorMetrics


OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs')
SNAPSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'snapshots')
RUNS_DIR = os.path.join(SNAPSHOT_DIR, 'runs')
MAX_SPREAD_RATIO = 0.5
MIN_OPEN_INTEREST = 1
MIN_TRADABLE_PRICE = 0.01
DEFAULT_BOOTSTRAP = 500


def _ensure_output_dir() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _load_manifest_from_path(path: str) -> Dict[str, object]:
    verify_checksum(path)
    with open(path, 'r', encoding='utf-8') as handle:
        return json.load(handle)


def _collect_manifests() -> List[Dict[str, object]]:
    manifests = []
    run_manifests = list_run_manifests()
    for run_id, path in run_manifests.items():
        try:
            manifest = _load_manifest_from_path(path)
            manifest['run_id'] = run_id
            manifests.append(manifest)
        except Exception:
            continue
    legacy_path = os.path.join(SNAPSHOT_DIR, 'manifest.json')
    if os.path.exists(legacy_path):
        try:
            manifests.append(_load_manifest_from_path(legacy_path))
        except Exception:
            pass
    return manifests


def _resolve_snapshot_file(snapshot_info: Dict[str, object]) -> str:
    filename = snapshot_info.get('file')
    if not filename:
        raise ValueError("manifest snapshots 缺少 file")
    return resolve_snapshot_path(filename)


def _extract_chain_row(chain_df: pd.DataFrame, contract_symbol: str) -> Dict[str, object]:
    row = chain_df[chain_df['contractSymbol'] == contract_symbol]
    if row.empty:
        raise ValueError(f"找不到 contractSymbol={contract_symbol} 的记录")
    return row.iloc[0].to_dict()


def _normalize_expiry_key(expiry_value: object) -> object:
    if expiry_value is None:
        return None
    if isinstance(expiry_value, (int, float)):
        return pd.to_datetime(expiry_value, unit='s').strftime('%Y-%m-%d')
    if isinstance(expiry_value, str) and expiry_value.isdigit():
        return pd.to_datetime(int(expiry_value), unit='s').strftime('%Y-%m-%d')
    return expiry_value


def _resolve_snapshot_files(snapshot_info: object, run_id: str = None) -> Dict[object, str]:
    if snapshot_info is None:
        return {}
    if isinstance(snapshot_info, str):
        return {None: resolve_snapshot_path(snapshot_info, run_id=run_id)}
    if isinstance(snapshot_info, dict):
        if 'file' in snapshot_info:
            filename = snapshot_info.get('file')
            if not filename:
                raise ValueError("manifest snapshots 缺少 file")
            return {None: resolve_snapshot_path(filename, run_id=run_id)}
        resolved = {}
        for key, value in snapshot_info.items():
            if value is None:
                continue
            expiry_key = _normalize_expiry_key(key)
            filename = value.get('file') if isinstance(value, dict) else value
            if filename:
                resolved[expiry_key] = resolve_snapshot_path(filename, run_id=run_id)
        return resolved
    raise ValueError("manifest snapshots 格式不支持")


def _filter_chain_by_expiry(chain_df: pd.DataFrame, expiry_value: object) -> pd.DataFrame:
    if expiry_value is None:
        return chain_df
    if 'expiry' not in chain_df.columns:
        return chain_df
    return chain_df[chain_df['expiry'] == expiry_value]


def _is_liquid_row(row: pd.Series) -> bool:
    spread_t0 = row.get('spread_t0')
    spread_t5 = row.get('spread_t5')
    price_t0 = row.get('price_used_t0')
    price_t5 = row.get('price_used_t5')
    bid_t0 = row.get('bid_t0')
    ask_t0 = row.get('ask_t0')
    bid_t5 = row.get('bid_t5')
    ask_t5 = row.get('ask_t5')
    oi_t0 = row.get('open_interest_t0')
    oi_t5 = row.get('open_interest_t5')

    if price_t0 is None or pd.isna(price_t0) or price_t0 < MIN_TRADABLE_PRICE:
        return False
    if price_t5 is None or pd.isna(price_t5) or price_t5 < MIN_TRADABLE_PRICE:
        return False
    if pd.notna(spread_t0) and price_t0 > 0 and spread_t0 / price_t0 > MAX_SPREAD_RATIO:
        return False
    if pd.notna(spread_t5) and price_t5 > 0 and spread_t5 / price_t5 > MAX_SPREAD_RATIO:
        return False
    if pd.isna(bid_t0) or pd.isna(ask_t0) or bid_t0 <= 0 or ask_t0 <= 0:
        return False
    if pd.isna(bid_t5) or pd.isna(ask_t5) or bid_t5 <= 0 or ask_t5 <= 0:
        return False
    if pd.notna(oi_t0) and oi_t0 < MIN_OPEN_INTEREST:
        return False
    if pd.notna(oi_t5) and oi_t5 < MIN_OPEN_INTEREST:
        return False
    return True


def _calc_spread(bid: object, ask: object) -> object:
    if pd.notna(bid) and pd.notna(ask) and bid > 0 and ask > 0:
        return float(ask) - float(bid)
    return None


def _calc_mid(bid: float, ask: float, last: float) -> Dict[str, object]:
    if pd.notna(bid) and pd.notna(ask) and bid > 0 and ask > 0:
        return {'price_used': float((bid + ask) / 2), 'price_source': 'mid'}
    if pd.notna(last) and last > 0:
        return {'price_used': float(last), 'price_source': 'last'}
    return {'price_used': None, 'price_source': 'missing'}


def build_sample_table() -> pd.DataFrame:
    manifests = _collect_manifests()
    rows = []
    for manifest in manifests:
        snapshots = manifest.get('snapshots', {})
        if 't0' not in snapshots or 't5' not in snapshots:
            continue
        contract_key = manifest.get('contract_key') or {}
        expiry_keys = []
        if isinstance(manifest.get('expiries'), list):
            expiry_keys = [_normalize_expiry_key(item) for item in manifest.get('expiries')]
        else:
            expiry_key = _normalize_expiry_key(contract_key.get('expiry') or contract_key.get('expiry_epoch'))
            if expiry_key is not None:
                expiry_keys = [expiry_key]

        run_id = manifest.get('run_id')
        t0_map = _resolve_snapshot_files(snapshots.get('t0'), run_id=run_id)
        t5_map = _resolve_snapshot_files(snapshots.get('t5'), run_id=run_id)
        if not expiry_keys:
            expiry_keys = list({key for key in list(t0_map.keys()) + list(t5_map.keys()) if key is not None})
        if not expiry_keys:
            expiry_keys = [None]

        for expiry_key in expiry_keys:
            t0_path = t0_map.get(expiry_key) or t0_map.get(None)
            t5_path = t5_map.get(expiry_key) or t5_map.get(None)
            if not t0_path or not t5_path:
                continue

            verify_checksum(t0_path)
            verify_checksum(t5_path)

            t0_snapshot = load_snapshot(t0_path)
            t5_snapshot = load_snapshot(t5_path)
            if 'chain' not in t0_snapshot or 'chain' not in t5_snapshot:
                continue

            t0_chain = _filter_chain_by_expiry(t0_snapshot['chain'], expiry_key)
            t5_chain = _filter_chain_by_expiry(t5_snapshot['chain'], expiry_key)
            if t0_chain.empty or t5_chain.empty:
                continue

            t0_chain = t0_chain.copy()
            t5_chain = t5_chain.copy()
            t0_chain['openInterest'] = t0_chain.get('openInterest')
            t5_chain['openInterest'] = t5_chain.get('openInterest')

            merged = pd.merge(
                t0_chain,
                t5_chain,
                on='contractSymbol',
                suffixes=('_t0', '_t5')
            )
            if merged.empty:
                continue

            for _, row in merged.iterrows():
                if 'expiry_t0' in row and 'expiry_t5' in row and row['expiry_t0'] != row['expiry_t5']:
                    continue
                if 'strike_t0' in row and 'strike_t5' in row and pd.notna(row['strike_t5']):
                    if float(row['strike_t0']) != float(row['strike_t5']):
                        continue

                t0_mid = _calc_mid(row.get('bid_t0'), row.get('ask_t0'), row.get('last_t0'))
                t5_mid = _calc_mid(row.get('bid_t5'), row.get('ask_t5'), row.get('last_t5'))
                iv_t0 = row.get('iv_t0')
                iv_t5 = row.get('iv_t5')
                spot_t0 = float(t0_snapshot.get('spot'))
                spot_t5 = float(t5_snapshot.get('spot'))
                strike = row.get('strike_t0')

                sample_row = {
                    'run_id': manifest.get('run_id'),
                    'ticker': manifest.get('ticker'),
                    'contract_symbol': row.get('contractSymbol'),
                    'expiry': row.get('expiry_t0'),
                    'strike': strike,
                    'option_type': row.get('optionType_t0'),
                    't0_timestamp': t0_snapshot.get('timestamp'),
                    't5_timestamp': t5_snapshot.get('timestamp'),
                    'spot_t0': spot_t0,
                    'spot_t5': spot_t5,
                    'spot_change': spot_t5 - spot_t0,
                    'moneyness_t0': None if strike is None else float(strike) / spot_t0,
                    'iv_t0': iv_t0,
                    'iv_t5': iv_t5,
                    'iv_change': None if iv_t0 is None or iv_t5 is None else float(iv_t5) - float(iv_t0),
                    'bid_t0': row.get('bid_t0'),
                    'ask_t0': row.get('ask_t0'),
                    'last_t0': row.get('last_t0'),
                    'bid_t5': row.get('bid_t5'),
                    'ask_t5': row.get('ask_t5'),
                    'last_t5': row.get('last_t5'),
                    'price_used_t0': t0_mid['price_used'],
                    'price_source_t0': t0_mid['price_source'],
                    'price_used_t5': t5_mid['price_used'],
                    'price_source_t5': t5_mid['price_source'],
                    'spread_t0': _calc_spread(row.get('bid_t0'), row.get('ask_t0')),
                    'spread_t5': _calc_spread(row.get('bid_t5'), row.get('ask_t5')),
                    'open_interest_t0': row.get('openInterest_t0'),
                    'open_interest_t5': row.get('openInterest_t5'),
                    'data_source': manifest.get('data_source'),
                    'pricing_rule': manifest.get('pricing_rule'),
                }

                sample_row['is_tradable'] = _is_liquid_row(pd.Series(sample_row))
                rows.append(sample_row)

    sample_df = pd.DataFrame(rows)
    if sample_df.empty:
        return sample_df

    sample_df = sample_df.sort_values('t0_timestamp').reset_index(drop=True)
    sample_df['factor_a'] = IVFactorDefinition.compute_factor_version_a(sample_df['iv_t0'])
    sample_df['factor_b'] = IVFactorDefinition.compute_factor_version_b(sample_df['iv_t0'])
    sample_df['baseline_iv_level'] = sample_df['iv_t0']
    sample_df['baseline_iv_change_lag1'] = sample_df['iv_change'].shift(1)
    return sample_df


def _make_group_labels(sample_df: pd.DataFrame) -> pd.Series:
    return sample_df['t0_timestamp'].astype(str) + "|" + sample_df['expiry'].astype(str)


def _build_bucket_stats(sample_df: pd.DataFrame, label: str, bucket_col: str) -> List[Dict[str, object]]:
    rows = []
    if bucket_col not in sample_df.columns:
        return rows
    valid = sample_df.dropna(subset=[bucket_col, 'factor_b', 'iv_change'])
    if valid.empty:
        return rows
    quantiles = pd.qcut(valid[bucket_col], q=3, labels=False, duplicates='drop')
    valid = valid.assign(_bucket=quantiles)
    for bucket_id, subset in valid.groupby('_bucket'):
        ic_stats = FactorMetrics.spearman_ic_tstat(subset['factor_b'], subset['iv_change'])
        rows.append({
            'factor': 'factor_b',
            'target': 'iv_change',
            'group': f"{label}_bucket_{bucket_id}",
            'n': ic_stats['n'],
            'spearman_ic': ic_stats['ic'],
            'spearman_t_stat': ic_stats['t_stat'],
            'beta': None,
            'alpha': None,
            'r_value': None,
            'p_value': None,
            'stderr': None,
        })
    return rows


def build_stats_table(sample_df: pd.DataFrame) -> pd.DataFrame:
    if sample_df.empty:
        return pd.DataFrame()

    stats_rows = []
    targets = {
        'iv_change': sample_df['iv_change'],
    }
    factors = {
        'factor_a': sample_df['factor_a'],
        'factor_b': sample_df['factor_b'],
        'baseline_iv_level': sample_df['baseline_iv_level'],
        'baseline_iv_change_lag1': sample_df['baseline_iv_change_lag1'],
    }

    sample_df = sample_df.copy()
    sample_df['group_label'] = _make_group_labels(sample_df)
    control_vars = sample_df[['moneyness_t0', 'spread_t0', 'open_interest_t0']].copy()

    for factor_name, factor_series in factors.items():
        for target_name, target_series in targets.items():
            ic_stats = FactorMetrics.spearman_ic_tstat(factor_series, target_series)
            reg_stats = FactorMetrics.linear_regression_stats(factor_series, target_series)
            partial_ic = FactorMetrics.partial_spearman_ic(factor_series, target_series, control_vars)
            bootstrap_ic = FactorMetrics.spearman_ic_block_bootstrap(
                factor_series,
                target_series,
                sample_df['group_label'],
                n_bootstrap=DEFAULT_BOOTSTRAP,
            )
            stats_rows.append({
                'factor': factor_name,
                'target': target_name,
                'n': ic_stats['n'],
                'spearman_ic': ic_stats['ic'],
                'spearman_t_stat': ic_stats['t_stat'],
                'partial_spearman_ic': partial_ic['ic'],
                'partial_spearman_t': partial_ic['t_stat'],
                'bootstrap_ic_mean': bootstrap_ic['ic_mean'],
                'bootstrap_ic_std': bootstrap_ic['ic_std'],
                'bootstrap_t_stat': bootstrap_ic['t_stat'],
                'beta': reg_stats['beta'],
                'alpha': reg_stats['alpha'],
                'r_value': reg_stats['r_value'],
                'p_value': reg_stats['p_value'],
                'stderr': reg_stats['stderr'],
                'group': 'all'
            })

    if 'spread_t0' in sample_df.columns:
        median_spread = sample_df['spread_t0'].median(skipna=True)
        if pd.notna(median_spread):
            for label, subset in [('spread_low', sample_df[sample_df['spread_t0'] <= median_spread]),
                                  ('spread_high', sample_df[sample_df['spread_t0'] > median_spread])]:
                ic_stats = FactorMetrics.spearman_ic_tstat(subset['factor_b'], subset['iv_change'])
                stats_rows.append({
                    'factor': 'factor_b',
                    'target': 'iv_change',
                    'group': label,
                    'n': ic_stats['n'],
                    'spearman_ic': ic_stats['ic'],
                    'spearman_t_stat': ic_stats['t_stat'],
                    'partial_spearman_ic': None,
                    'partial_spearman_t': None,
                    'bootstrap_ic_mean': None,
                    'bootstrap_ic_std': None,
                    'bootstrap_t_stat': None,
                    'beta': None,
                    'alpha': None,
                    'r_value': None,
                    'p_value': None,
                    'stderr': None,
                })

    stats_rows.extend(_build_bucket_stats(sample_df, 'moneyness', 'moneyness_t0'))
    stats_rows.extend(_build_bucket_stats(sample_df, 'spread', 'spread_t0'))
    stats_rows.extend(_build_bucket_stats(sample_df, 'open_interest', 'open_interest_t0'))

    return pd.DataFrame(stats_rows)


def main() -> None:
    _ensure_output_dir()
    sample_df = build_sample_table()
    sample_path = os.path.join(OUTPUT_DIR, 'sample_table.csv')
    sample_df.to_csv(sample_path, index=False)

    tradable_df = sample_df[sample_df['is_tradable'] == True].copy()
    tradable_path = os.path.join(OUTPUT_DIR, 'sample_table_tradable.csv')
    tradable_df.to_csv(tradable_path, index=False)

    stats_df = build_stats_table(tradable_df)
    stats_path = os.path.join(OUTPUT_DIR, 'stats_table_tradable.csv')
    stats_df.to_csv(stats_path, index=False)

    full_stats_df = build_stats_table(sample_df)
    full_stats_path = os.path.join(OUTPUT_DIR, 'stats_table_full.csv')
    full_stats_df.to_csv(full_stats_path, index=False)

    print("=" * 80)
    print(f"样本表: {sample_path}")
    print(f"可交易样本表: {tradable_path}")
    print(f"统计表(主结论/可交易): {stats_path}")
    print(f"统计表(全量/附录): {full_stats_path}")
    print(f"样本量: {len(sample_df)} (可交易: {len(tradable_df)})")
    print("=" * 80)


if __name__ == '__main__':
    main()