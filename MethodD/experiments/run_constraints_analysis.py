"""
约束条件分析演示：财报窗口、融券利率等
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from datetime import datetime, timedelta

# 导入约束条件模块
from src.data.constraints_filter import (
    EarningsWindowFilter, 
    BorrowRateFilter, 
    ConstraintsAnalyzer
)


def main():
    """主演示函数"""
    print("=" * 80)
    print("IV 收敛因子约束条件分析")
    print("=" * 80)
    print()
    
    # 第一步：财报窗口分析
    print("【第一步】财报窗口分析")
    print("-" * 80)
    
    ticker = 'NVDA'
    earnings_info = EarningsWindowFilter.get_earnings_window_info(ticker)
    
    print(f"股票代码: {ticker}")
    print(f"下一个财报日期: {earnings_info['next_earnings']}")
    print()
    
    print("财报窗口列表（前 3 日 + 后 2 日）:")
    for i, window in enumerate(earnings_info['windows'], 1):
        print(f"  {i}. 财报日期: {window['earnings_date'].strftime('%Y-%m-%d')}")
        print(f"     窗口: {window['window_start'].strftime('%Y-%m-%d')} ~ {window['window_end'].strftime('%Y-%m-%d')}")
        print(f"     距离: {window['days_to_earnings']} 天")
    print()
    
    # 第二步：融券利率分析
    print("【第二步】融券利率分析")
    print("-" * 80)
    
    tickers = ['NVDA', 'AAPL', 'TSLA', 'AMD', 'MSFT', 'GOOGL']
    borrow_rate_info = BorrowRateFilter.get_borrow_rate_info(tickers)
    
    print("融券利率信息:")
    print(borrow_rate_info.to_string(index=False))
    print()
    
    # 筛选融券利率 < 2% 的股票
    eligible_tickers = BorrowRateFilter.filter_by_borrow_rate(tickers, max_rate=0.02)
    print(f"融券利率 < 2% 的股票（适合做空）: {', '.join(eligible_tickers)}")
    print()
    
    # 第三步：综合约束条件分析
    print("【第三步】综合约束条件分析")
    print("-" * 80)
    
    start_date = '2025-01-01'
    end_date = '2025-03-31'
    
    constraints = ConstraintsAnalyzer.analyze_constraints(ticker, start_date, end_date)
    
    print(f"分析期间: {constraints['period']}")
    print(f"总交易日: {constraints['total_days']}")
    print(f"可交易日: {constraints['trading_days']}")
    print(f"被过滤日: {constraints['filtered_days']}")
    print(f"过滤比例: {constraints['filter_ratio']}")
    print()
    
    print(f"融券利率: {constraints['borrow_rate']}")
    print(f"适合做空: {'是' if constraints['eligible_for_short'] else '否'}")
    print()
    
    # 第四步：关键发现
    print("【第四步】关键发现")
    print("=" * 80)
    print()
    
    print("1. 财报窗口影响:")
    print(f"   - 财报前后 5 天内需要剔除信号")
    print(f"   - 本期间内有 {len(earnings_info['windows'])} 个财报窗口")
    print(f"   - 被过滤的交易日占比: {constraints['filter_ratio']}")
    print()
    
    print("2. 融券利率约束:")
    print(f"   - {ticker} 融券利率: {constraints['borrow_rate']}")
    print(f"   - 做空成本: {'低（< 2%）' if constraints['eligible_for_short'] else '高（>= 2%）'}")
    print()
    
    print("3. 策略建议:")
    if constraints['eligible_for_short']:
        print(f"   - {ticker} 适合做空策略")
    else:
        print(f"   - {ticker} 融券利率较高，做空成本大")
    
    print(f"   - 避开财报窗口: {[w['earnings_date'].strftime('%Y-%m-%d') for w in earnings_info['windows']]}")
    print()
    
    print("=" * 80)
    print("分析完成！")
    print("=" * 80)


if __name__ == '__main__':
    main()
