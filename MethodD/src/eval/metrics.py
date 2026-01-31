"""
评估指标：因子和策略评估
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from scipy import stats


class FactorMetrics:
    """因子评估指标"""
    
    @staticmethod
    def calculate_ic(factor_values: pd.Series, 
                     future_returns: pd.Series) -> float:
        """计算信息系数 (Information Coefficient)"""
        valid_idx = ~(factor_values.isna() | future_returns.isna())
        factor_clean = factor_values[valid_idx]
        returns_clean = future_returns[valid_idx]
        
        if len(factor_clean) < 2:
            return 0
        
        ic = stats.spearmanr(factor_clean, returns_clean)[0]
        return ic
    
    @staticmethod
    def calculate_quantile_returns(factor_values: pd.Series,
                                   returns: pd.Series,
                                   n_quantiles: int = 5) -> Dict:
        """计算分位数组合收益"""
        quantiles = pd.qcut(factor_values, q=n_quantiles, labels=False, duplicates='drop')
        
        result = {}
        for q in range(n_quantiles):
            mask = quantiles == q
            avg_return = returns[mask].mean()
            result[f'Q{q+1}'] = avg_return
        
        result['Top-Bottom'] = result[f'Q{n_quantiles}'] - result['Q1']
        return result

    @staticmethod
    def spearman_ic_tstat(factor_values: pd.Series, target_values: pd.Series) -> Dict:
        """计算 Spearman IC 与近似 t-stat（单样本相关系数）"""
        valid_idx = ~(factor_values.isna() | target_values.isna())
        x = factor_values[valid_idx]
        y = target_values[valid_idx]
        n = len(x)
        if n < 3:
            return {'n': n, 'ic': 0.0, 't_stat': 0.0}
        ic = stats.spearmanr(x, y)[0]
        denom = max(1e-8, 1 - ic ** 2)
        t_stat = ic * np.sqrt((n - 2) / denom)
        return {'n': n, 'ic': float(ic), 't_stat': float(t_stat)}

    @staticmethod
    def spearman_ic_block_bootstrap(
        factor_values: pd.Series,
        target_values: pd.Series,
        group_labels: pd.Series,
        n_bootstrap: int = 500,
        random_state: int = 42,
    ) -> Dict:
        """按组 block bootstrap 的 Spearman IC（修正相关结构）"""
        df = pd.DataFrame({
            'factor': factor_values,
            'target': target_values,
            'group': group_labels,
        }).dropna()
        if df.empty or df['group'].nunique() < 2:
            return {
                'n': len(df),
                'n_groups': int(df['group'].nunique()),
                'ic_mean': 0.0,
                'ic_std': 0.0,
                't_stat': 0.0,
            }

        rng = np.random.default_rng(random_state)
        groups = df['group'].dropna().unique().tolist()
        ic_samples = []
        for _ in range(n_bootstrap):
            sampled_groups = rng.choice(groups, size=len(groups), replace=True)
            sampled_df = pd.concat([df[df['group'] == g] for g in sampled_groups], ignore_index=True)
            ic = stats.spearmanr(sampled_df['factor'], sampled_df['target'])[0]
            ic_samples.append(ic if np.isfinite(ic) else 0.0)

        ic_samples = np.array(ic_samples)
        ic_mean = float(np.nanmean(ic_samples))
        ic_std = float(np.nanstd(ic_samples, ddof=1))
        t_stat = float(ic_mean / ic_std) if ic_std > 0 else 0.0
        return {
            'n': len(df),
            'n_groups': len(groups),
            'ic_mean': ic_mean,
            'ic_std': ic_std,
            't_stat': t_stat,
        }

    @staticmethod
    def partial_spearman_ic(
        factor_values: pd.Series,
        target_values: pd.Series,
        controls: Optional[pd.DataFrame] = None,
    ) -> Dict:
        """控制变量后的 Spearman IC（防止替身变量）"""
        if controls is None or controls.empty:
            return FactorMetrics.spearman_ic_tstat(factor_values, target_values)

        df = pd.concat([factor_values, target_values, controls], axis=1).dropna()
        if df.shape[0] < 3:
            return {'n': df.shape[0], 'ic': 0.0, 't_stat': 0.0}

        x = df.iloc[:, 0].astype(float)
        y = df.iloc[:, 1].astype(float)
        control_matrix = df.iloc[:, 2:].astype(float)
        control_matrix = np.column_stack([np.ones(len(control_matrix)), control_matrix.values])

        beta_x, _, _, _ = np.linalg.lstsq(control_matrix, x.values, rcond=None)
        beta_y, _, _, _ = np.linalg.lstsq(control_matrix, y.values, rcond=None)
        x_resid = x.values - control_matrix @ beta_x
        y_resid = y.values - control_matrix @ beta_y

        ic = stats.spearmanr(x_resid, y_resid)[0]
        denom = max(1e-8, 1 - ic ** 2)
        t_stat = ic * np.sqrt((len(x_resid) - 2) / denom)
        return {'n': len(x_resid), 'ic': float(ic), 't_stat': float(t_stat)}

    @staticmethod
    def linear_regression_stats(x: pd.Series, y: pd.Series) -> Dict:
        """线性回归统计（斜率/截距/p 值/相关）"""
        valid_idx = ~(x.isna() | y.isna())
        x_clean = x[valid_idx]
        y_clean = y[valid_idx]
        n = len(x_clean)
        if n < 3 or x_clean.nunique(dropna=True) <= 1:
            return {
                'n': n,
                'beta': 0.0,
                'alpha': 0.0,
                'r_value': 0.0,
                'p_value': 1.0,
                'stderr': 0.0,
            }
        res = stats.linregress(x_clean, y_clean)
        return {
            'n': n,
            'beta': float(res.slope),
            'alpha': float(res.intercept),
            'r_value': float(res.rvalue),
            'p_value': float(res.pvalue),
            'stderr': float(res.stderr),
        }


class StrategyMetrics:
    """策略评估指标"""
    
    @staticmethod
    def calculate_sharpe_ratio(returns: pd.Series, 
                              risk_free_rate: float = 0.02) -> float:
        """计算夏普比率"""
        excess_returns = returns - risk_free_rate / 252
        if excess_returns.std() == 0:
            return 0
        return (excess_returns.mean() * 252) / (excess_returns.std() * np.sqrt(252))
    
    @staticmethod
    def calculate_max_drawdown(returns: pd.Series) -> float:
        """计算最大回撤"""
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        return drawdown.min()
    
    @staticmethod
    def calculate_win_rate(returns: pd.Series) -> float:
        """计算胜率"""
        if len(returns) == 0:
            return 0
        return (returns > 0).sum() / len(returns)
