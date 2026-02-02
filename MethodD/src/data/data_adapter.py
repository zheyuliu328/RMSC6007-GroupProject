"""
数据适配器：对接外部数据源并标准化输出
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import yfinance as yf


class DataAdapter:
    """数据源适配器接口"""

    def __init__(self, start_date: str = "2020-01-01", end_date: str = "2025-01-01"):
        self.start_date = start_date
        self.end_date = end_date

    def download_stock_prices(self, tickers: List[str]) -> pd.DataFrame:
        """
        下载正股价格

        参数:
            tickers: 股票代码列表

        返回:
            DataFrame: 调整后收盘价，索引为日期，列为股票代码
        """
        try:
            data = yf.download(
                tickers, start=self.start_date, end=self.end_date, progress=False
            )
            if len(tickers) == 1:
                return data[["Adj Close"]].rename(columns={"Adj Close": tickers[0]})
            else:
                return data["Adj Close"]
        except Exception as e:
            print(f"Error downloading stock prices: {e}")
            return pd.DataFrame()

    def generate_synthetic_iv(
        self, prices: pd.DataFrame, base_iv: float = 0.20
    ) -> pd.DataFrame:
        """
        生成合成 IV 数据（用于演示）

        参数:
            prices: 股票价格 DataFrame
            base_iv: 基础 IV 水平

        返回:
            DataFrame: IV 时间序列
        """
        np.random.seed(42)
        iv_data = pd.DataFrame(index=prices.index)

        for col in prices.columns:
            # 生成随机游走的 IV
            returns = prices[col].pct_change().fillna(0)
            volatility = returns.rolling(20).std() * np.sqrt(252)

            # 添加均值回归和随机噪声
            iv = base_iv + 0.1 * volatility + 0.05 * np.random.randn(len(prices))
            iv = np.maximum(iv, 0.05)  # 确保 IV > 0
            iv_data[col] = iv

        return iv_data


class DataValidator:
    """数据质量检查"""

    @staticmethod
    def check_missing_data(data: pd.DataFrame, max_consecutive: int = 5) -> Dict:
        """检查缺失数据"""
        result = {
            "total_missing": data.isnull().sum().sum(),
            "missing_by_column": data.isnull().sum().to_dict(),
            "max_consecutive_missing": 0,
        }

        for col in data.columns:
            consecutive = (data[col].isnull().astype(int).diff() != 0).cumsum()
            max_cons = data[col].isnull().groupby(consecutive).sum().max()
            result["max_consecutive_missing"] = max(
                result["max_consecutive_missing"], max_cons
            )

        return result

    @staticmethod
    def check_outliers(data: pd.DataFrame, threshold: float = 5.0) -> Dict:
        """检查异常值（5-sigma 规则）"""
        result = {}
        for col in data.columns:
            mean = data[col].mean()
            std = data[col].std()
            outliers = ((data[col] - mean).abs() > threshold * std).sum()
            result[col] = outliers
        return result
