# MethodD 一键运行指南

## 快速开始

本指南提供从零到完整结果的一键运行路径。

### 前置条件

- Python 3.8+
- pip 或 conda

### Docker 快速开始（推荐）

统一容器复现，解决组员环境不一致问题：

```bash
cd RMSC6007_GroupProject/MethodD
docker compose build
docker compose run --rm methodd
```

**验收复现（容器内一键跑通闭环）**：

```bash
cd ~/Documents/RMSC6007_GroupProject/MethodD

# 1) 运行并确认退出码
docker compose run --rm -T methodd; echo $?

# 2) 确认最新日志无 ERROR/Traceback
ls -t logs/run_*.log | head -n 1
grep -n "ERROR\|Traceback\|❌" -n "$(ls -t logs/run_*.log | head -n 1)" || echo "NO_ERROR_FOUND"

# 3) 确认 outputs/checksums.md5 非空
test -s outputs/checksums.md5 && echo OK
```

**说明**：
- 容器入口固定为 `bash run_all_demos.sh`
- `logs/`、`outputs/`、`data/` 会映射回宿主机

**注意**：
- NVDA 覆盖式卖 call 默认读取 `data/snapshots/` 内的离线真实快照，不联网
- 缺少 manifest / checksum / t0/t5 快照任意一项将直接 FAIL
- 校验以“文件存在、字段齐全、checksum 一致、日志无 ERROR”为硬门槛
- Hash 为审计要求，不可省略

**修复记录**：
- 已将 `fillna(method=...)` 替换为 `ffill/bfill`，避免 pandas 版本兼容报错。

### 第一步：安装依赖

```bash
cd RMSC6007_GroupProject/MethodD

# 创建虚拟环境（可选但推荐）
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖（固定版本）
pip install -r requirements.txt
```

### 第二步：运行完整演示

```bash
# 方式 1：运行所有演示脚本（推荐）
bash run_all_demos.sh 2>&1 | tee logs/run_$(date +%Y%m%d_%H%M%S).log

# 方式 2：逐个运行演示脚本
python3 experiments/run_iv_factor_demo.py
python3 experiments/run_nvda_covered_call_demo.py
python3 experiments/run_constraints_analysis.py
```

### 第三步：验证输出（硬要求）

运行完成后，**必须检查以下文件是否存在且非空**：

**日志文件**（必须存在）：
```bash
ls -lh logs/run_*.log
# 预期：文件大小 > 1KB
```

**输出文件**（必须存在）：
```bash
ls -lh outputs/
# 预期文件：
# - factor_analysis_report.csv (> 1KB)
# - backtest_results.csv (> 1KB)
# - nvda_covered_call_demo.csv (> 1KB)
# - research_report.html (> 10KB)
```

**验证命令**：
```bash
# 检查日志行数
wc -l logs/run_*.log
# 预期：> 100 行

# 检查CSV行数
wc -l outputs/*.csv
# 预期：每个CSV > 10 行

# 检查文件哈希（用于复现验证）
md5sum logs/run_*.log outputs/*.csv
```

**判定成功的校验点**：
- ✅ logs/run_*.log 存在且 > 100 行
- ✅ outputs/*.csv 存在且 > 10 行
- ✅ outputs/research_report.html 存在且 > 10KB
- ✅ 所有CSV文件都能用 pandas 读取
- ✅ 日志中没有 ERROR 或 CRITICAL

**如果验证失败**：
- 检查 logs/run_*.log 中的错误信息
- 确保网络连接正常（Yahoo Finance 可能有速率限制）
- 删除缓存重试：rm -rf data/cache/

---

## 演示脚本说明

### 1. IV 因子演示 (run_iv_factor_demo.py)

展示 IV 因子的基础功能：

```bash
python3 experiments/run_iv_factor_demo.py
```

**输出**：
- 因子计算（Version A 和 Version B）
- Rank-IC 分析
- 信号生成（阈值和分位数策略）
- 基础回测结果

**预期运行时间**：2-5 分钟

---

### 2. NVDA 覆盖式卖 call 演示 (run_nvda_covered_call_demo.py)

默认模式为离线真实快照复算：

```bash
python3 experiments/run_nvda_covered_call_demo.py
```

**严格抓取（落盘 t0/t5 快照）**：

```bash
python3 experiments/run_nvda_covered_call_demo.py --strict-t0
# 第 5 个交易日后再运行
python3 experiments/run_nvda_covered_call_demo.py --strict-t5
```

**研究样本累积（前向采集 + 可复算统计）**：

目标：累计 20–40 个交易日的 t0/t5 快照样本。每次 t0 生成独立 run_id，t5 必须带 run_id 以避免覆盖。

```bash
# 每天收盘后抓 t0（会输出 run_id）
python3 tools/capture_snapshots.py t0 --ticker NVDA

# 第 5 个交易日后再抓 t5（必须带 run_id）
python3 tools/capture_snapshots.py t5 --run-id <RUN_ID>

# 累积样本后生成统计输出
python3 experiments/run_iv_factor_study.py
```

**定时定点采集（推荐）**：

```bash
# t0 + t5 回填一体化（维护 index.csv）
python3 tools/scheduled_capture.py --tickers NVDA --mode both

# 仅采集 t0
python3 tools/scheduled_capture.py --tickers NVDA,AAPL --mode t0

# 仅回填 t5
python3 tools/scheduled_capture.py --mode t5
```

说明：
- `data/snapshots/runs/index.csv` 会记录 run_id、t5_due_date、回填状态。
- 建议在美股收盘附近运行，保证 bid/ask 完整性。
- t5 回填会自动扫描 runs/ 目录，补齐已到期批次。

**macOS 定时任务（launchd，两档兜底）**：

- 主档：北京时间 06:20（收盘后高质量）
- 副档：北京时间 09:30（补偿档，防断档）

步骤：
1. 复制以下两个 plist 到 `~/Library/LaunchAgents/`
2. 执行 `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/<plist文件>`
3. `launchctl list | grep methodd` 确认已加载

主档 `com.methodd.capture.close.plist`（06:20）：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key><string>com.methodd.capture.close</string>
    <key>ProgramArguments</key>
    <array>
      <string>/usr/bin/python3</string>
      <string>tools/scheduled_capture.py</string>
      <string>--tickers</string><string>NVDA,AAPL,MSFT</string>
      <string>--mode</string><string>both</string>
    </array>
    <key>WorkingDirectory</key><string>/Users/zheyuliu/Documents/RMSC6007_GroupProject/MethodD</string>
    <key>StartCalendarInterval</key>
    <dict><key>Hour</key><integer>6</integer><key>Minute</key><integer>20</integer></dict>
    <key>StandardOutPath</key><string>data/snapshots/runs/launchd_capture.log</string>
    <key>StandardErrorPath</key><string>data/snapshots/runs/launchd_capture.err</string>
  </dict>
</plist>
```

副档 `com.methodd.capture.fallback.plist`（09:30）：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key><string>com.methodd.capture.fallback</string>
    <key>ProgramArguments</key>
    <array>
      <string>/usr/bin/python3</string>
      <string>tools/scheduled_capture.py</string>
      <string>--tickers</string><string>NVDA,AAPL,MSFT</string>
      <string>--mode</string><string>both</string>
    </array>
    <key>WorkingDirectory</key><string>/Users/zheyuliu/Documents/RMSC6007_GroupProject/MethodD</string>
    <key>StartCalendarInterval</key>
    <dict><key>Hour</key><integer>9</integer><key>Minute</key><integer>30</integer></dict>
    <key>StandardOutPath</key><string>data/snapshots/runs/launchd_capture.log</string>
    <key>StandardErrorPath</key><string>data/snapshots/runs/launchd_capture.err</string>
  </dict>
</plist>
```

可选（自动唤醒）：
```bash
# 每天 06:10 唤醒（给网络缓冲）
sudo pmset repeat wakeorpoweron MTWRFSU 06:10:00
```

**输出文件（唯一审计来源）**：
- `outputs/sample_table.csv`（全量样本，每笔观测的 t0/t5、IV、点差、因子值）
- `outputs/sample_table_tradable.csv`（可交易样本子集）
- `outputs/stats_table_tradable.csv`（主结论：可交易样本的 IC/t-stat/回归/分组）
- `outputs/stats_table_full.csv`（附录：全量样本统计）

**输出**：
- 单条 realized PnL（Stock/Option/Total）
- 同合约匹配状态与失败原因
- t0/t5 的 bid/ask/last、mid_used、price_used、iv、spot

**预期运行时间**：1-2 分钟（离线）

---

### 3. 约束条件分析演示 (run_constraints_analysis.py)

展示财报窗口和融券利率的约束条件：

```bash
python3 experiments/run_constraints_analysis.py
```

**输出**：
- 财报窗口过滤（前 3 日 + 后 2 日）
- 融券利率过滤（< 2%）
- 综合约束条件影响

**预期运行时间**：1-2 分钟

---

## 数据缓存

首次运行时，IV 因子链路可能从 Yahoo Finance 下载数据并缓存到 `data/cache/` 目录。后续运行会使用缓存数据，速度会更快。

如果需要重新下载数据，删除 `data/cache/` 目录即可：

```bash
rm -rf data/cache/
```

---

## 故障排除

### 问题 1：yfinance 下载失败

**症状**：`Error downloading data from Yahoo Finance`

**解决方案**：
1. 检查网络连接
2. 等待几分钟后重试（Yahoo Finance 可能有速率限制）
3. 删除缓存重新下载：`rm -rf data/cache/`

### 问题 2：缺少依赖

**症状**：`ModuleNotFoundError: No module named 'xxx'`

**解决方案**：
```bash
pip install -r requirements.txt
```

### 问题 3：权限错误

**症状**：`Permission denied: 'run_all_demos.sh'`

**解决方案**：
```bash
chmod +x run_all_demos.sh
bash run_all_demos.sh
```

### 问题 4：样本数量不足

**症状**：`sample_table_tradable.csv` 行数太少或 stats 为空

**解决方案**：
1. 确认已有 t0/t5 快照与 manifest/sha256（位于 data/snapshots/runs/<run_id>/）
2. 按交易日持续采集 20–40 天（每日新 run_id）
3. 重新运行 `python3 experiments/run_iv_factor_study.py`

---

## 验证运行成功

运行完成后，检查以下文件是否存在：

```bash
# 检查输出文件
ls -la outputs/

# 检查日志文件
ls -la logs/

# 检查数据缓存
ls -la data/cache/
```

如果所有文件都存在，说明运行成功。

---

## 下一步

1. 阅读 `DATA_SPECIFICATION.md` 了解数据口径
2. 阅读 `COVERED_CALL_SPECIFICATION.md` 了解 PnL 计算方式
3. 阅读 `CONSTRAINTS_SPECIFICATION.md` 了解约束条件
4. 阅读 `RESEARCH_REPORT.md` 查看完整的研究论证

---

## 支持

如有问题，请检查：
1. Python 版本：`python3 --version`
2. 依赖版本：`pip list`
3. 运行日志：`logs/run_*.log`
