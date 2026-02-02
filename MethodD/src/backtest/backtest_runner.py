"""
回测引擎：执行交易信号回测
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


class BacktestRunner:
    """回测引擎"""

    def __init__(
        self, initial_capital: float = 100000, transaction_cost: float = 0.001
    ):
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost

    def run_backtest(
        self, prices: pd.DataFrame, signals: pd.DataFrame, holding_period: int = 5
    ) -> Dict:
        """
        运行回测

        参数:
            prices: 股票价格 DataFrame
            signals: 交易信号 DataFrame
            holding_period: 持有期

        返回:
            Dict: 回测结果
        """
        # 初始化
        portfolio_value = [self.initial_capital]
        positions = {}
        trades = []

        # 逐日回测
        for i in range(len(prices)):
            date = prices.index[i]

            # 处理持有期到期的头寸
            for symbol in list(positions.keys()):
                entry_date, entry_price, signal = positions[symbol]
                days_held = (date - entry_date).days

                if days_held >= holding_period:
                    # 平仓
                    exit_price = prices.loc[date, symbol]
                    pnl = (exit_price - entry_price) * signal
                    trades.append(
                        {
                            "date": date,
                            "symbol": symbol,
                            "entry_price": entry_price,
                            "exit_price": exit_price,
                            "pnl": pnl,
                            "signal": signal,
                        }
                    )
                    del positions[symbol]

            # 处理新信号
            if i < len(signals):
                for symbol in signals.columns:
                    signal = signals.iloc[i][symbol]
                    if signal != 0 and symbol not in positions:
                        entry_price = prices.loc[date, symbol]
                        positions[symbol] = (date, entry_price, signal)

            # 计算组合价值
            current_value = self.initial_capital
            for symbol, (entry_date, entry_price, signal) in positions.items():
                current_price = prices.loc[date, symbol]
                current_value += (current_price - entry_price) * signal

            portfolio_value.append(current_value)

        # 计算回测指标
        returns = pd.Series(portfolio_value).pct_change().dropna()

        result = {
            "portfolio_value": portfolio_value,
            "trades": trades,
            "total_return": (portfolio_value[-1] - self.initial_capital)
            / self.initial_capital,
            "annual_return": returns.mean() * 252,
            "annual_volatility": returns.std() * np.sqrt(252),
            "sharpe_ratio": (returns.mean() * 252) / (returns.std() * np.sqrt(252))
            if returns.std() > 0
            else 0,
            "max_drawdown": self._calculate_max_drawdown(portfolio_value),
            "num_trades": len(trades),
        }

        return result

    @staticmethod
    def _calculate_max_drawdown(portfolio_values: list) -> float:
        """计算最大回撤"""
        cummax = np.maximum.accumulate(portfolio_values)
        drawdown = (np.array(portfolio_values) - cummax) / cummax
        return np.min(drawdown)
