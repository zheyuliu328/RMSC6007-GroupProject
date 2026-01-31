# MethodD: IV 收敛因子测试架构

**RMSC 6007 Group Project | Term 2, 2025-26**

## 🚀 新手首选：2分钟 Docker 一键跑通（最推荐）

**适合第一次上手的同学**：不用本地装 Python 环境，按步骤复制即可。

**前置（只需一次）**
1. 安装并启动 **Docker Desktop**
2. 确保终端能运行 `docker` 命令（首次可能需要重启终端）

**macOS 安装流程（通用版）**
1. 访问 https://www.docker.com/products/docker-desktop/ 下载 macOS 安装包
2. 按提示安装后，打开 Docker Desktop 并等待状态显示为 “Running”
3. 首次启动若提示权限（如系统扩展/后台项目），按提示允许并重启
4. 终端执行 `docker version`，确认客户端与服务端均可访问

**Windows 安装流程（通用版）**
1. 访问 https://www.docker.com/products/docker-desktop/ 下载 Windows 安装包
2. 安装过程中如提示启用 **WSL2** 或 **Hyper-V**：按向导开启并重启
3. 重启后打开 Docker Desktop，等待状态显示为 “Running”
4. PowerShell 执行 `docker version`，确认客户端与服务端均可访问

**通用检查清单（两端一致）**
- `docker version` 显示 Client/Server 都有信息
- `docker info` 不报错，且能看到运行状态
- 首次使用建议重启终端，避免 PATH 未刷新

**一步跑通**
```bash
cd MethodD
docker compose run --rm -T methodd
```

**你会得到的产物**
- logs/run_*.log
- outputs/checksums.md5
- outputs/nvda_covered_call_demo.csv

**验收（推荐）**
```bash
make verify
```

**常见问题（新手提示）**
- 如果提示 `Cannot connect to the Docker daemon`：先打开 Docker Desktop 等待启动完成
- 如果提示 `command not found: docker`：确认 Docker Desktop 已安装并重启终端

## 🎯 项目概述

一个专业级的 IV（隐含波动率）收敛因子研究系统，用于测试 IV 偏离是否预测未来正股超额收益，以及期权叠加策略是否改善风险收益。

### 核心特性
- **双链路验证**：因子有效性链路（不碰期权执行）+ 交易可行性链路（期权叠加结构）
- **可复现架构**：数据快照、因子定义、信号规则、成本模型、对照实验
- **消融实验**：逐项关闭规则看效果变化，验证逻辑链条
- **Walk-Forward 验证**：样本外验证，避免过拟合

## 🛠️ 技术栈

| 组件 | 库 | 用途 |
|------|-----|------|
| **数据获取** | yfinance | 正股价格 |
| **数据处理** | pandas, numpy | 时间序列处理 |
| **因子计算** | pandas | IV 因子定义 |
| **期权定价** | scipy.stats | Black-Scholes 定价 |
| **回测** | pandas, numpy | 信号回测 |
| **可视化** | matplotlib, pandas | 结果展示 |

## 📁 项目结构

```
MethodD/
├── README.md                          # 本文件
├── IV_FACTOR_ARCHITECTURE.md          # 详细架构设计
├── requirements.txt                   # 依赖
│
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── data_adapter.py           # 数据源适配器
│   │   ├── data_store.py             # 数据存储
│   │   └── data_validator.py         # 数据质量检查
│   │
│   ├── factor/
│   │   ├── __init__.py
│   │   ├── factor_definition.py      # 因子定义（Version A/B）
│   │   ├── neutralizer.py            # 中性化处理
│   │   └── bucketizer.py             # 分组处理
│   │
│   ├── signal/
│   │   ├── __init__.py
│   │   ├── signal_policy.py          # 信号生成规则
│   │   └── filters.py                # 事件过滤器
│   │
│   ├── pricing/
│   │   ├── __init__.py
│   │   ├── bs_pricer.py              # Black-Scholes 定价
│   │   └── option_chain_pricer.py    # 期权链定价
│   │
│   ├── backtest/
│   │   ├── __init__.py
│   │   ├── backtest_runner.py        # 回测引擎
│   │   ├── walk_forward_splitter.py  # 样本外切分
│   │   └── execution_simulator.py    # 执行模拟
│   │
│   ├── eval/
│   │   ├── __init__.py
│   │   ├── metrics.py                # 评估指标
│   │   └── ablation.py               # 消融实验
│   │
│   └── report/
│       ├── __init__.py
│       └── report_builder.py         # 报告生成
│
├── experiments/
│   ├── config_baseline.yaml          # 基础配置
│   └── config_with_options.yaml      # 期权配置
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_factor_analysis.ipynb
│   ├── 03_backtest_results.ipynb
│   └── 04_ablation_study.ipynb
│
├── tests/
│   ├── test_data_loader.py
│   ├── test_factor.py
│   ├── test_signal.py
│   └── test_backtest.py
│
└── data/
    ├── raw/                          # 原始数据快照
    └── processed/                    # 清洗后数据
```

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行最小可行模拟
```bash
python experiments/run_iv_factor_demo.py
```

### 3. NVDA 覆盖式卖 call（离线真实快照复算）

默认模式不联网，必须存在 `data/snapshots/runs/<run_id>/manifest.json` 与 t0/t5 快照 + checksum。

```bash
python experiments/run_nvda_covered_call_demo.py
```

如需抓取真实快照（严格模式，仅抓取 + 落盘）：

```bash
python tools/capture_snapshots.py t0 --ticker NVDA
# 第 5 个交易日后再运行（指定 run_id）
python tools/capture_snapshots.py t5 --run-id <RUN_ID>
```

**定时定点采集（推荐）**：

```bash
# 同时执行 t0 采集 + 到期 t5 回填（维护 index.csv）
python tools/scheduled_capture.py --tickers NVDA --mode both

# 只抓 t0
python tools/scheduled_capture.py --tickers NVDA,AAPL --mode t0

# 只回填 t5
python tools/scheduled_capture.py --mode t5
```

说明：
- 脚本会在 `data/snapshots/runs/` 下维护 `index.csv`，记录 run_id、t5_due_date、回填状态。
- 建议在美股收盘附近运行（保证 bid/ask 完整）。
- run_id 永不覆盖，适合长期累计样本池。

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

**醒来补跑（建议开启）**：

如果机器睡眠错过定点任务，可以用“登录即跑 + 每 2 小时补跑”兜底（不要求 pmset 唤醒）。

示例 `com.methodd.scheduled_capture.plist`：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key><string>com.methodd.scheduled_capture</string>
    <key>ProgramArguments</key>
    <array>
      <string>/usr/bin/python3</string>
      <string>/Users/zheyuliu/Documents/RMSC6007_GroupProject/MethodD/tools/scheduled_capture.py</string>
      <string>--mode</string><string>both</string>
      <string>--tickers</string><string>NVDA,AAPL,MSFT,AMZN,TSLA</string>
    </array>
    <key>StartInterval</key><integer>7200</integer>
    <key>RunAtLoad</key><true/>
    <key>WorkingDirectory</key><string>/Users/zheyuliu/Documents/RMSC6007_GroupProject/MethodD</string>
    <key>StandardOutPath</key><string>logs/scheduled_capture.out</string>
    <key>StandardErrorPath</key><string>logs/scheduled_capture.err</string>
  </dict>
</plist>
```

说明：
- `RunAtLoad` 确保登录后立即补跑。
- `StartInterval` 每 2 小时扫一次，自动补齐到期 t5。
- 若机器长期睡眠，需结合 pmset 唤醒才能“无人值守”执行。

### 4. 查看结果
```bash
# 因子有效性检验
python experiments/factor_effectiveness_test.py

# 期权叠加策略检验
python experiments/option_strategy_test.py
```

## 📊 核心概念

### 因子定义
**Version A（聊天版）**：
```
f_t = (IV_t - median(IV_{t-9..t})) / median(IV_{t-9..t})
```

**Version B（研究版稳健标准化）**：
```
z_t = (IV_t - median(IV_{t-9..t})) / MAD(IV_{t-9..t})
其中 MAD = median(|x - median(x)|)
```

### 信号规则
- **分位数策略**：Top Q 做空、Bottom Q 做多
- **阈值策略**：f_t < -0.15 做多、f_t > 0.15 做空

### 持有期
- H = 5 日（默认）
- 支持参数化：3/5/7/10 日

### 成本模型
- 交易成本：0/低/中/高
- 借券费率：可配置
- 点差：固定或比例

## 📈 消融实验清单

- [ ] 剔除财报窗口 on/off
- [ ] 因子 A vs 因子 B
- [ ] 阈值策略 vs 分位策略
- [ ] 持有期 3/5/7/10
- [ ] 成本 0/低/中/高
- [ ] 覆盖式卖 call on/off

## 📋 验收标准

### 因子层（必须）
- ✅ IV 数据获取与清洗
- ✅ 因子计算（Version A/B）
- ✅ Rank-IC 分析
- ✅ 分位数组合收益
- ✅ 财报窗口对照实验

### 策略层（可选）
- ✅ 期权定价（Black-Scholes）
- ✅ 覆盖式卖 call 结构
- ✅ 回撤与收益曲线对比
- ✅ 成本敏感性分析

## 🔗 参考资源

- [IV 因子架构设计](./IV_FACTOR_ARCHITECTURE.md)
- [实现指南](./IMPLEMENTATION_GUIDE.md)

## 📝 许可证

BSD 3-Clause License
