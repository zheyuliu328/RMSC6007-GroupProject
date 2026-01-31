# 方案C 实现指南（续）：第二步到第四步

---

## 第二步：因子回归（Rolling Regression）

### 为什么这一步很重要？

**目标**：估计时间变化的因子暴露（beta），理解资产如何随时间响应风险因子

**关键问题**：
- 为什么要用rolling window而不是全样本回归？
- 如何处理多个资产的并行回归？
- 如何评估回归质量？

### 使用的库与原因

#### 1. **linearmodels** - 滚动回归
```python
from linearmodels.regression import RollingOLS
import pandas as pd

# 为什么用linearmodels？
# ✅ 专门为面板/滚动回归设计
# ✅ 支持多个资产的并行处理
# ✅ 返回完整的统计诊断
# ✅ 比手写循环快10倍以上

# 设置rolling window
window = 252  # 252个交易日 ≈ 1年

# 对每个资产进行滚动回归
for asset in assets:
    # 准备数据：超额收益 ~ 因子
    y = excess_returns[asset]  # 因变量
    X = ff_factors[['Mkt-RF', 'SMB', 'HML']]  # 自变量（FF3）
    
    # 滚动OLS回归
    model = RollingOLS(y, X, window=window)
    results = model.fit()
    
    # 提取时间变化的beta
    betas = results.params  # DataFrame: (日期, 因子) -> beta值
    r_squared = results.rsquared  # 模型解释力
    pvalues = results.pvalues  # 显著性检验
```

**项目中的角色**：
- 估计每个资产对每个因子的时间变化暴露
- 生成rolling R²（模型解释力随时间变化）
- 计算alpha（模型截距，代表超额收益）

#### 2. **statsmodels** - 统计诊断
```python
from statsmodels.regression.linear_model import OLS
import statsmodels.api as sm

# 为什么用statsmodels？
# ✅ 完整的统计诊断工具
# ✅ 显著性检验（t-test, F-test）
# ✅ 异方差检验（Breusch-Pagan）
# ✅ 自相关检验（Durbin-Watson）

# 对单个时间段进行详细诊断
X_with_const = sm.add_constant(X)  # 添加截距项
model = OLS(y, X_with_const)
results = model.fit()

# 获取诊断信息
print(results.summary())  # 完整的回归报告
# 包含：
# - 系数估计值和标准误
# - t统计量和p值
# - R²和调整R²
# - F统计量
# - Durbin-Watson统计量（检验自相关）
```

**项目中的角色**：
- 验证回归结果的统计显著性
- 检验模型假设（异方差、自相关）
- 生成详细的诊断报告

### 代码框架

```python
# src/factor_regression.py

from linearmodels.regression import RollingOLS
import statsmodels.api as sm
import pandas as pd
import numpy as np

class FactorRegression:
    def __init__(self, window=252):
        """
        window: rolling window大小（交易日数）
        为什么选252？
        - 252 ≈ 1年的交易日
        - 足够长以获得稳定的估计
        - 足够短以捕捉时间变化
        """
        self.window = window
    
    def rolling_regression(self, excess_returns, factors, asset_name):
        """
        对单个资产进行滚动回归
        
        输入：
        - excess_returns: Series，资产的超额收益
        - factors: DataFrame，因子收益（Mkt-RF, SMB, HML等）
        - asset_name: str，资产名称
        
        输出：
        - betas: DataFrame，时间变化的因子暴露
        - alphas: Series，时间变化的alpha
        - r_squared: Series，模型解释力
        """
        # 使用linearmodels进行滚动回归
        model = RollingOLS(excess_returns, factors, window=self.window)
        results = model.fit()
        
        # 提取结果
        betas = results.params  # 因子暴露
        alphas = results.alpha  # 截距（alpha）
        r_squared = results.rsquared  # 解释力
        
        return {
            'betas': betas,
            'alphas': alphas,
            'r_squared': r_squared,
            'asset': asset_name
        }
    
    def compute_diagnostics(self, excess_returns, factors):
        """
        计算统计诊断
        
        为什么需要诊断？
        - 验证OLS假设是否满足
        - 检测异方差（Breusch-Pagan）
        - 检测自相关（Durbin-Watson）
        - 评估模型质量
        """
        X = sm.add_constant(factors)
        model = OLS(excess_returns, X)
        results = model.fit()
        
        diagnostics = {
            'r_squared': results.rsquared,
            'adj_r_squared': results.rsquared_adj,
            'f_statistic': results.fvalue,
            'f_pvalue': results.f_pvalue,
            'durbin_watson': sm.stats.durbin_watson(results.resid),
            'condition_number': np.linalg.cond(X.T @ X)
        }
        
        return diagnostics
```

---

## 第三步：归因分析（Return Attribution）

### 为什么这一步很重要？

**目标**：分解实现的收益，理解每个因子的贡献

**关键问题**：
- 资产的收益来自哪些因子？
- 在不同市场状态下，因子贡献如何变化？
- 哪些因子在危机期间最重要？

### 使用的库与原因

#### 1. **numpy** - 数值计算
```python
import numpy as np

# 为什么用numpy？
# ✅ 高效的矩阵运算
# ✅ 支持向量化操作（比循环快100倍）
# ✅ 底层C实现，性能最优

# 归因分解公式：
# 实现收益 = alpha + beta1*factor1 + beta2*factor2 + ... + residual

# 计算每个因子的贡献
factor_contributions = betas * factors  # 逐元素相乘
# 结果：每个时间点，每个因子对收益的贡献

# 计算总贡献
total_factor_contribution = factor_contributions.sum(axis=1)
alpha_contribution = alphas
residual = excess_returns - total_factor_contribution - alpha_contribution
```

**项目中的角色**：
- 高效计算因子贡献
- 分解收益成分
- 计算残差（非因子解释的部分）

#### 2. **pandas** - 数据聚合与分析
```python
import pandas as pd

# 为什么用pandas？
# ✅ 灵活的数据聚合
# ✅ 时间序列分组（按月、按季度）
# ✅ 多维数据透视表

# 按月份聚合因子贡献
monthly_contribution = factor_contributions.resample('M').sum()

# 按市场状态分组
calm_periods = volatility < volatility.quantile(0.33)
stressed_periods = volatility > volatility.quantile(0.67)

calm_contribution = factor_contributions[calm_periods].mean()
stressed_contribution = factor_contributions[stressed_periods].mean()

# 创建归因表
attribution_table = pd.DataFrame({
    'Calm_Periods': calm_contribution,
    'Stressed_Periods': stressed_contribution,
    'Difference': stressed_contribution - calm_contribution
})
```

**项目中的角色**：
- 按时间段聚合因子贡献
- 按市场状态分组分析
- 生成归因汇总表

### 代码框架

```python
# src/attribution.py

import numpy as np
import pandas as pd

class ReturnAttribution:
    def __init__(self, betas, alphas, factors, excess_returns):
        """
        初始化归因分析
        
        输入：
        - betas: DataFrame，时间变化的因子暴露
        - alphas: Series，时间变化的alpha
        - factors: DataFrame，因子收益
        - excess_returns: Series，实现的超额收益
        """
        self.betas = betas
        self.alphas = alphas
        self.factors = factors
        self.excess_returns = excess_returns
    
    def decompose_returns(self):
        """
        分解收益成分
        
        公式：
        Excess Return = Alpha + Sum(Beta_i * Factor_i) + Residual
        
        为什么这个分解很重要？
        - 量化每个因子的贡献
        - 识别非因子收益（alpha）
        - 评估模型解释力
        """
        # 计算因子贡献
        factor_contributions = self.betas * self.factors
        
        # 计算总因子贡献
        total_factor_contribution = factor_contributions.sum(axis=1)
        
        # 计算残差
        residual = self.excess_returns - self.alphas - total_factor_contribution
        
        return {
            'factor_contributions': factor_contributions,
            'alpha_contribution': self.alphas,
            'residual': residual,
            'total_explained': total_factor_contribution + self.alphas
        }
    
    def regime_analysis(self, volatility_threshold=None):
        """
        按市场状态分析因子贡献
        
        为什么需要regime分析？
        - 因子在不同市场状态下表现不同
        - 危机期间某些因子更重要
        - 帮助理解风险来源
        """
        if volatility_threshold is None:
            # 使用波动率的33/67分位数
            vol = self.excess_returns.rolling(20).std()
            threshold_low = vol.quantile(0.33)
            threshold_high = vol.quantile(0.67)
        
        # 定义市场状态
        calm = vol <= threshold_low
        normal = (vol > threshold_low) & (vol <= threshold_high)
        stressed = vol > threshold_high
        
        # 计算各状态下的平均贡献
        decomp = self.decompose_returns()
        
        regimes = {
            'calm': decomp['factor_contributions'][calm].mean(),
            'normal': decomp['factor_contributions'][normal].mean(),
            'stressed': decomp['factor_contributions'][stressed].mean()
        }
        
        return regimes
```

---

## 第四步：预测评估（Walk-Forward Evaluation）

### 为什么这一步很重要？

**目标**：评估因子模型是否有真实的预测能力（不是过拟合）

**关键问题**：
- 因子模型能否预测未来收益？
- 与简单baseline相比是否有优势？
- 预测能力在不同时期是否稳定？

### 使用的库与原因

#### 1. **numpy** - Walk-forward循环
```python
import numpy as np

# 为什么用numpy？
# ✅ 高效的数组操作
# ✅ 支持向量化预测
# ✅ 内存效率高

# Walk-forward评估框架
train_window = 252 * 3  # 3年训练数据
test_window = 252  # 1年测试数据

predictions = []
actuals = []

for t in range(train_window, len(data) - test_window, test_window):
    # 1. 在历史数据上训练
    X_train = factors[t-train_window:t]
    y_train = excess_returns[t-train_window:t]
    
    # 2. 估计因子暴露
    betas = np.linalg.lstsq(X_train, y_train)[0]
    
    # 3. 在测试期预测
    X_test = factors[t:t+test_window]
    y_pred = X_test @ betas
    
    # 4. 记录预测和实际
    predictions.append(y_pred)
    actuals.append(excess_returns[t:t+test_window])
```

**项目中的角色**：
- 实现walk-forward循环
- 避免look-ahead bias（前瞻偏差）
- 评估真实的out-of-sample性能

#### 2. **sklearn.metrics** - 预测评估
```python
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np

# 为什么用sklearn？
# ✅ 标准化的评估指标
# ✅ 与业界一致
# ✅ 易于比较不同模型

# 计算预测误差
m
