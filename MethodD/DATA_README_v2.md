# MethodD 数据统一说明书（v2）

## 0. 只解决一件事
所有人使用 **同一份 Nasdaq 全量口径数据**，结果可复算且一致。

---

## 1. 三条铁律（必须遵守）
1. **唯一索引**：`run_id = "{date}|{ticker}"`
2. **固定随机源**：全局 `seed` + `seed + hash(ticker)`
3. **固定 schema**：字段/含义定死，改动必须走 PR + 更新契约说明

---

## 2. 本次 v2 统一了什么

### 2.1 Nasdaq 全量 Universe
- `data/universe/nasdaq/nasdaqlisted_snapshot.txt`
- `data/universe/nasdaq/universe.csv`

### 2.2 分区 Parquet（不进 Git）
按 ticker 分区存储，仓库只保留生成器与契约文件。

### 2.3 固化 Pool（High Cap + High Beta）
- `data/simulated/nasdaq_full/v1/universe_meta.csv`
- `data/simulated/nasdaq_full/v1/pool_membership.csv`

### 2.4 Options Premium 最小表
- `data/simulated/nasdaq_full/v1/options/`
- 字段：`date, ticker, run_id, tenor_days, strike_type(ATM), call_premium, put_premium`

### 2.5 门控字段 + 固定阈值
- `iv_signal_median10`，阈值 **0.15**（固定，不走分位数）
- `macd_cross_flag` + `macd_fast_slope`
- `bb_midline_break_flag` + `bb_break_side`

---

## 3. 数据契约清单（可提交 Git 的轻量文件）

**Universe**
- `data/universe/nasdaq/nasdaqlisted_snapshot.txt`
- `data/universe/nasdaq/universe.csv`

**配置（唯一允许手动改的输入）**
- `data/simulated/nasdaq_full/v1/config.yaml`

**完整性锚点**
- `data/simulated/nasdaq_full/v1/manifest.json`

---

## 4. 新手流程（只需要复制命令）

### 4.1 生成统一 universe
```bash
cd MethodD
python3 scripts/fetch_universe.py
```

### 4.2 生成 nasdaq-full v1
```bash
python3 scripts/generate_sim_data.py \
  --config data/simulated/nasdaq_full/v1/config.yaml \
  --universe data/universe/nasdaq/universe.csv
```

### 4.3 统一验收（必须跑）
```bash
python3 scripts/validate_sim_data.py \
  --data-dir data/simulated/nasdaq_full/v1 \
  --universe data/universe/nasdaq/universe.csv
```
**通过标准**：manifest hash OK、run_id 正常、分区完整、IV spike 在区间。

---

## 5. 绝对禁止（会把仓库炸掉）
不要 push 以下目录：
- `data/simulated/nasdaq_full/v1/prices/`
- `data/simulated/nasdaq_full/v1/iv/`
- `data/simulated/nasdaq_full/v1/targets/`
- `data/simulated/nasdaq_full/v1/options/`

这些目录已在 `.gitignore` 忽略，正常不会被提交。

---

## 6. 会上策略口径（简版）
- **IV gate**：`iv_signal_median10 > 0.15`
- **MACD gate**：交叉 + 快线斜率
- **BB gate**：10 日中线突破
- **Pool**：High Cap + High Beta（见 `pool_membership.csv`）
- **Options**：最小 premium 表用于 covered call / short put

---

## 7. 需要改契约时
只允许改：`config.yaml` + `dataset_version`。
如果新增字段或改含义，必须同步更新：
- 生成器脚本
- validate 脚本
- README + 本文件
- manifest 逻辑