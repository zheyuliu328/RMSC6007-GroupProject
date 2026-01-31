"""
因子定义：IV 收敛因子的两个版本
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


class IVFactorDefinition:
    """IV 因子定义"""
    
    @staticmethod
    def compute_factor_version_a(iv_series: pd.Series, window: int = 10) -> pd.Series:
        """
        Version A（聊天版）：简单标准化
        f_t = (IV_t - median(IV_{t-window..t})) / median(IV_{t-window..t})
        """
        median_iv = iv_series.rolling(window=window, min_periods=1).median()
        factor = (iv_series - median_iv) / (median_iv + 1e-8)
        return factor
    
    @staticmethod
    def compute_factor_version_b(iv_series: pd.Series, window: int = 10) -> pd.Series:
        """
        Version B（研究版稳健标准化）：使用 MAD（中位绝对偏差）
        z_t = (IV_t - median(IV_{t-window..t})) / MAD(IV_{t-window..t})
        其中 MAD = median(|x - median(x)|)
        """
        def mad(x):
            """计算中位绝对偏差"""
            median = np.median(x)
            return np.median(np.abs(x - median))
        
        median_iv = iv_series.rolling(window=window, min_periods=1).median()
        mad_iv = iv_series.rolling(window=window, min_periods=1).apply(mad, raw=True)
        
        factor = (iv_series - median_iv) / (mad_iv + 1e-8)
        return factor
    
    @staticmethod
    def compute_both_versions(iv_series: pd.Series, window: int = 10) -> pd.DataFrame:
        """计算两个版本的因子"""
        factor_a = IVFactorDefinition.compute_factor_version_a(iv_series, window)
        factor_b = IVFactorDefinition.compute_factor_version_b(iv_series, window)
        
        return pd.DataFrame({
            'factor_a': factor_a,
            'factor_b': factor_b
        })


class FactorBucketizer:
    """因子分组：按分位数分组"""
    
    @staticmethod
    def bucketize_by_quantile(factor_series: pd.Series, n_buckets: int = 5) -> pd.Series:
        """
        按分位数分组
        
        参数:
            factor_series: 因子序列
            n_buckets: 分组数量
            
        返回:
            Series: 分组标签（0 到 n_buckets-1）
        """
        return pd.qcut(factor_series, q=n_buckets, labels=False, duplicates='drop')
    
    @staticmethod
    def get_top_bottom_signals(factor_series: pd.Series, n_buckets: int = 5) -> Dict:
        """
        获取 Top 和 Bottom 分组的信号
        
        返回:
            Dict: {'top': top_indices, 'bottom': bottom_indices}
        """
        buckets = FactorBucketizer.bucketize_by_quantile(factor_series, n_buckets)
        
        top_indices = buckets[buckets == n_buckets - 1].index
        bottom_indices = buckets[buckets == 0].index
        
        return {
            'top': top_indices,
            'bottom': bottom_indices
        }


class FactorNeutralizer:
    """因子中性化（可选）"""
    
    @staticmethod
    def neutralize_by_market_cap(factor_series: pd.Series, 
                                 market_cap: pd.Series) -> pd.Series:
        """
        按市值中性化因子
        
        参数:
            factor_series: 因子序列
            market_cap: 市值序列
            
        返回:
            Series: 中性化后的因子
        """
        # 简单的线性回归中性化
        from sklearn.linear_model import LinearRegression
        
        X = np.log(market_cap.values).reshape(-1, 1)
        y = factor_series.values
        
        model = LinearRegression()
        model.fit(X, y)
        residuals = y - model.predict(X)
        
        return pd.Series(residuals, index=factor_series.index)
