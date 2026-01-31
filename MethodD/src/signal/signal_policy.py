"""
信号生成策略：从因子生成交易信号
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


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


class EarningsWindowFilter:
    """财报窗口过滤器"""
    
    @staticmethod
    def filter_earnings_window(signal_series: pd.Series, 
                              earnings_dates: List[pd.Timestamp],
                              window_days: int = 2) -> pd.Series:
        """
        在财报日期前后 window_days 天内过滤信号
        
        参数:
            signal_series: 原始信号序列
            earnings_dates: 财报日期列表
            window_days: 窗口天数
            
        返回:
            Series: 过滤后的信号
        """
        filtered_signal = signal_series.copy()
        
        for earnings_date in earnings_dates:
            # 财报前后 window_days 天
            start = earnings_date - pd.Timedelta(days=window_days)
            end = earnings_date + pd.Timedelta(days=window_days)
            
            # 在这个窗口内设置信号为 0
            mask = (filtered_signal.index >= start) & (filtered_signal.index <= end)
            filtered_signal[mask] = 0
        
        return filtered_signal


class SignalProcessor:
    """信号处理器：生成最终交易信号"""
    
    def __init__(self, holding_period: int = 5, 
                 filter_earnings: bool = True):
        self.holding_period = holding_period
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
