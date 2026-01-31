# MethodD 五项关键交付件

## 交付件清单

本文档明确列出 MethodD 项目的五项关键交付件，确保项目的**可复现性、可验证性、可辩护性**。

---

## 第一项：复现闭环

### 目标
提供一条从零到结果的完整命令路径，包括依赖管理、数据下载、缓存策略、随机种子、运行日志、产出文件。

### 交付物
- ✅ `requirements.txt` - 固定版本依赖
- ✅ `QUICK_START.md` - 一键运行指南
- ✅ `run_all_demos.sh` - 完整演示脚本
- ✅ `logs/` 目录 - 运行日志输出
- ✅ `outputs/` 目录 - 产出报告文件

### 验证方式

**必须生成的文件**：
```bash
# 日志文件
logs/run_20250130_*.log (> 100 行)

# 输出文件
outputs/factor_analysis_report.csv (> 10 行)
outputs/backtest_results.csv (> 10 行)
outputs/nvda_covered_call_demo.csv (> 10 行)
outputs/research_report.html (> 10KB)
```

**校验命令**：
```bash
# 检查文件存在性
test -f logs/run_*.log && echo "✅ 日志文件存在"
test -f outputs/factor_analysis_report.csv && echo "✅ 因子分析报告存在"

# 检查文件大小
du -h logs/run_*.log outputs/*.csv

# 检查文件哈希（用于复现验证）
md5sum logs/run_*.log outputs/*.csv > outputs/checksums.md5
```

**判定成功**：
- ✅ 所有文件都存在
- ✅ 日志文件 > 100 行
- ✅ CSV文件 > 10 行
- ✅ HTML报告 > 10KB
- ✅ 日志中没有 ERROR 或 CRITICAL

---

## 第二项：数据口径与可得性声明

### 目标
清晰写出 IV 的定义、数据来源、处理方式，避免"从 Yahoo 获取历史 IV"的模糊表述。

### 交付物
- ✅ `DATA_SPECIFICATION.md` - 数据口径详细说明
  - IV 定义：30D ATM，如何选 ATM，如何处理到期离散，如何插值到 30D
  - 数据来源：Yahoo Finance 期权链快照 vs 自建历史库
  - 数据可得性：当前快照 vs 历史时间序列
  - 限制条件：forward test vs backtest

### 验证方式
- 数据源代码可追溯（yfinance 版本、API 调用方式）
- 数据缓存文件有时间戳
- 报告中明确标注数据时间范围
- **所有数值结论必须标注 [DEMO ONLY] 或 [RESEARCH]**
- **Demo 档数据不能进入最终研究报告**

---

## 第三项：覆盖式卖 call 的定价与结算口径

### 目标
明确 PnL 计算方式，避免"大概率不会被行权"的模糊表述。

### 交付物
- ✅ `COVERED_CALL_SPECIFICATION.md` - 定价与结算口径说明
  - 持有期：5 天平仓（不是持有到期）
  - PnL 计算：mark-to-market 平仓价差
  - 定价方式：BS 标价 vs 真实 bid/ask 中间价
  - 上行封顶：明确显示在结果中

### 验证方式
- 三个场景演示中明确显示上行封顶
- PnL 分解：正股 + 期权权利金
- 平仓价格来源明确（BS 定价参数、IV 值）
- **所有数字必须能一行行验证**
- **与 outputs/nvda_covered_call_demo.csv 逐项对齐**

---

## 第四项：约束条件的可验证输入

### 目标
财报窗口、融券利率等约束条件有可追溯的数据源和落盘文件。

### 交付物
- ✅ `CONSTRAINTS_SPECIFICATION.md` - 约束条件说明
  - 财报窗口：数据源（如 Yahoo Finance 财报日历）、落盘文件
  - 融券利率：数据源（如 Interactive Brokers、Markit）、占位符处理
  - 过滤规则：前 3 日 + 后 2 日、< 2% 融券利率

### 验证方式
- `data/earnings_calendar.csv` - 财报日历落盘文件（Demo 使用静态样例）
- `data/short_borrow_rates.csv` - 融券利率落盘文件（Demo 使用静态样例）
- 约束条件分析脚本可独立运行
- **所有约束条件数据必须标注来源**
- **Demo 档数据不能进入研究结论**

---

## 第五项：研究论证输出而不是策略叙事

### 目标
产出因子方案可行性的量化证据，而不是单票三场景的 sanity check。

### 交付物
- ✅ `RESEARCH_REPORT.md` - 完整研究论证报告
  - Rank-IC 分析：因子与收益的秩相关性
  - IC 衰减：不同持有期的 IC 变化
  - 分位数组合收益：Top/Bottom 分位数的收益差
  - 消融实验：财报窗口 on/off、融券利率 on/off
  - 持有期消融：3/5/7 天的对比
  - 成本敏感性：交易成本对收益的影响

### 验证方式
- 报告中包含完整的统计表格和图表
- 每个指标都有明确的计算方式和数据来源
- **所有具体数值必须标注 [DEMO ONLY] 或 [RESEARCH]**
- **所有数值必须能在 outputs/*.csv 中找到**
- **没有未标注的具体数字（如"年化185%"）**
- NVDA 单票三场景作为 sanity check 附录，不作为主要证据

---

## 文件结构

```
RMSC6007_GroupProject/MethodD/
├── DELIVERABLES.md                    # 本文件
├── QUICK_START.md                     # 一键运行指南
├── DATA_SPECIFICATION.md              # 数据口径说明
├── COVERED_CALL_SPECIFICATION.md      # 覆盖式卖 call 定价说明
├── CONSTRAINTS_SPECIFICATION.md       # 约束条件说明
├── RESEARCH_REPORT.md                 # 研究论证报告
├── requirements.txt                   # 固定版本依赖
├── run_all_demos.sh                   # 完整演示脚本
├── src/                               # 源代码
├── experiments/                       # 演示脚本
├── data/                              # 数据目录
│   ├── earnings_calendar.csv          # 财报日历
│   ├── short_borrow_rates.csv         # 融券利率
│   └── cache/                         # 数据缓存
├── outputs/                           # 产出报告
│   ├── factor_analysis_report.csv     # 因子分析报告
│   ├── backtest_results.csv           # 回测结果
│   └── research_report.html           # 研究论证报告
└── logs/                              # 运行日志
    └── run_*.log                      # 运行日志文件
```

---

## 验证清单

- [ ] 第一项：`bash run_all_demos.sh` 能从零到完整结果
  - [ ] logs/run_*.log 存在且 > 100 行
  - [ ] outputs/*.csv 存在且 > 10 行
  - [ ] outputs/research_report.html 存在且 > 10KB
  - [ ] 日志中没有 ERROR 或 CRITICAL

- [ ] 第二项：`DATA_SPECIFICATION.md` 明确说明 IV 定义和数据来源
  - [ ] 分档标准明确（Demo vs Research）
  - [ ] 所有数值结论标注了档次
  - [ ] 没有混用 Demo 和 Research 数据

- [ ] 第三项：`COVERED_CALL_SPECIFICATION.md` 明确 PnL 计算口径
  - [ ] 三个场景都有完整审计表
  - [ ] 所有数字能一行行验证
  - [ ] 与 CSV 输出逐项对齐

- [ ] 第四项：`data/earnings_calendar.csv` 和 `data/short_borrow_rates.csv` 存在
  - [ ] 两个文件都存在
  - [ ] 文件格式正确
  - [ ] Demo 档标注了 [DEMO ONLY]

- [ ] 第五项：`RESEARCH_REPORT.md` 包含指标定义和实验设计
  - [ ] 所有具体数值标注了 [DEMO ONLY]
  - [ ] 没有未标注的具体数字
  - [ ] 所有数值都能在 outputs/*.csv 中找到
  - [ ] 指标定义和实验设计保留

---

## 完成状态

✅ **已完成**：
1. ✅ `QUICK_START.md` - 一键运行指南（含硬要求）
2. ✅ `DATA_SPECIFICATION.md` - 数据口径说明（分档标准）
3. ✅ `COVERED_CALL_SPECIFICATION.md` - 覆盖式卖 call 定价说明（审计表）
4. ✅ `CONSTRAINTS_SPECIFICATION.md` - 约束条件说明（落盘文件）
5. ✅ `RESEARCH_REPORT.md` - 研究论证报告（降级数值）
6. ✅ `DELIVERABLES.md` - 本文件（更新校验点）

⏳ **待完成**：
1. 创建 `run_all_demos.sh` - 完整演示脚本
2. 创建 `data/earnings_calendar.csv` - 财报日历（Demo 样例）
3. 创建 `data/short_borrow_rates.csv` - 融券利率（Demo 样例）
4. 运行演示脚本验证所有交付件
