"""
价格因子：Bollinger、MA200 突破强度、MACD
"""

from typing import Tuple

import numpy as np
import pandas as pd


def compute_bollinger(close: pd.Series, window: int = 20) -> Tuple[float, float]:
    """
    计算 Bollinger 位置分数与带宽

    返回:
        (bb_pos, bb_bw)
    """
    if close is None or close.empty:
        return float("nan"), float("nan")
    close = close.astype(float)
    ma = close.rolling(window=window, min_periods=window).mean()
    sd = close.rolling(window=window, min_periods=window).std(ddof=0)
    ma_last = ma.iloc[-1]
    sd_last = sd.iloc[-1]
    if np.isnan(ma_last) or np.isnan(sd_last) or sd_last == 0:
        return float("nan"), float("nan")
    bb_pos = (close.iloc[-1] - ma_last) / (2 * sd_last)
    bb_bw = (4 * sd_last) / ma_last if ma_last != 0 else float("nan")
    return float(bb_pos), float(bb_bw)


def compute_bb_midline_break(close: pd.Series, window: int = 10) -> Tuple[int, int]:
    """
    计算 BB 中线突破方向（基于 10 日中线）

    返回:
        (break_flag, break_side)
        break_flag: 是否突破中线 (0/1)
        break_side: 1 上穿 / -1 下穿 / 0 无突破
    """
    if close is None or close.empty:
        return 0, 0
    close = close.astype(float)
    ma = close.rolling(window=window, min_periods=window).mean()
    if len(close) < window + 1:
        return 0, 0
    prev_ma = ma.iloc[-2]
    curr_ma = ma.iloc[-1]
    if np.isnan(prev_ma) or np.isnan(curr_ma):
        return 0, 0
    prev_diff = close.iloc[-2] - prev_ma
    curr_diff = close.iloc[-1] - curr_ma
    if prev_diff <= 0 < curr_diff:
        return 1, 1
    if prev_diff >= 0 > curr_diff:
        return 1, -1
    return 0, 0


def compute_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 20,
) -> float:
    """
    计算 ATR（如缺 High/Low 则回退为 close-to-close 波动）
    """
    if close is None or close.empty:
        return float("nan")
    close = close.astype(float)

    if high is None or low is None or high.empty or low.empty:
        std = close.pct_change().rolling(window=window, min_periods=window).std(ddof=0)
        return float(std.iloc[-1]) if not std.empty else float("nan")

    high = high.astype(float)
    low = low.astype(float)
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = tr.rolling(window=window, min_periods=window).mean()
    return float(atr.iloc[-1]) if not atr.empty else float("nan")


def compute_ma200_break(close: pd.Series, atr: float, window: int = 200) -> float:
    """
    计算 MA200 突破强度 (Close - MA200) / ATR
    """
    if close is None or close.empty:
        return float("nan")
    close = close.astype(float)
    ma = close.rolling(window=window, min_periods=window).mean()
    ma_last = ma.iloc[-1]
    if np.isnan(ma_last) or atr in (None, 0) or np.isnan(atr):
        return float("nan")
    return float((close.iloc[-1] - ma_last) / atr)


def compute_macd_hist(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> float:
    """
    计算 MACD Histogram（柱体）
    """
    if close is None or close.empty:
        return float("nan")
    close = close.astype(float)
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - signal_line
    return float(hist.iloc[-1])


def compute_macd_cross_fast_slope(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> Tuple[int, float]:
    """
    计算 MACD 金叉/死叉标记与快线斜率

    返回:
        (cross_flag, fast_slope)
        cross_flag: 1=金叉, -1=死叉, 0=无交叉
        fast_slope: 快线 EMA 的一阶差分
    """
    if close is None or close.empty or len(close) < slow + signal:
        return 0, float("nan")
    close = close.astype(float)
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    prev_diff = macd.iloc[-2] - signal_line.iloc[-2]
    curr_diff = macd.iloc[-1] - signal_line.iloc[-1]
    cross_flag = 0
    if prev_diff <= 0 < curr_diff:
        cross_flag = 1
    elif prev_diff >= 0 > curr_diff:
        cross_flag = -1
    fast_slope = float(ema_fast.iloc[-1] - ema_fast.iloc[-2])
    return cross_flag, fast_slope
