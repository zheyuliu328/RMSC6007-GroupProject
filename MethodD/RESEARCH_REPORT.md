# MethodD 价格因子研究补充说明（Price Factors）

## 目的
在 IV 上升场景里，方向可能来自“上破扩张”或“下破扩张”。本补充引入三类价格因子，用连续分数统一刻画方向与强度，辅助判断 IV 上升时的对冲方向。

本次新增因子全部基于 **标的历史价格序列**（至少 200 日，建议 260+ 日），并写回 `sample_table`，用于在 `stats_table` 中检验对 `spot_return_5d` 与 `iv_change` 的关系。

---

## 因子 P1：Bollinger Bands 位置 / 带宽

**定义（默认窗口 n=20）：**

- 中轨：`MA20 = mean(Close_{t-19..t})`
- 标准差：`SD20 = std(Close_{t-19..t})`
- 上下轨：`Upper = MA20 + 2·SD20`，`Lower = MA20 − 2·SD20`

**位置分数（方向连续变量）：**

```
BB_pos = (Close_t − MA20) / (2·SD20)
```

**带宽（波动状态）：**

```
BB_bw = (Upper − Lower) / MA20 = 4·SD20 / MA20
```

**作用：**
- `BB_pos` 表示短期分布中的相对位置，正值偏强、负值偏弱。
- `BB_bw` 表示波动扩张或收敛状态。

**为什么：**
同样的 IV 上升，可能是“上涨突破”或“下跌崩溃”。`BB_pos` 把方向统一成可比较的连续分数，适合映射对冲强度。

**例子：**
- MA20=100，SD20=2，Close=104 → `BB_pos = 1.0`
- MA20=100，SD20=2，Close=96 → `BB_pos = -1.0`

**落地字段：**
- `bb_pos_t0`
- `bb_bw_t0`

---

## 因子 P2：MA200 突破强度

**定义：**

- `MA200 = mean(Close_{t-199..t})`
- 标准化因子：`MA200_break = (Close_t − MA200) / ATR20`

**ATR20 说明：**
- 标准版为 ATR（平均真实波幅）
- 若暂缺 High/Low，则可用 20 日 close-to-close 波动替代

**作用：**
衡量价格相对长期基准是否显著偏离，偏离越大越像 regime change。

**为什么：**
短期动量在震荡期容易频繁翻转。MA200 是慢变量，可作为方向过滤器或权重。

**例子：**
- Close=210，MA200=200，ATR20=5 → `MA200_break = 2.0`
- Close=195，MA200=200，ATR20=5 → `MA200_break = -1.0`

**落地字段：**
- `ma200_break_t0`

---

## 因子 P3：MACD 趋势强度（Histogram）

**定义（12,26,9）：**

- `EMA12 = EMA(Close, 12)`
- `EMA26 = EMA(Close, 26)`
- `MACD = EMA12 − EMA26`
- `Signal = EMA(MACD, 9)`
- `MACD_hist = MACD − Signal`

**作用：**
`MACD_hist` 为方向 + 强度的连续量，正且扩大为上行动量增强，负且变小为下行动量增强。

**为什么：**
对冲强度需要连续量，不是单纯多空。MACD_hist 自带强弱信息，适合映射 hedge ratio。

**落地字段：**
- `macd_hist_t0`

---

## 落地方式（最小改动）

### 1) 拉取历史价格序列
在研究脚本中以 `ticker + t0_timestamp` 为锚点，回溯 260~400 个交易日日线，取 Close（及 High/Low）。

### 2) 写回 sample_table
对同一 run 的全部合约写入同一组标的级特征：

- `bb_pos_t0`
- `bb_bw_t0`
- `ma200_break_t0`
- `macd_hist_t0`

同时补齐会议口径的门控字段与阈值（仅用于 gate，不影响连续特征）：

- `iv_signal_median10`：`(IV_t - median(IV_{t-9..t})) / median(IV_{t-9..t})`
- `macd_cross_flag`：MACD 线与 Signal 线交叉（含方向判断）
- `macd_fast_slope`：快线 EMA 的一阶差分斜率
- `bb_midline_break_flag`：价格相对 10 日均线的突破布尔值
- `bb_break_side`：突破方向（above/below）

门控阈值使用固定值：`iv_signal_threshold = 0.15`（不走分位数）

并新增方向目标：

```
spot_return_5d = (spot_t5 - spot_t0) / spot_t0
```

### 3) stats_table 检验
- 对 `spot_return_5d` 做 Spearman IC 与回归
- 并在 `iv_change > 0` 子样本上重复检验，直指“IV 上升时的方向”问题

---

## 数据机制提醒（必须注明）

当前管道若 `t0` 与 `t5` 来自同日补抓，`spot_return_5d` 会接近 0，因子无法体现方向预测力。必须用 `scheduled_capture` 产生真实 5 个交易日间隔样本后再检验。

---

## 代码落地字段清单

**sample_table 新增列：**
- `bb_pos_t0`
- `bb_bw_t0`
- `ma200_break_t0`
- `macd_hist_t0`
- `spot_return_5d`
- `iv_signal_median10`
- `macd_cross_flag`
- `macd_fast_slope`
- `bb_midline_break_flag`
- `bb_break_side`

**stats_table 新增目标/分组：**
- target: `spot_return_5d`
- group: `iv_change_pos`（只看 `iv_change > 0` 子样本）

---

## 对外话术（最简版）
我们加三个 price 因子不是为了预测收益，而是为了解决 IV 上升时方向不确定的问题。Bollinger 给短期位置分数，MA200 给长期趋势过滤强度，MACD_hist 给方向动量强弱。我们用 5 日标的回报方向 `spot_return_5d` 做验证，并在 `iv_change > 0` 子样本里做条件检验，直接回答“IV 上升到底更可能涨还是跌”。