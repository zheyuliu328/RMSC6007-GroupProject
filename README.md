# RMSC 6007 Group Project - 项目选择与执行指南

**课程**: Risk and Financial Data Analytics with Python (RMSC 6007)  
**学期**: Term 2, 2025-26  
**Proposal截止**: 2026年1月25日中午12:00

---

## 📚 项目概述

本项目要求小组选择一个**融合多个开源Python库**的金融风险分析框架，通过统一接口、可复现实验、自动化报告等方式，展示对时间序列、GARCH、VaR、回测等课程核心内容的理解和应用。

**核心原则**：
- ✅ 基于现有开源库（100+ stars）进行集成与扩展
- ✅ 明确标注来源与贡献（LICENSE + 文档）
- ✅ 交付物是"统一接口 + 可复现实验 + 自动化报告"
- ✅ 不是"从零开始重写"，而是"有意义的工程集成"

---

## 🤝 协同与复现（必读）

本项目协同流程已制度化，**main 分支只接可运行版本**，所有改动必须走 feature 分支 + PR 审阅。

- 协同规则：`CONTRIBUTING.md`
- PR 模板：`pull_request_template.md`
- Issue 模板：`.github/ISSUE_TEMPLATE/`
- 数据快照不进 Git（Release 附件或独立 data repo）

复现最小流程：

```bash
python3 MethodD/tools/capture_snapshots.py --ticker NVDA t0
python3 MethodD/tools/capture_snapshots.py t5
python3 MethodD/experiments/run_iv_factor_study.py
```

---

## 🎯 三个项目方案

### 📋 方案A：VaR/ES 风险度量与回测框架 ⭐⭐⭐⭐⭐ **推荐**

**难度**: ⭐⭐⭐ | **工作量**: 中等 | **展示效果**: 最好

**核心库**: QuantStats (6.6k⭐) + arch (1.5k⭐) + vectorbt (6.5k⭐)

**主要内容**:
- 4种VaR/ES方法（Historical、Parametric、Monte Carlo、GARCH）
- 规范回测（Kupiec POF + Christoffersen独立性检验）
- 自动化HTML报告与对比表

**为什么选A**:
- 覆盖面最广，工程交付清晰
- 展示效果最好（对比表、可视化）
- 工作量可控，12周内完成
- 可扩展性强（GARCH作Extension）

**详见**: `MethodA/README.md`

---

### 📈 方案B：GARCH 波动率预测与VaR链条 ⭐⭐⭐⭐⭐

**难度**: ⭐⭐⭐⭐ | **工作量**: 中等偏高 | **展示效果**: 学术深度最高

**核心库**: arch (1.5k⭐) + statsmodels (10k+⭐) + vectorbt (6.5k⭐)

**主要内容**:
- 多种GARCH模型（GARCH、EGARCH、GJR-GARCH、TGARCH）
- 波动率预测与VaR转换
- 模型对比与性能评估

**为什么选B**:
- 学术深度最高，适合想深入研究的团队
- 覆盖RMSC课程的核心内容（GARCH、时间序列）
- 可发展成学术论文

**详见**: `MethodB/README.md`

---

### 💼 方案C：因子暴露与风险归因分析 ⭐⭐⭐⭐

**难度**: ⭐⭐⭐⭐ | **工作量**: 中等偏高 | **展示效果**: 最专业

**核心库**: linearmodels (1.1k⭐) + statsmodels (10k+⭐)

**主要内容**:
- CAPM与Fama-French因子模型
- 时间变化的因子暴露估计
- 风险归因与回测

**为什么选C**:
- 最专业、最"资产管理"
- 因子分析是业界标准方法
- 适合有金融背景的团队

**详见**: `MethodC/README.md`

---

## 📅 时间表

| 阶段 | 时间 | 任务 |
|------|------|------|
| **提案** | 1月25日中午 | 提交Google Form |
| **第1-3周** | 1月26-2月8日 | 框架搭建、核心模块实现 |
| **第4-6周** | 2月9-2月22日 | 集成、优化、回测 |
| **第7-9周** | 2月23-3月8日 | 文档、测试、报告 |
| **第10-12周** | 3月9-3月22日 | 最终演示、提交 |

---

## 📂 项目文件结构

```
RMSC6007_GroupProject/
├── README.md                          # 本文件
├── MEETING_CHECKLIST.md               # 今晚7:30会议清单
├── GOOGLE_FORM_SUBMISSION.md          # Google Form提交文本
├── WEEK1_TASKS.md                     # 第一周任务分工
│
├── MethodA/
│   ├── README.md                      # 方案A详细说明
│   └── requirements.txt               # 方案A依赖
│
├── MethodB/
│   ├── README.md                      # 方案B详细说明
│   └── requirements.txt               # 方案B依赖
│
└── MethodC/
    ├── README.md                      # 方案C详细说明
    └── requirements.txt               # 方案C依赖
```

---

## 🚀 快速开始

### 步骤1：今晚7:30会议（30分钟）
1. 展示三个方案README
2. 投票选择方案（A/B/C）
3. 确认数据范围（5-10个资产）
4. 分工确认（5人分工）
5. 确定Proposal写作负责人

**使用**: `MEETING_CHECKLIST.md`

### 步骤2：明天上午（提交前）
1. 完成Proposal英文写作
2. 全组审校
3. 填写Google Form
4. **中午12:00前提交**

**使用**: `GOOGLE_FORM_SUBMISSION.md`

### 步骤3：明天下午（提交后）
1. 创建GitHub repo
2. 初始化项目结构
3. 分配第一周任务

**使用**: `WEEK1_TASKS.md`

---

## 📋 Google Form 提交清单

- [ ] 选定方案（A/B/C）
- [ ] 5人信息完整（学号、邮箱）
- [ ] Topic清晰明确
- [ ] Objectives（3个）
- [ ] Data to be Analyzed（2-3个数据源）
- [ ] Possible Comparisons（3个）
- [ ] Expected Outcomes（3个）
- [ ] Possible Extensions（3个）
- [ ] 英文语法检查
- [ ] **中午12:00前提交**

---

## 👥 分工模板（5人）

| 角色 | 职责 | 交付物 |
|------|------|--------|
| **项目经理** | Repo结构、API设计、集成 | 统一API、demo脚本 |
| **成员B** | 风险模型实现 | VaR/ES方法、单元测试 |
| **成员C** | 回测框架 | 统计检验、结果表格 |
| **成员D** | 数据工程 | 数据脚本、Notebook |
| **成员E** | 报告可视化 | HTML报告、文档 |

---

## ✅ 验收标准

### 最终交付物必须包含：
1. **Python包**: 可通过`pip install -e .`安装
2. **统一API**: 单一函数调用完成分析
3. **Jupyter Notebook**: 一键跑通的完整演示
4. **自动化报告**: HTML/Markdown格式
5. **单元测试**: 80%+代码覆盖率
6. **完整文档**: API参考、使用指南、方法论
7. **GitHub repo**: 清晰的提交历史、PR审查记录

### 代码质量标准：
- ✅ 遵循PEP 8规范
- ✅ 所有函数有docstring
- ✅ 错误处理完善
- ✅ 数值稳定性检查
- ✅ 可复现性（固定随机种子）

---

## 🔗 关键资源

### 开源库文档
- [QuantStats](https://github.com/ranaroussi/quantstats)
- [arch](https://github.com/bashtage/arch)
- [vectorbt](https://github.com/polakowo/vectorbt)
- [PyPortfolioOpt](https://github.com/PyPortfolio/PyPortfolioOpt)
- [linearmodels](https://github.com/bashtage/linearmodels)

### 数据源
- [Yahoo Finance (yfinance)](https://github.com/ranaroussi/yfinance)
- [FRED (pandas-datareader)](https://pandas-datareader.readthedocs.io/)
- [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)

### 参考文献
- Basel Committee (2019). Minimum capital requirements for market risk
- Christoffersen, P. (1998). Evaluating interval forecasts
- Kupiec, P. (1995). Techniques for verifying the accuracy of risk measurement models
- Fama, E., & French, K. (1993). Common risk factors in stock returns

---

## 📞 支持与沟通

- **项目经理**: 协调跨模块问题
- **周会**: 每周一晚上7:30
- **代码审查**: 所有PR需要至少1人审核
- **紧急问题**: 立即在团队渠道反馈

---

## 🎓 学习目标

通过本项目，你将学到：
- ✅ 如何集成多个开源库
- ✅ 金融风险度量的实践应用
- ✅ 时间序列与GARCH建模
- ✅ 统计回测与模型验证
- ✅ 专业的Python工程实践
- ✅ 团队协作与项目管理

---

## 📝 许可证与归属

本项目基于以下开源库：
- QuantStats (Apache 2.0)
- arch (University of Illinois/NCSA)
- vectorbt (Apache 2.0)
- linearmodels (BSD 3-Clause)

所有贡献必须明确标注来源，保留原项目LICENSE文件。

---

**准备好了吗？今晚7:30见！** 🚀
