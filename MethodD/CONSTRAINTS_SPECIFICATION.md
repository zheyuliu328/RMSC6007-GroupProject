# MethodD 约束条件可验证输入说明

## 概述

本文档明确说明 MethodD 项目中使用的约束条件（财报窗口、融券利率等）的定义、数据来源、处理方式，确保约束条件的**可追溯性和可验证性**。

---

## 第一部分：财报窗口约束

### 1.1 财报窗口的定义

**财报窗口**：上市公司发布财报前后的时间段，通常存在较高的波动率和信息不对称。

**定义**：
- **前窗口**：财报发布前 3 个交易日
- **后窗口**：财报发布后 2 个交易日
- **总窗口**：前 3 日 + 发布日 + 后 2 日 = 6 个交易日

**过滤规则**：
- 在财报窗口内的交易日，不进行覆盖式卖 call 操作
- 原因：财报发布可能导致大幅波动，增加风险

### 1.2 财报日期数据来源

**数据来源**：Yahoo Finance 财报日历

**获取方式**：
```python
import yfinance as yf

ticker = yf.Ticker('NVDA')
# 获取财报日期（需要通过 web scraping 或 API）
# Yahoo Finance 不直接提供财报日期 API，需要自建或使用第三方库
```

**替代方案**：
1. **手动维护**：`data/earnings_calendar.csv`
2. **第三方库**：使用 `earnings_dates` 库或 Alpha Vantage API
3. **占位符**：在演示中使用预定义的财报日期

### 1.3 财报日历落盘文件（硬要求）

**文件位置**：`data/earnings_calendar.csv`

**当前状态**：
- ✅ 接口已预留
- ⚠️ Demo 使用静态样例文件（见下表）
- ❌ 不进入研究结论

**Demo 样例文件内容**：
```csv
ticker,earnings_date,fiscal_quarter
NVDA,2025-01-22,Q4 2024
NVDA,2025-04-16,Q1 2025
NVDA,2025-07-16,Q2 2025
NVDA,2025-10-22,Q3 2025
AAPL,2025-01-28,Q1 2025
AAPL,2025-04-30,Q2 2025
...
```

**字段说明**：
- `ticker`：股票代码
- `earnings_date`：财报发布日期（YYYY-MM-DD）
- `fiscal_quarter`：财政季度

**Research 档要求**：
- 数据来源：Yahoo Finance 财报日历 OR SEC EDGAR
- 时间范围：至少 1 年以上
- 验证方式：与官方财报发布日期对齐
- 标注要求：CSV 中添加 `data_source` 列

### 1.4 财报窗口过滤实现

**代码位置**：`src/data/constraints_filter.py`

**关键函数**：
```python
@staticmethod
def is_in_earnings_window(date, ticker, earnings_calendar, 
                          pre_days=3, post_days=2):
    """
    检查日期是否在财报窗口内
    
    参数:
        date: 检查日期
        ticker: 股票代码
        earnings_calendar: 财报日历 DataFrame
        pre_days: 财报前天数（默认 3）
        post_days: 财报后天数（默认 2）
    
    返回:
        bool: 是否在财报窗口内
    """
    # 获取该股票的财报日期
    earnings_dates = earnings_calendar[
        earnings_calendar['ticker'] == ticker
    ]['earnings_date'].values
    
    # 检查是否在任何财报窗口内
    for earnings_date in earnings_dates:
        window_start = earnings_date - timedelta(days=pre_days)
        window_end = earnings_date + timedelta(days=post_days)
        
        if window_start <= date <= window_end:
            return True
    
    return False
```

### 1.5 财报窗口过滤的影响

**演示结果**（NVDA 2025-01-01 ~ 2025-03-31）：

| 指标 | 值 |
|------|-----|
| 总交易日 | 60 |
| 财报窗口内交易日 | 4 |
| 可交易日 | 56 |
| 过滤比例 | 6.7% |

**财报日期**：
- 2025-01-22（Q4 2024）：窗口 2025-01-17 ~ 2025-01-24
- 2025-04-16（Q1 2025）：超出时间范围

---

## 第二部分：融券利率约束

### 2.1 融券利率的定义

**融券利率**：借入股票进行卖空的成本，通常以年化百分比表示。

**关键特征**：
- **高融券利率**：表示股票难以借入，成本高
- **低融券利率**：表示股票容易借入，成本低
- **影响**：融券利率越高，做空策略的成本越高

**过滤规则**：
- 只在融券利率 < 2% 的股票上进行覆盖式卖 call 操作
- 原因：融券利率过高会侵蚀收益

### 2.2 融券利率数据来源

**主要数据源**：

| 数据源 | 说明 | 可得性 |
|------|------|--------|
| **Interactive Brokers** | 专业券商，提供实时融券利率 | 需要账户 |
| **Markit** | 专业数据提供商 | 需要订阅 |
| **Yahoo Finance** | 有限的融券利率数据 | 部分股票可用 |
| **自建数据库** | 每日采集融券利率 | 需要长期维护 |

**当前实现**：
- 使用预定义的融券利率（占位符）
- 或从 Yahoo Finance 获取（如果可用）

### 2.3 融券利率落盘文件（硬要求）

**文件位置**：`data/short_borrow_rates.csv`

**当前状态**：
- ✅ 接口已预留
- ⚠️ Demo 使用静态样例文件（见下表）
- ❌ 不进入研究结论

**Demo 样例文件内容**：
```csv
ticker,date,short_borrow_rate
NVDA,2025-01-29,0.015
NVDA,2025-01-28,0.015
NVDA,2025-01-27,0.015
AAPL,2025-01-29,0.008
AAPL,2025-01-28,0.008
...
```

**字段说明**：
- `ticker`：股票代码
- `date`：日期（YYYY-MM-DD）
- `short_borrow_rate`：融券利率（小数形式，如 0.015 = 1.5%）

**Research 档要求**：
- 数据来源：Interactive Brokers OR Markit OR 自建采集
- 时间范围：至少 1 年以上，每日更新
- 验证方式：与券商实际融券利率对齐
- 标注要求：CSV 中添加 `data_source` 列

**重要声明**：
- ❌ 不要在报告里写"NVDA 融券利率 1.5%"而不标注来源
- ✅ 要写"根据 data/short_borrow_rates.csv，NVDA 融券利率 1.5%"
- ✅ 如果是 Demo，要标注"[DEMO ONLY]"

### 2.4 融券利率过滤实现

**代码位置**：`src/data/constraints_filter.py`

**关键函数**：
```python
@staticmethod
def is_shortable(ticker, date, short_borrow_rates, 
                 max_rate=0.02):
    """
    检查股票是否可融券（融券利率 < 阈值）
    
    参数:
        ticker: 股票代码
        date: 检查日期
        short_borrow_rates: 融券利率 DataFrame
        max_rate: 最大融券利率（默认 2%）
    
    返回:
        bool: 是否可融券
    """
    # 获取该日期的融券利率
    rate_data = short_borrow_rates[
        (short_borrow_rates['ticker'] == ticker) &
        (short_borrow_rates['date'] == date)
    ]
    
    if rate_data.empty:
        # 如果没有数据，假设可融券
        return True
    
    rate = rate_data['short_borrow_rate'].values[0]
    return rate < max_rate
```

### 2.5 融券利率过滤的影响

**演示结果**（NVDA）：

| 指标 | 值 |
|------|-----|
| 融券利率 | 1.5% |
| 是否可融券 | 是 |
| 融券成本（年化） | 1.5% |
| 融券成本（5 天） | 0.03% |

**成本计算**：
```
5 天融券成本 = 融券利率 × (5 / 252)
            = 1.5% × 0.0198
            = 0.03%
```

---

## 第三部分：综合约束条件

### 3.1 约束条件的组合

**综合过滤规则**：
```
可交易 = 不在财报窗口 AND 融券利率 < 2%
```

**实现**：
```python
def is_tradable(date, ticker, earnings_calendar, 
                short_borrow_rates):
    """
    检查是否满足所有约束条件
    """
    # 检查财报窗口
    if is_in_earnings_window(date, ticker, earnings_calendar):
        return False
    
    # 检查融券利率
    if not is_shortable(ticker, date, short_borrow_rates):
        return False
    
    return True
```

### 3.2 约束条件的影响分析

**演示结果**（NVDA 2025-01-01 ~ 2025-03-31）：

| 约束条件 | 过滤日数 | 过滤比例 |
|---------|---------|---------|
| 无约束 | 0 | 0% |
| 仅财报窗口 | 4 | 6.7% |
| 仅融券利率 | 0 | 0% |
| 综合约束 | 4 | 6.7% |

**结论**：
- 财报窗口是主要的过滤因素
- 融券利率对 NVDA 影响较小（利率较低）

---

## 第四部分：约束条件的可验证性

### 4.1 数据源验证

**验证步骤**：

1. **检查财报日历文件**：
   ```bash
   cat data/earnings_calendar.csv | head -10
   ```

2. **检查融券利率文件**：
   ```bash
   cat data/short_borrow_rates.csv | head -10
   ```

3. **验证数据格式**：
   ```python
   import pandas as pd
   
   earnings = pd.read_csv('data/earnings_calendar.csv')
   print(earnings.dtypes)
   print(earnings.head())
   
   rates = pd.read_csv('data/short_borrow_rates.csv')
   print(rates.dtypes)
   print(rates.head())
   ```

### 4.2 约束条件过滤验证

**验证步骤**：

1. **运行约束条件分析脚本**：
   ```bash
   python3 experiments/run_constraints_analysis.py
   ```

2. **检查输出**：
   - 财报窗口过滤日数
   - 融券利率过滤日数
   - 综合过滤日数

3. **手动验证**：
   ```python
   from src.data.constraints_filter import ConstraintsAnalyzer
   
   results = ConstraintsAnalyzer.analyze_constraints(
       'NVDA', '2025-01-01', '2025-03-31'
   )
   print(results)
   ```

---

## 第五部分：约束条件的限制与改进

### 5.1 当前限制

| 限制 | 说明 |
|------|------|
| **财报日期** | 需要手动维护或使用第三方 API |
| **融券利率** | 需要每日采集，当前使用占位符 |
| **数据延迟** | 融券利率可能有延迟 |
| **覆盖范围** | 只覆盖主要股票 |

### 5.2 改进方向

1. **自动化财报日期获取**：
   - 集成 Alpha Vantage API
   - 或使用 web scraping 从 Yahoo Finance 获取

2. **自动化融券利率采集**：
   - 每日自动采集融券利率
   - 存储到数据库

3. **扩展约束条件**：
   - 添加流动性约束（成交量 > 阈值）
   - 添加价格约束（价格 > 阈值）
   - 添加波动率约束（IV 在合理范围内）

4. **约束条件的权重**：
   - 不同约束条件的权重不同
   - 可以配置约束条件的严格程度

---

## 第六部分：约束条件的代码实现

### 6.1 约束条件分析器

**位置**：`src/data/constraints_filter.py`

**关键类**：
```python
class ConstraintsAnalyzer:
    """约束条件分析器"""
    
    @staticmethod
    def analyze_constraints(ticker, start_date, end_date):
        """
        分析约束条件的影响
        
        返回:
            Dict: 包含各项约束条件的分析结果
        """
```

### 6.2 约束条件过滤器

**位置**：`src/data/constraints_filter.py`

**关键类**：
```python
class ConstraintsFilter:
    """约束条件过滤器"""
    
    @staticmethod
    def filter_tradable_dates(dates, ticker, earnings_calendar, 
                              short_borrow_rates):
        """
        过滤出满足所有约束条件的交易日
        
        返回:
            List: 满足条件的交易日列表
        """
```

---

## 第七部分：约束条件的使用示例

### 7.1 基础使用

```python
from src.data.constraints_filter import ConstraintsAnalyzer

# 分析约束条件
results = ConstraintsAnalyzer.analyze_constraints(
    'NVDA', '2025-01-01', '2025-03-31'
)

print(f"总交易日: {results['total_trading_days']}")
print(f"财报窗口过滤: {results['earnings_window_filtered']}")
print(f"融券利率过滤: {results['short_borrow_filtered']}")
print(f"综合过滤: {results['total_filtered']}")
```

### 7.2 高级使用

```python
from src.data.constraints_filter import ConstraintsFilter

# 过滤出满足条件的交易日
tradable_dates = ConstraintsFilter.filter_tradable_dates(
    dates=all_dates,
    ticker='NVDA',
    earnings_calendar=earnings_df,
    short_borrow_rates=rates_df
)

# 在这些日期上进行交易
for date in tradable_dates:
    # 执行交易逻辑
    pass
```

---

## 第八部分：约束条件的消融实验

### 8.1 消融实验的定义

**消融实验**：逐个移除约束条件，观察对结果的影响。

**实验设计**：

| 实验 | 财报窗口 | 融券利率 | 说明 |
|------|---------|---------|------|
| 基础 | ✓ | ✓ | 应用所有约束条件 |
| 无财报窗口 | ✗ | ✓ | 移除财报窗口约束 |
| 无融券利率 | ✓ | ✗ | 移除融券利率约束 |
| 无约束 | ✗ | ✗ | 不应用任何约束条件 |

### 8.2 消融实验的结果

**预期结果**：

| 实验 | 可交易日 | 收益 | 说明 |
|------|---------|------|------|
| 基础 | 56 | 基准 | 参考点 |
| 无财报窗口 | 60 | 基准 + X% | 财报窗口的影响 |
| 无融券利率 | 56 | 基准 | 融券利率影响较小 |
| 无约束 | 60 | 基准 + Y% | 总体约束条件的影响 |

---

## 第九部分：Demo vs Research 的数据源对照

| 约束条件 | Demo 档 | Research 档 | 标注要求 |
|---------|--------|-----------|---------|
| 财报日历 | 静态样例 | Yahoo/SEC | [DEMO ONLY] vs [RESEARCH] |
| 融券利率 | 静态样例 | IB/Markit | [DEMO ONLY] vs [RESEARCH] |
| 交易成本 | 假设$0 | 实际成本 | [DEMO ONLY] vs [RESEARCH] |

**规则**：
- Demo 档的所有结论前必须标注 **[DEMO ONLY]**
- Research 档的所有结论前必须标注 **[RESEARCH]** + 数据来源
- 混用 Demo 和 Research 数据是严格禁止的

---

## 总结

| 项目 | 说明 |
|------|------|
| **财报窗口** | 前 3 日 + 后 2 日，数据来源 Yahoo Finance（Demo）或 SEC EDGAR（Research） |
| **融券利率** | < 2%，数据来源 Interactive Brokers / Markit（Research）或静态样例（Demo） |
| **过滤规则** | 不在财报窗口 AND 融券利率 < 2% |
| **数据文件** | `data/earnings_calendar.csv` 和 `data/short_borrow_rates.csv` |
| **验证方式** | 运行 `run_constraints_analysis.py` |
| **消融实验** | 逐个移除约束条件，观察影响 |
| **标注要求** | Demo 档标注 [DEMO ONLY]，Research 档标注 [RESEARCH] + 来源 |

---

## 参考资源

- [Earnings Calendar](https://finance.yahoo.com/calendar/earnings)
- [Short Borrow Rates](https://www.interactivebrokers.com/)
- [Markit Short Borrow Rates](https://www.markit.com/)
