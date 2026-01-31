# MethodD 数据口径与可得性声明

## 概述

本文档明确说明 MethodD 项目中使用的数据定义、来源、处理方式，确保数据的**可追溯性、可验证性、可复现性**。

---

## 第一部分：IV（隐含波动率）定义

### 1.1 IV 的定义

**隐含波动率（Implied Volatility, IV）** 是指从期权市场价格反推出来的波动率，代表市场对未来波动的预期。

**关键特征**：
- **来源**：从期权价格反推（使用 Black-Scholes 模型或其他定价模型）
- **不同于 HV**：历史波动率（HV）是从历史收益率计算的，两者是不同的对象
- **口径混用风险**：将 HV 和 IV 混用会导致"因子定义失真"

### 1.2 ATM 30D IV 的定义

**ATM 30D IV** 是指：
- **ATM（At-The-Money）**：行权价最接近当前股价的期权
- **30D（30 天）**：到期日期距离当前日期约 30 天的期权
- **IV**：该期权的隐含波动率

**选择 ATM 的方式**：
```
ATM Call = argmin(|Strike - Current_Price|)
```
即选择行权价与当前股价差距最小的 call 期权。

### 1.3 到期离散处理与插值

**问题**：Yahoo Finance 期权链中的到期日期是离散的（如 1 月 17 日、1 月 24 日、1 月 31 日等），不一定恰好是 30 天。

**处理方式**：
1. **寻找最接近 30 天的到期日期**：
   - 允许范围：20-40 天（±10 天容差）
   - 选择标准：`min(|DTE - 30|)`

2. **插值方式**（如果需要精确 30 天）：
   - 使用线性插值：`IV_30D = IV_near + (IV_far - IV_near) * (30 - DTE_near) / (DTE_far - DTE_near)`
   - 当前实现：使用最接近的单一到期日期（简化处理）

### 1.4 IV 的计算方式

使用 Black-Scholes 模型反推：

```
Call_Price = S * N(d1) - K * exp(-r*T) * N(d2)

其中：
d1 = [ln(S/K) + (r + σ²/2)*T] / (σ*√T)
d2 = d1 - σ*√T

给定 Call_Price，求解 σ（IV）
```

**实现**：使用 scipy.optimize 的数值求解方法。

---

## 第二部分：IV 数据分档标准

### 2.1 Demo 档（演示档）

**定义**：仅支持 Yahoo Finance 当下快照与合成序列

**特征**：
- 数据来源：Yahoo Finance 当前快照 + 合成历史数据
- 时间范围：最多 3 个月
- 用途：代码路径演示、指标定义验证、sanity check
- 结论用途：❌ **不能用于研究结论、不能用于策略评估**
- 标注要求：所有输出必须标注 **⚠️ [DEMO ONLY]**

**示例**：
```
⚠️ [DEMO ONLY] NVDA 2025-01-01 ~ 2025-03-31 的 Rank-IC 为 0.12
（基于 Yahoo Finance 当前快照，仅用于演示因子定义）
```

### 2.2 Research 档（研究档）

**定义**：必须是历史 ATM 30D IV 时间序列

**特征**：
- 数据来源：自建每日落盘期权链构造的 IV 序列 **OR** 第三方历史期权库
- 时间范围：至少 1 年以上
- 用途：完整历史回测、因子评估、策略验证
- 结论用途：✅ **可用于研究结论、可用于策略评估**
- 标注要求：所有输出必须标注 **[RESEARCH]** + 数据来源

**数据来源示例**：
- ✅ 自建：每日采集期权链，构造 ATM 30D IV 时间序列
- ✅ 第三方：OptionMetrics、Bloomberg、Wind 等历史期权库
- ❌ Yahoo Finance 当前快照（不是历史序列）

**示例**：
```
[RESEARCH] NVDA 2015-2025 的 Rank-IC 为 0.15
（基于自建每日期权链数据库，2015-01-01 ~ 2025-01-29）
```

### 2.3 分档的强制规则

**重要声明**：

| 规则 | 说明 |
|------|------|
| **混用禁止** | 严格禁止混用 Demo 和 Research 档的数据 |
| **标注必须** | 每个数值结论前必须标注档次和数据来源 |
| **Demo 限制** | Demo 档的所有结论只能用于演示，不能进入最终研究报告 |
| **Research 要求** | Research 档必须有完整的数据来源追溯 |

---

## 第三部分：数据来源

### 2.1 Yahoo Finance 期权链数据

**数据源**：Yahoo Finance API（通过 yfinance 库）

**获取方式**：
```python
import yfinance as yf

ticker = yf.Ticker('NVDA')
expirations = ticker.options  # 获取所有可用到期日期
opt_chain = ticker.option_chain('2025-01-31')  # 获取特定到期日期的期权链
calls = opt_chain.calls  # 获取 call 期权数据
```

**数据字段**：
- `strike`：行权价
- `lastPrice`：最后成交价
- `bid`：买价
- `ask`：卖价
- `impliedVolatility`：隐含波动率（yfinance 已计算）
- `volume`：成交量
- `openInterest`：持仓量

### 2.2 数据可得性限制

**关键限制**：

| 限制项 | 说明 |
|------|------|
| **快照 vs 历史** | Yahoo Finance 提供的是**当前快照**，不是历史时间序列 |
| **历史 IV 数据** | 无法直接获取 2010-2025 的历史 IV 时间序列 |
| **回测 vs Forward Test** | 只能做 **forward test**（从今天开始），不能做完整历史回测 |
| **数据延迟** | 期权数据通常延迟 15-20 分钟 |
| **流动性** | 只有流动性较好的期权才有可靠的 IV 数据 |

### 2.3 自建历史库的必要性

要实现完整的历史回测（如 2010-2025），需要：

1. **每日采集**：每个交易日自动采集期权链数据
2. **落盘存储**：将采集的数据存储到数据库或 CSV 文件
3. **时间序列构建**：形成 ATM 30D IV 的历史时间序列

**当前项目状态**：
- ✅ 支持从 Yahoo Finance 获取当前快照
- ❌ 没有自建历史库（需要长期采集）
- ⚠️ 演示脚本使用合成数据或有限的历史数据

---

## 第三部分：数据处理流程

### 3.1 数据下载与缓存

**流程**：
```
1. 检查本地缓存 (data/cache/)
   ↓
2. 如果缓存存在且未过期，使用缓存
   ↓
3. 如果缓存不存在或已过期，从 Yahoo Finance 下载
   ↓
4. 将下载的数据保存到缓存
   ↓
5. 返回数据
```

**缓存策略**：
- 缓存位置：`data/cache/`
- 缓存文件格式：CSV（带时间戳）
- 缓存有效期：1 天（可配置）
- 缓存文件名：`{ticker}_{start_date}_{end_date}_{timestamp}.csv`

### 3.2 数据清洗

**清洗步骤**：

1. **缺失值处理**：
   - 前向填充（forward fill）：用前一个值填充缺失值
   - 后向填充（backward fill）：用后一个值填充缺失值
   - 限制填充次数：最多连续填充 5 个缺失值

2. **异常值检测**：
   - IV 范围检查：0 < IV < 5（排除异常值）
   - 价格范围检查：排除明显错误的价格

3. **对齐处理**：
   - 确保所有股票的数据日期对齐
   - 处理停牌、退市等特殊情况

### 3.3 数据验证

**验证检查**：

```python
# 检查数据完整性
assert not df.empty, "数据为空"
assert df['iv_atm_30d'].notna().sum() > 0, "IV 数据全为缺失"

# 检查数据范围
assert (df['iv_atm_30d'] > 0).all(), "IV 应大于 0"
assert (df['iv_atm_30d'] < 5).all(), "IV 应小于 5"

# 检查数据时间范围
assert df.index.min() >= start_date, "数据开始日期不符"
assert df.index.max() <= end_date, "数据结束日期不符"
```

---

## 第四部分：数据使用声明

### 4.1 当前项目的数据使用

**演示脚本中的数据**：

| 脚本 | 数据来源 | 数据类型 | 时间范围 |
|------|--------|--------|--------|
| `run_iv_factor_demo.py` | Yahoo Finance | 当前快照 + 合成历史 | 2025-01-01 ~ 2025-03-31 |
| `run_nvda_covered_call_demo.py` | Yahoo Finance | 当前快照 | 2025-01-29（当前日期） |
| `run_constraints_analysis.py` | Yahoo Finance + 内置 | 当前快照 + 财报日历 | 2025-01-01 ~ 2025-03-31 |

### 4.2 数据限制条件

**重要声明**：

1. **Demo 档限制**：
   - 当前演示使用的是**当前快照**或**有限的历史数据**
   - ❌ 不能声称做了 2010-2025 的完整历史回测
   - ❌ 只能做 **forward test**（从今天开始的前向测试）
   - ❌ 不能进入研究结论

2. **Research 档要求**：
   - 必须是历史 ATM 30D IV 时间序列
   - 必须至少 1 年以上的数据
   - 必须有完整的数据来源追溯
   - ✅ 可以进行完整历史回测
   - ✅ 可以进入研究结论

3. **IV 数据的真实性**：
   - Demo 档：IV 来自 Yahoo Finance 期权链，反映当前市场预期
   - Research 档：IV 来自自建或第三方历史库，反映历史市场预期
   - 用于演示和 sanity check，不能作为完整研究的证据

4. **数据可得性**：
   - 只有流动性较好的股票才有可靠的期权数据
   - 小盘股或流动性差的股票可能无法获取数据
   - 期权数据通常延迟 15-20 分钟

### 4.3 数据使用的正确表述

**✅ 正确表述（Demo 档）**：
- "⚠️ [DEMO ONLY] 使用 Yahoo Finance 当前期权链快照计算 ATM 30D IV"
- "⚠️ [DEMO ONLY] 基于当前 IV 快照进行 forward test 验证"
- "⚠️ [DEMO ONLY] 使用 BS 模型反推的 IV 进行因子计算"

**✅ 正确表述（Research 档）**：
- "[RESEARCH] 使用自建每日期权链数据库（2015-2025）计算 ATM 30D IV"
- "[RESEARCH] 基于历史 IV 时间序列进行完整回测"
- "[RESEARCH] 使用 OptionMetrics 历史期权库进行因子评估"

**❌ 错误表述**：
- "从 Yahoo Finance 获取 2010-2025 的历史 IV 时间序列"
- "使用历史 IV 数据进行完整回测"（未标注数据来源）
- "年化收益 185%"（未标注数据档次和时间范围）

---

## 第五部分：数据文件结构

### 5.1 数据目录结构

```
RMSC6007_GroupProject/MethodD/data/
├── cache/                          # 数据缓存目录
│   ├── NVDA_2025-01-01_2025-03-31_20250129.csv
│   ├── AAPL_2025-01-01_2025-03-31_20250129.csv
│   └── ...
├── earnings_calendar.csv           # 财报日历（落盘文件）
├── short_borrow_rates.csv          # 融券利率（落盘文件）
└── README.md                       # 数据说明
```

### 5.2 缓存文件格式

**文件名**：`{ticker}_{start_date}_{end_date}_{timestamp}.csv`

**文件内容**：
```
date,close,iv_atm_30d
2025-01-02,192.50,0.45
2025-01-03,193.20,0.44
2025-01-06,194.10,0.43
...
```

**字段说明**：
- `date`：交易日期（YYYY-MM-DD）
- `close`：收盘价
- `iv_atm_30d`：ATM 30D 隐含波动率

---

## 第六部分：数据验证与复现

### 6.1 数据验证方式

**验证步骤**：

1. **检查缓存文件**：
   ```bash
   ls -la data/cache/
   ```

2. **检查数据内容**：
   ```python
   import pandas as pd
   df = pd.read_csv('data/cache/NVDA_2025-01-01_2025-03-31_20250129.csv')
   print(df.head())
   print(df.describe())
   ```

3. **检查数据完整性**：
   ```python
   print(f"数据行数: {len(df)}")
   print(f"缺失值: {df.isna().sum()}")
   print(f"IV 范围: {df['iv_atm_30d'].min()} ~ {df['iv_atm_30d'].max()}")
   ```

### 6.2 数据复现

**复现步骤**：

1. **删除缓存**：
   ```bash
   rm -rf data/cache/
   ```

2. **重新运行脚本**：
   ```bash
   python3 experiments/run_iv_factor_demo.py
   ```

3. **验证结果**：
   - 新的缓存文件应该被创建
   - 结果应该与之前的运行一致（如果数据相同）

---

## 第七部分：数据源代码

### 7.1 数据加载代码

**位置**：`src/data/real_data_loader.py`

**关键函数**：
```python
def get_atm_iv_history(ticker, start_date, end_date, target_dte=30):
    """
    获取 ATM 30D IV 历史数据
    
    参数:
        ticker: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        target_dte: 目标到期天数（默认 30）
    
    返回:
        DataFrame: 包含日期、收盘价、ATM IV 的数据
    """
```

### 7.2 数据适配器代码

**位置**：`src/data/data_adapter.py`

**功能**：
- 数据源适配（支持多个数据源）
- 缓存管理
- 数据清洗和验证

---

## 总结

| 项目 | Demo 档 | Research 档 |
|------|---------|-----------|
| **IV 定义** | 从期权价格反推的隐含波动率，ATM 30D | 从期权价格反推的隐含波动率，ATM 30D |
| **数据来源** | Yahoo Finance 期权链快照 | 自建每日期权链 OR 第三方历史库 |
| **时间范围** | 最多 3 个月 | 至少 1 年以上 |
| **回测类型** | Forward test（从今天开始） | 完整历史回测 |
| **缓存策略** | 本地 CSV 缓存，1 天有效期 | 数据库或长期存储 |
| **验证方式** | 代码可追溯，缓存文件有时间戳 | 数据来源完全可追溯 |
| **使用限制** | 仅用于演示和 sanity check | 可用于研究结论 |
| **标注要求** | ⚠️ [DEMO ONLY] | [RESEARCH] + 来源 |
| **进入报告** | ❌ 不能 | ✅ 可以 |

---

## 参考资源

- [Yahoo Finance Options Data Download with Python yfinance](https://www.macroption.com/yahoo-finance-options-python/)
- [Historical Volatility and Implied Volatility](https://www.quantconnect.com/learning/articles/introduction-to-options/historical-volatility-and-implied-volatility)
- [Black-Scholes Model](https://en.wikipedia.org/wiki/Black%E2%80%93Scholes_model)
