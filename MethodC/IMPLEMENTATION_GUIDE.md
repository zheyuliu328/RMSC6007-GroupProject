# 方案C 实现指南：因子暴露与风险归因分析

**详细的技术实现说明 | 库选择理由 | 项目架构**

---

## 📚 目录

1. [技术栈与库选择](#技术栈与库选择)
2. [项目架构](#项目架构)
3. [第一步：数据获取](#第一步数据获取)
4. [第二步：因子回归](#第二步因子回归)
5. [第三步：归因分析](#第三步归因分析)
6. [第四步：预测评估](#第四步预测评估)
7. [代码示例](#代码示例)

---

## 🛠️ 技术栈与库选择

### 核心库选择矩阵

| 功能 | 库 | Stars | 为什么选它 | 项目中的角色 |
|------|-----|-------|----------|-----------|
| **数据获取** | yfinance | 14.5k⭐ | 免费、稳定、无需API key | 下载股票价格 |
| **因子数据** | pandas-datareader | 2.9k⭐ | 直接读取Kenneth French数据 | 自动下载FF因子 |
| **数据处理** | pandas | 43k⭐ | 业界标准，时间序列处理强大 | 数据对齐、清洗、转换 |
| **滚动回归** | linearmodels | 1.1k⭐ | 专门为面板/滚动回归设计 | 时间变化的beta估计 |
| **统计检验** | statsmodels | 10k+⭐ | 完整的统计工具箱 | OLS诊断、显著性检验 |
| **数值计算** | numpy | 26k⭐ | 高效矩阵运算 | 底层数值计算 |
| **可视化** | matplotlib/plotly | 18k/15k⭐ | 静态/交互式图表 | 结果展示 |
| **测试** | pytest | 11k⭐ | Python标准测试框架 | 单元测试、集成测试 |

---

## 📁 项目架构

### 完整的项目结构

```
factor-research-toolkit/
│
├── src/
│   ├── __init__.py
│   ├── data_loader.py          # 第一步：数据获取
│   │   ├── download_stock_prices()      # yfinance
│   │   ├── download_ff_factors()        # pandas-datareader
│   │   └── align_and_preprocess()       # pandas
│   │
│   ├── factor_regression.py    # 第二步：因子回归
│   │   ├── rolling_regression()         # linearmodels
│   │   ├── estimate_betas()             # statsmodels
│   │   └── compute_diagnostics()        # statsmodels
│   │
│   ├── attribution.py          # 第三步：归因分析
│   │   ├── decompose_returns()          # numpy
│   │   ├── factor_contribution()        # pandas
│   │   └── regime_analysis()            # pandas
│   │
│   ├── forecasting.py          # 第四步：预测评估
│   │   ├── walk_forward_forecast()      # numpy
│   │   ├── evaluate_forecast()          # sklearn metrics
│   │   └── compare_baselines()          # pandas
│   │
│   └── visualization.py        # 可视化
│       ├── plot_betas()                 # matplotlib
│       ├── plot_attribution()           # plotly
│       └── plot_forecast_comparison()   # matplotlib
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_rolling_regression.ipynb
│   ├── 03_attribution_analysis.ipynb
│   └── 04_forecast_evaluation.ipynb
│
├── tests/
│   ├── test_data_loader.py
│   ├── test_factor_regression.py
│   ├── test_attribution.py
│   └── test_forecasting.py
│
├── requirements.txt
├── setup.py
└── README.md
```

---

## 第一步：数据获取

### 为什么这一步很重要？

**目标**：获取干净、对齐的数据，为后续分析奠定基础

**关键问题**：
- 如何处理不同交易日历（美股vs港股）？
- 如何处理缺失值？
- 如何确保数据一致性？

### 使用的库与原因

#### 1. **yfinance** - 股票价格数据
```python
import yfinance as yf

# 为什么用yfinance？
# ✅ 免费、无需API key
# ✅ 支持多个市场（US, HK, etc）
# ✅ 自动处理股票分割、分红调整
# ✅ 返回pandas DataFrame，易于处理

prices = yf.download(['AAPL', 'MSFT', 'JPM'], 
                      start='2015-01-01', 
                      end='2025-01-01')
# 返回: DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']
```

**项目中的角色**：
- 获取10-30个股票的日收盘价
- 自动调整分红和股票分割
- 处理多个资产的并行下载

#### 2. **pandas-datareader** - Fama-French因子数据
```python
import pandas_datareader as pdr

# 为什么用pandas-datareader？
# ✅ 直接连接Kenneth French数据库
# ✅ 自动下载FF3、FF5因子
# ✅ 返回pandas DataFrame，格式标准

ff_factors = pdr.data.FamaFrenchReader('F-F_Research_Data_Factors_daily', 
                                        start='2015-01-01', 
                                        end='2025-01-01').read()
# 返回: DataFrame with columns ['Mkt-RF', 'SMB', 'HML', 'RF'] (FF3)
```

**项目中的角色**：
- 自动下载FF3因子（Mkt-RF, SMB, HML）
- 自动下载FF5因子（额外RMW, CMA）
- 确保因子数据与股票数据日期对齐

#### 3. **pandas** - 数据对齐与清洗
```python
import pandas as pd

# 为什么用pandas？
# ✅ 时间序列处理最强大
# ✅ 自动处理日期对齐
# ✅ 灵活的缺失值处理
# ✅ 高效的数据转换

# 对齐不同来源的数据
aligned_data = pd.concat([stock_returns, ff_factors], 
                         axis=1, 
                         join='inner')  # 只保留共同日期

# 处理缺失值
aligned_data = aligned_data.fillna(method='ffill', limit=5)  # 最多前向填充5天

# 计算超额收益
excess_returns = stock_returns - ff_factors['RF']
```

**项目中的角色**：
- 对齐股票数据和因子数据的日期
- 处理缺失值（forward-fill）
- 计算超额收益（stock return - risk-free rate）
- 创建rolling window数据集

### 代码框架

```python
# src/data_loader.py

import yfinance as yf
import pandas_datareader as pdr
import pandas as pd

class FactorDataLoader:
    def __init__(self, start_date='2015-01-01', end_date='2025-01-01'):
        self.start_date = start_date
        self.end_date = end_date
    
    def download_stock_prices(self, tickers):
        """
        使用yfinance下载股票价格
        
        为什么这样设计？
        - 批量下载多个资产（高效）
        - 自动调整分红和分割
        - 返回标准化的DataFrame
        """
        prices = yf.download(tickers, 
                            start=self.start_date, 
                            end=self.end_date)
        return prices['Adj Close']  # 只保留调整后的收盘价
    
    def download_ff_
