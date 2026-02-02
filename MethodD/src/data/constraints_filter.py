"""
约束条件过滤器：财报窗口、融券利率等
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple


class EarningsWindowFilter:
    """财报窗口过滤器"""

    @staticmethod
    def _load_earnings_calendar() -> pd.DataFrame:
        """读取本地财报日历（Demo 样例）"""
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "earnings_calendar.csv",
        )
        if os.path.exists(data_path):
            return pd.read_csv(data_path, parse_dates=["earnings_date"])
        return pd.DataFrame(columns=["ticker", "earnings_date"])

    @staticmethod
    def get_earnings_dates(ticker: str) -> List[datetime]:
        """
        获取财报日期（模拟实现）

        参数:
            ticker: 股票代码

        返回:
            List: 财报日期列表
        """
        # 优先读取本地 Demo 样例（可追溯）
        calendar_df = EarningsWindowFilter._load_earnings_calendar()
        if not calendar_df.empty:
            filtered = calendar_df[calendar_df["ticker"] == ticker]
            return filtered["earnings_date"].dt.to_pydatetime().tolist()

        # 回退：模拟数据
        earnings_calendar = {
            "NVDA": [
                datetime(2025, 1, 22),
                datetime(2025, 4, 16),
                datetime(2025, 7, 23),
                datetime(2025, 10, 22),
            ],
            "AAPL": [
                datetime(2025, 1, 29),
                datetime(2025, 4, 30),
                datetime(2025, 7, 30),
                datetime(2025, 10, 29),
            ],
        }
        return earnings_calendar.get(ticker, [])

    @staticmethod
    def filter_earnings_window(
        dates: pd.DatetimeIndex, ticker: str, window_days: int = 5
    ) -> pd.DatetimeIndex:
        """
        过滤财报窗口内的日期（前 3 日 + 后 2 日）

        参数:
            dates: 日期索引
            ticker: 股票代码
            window_days: 窗口天数（默认 5 = 前 3 + 后 2）

        返回:
            DatetimeIndex: 过滤后的日期
        """
        earnings_dates = EarningsWindowFilter.get_earnings_dates(ticker)

        # 创建过滤掩码
        mask = pd.Series(True, index=dates)

        for earnings_date in earnings_dates:
            # 财报前 3 日 + 后 2 日
            start = earnings_date - timedelta(days=3)
            end = earnings_date + timedelta(days=2)

            # 标记为 False（过滤掉）
            window_mask = (dates >= start) & (dates <= end)
            mask[window_mask] = False

        return dates[mask]

    @staticmethod
    def get_earnings_window_info(ticker: str) -> Dict:
        """获取财报窗口信息"""
        earnings_dates = EarningsWindowFilter.get_earnings_dates(ticker)

        windows = []
        for earnings_date in earnings_dates:
            start = earnings_date - timedelta(days=3)
            end = earnings_date + timedelta(days=2)
            windows.append(
                {
                    "earnings_date": earnings_date,
                    "window_start": start,
                    "window_end": end,
                    "days_to_earnings": (earnings_date - datetime.now()).days,
                }
            )

        return {
            "ticker": ticker,
            "next_earnings": earnings_dates[0] if earnings_dates else None,
            "windows": windows,
        }


class BorrowRateFilter:
    """融券利率过滤器"""

    @staticmethod
    def _load_borrow_rates() -> pd.DataFrame:
        """读取本地融券利率（Demo 样例）"""
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "short_borrow_rates.csv",
        )
        if os.path.exists(data_path):
            return pd.read_csv(data_path)
        return pd.DataFrame(columns=["ticker", "borrow_rate"])

    @staticmethod
    def get_borrow_rates(tickers: List[str]) -> Dict[str, float]:
        """
        获取融券利率（模拟实现）

        参数:
            tickers: 股票代码列表

        返回:
            Dict: 股票代码 -> 融券利率
        """
        # 优先读取本地 Demo 样例（可追溯）
        borrow_df = BorrowRateFilter._load_borrow_rates()
        if not borrow_df.empty:
            rates = borrow_df.set_index("ticker")["borrow_rate"].to_dict()
        else:
            # 回退：模拟数据
            rates = {
                "NVDA": 0.015,  # 1.5%
                "AAPL": 0.008,  # 0.8%
                "TSLA": 0.025,  # 2.5%
                "AMD": 0.018,  # 1.8%
                "MSFT": 0.010,  # 1.0%
                "GOOGL": 0.012,  # 1.2%
            }

        result = {}
        for ticker in tickers:
            result[ticker] = rates.get(ticker, 0.02)  # 默认 2%

        return result

    @staticmethod
    def filter_by_borrow_rate(tickers: List[str], max_rate: float = 0.02) -> List[str]:
        """
        按融券利率过滤（< 2%）

        参数:
            tickers: 股票代码列表
            max_rate: 最大融券利率（默认 2%）

        返回:
            List: 符合条件的股票代码
        """
        borrow_rates = BorrowRateFilter.get_borrow_rates(tickers)

        filtered = []
        for ticker, rate in borrow_rates.items():
            if rate < max_rate:
                filtered.append(ticker)

        return filtered

    @staticmethod
    def get_borrow_rate_info(tickers: List[str]) -> pd.DataFrame:
        """获取融券利率信息"""
        borrow_rates = BorrowRateFilter.get_borrow_rates(tickers)

        data = []
        for ticker, rate in borrow_rates.items():
            data.append(
                {
                    "ticker": ticker,
                    "borrow_rate": rate,
                    "borrow_rate_pct": f"{rate:.2%}",
                    "eligible_for_short": rate < 0.02,
                }
            )

        return pd.DataFrame(data)


class ConstraintsAnalyzer:
    """约束条件分析器"""

    @staticmethod
    def analyze_constraints(ticker: str, start_date: str, end_date: str) -> Dict:
        """
        分析约束条件对交易的影响

        参数:
            ticker: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        返回:
            Dict: 约束条件分析结果
        """
        # 生成日期范围
        dates = pd.date_range(start=start_date, end=end_date, freq="D")

        # 财报窗口过滤
        earnings_info = EarningsWindowFilter.get_earnings_window_info(ticker)
        filtered_dates = EarningsWindowFilter.filter_earnings_window(dates, ticker)

        # 融券利率检查
        borrow_rate = BorrowRateFilter.get_borrow_rates([ticker])[ticker]
        eligible_for_short = borrow_rate < 0.02

        # 计算统计信息
        total_days = len(dates)
        trading_days = len(filtered_dates)
        filtered_days = total_days - trading_days

        return {
            "ticker": ticker,
            "period": f"{start_date} to {end_date}",
            "total_days": total_days,
            "trading_days": trading_days,
            "filtered_days": filtered_days,
            "filter_ratio": f"{filtered_days / total_days:.1%}",
            "earnings_info": earnings_info,
            "borrow_rate": f"{borrow_rate:.2%}",
            "eligible_for_short": eligible_for_short,
            "next_earnings": earnings_info["next_earnings"],
            "days_to_next_earnings": (
                earnings_info["next_earnings"] - datetime.now()
            ).days
            if earnings_info["next_earnings"]
            else None,
        }
