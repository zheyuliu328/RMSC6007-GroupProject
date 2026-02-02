"""
信号生成策略：从因子生成交易信号
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


class SignalPolicy:
    """信号生成策略"""
    
    @staticmethod
    def threshold_strategy(factor_series: pd.Series, 
                          long_threshold: float = -0.15,
                          short_threshold: float = 0.15) -> pd.Series:
        """
        阈值策略：
        - factor < long_threshold: 做多信号 (1)
        - factor > short_threshold: 做空信号 (-1)
        - 否则: 无信号 (0)
        """
        signal = pd.Series(0, index=factor_series.index, dtype=int)
        signal[factor_series < long_threshold] = 1
        signal[factor_series > short_threshold] = -1
        return signal

    @staticmethod
    def build_trade_plan(signal_series: pd.Series) -> pd.Series:
        """
        根据信号生成交易动作说明

        规则:
            1: 做多正股 + 卖出平值 call（覆盖式卖出）
           -1: 做空正股 + 买入平值 put
            0: 无交易
        """
        plan = pd.Series('观望', index=signal_series.index)
        plan[signal_series == 1] = '做多正股+卖出平值call'
        plan[signal_series == -1] = '做空正股+买入平值put'
        return plan

    @staticmethod
    def quantile_strategy(factor_series: pd.Series,
                          n_buckets: int = 5) -> pd.Series:
        """
        分位数策略：
        - Top 分位数: 做空信号 (-1)
        - Bottom 分位数: 做多信号 (1)
        - 中间: 无信号 (0)
        """
        buckets = pd.qcut(factor_series, q=n_buckets, labels=False, duplicates='drop')

        signal = pd.Series(0, index=factor_series.index, dtype=int)
        signal[buckets == 0] = 1  # Bottom: 做多
        signal[buckets == n_buckets - 1] = -1  # Top: 做空

        return signal


@dataclass
class TripleGateConfig:
    """三重门控信号配置"""

    iv_thr: float = 0.15
    ma_thr: float = 1.0
    bb_pos_thr: float = 1.0
    bb_bw_thr: float = 0.04
    use_bb_bw_filter: bool = False


def compute_triple_gate_signal(row: pd.Series, config: TripleGateConfig) -> pd.Series:
    """
    三重门控信号计算（run 级）

    规则:
        1) IV 触发：iv_signal_median10 >= iv_thr
        2) MA200 方向：ma200_break_t0 >= ma_thr 或 <= -ma_thr
        3) MACD 交叉：macd_cross_flag 与 ma200 方向一致
        4) BB 中线突破：bb_midline_break_flag=1 且 bb_break_side 与方向一致
        5) 可选带宽过滤：bb_bw_t0 >= bb_bw_thr

    返回:
        Series: signal_flag, signal_side
    """
    iv_signal = row.get('iv_signal_median10', row.get('iv_signal'))
    ma_break = row.get('ma200_break_t0')
    bb_pos = row.get('bb_pos_t0')
    bb_bw = row.get('bb_bw_t0')
    macd_cross = row.get('macd_cross_flag')
    bb_mid_flag = row.get('bb_midline_break_flag')
    bb_break_side = row.get('bb_break_side')

    if pd.isna(iv_signal) or pd.isna(ma_break):
        return pd.Series({'signal_flag': 0, 'signal_side': 0})

    iv_trigger = float(iv_signal) >= config.iv_thr
    ma_long = float(ma_break) >= config.ma_thr
    ma_short = float(ma_break) <= -config.ma_thr
    bb_long = float(bb_pos) >= config.bb_pos_thr if pd.notna(bb_pos) else False
    bb_short = float(bb_pos) <= -config.bb_pos_thr if pd.notna(bb_pos) else False
    macd_long = pd.notna(macd_cross) and int(macd_cross) == 1
    macd_short = pd.notna(macd_cross) and int(macd_cross) == -1
    bb_mid_ok = pd.notna(bb_mid_flag) and int(bb_mid_flag) == 1
    bb_mid_long = bb_mid_ok and pd.notna(bb_break_side) and int(bb_break_side) == 1
    bb_mid_short = bb_mid_ok and pd.notna(bb_break_side) and int(bb_break_side) == -1

    bb_bw_ok = True
    if config.use_bb_bw_filter:
        if pd.isna(bb_bw):
            bb_bw_ok = False
        else:
            bb_bw_ok = float(bb_bw) >= config.bb_bw_thr

    long_cond = iv_trigger and ma_long and macd_long and bb_mid_long and bb_bw_ok
    short_cond = iv_trigger and ma_short and macd_short and bb_mid_short and bb_bw_ok

    if long_cond:
        return pd.Series({'signal_flag': 1, 'signal_side': 1})
    if short_cond:
        return pd.Series({'signal_flag': 1, 'signal_side': -1})
    return pd.Series({'signal_flag': 0, 'signal_side': 0})


def apply_triple_gate_signals(run_df: pd.DataFrame,
                              config: TripleGateConfig) -> pd.DataFrame:
    """
    在 run 级表上批量计算三重门控信号

    参数:
        run_df: run 级 DataFrame（含 iv_signal_median10、ma200_break_t0、macd_cross_flag、bb_midline_break_flag）
        config: TripleGateConfig

    返回:
        DataFrame: signal_flag, signal_side
    """
    if run_df is None or run_df.empty:
        return pd.DataFrame(columns=['signal_flag', 'signal_side'])
    signals = run_df.apply(lambda row: compute_triple_gate_signal(row, config), axis=1)
    return signals


class EarningsWindowFilter:
    """财报窗口过滤器"""
    
    @staticmethod
    def filter_earnings_window(signal_series: pd.Series, 
                              earnings_dates: List[pd.Timestamp],
                              pre_days: int = 3,
                              post_days: int = 2) -> pd.Series:
        """
        在财报日期前 3 日 + 后 2 日内过滤信号
        
        参数:
            signal_series: 原始信号序列
            earnings_dates: 财报日期列表
            pre_days: 财报前过滤天数
            post_days: 财报后过滤天数
            
        返回:
            Series: 过滤后的信号
        """
        filtered_signal = signal_series.copy()
        
        for earnings_date in earnings_dates:
            # 财报前 3 日 + 后 2 日
            start = earnings_date - pd.Timedelta(days=pre_days)
            end = earnings_date + pd.Timedelta(days=post_days)
            
            # 在这个窗口内设置信号为 0
            mask = (filtered_signal.index >= start) & (filtered_signal.index <= end)
            filtered_signal[mask] = 0
        
        return filtered_signal


class SignalProcessor:
    """信号处理器：生成最终交易信号"""
    
    def __init__(self, holding_period: int = 7, 
                 filter_earnings: bool = True):
        self.holding_period = min(holding_period, 7)
        self.filter_earnings = filter_earnings
    
    def generate_signals(self, factor_series: pd.Series,
                        strategy: str = 'threshold',
                        earnings_dates: List[pd.Timestamp] = None) -> pd.Series:
        """
        生成交易信号
        
        参数:
            factor_series: 因子序列
            strategy: 策略类型 ('threshold' 或 'quantile')
            earnings_dates: 财报日期列表
            
        返回:
            Series: 交易信号
        """
        if strategy == 'threshold':
            signal = SignalPolicy.threshold_strategy(factor_series)
        elif strategy == 'quantile':
            signal = SignalPolicy.quantile_strategy(factor_series)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # 应用财报窗口过滤
        if self.filter_earnings and earnings_dates:
            signal = EarningsWindowFilter.filter_earnings_window(signal, earnings_dates)
        
        return signal
