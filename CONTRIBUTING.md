# 协同贡献规范（RMSC6007 Group Project）

本项目采用 **GitHub 私有仓库 + PR 审阅 + 固定产物** 的协同模式，目标是确保**同一份输入快照、同一份代码版本、同一套命令**，任何人都能复现相同的 `sample_table.csv` 与 `stats_table.csv`。

## 1. 分支与发布规则

- **main 分支永远保持可运行**：
  - `python3 MethodD/tools/capture_snapshots.py ...`
  - `python3 MethodD/experiments/run_iv_factor_study.py`
  - main 不接受半成品或无法复现的提交。

- **个人改动必须走 feature 分支 + PR**：
  - 命名规范：`feat/<name>-<topic>`
  - 示例：`feat/alice-report-edits`、`feat/bob-factor-v2`

## 2. PR 必须回答的三件事

1. **口径是否变化**
   - manifest schema、pricing_rule、过滤阈值、样本定义、目标变量定义
2. **可复现性是否破坏**
   - 同一快照包 + 同一 commit 产物一致
3. **输出是否变化**
   - `MethodD/outputs/sample_table.csv`
   - `MethodD/outputs/stats_table.csv`

## 3. 数据快照策略

- **代码仓库只保留 schema / 脚本 / 小型示例快照**。
- **真实快照不进 Git**，使用以下方式之一：
  1. GitHub Release 附件（zip）
  2. 独立私有仓库：`MethodD-data`

## 4. 提交规范

- 每次提交尽量聚焦一个主题（单功能/单修复）。
- 必须在 PR 描述中列出：
  - 修改文件列表
  - 影响的命令
  - 是否更改口径
  - 是否新增/修改输出 CSV

## 5. 权限与角色

- **Owner 权限**（你本人）保留：
  - 合并 main 权限
  - 修改采集口径与 manifest schema 权限
- 其他成员只允许走 feature 分支提交 PR。

## 6. 复现实验最小流程

```bash
python3 MethodD/tools/capture_snapshots.py --ticker NVDA t0
python3 MethodD/tools/capture_snapshots.py t5
python3 MethodD/experiments/run_iv_factor_study.py
```

产物：
- `MethodD/outputs/sample_table.csv`
- `MethodD/outputs/stats_table.csv`
