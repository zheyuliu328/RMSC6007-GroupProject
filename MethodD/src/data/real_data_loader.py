"""
真实数据加载器：从 Yahoo Finance 获取 ATM 30D IV 和期权链数据
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import warnings
import time

warnings.filterwarnings('ignore')


class RealIVDataLoader:
    """从 Yahoo Finance 获取真实 IV 数据"""
    
    @staticmethod
    def get_atm_iv_history(ticker: str, start_date: str, end_date: str, 
                           target_dte: int = 30) -> pd.DataFrame:
        """
        获取 ATM 30D IV 历史数据
        
        参数:
            ticker: 股票代码（如 'NVDA'）
            start_date: 开始日期
            end_date: 结束日期
            target_dte: 目标到期天数（默认 30）
            
        返回:
            DataFrame: 包含日期、收盘价、ATM IV 的数据
        """
        # 获取股票价格数据
        stock_data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if stock_data.empty:
            raise ValueError(f"无法获取 {ticker} 的数据")
        
        # 初始化 IV 列
        iv_data = pd.DataFrame(index=stock_data.index)
        iv_data['close'] = stock_data['Close']
        iv_data['iv_atm_30d'] = np.nan
        
        # 对于每个交易日，尝试获取期权链数据
        for date in stock_data.index:
            try:
                # 获取该日期的期权链
                ticker_obj = yf.Ticker(ticker)
                
                # 获取可用的到期日期
                expirations = ticker_obj.options
                if not expirations:
                    continue
                
                # 找到最接近 target_dte 的到期日期
                target_expiration = None
                min_diff = float('inf')
                
                for exp in expirations:
                    exp_date = pd.to_datetime(exp)
                    dte = (exp_date - date).days
                    
                    if 20 <= dte <= 40:  # 允许 20-40 天的范围
                        diff = abs(dte - target_dte)
                        if diff < min_diff:
                            min_diff = diff
                            target_expiration = exp
                
                if target_expiration is None:
                    continue
                
                # 获取该到期日期的期权链
                opt_chain = ticker_obj.option_chain(target_expiration)
                calls = opt_chain.calls
                
                if calls.empty:
                    continue
                
                # 找到 ATM call（行权价最接近当前价格）
                current_price = stock_data.loc[date, 'Close']
                calls['strike_diff'] = abs(calls['strike'] - current_price)
                atm_call = calls.loc[calls['strike_diff'].idxmin()]
                
                # 提取 IV（隐含波动率）
                if not pd.isna(atm_call['impliedVolatility']):
                    iv_data.loc[date, 'iv_atm_30d'] = atm_call['impliedVolatility']
                    
            except Exception as e:
                # 如果获取失败，继续下一个日期
                continue
        
        # 前向填充缺失的 IV 值
        iv_data['iv_atm_30d'] = iv_data['iv_atm_30d'].ffill(limit=5)
        
        # 如果仍有缺失值，使用后向填充
        iv_data['iv_atm_30d'] = iv_data['iv_atm_30d'].bfill()
        
        return iv_data.dropna()
    
    @staticmethod
    def get_option_chain_snapshot(ticker: str, expiration: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        获取特定到期日期的期权链快照
        
        参数:
            ticker: 股票代码
            expiration: 到期日期（格式：'YYYY-MM-DD'）
            
        返回:
            Tuple: (calls DataFrame, puts DataFrame)
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            opt_chain = ticker_obj.option_chain(expiration)
            return opt_chain.calls, opt_chain.puts
        except Exception as e:
            print(f"获取期权链失败: {e}")
            return pd.DataFrame(), pd.DataFrame()


def _normalize_chain(df: pd.DataFrame, expiry: str, option_type: str) -> pd.DataFrame:
    """统一期权链字段口径"""
    if df is None or df.empty:
        return pd.DataFrame(columns=['expiry', 'strike', 'bid', 'ask', 'last', 'iv', 'contractSymbol', 'optionType'])

    normalized = df.copy()
    normalized['expiry'] = expiry
    normalized['optionType'] = option_type
    rename_map = {
        'lastPrice': 'last',
        'impliedVolatility': 'iv'
    }
    normalized = normalized.rename(columns=rename_map)
    columns = ['expiry', 'strike', 'bid', 'ask', 'last', 'iv', 'contractSymbol', 'optionType']
    for col in columns:
        if col not in normalized.columns:
            normalized[col] = np.nan
    return normalized[columns]


def _should_retry(error: Exception) -> bool:
    """判断是否需要重试（针对第三方 API 错误）"""
    message = str(error)
    retry_flags = ['502', '500', '503', '429', 'Bad Gateway', 'Service Unavailable', 'Too Many Requests']
    return any(flag in message for flag in retry_flags)


def fetch_nvda_option_chain(ticker: str = 'NVDA') -> Dict[str, object]:
    """抓取 NVDA 期权链快照与现价（统一字段输出）"""
    retry_schedule = [5, 10, 20, 30]
    attempt = 0

    while True:
        try:
            ticker_obj = yf.Ticker(ticker)
            spot_df = ticker_obj.history(period='1d', interval='1d')
            if spot_df.empty:
                raise ValueError(f"无法获取 {ticker} 现价")
            spot_price = float(spot_df['Close'].iloc[-1])

            expirations = ticker_obj.options
            if not expirations:
                raise ValueError(f"{ticker} 没有可用到期日")

            chain_frames = []
            for exp in expirations:
                chain = ticker_obj.option_chain(exp)
                calls = _normalize_chain(chain.calls, exp, 'call')
                puts = _normalize_chain(chain.puts, exp, 'put')
                chain_frames.extend([calls, puts])

            chain_df = pd.concat(chain_frames, ignore_index=True)
            snapshot_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            return {
                'ticker': ticker,
                'spot': spot_price,
                'timestamp': snapshot_time,
                'chain': chain_df
            }
        except Exception as e:
            if not _should_retry(e):
                raise
            wait_seconds = retry_schedule[attempt] if attempt < len(retry_schedule) else 60
            time.sleep(wait_seconds)
            attempt += 1


def load_snapshot(path: str) -> Dict[str, object]:
    """读取本地快照文件并统一字段"""
    if path.endswith('.json'):
        data = pd.read_json(path, typ='series').to_dict()
        if isinstance(data.get('chain'), list):
            data['chain'] = pd.DataFrame(data.get('chain', []))
        meta = data.get('meta') or {}
        if not data.get('timestamp') and meta.get('captured_at_utc'):
            data['timestamp'] = meta.get('captured_at_utc')
        if not data.get('ticker') and meta.get('ticker'):
            data['ticker'] = meta.get('ticker')
        return data

    if path.endswith('.csv'):
        chain_df = pd.read_csv(path)
        return {'chain': chain_df}

    raise ValueError(f"不支持的快照格式: {path}")


class CoveredCallPnLCalculator:
    """覆盖式卖 call 的 PnL 计算"""
    
    @staticmethod
    def calculate_covered_call_pnl(
        entry_price: float,
        exit_price: float,
        call_premium_received: float,
        call_premium_paid: float,
        strike_price: float,
        shares: int = 100
    ) -> Dict:
        """
        计算覆盖式卖 call 的完整 PnL
        
        参数:
            entry_price: 正股买入价格
            exit_price: 正股卖出价格
            call_premium_received: 卖出 call 收到的权利金
            call_premium_paid: 平仓 call 支付的权利金
            strike_price: call 行权价
            shares: 股数（默认 100）
            
        返回:
            Dict: 包含各项 PnL 的字典
        """
        # 正股 PnL
        stock_pnl = (exit_price - entry_price) * shares
        
        # 期权 PnL（权利金差价，按每股）
        option_pnl = (call_premium_received - call_premium_paid) * shares
        
        # 总 PnL
        total_pnl = stock_pnl + option_pnl
        
        # 上行封顶检查
        max_profit = (strike_price - entry_price) * shares + option_pnl
        is_capped = exit_price > strike_price
        
        return {
            'stock_pnl': stock_pnl,
            'option_pnl': option_pnl,
            'total_pnl': total_pnl,
            'max_profit': max_profit,
            'is_capped': is_capped,
            'stock_return': (exit_price - entry_price) / entry_price,
            'total_return': total_pnl / (entry_price * shares),
            'option_contribution': option_pnl / total_pnl if total_pnl != 0 else 0,
            'option_price_close': call_premium_paid
        }
    
    @staticmethod
    def simulate_three_scenarios(
        entry_price: float,
        call_premium_received: float,
        strike_price: float,
        iv_entry: float,
        iv_exit: float,
        shares: int = 100
    ) -> Dict:
        """
        模拟三个行情场景：涨、横盘、回调
        
        参数:
            entry_price: 买入价格
            call_premium_received: 卖出 call 收到的权利金
            strike_price: call 行权价
            iv_entry: 买入时 IV
            iv_exit: 平仓时 IV
            shares: 股数
            
        返回:
            Dict: 三个场景的 PnL 结果
        """
        from src.pricing.bs_pricer import BlackScholesOption
        
        results = {}
        
        # 场景 1：涨（+3.1%）
        exit_price_up = entry_price * 1.031
        call_premium_paid_up = BlackScholesOption.call_price(
            S=exit_price_up, K=strike_price, T=5/252, r=0.02, sigma=iv_exit
        ) / 100
        
        results['scenario_1_up'] = CoveredCallPnLCalculator.calculate_covered_call_pnl(
            entry_price=entry_price,
            exit_price=exit_price_up,
            call_premium_received=call_premium_received,
            call_premium_paid=call_premium_paid_up,
            strike_price=strike_price,
            shares=shares
        )
        
        # 场景 2：横盘
        exit_price_flat = entry_price
        call_premium_paid_flat = BlackScholesOption.call_price(
            S=exit_price_flat, K=strike_price, T=5/252, r=0.02, sigma=iv_exit
        ) / 100
        
        results['scenario_2_flat'] = CoveredCallPnLCalculator.calculate_covered_call_pnl(
            entry_price=entry_price,
            exit_price=exit_price_flat,
            call_premium_received=call_premium_received,
            call_premium_paid=call_premium_paid_flat,
            strike_price=strike_price,
            shares=shares
        )
        
        # 场景 3：回调（-2.1%）
        exit_price_down = entry_price * 0.979
        call_premium_paid_down = BlackScholesOption.call_price(
            S=exit_price_down, K=strike_price, T=5/252, r=0.02, sigma=iv_exit
        ) / 100
        
        results['scenario_3_down'] = CoveredCallPnLCalculator.calculate_covered_call_pnl(
            entry_price=entry_price,
            exit_price=exit_price_down,
            call_premium_received=call_premium_received,
            call_premium_paid=call_premium_paid_down,
            strike_price=strike_price,
            shares=shares
        )
        
        return results
