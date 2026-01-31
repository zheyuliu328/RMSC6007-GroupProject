# MethodD 研究论证报告（研究协议 + 可复算模板）

## 目标说明

本报告用于“因子有效性论证”，不做长期收益证明。
所有结论必须可从 `outputs/sample_table_tradable.csv` 与 `outputs/stats_table_tradable.csv` 复算，
**不允许**出现未在输出表中出现的数值。

---

## 1. 因子定义与预测目标

### 1.1 因子定义（输入字段锁定）

**IV 收敛因子（A/B 版本）**

- 期权选择规则：**30D 附近 ATM call，锁定同一 contractSymbol**
- 预测目标：**同一合约的 IV 变化**

```
IV_change = IV_t5(contractSymbol) - IV_t0(contractSymbol)

Factor A: f_t = (IV_t0 - median(IV)) / median(IV)
Factor B: z_t = (IV_t0 - median(IV)) / MAD(IV)
```

### 1.2 基准对照（必须输出）

- **Baseline 1**：naive IV level（不标准化，仅用 IV_t0）
- **Baseline 2**：lagged IV change（IV_change_{t-1}）

---

## 2. 研究协议（可审计约束）

1. **预测目标锁定**：仅使用同一 contractSymbol 的 IV_t5 - IV_t0。
2. **样本独立性修正**：显著性使用 block bootstrap（按 date×expiry 分组）。
3. **控制变量**：控制 moneyness、spread、open interest，输出 partial IC。
4. **分桶一致性**：按 moneyness / spread / open interest 分桶输出 IC。
5. **可交易性主结论**：主结论仅使用 bid/ask>0 且点差合理的样本。
6. **数据完整性**：manifest + checksum 缺失即 FAIL。
7. **输出唯一来源**：仅允许引用 outputs 生成的 CSV。

---

## 3. 输出文件清单（唯一审计来源）

| 类型 | 文件 | 说明 |
|------|------|------|
| 样本表 | `outputs/sample_table.csv` | 全量样本（含可交易标记） |
| 样本表 | `outputs/sample_table_tradable.csv` | 可交易样本（主结论） |
| 统计表 | `outputs/stats_table_tradable.csv` | 主结论统计（含 partial IC / bootstrap） |
| 统计表 | `outputs/stats_table_full.csv` | 全量样本统计（附录） |
| 单笔审计 | `outputs/nvda_covered_call_demo.csv` | 单笔复算（链路自洽验证） |

---

## 4. 可检验机制与假设

### 4.1 均值回归假设

- **命题**：IV 水平高 → 未来 IV_change 更可能为负
- **检验**：factor_a / factor_b vs iv_change 的 Spearman IC 与回归系数

### 4.2 事件窗口失效

- **命题**：财报窗口 IV 均值回归失效
- **检验**：财报窗口过滤前后 IC/t-stat 对比（在 stats_table 标记）

### 4.3 流动性约束

- **命题**：点差高或 openInterest 低时，预测强度下降
- **检验**：按 spread / open interest 分桶输出 IC 一致性

---

## 5. 统计检验模板（仅引用 CSV 字段）

### 5.1 主检验：IV 变化预测

从 `stats_table_tradable.csv` 读取：
- factor_a / factor_b 的 Spearman IC 与 t-stat
- partial Spearman IC（控制变量后的结果）
- block bootstrap t-stat（按 date×expiry）

### 5.2 基准对照

从 `stats_table_tradable.csv` 读取：
- baseline_iv_level
- baseline_iv_change_lag1

### 5.3 分组失效

从 `stats_table_tradable.csv` 读取：
- spread_low / spread_high 对比
- moneyness / spread / open_interest 分桶对比

---

## 6. 结果解读模板（占位）

-- 主检验 IC 与 t-stat：____（引用 stats_table_tradable）
-- partial IC 与 bootstrap t-stat：____（引用 stats_table_tradable）
-- Factor A/B 相对基准的提升：____（引用 stats_table_tradable）
-- 分桶一致性结论：____（引用 stats_table_tradable）

---

## 7. 复现与审计声明

- 任何结论必须可从 `outputs/sample_table_tradable.csv` 与 `outputs/stats_table_tradable.csv` 复算
- 文档中不得出现未出现在 outputs 的具体数值
- Demo 样例仅用于流程演示，不可进入研究结论