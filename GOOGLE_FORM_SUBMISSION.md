# Google Form Submission Templates

## 选择方案后，直接复制对应的文本到Google Form

---

## 📋 方案A：VaR/ES 风险度量与回测框架

### Proposed Topic
Unified VaR/ES Risk Measurement and Backtesting Framework in Python (Integrating QuantStats, arch, vectorbt)

### Objectives
• Objective 1: Build a unified Python pipeline that computes Value-at-Risk (VaR) and Expected Shortfall (ES) using multiple methods, including Historical Simulation, Parametric (Gaussian), Monte Carlo, and GARCH-based approaches.

• Objective 2: Implement standard backtesting procedures for VaR forecasts, including coverage tests (e.g., Kupiec POF) and independence tests (e.g., Christoffersen), and produce comparable diagnostics across methods.

• Objective 3: Generate reproducible risk reports (tables and visualizations) and a single-click notebook workflow that benchmarks methods across assets and market regimes.

### Data to be Analyzed
• Source 1: Daily adjusted close prices for 5–10 major equity indices or broad-market ETFs (e.g., S&P 500, Hang Seng, Nikkei 225 equivalents) downloaded via Yahoo Finance using yfinance; sample period fixed (e.g., 2015–2025).

• Source 2: Optional risk-free rate series from FRED via pandas-datareader for risk-adjusted metrics (Sharpe and excess-return calculations).

• Preprocessing: Align trading calendars, handle missing values (forward-fill where appropriate), compute log returns, and standardize rolling-window splits for in-sample fitting and out-of-sample evaluation.

### Possible Comparisons
• Comparison 1: Compare VaR/ES estimates across methods by realized exceedances, coverage ratios, and backtesting p-values under a consistent rolling-window protocol.

• Comparison 2: Stress-period robustness comparison by segmenting the sample into regimes (e.g., calm vs. crisis periods) and evaluating model stability and conservativeness.

• Comparison 3: Cross-asset comparison of tail risk: examine how tail behavior differs across markets and whether GARCH-based VaR improves performance during volatility clustering.

### Expected Outcomes
• Outcome 1: A modular, well-documented Python package with a unified API (single function call to compute VaR/ES + backtests) and reproducible notebooks.

• Outcome 2: An empirical benchmark report showing which VaR/ES methods are most accurate and robust across assets and regimes, with clear interpretation of backtesting results.

• Outcome 3: Engineering deliverables including tests (80%+ coverage), environment specification (requirements/lockfile), and an automated HTML/markdown risk report.

### Possible Extensions
• Extension 1: Add portfolio-level risk aggregation (multi-asset VaR/ES) and compare equal-weight vs. optimized portfolios using PyPortfolioOpt.

• Extension 2: Extend volatility modeling (EGARCH/GJR-GARCH) and evaluate incremental benefits over standard GARCH for VaR prediction.

• Extension 3: Provide a lightweight dashboard (e.g., Streamlit) for interactive exploration of risk forecasts and backtesting outcomes.

---

## 📈 方案B：GARCH 波动率预测与VaR链条

### Proposed Topic
Volatility Forecasting with GARCH-family Models and Its Impact on VaR Forecast Accuracy

### Objectives
• Objective 1: Implement and compare GARCH-family models (GARCH, EGARCH, GJR-GARCH) to capture volatility clustering and asymmetry in financial returns.

• Objective 2: Translate conditional volatility forecasts into forward-looking VaR forecasts and evaluate accuracy using rolling out-of-sample backtesting.

• Objective 3: Produce a reproducible benchmark notebook and report that explains model choice, parameter stability, and forecast performance across assets and regimes.

### Data to be Analyzed
• Source 1: Daily return series for a set of indices/ETFs or a diversified basket of liquid large-cap stocks from Yahoo Finance using yfinance, covering 2015-2025.

• Source 2: Optional volatility index proxies (e.g., VIX-like series when available) for external comparison and validation of GARCH-implied volatility.

• Preprocessing: Stationarity checks (ADF test), return transformation, rolling-window splits, and consistent forecasting horizon settings (1-day, 5-day, 20-day ahead).

### Possible Comparisons
• Comparison 1: Model selection comparison using AIC/BIC and forecast error metrics (RMSE, MAE) for realized volatility proxies.

• Comparison 2: VaR backtesting comparison between GARCH-based VaR and simpler VaR approaches (historical/parametric) using Kupiec and Christoffersen tests.

• Comparison 3: Asset-class/market comparison of asymmetry and leverage effects across different equity indices and sectors.

### Expected Outcomes
• Outcome 1: A validated GARCH-based risk forecasting pipeline with clear documentation and reproducible experiments across multiple assets.

• Outcome 2: Evidence-based conclusions on when sophisticated volatility models materially improve VaR performance vs. simpler methods.

• Outcome 3: A reusable codebase for volatility modeling and risk forecasting tasks with 80%+ test coverage.

### Possible Extensions
• Extension 1: Multivariate correlation dynamics (DCC-GARCH) for portfolio-level risk and contagion analysis.

• Extension 2: Regime-switching volatility models for crisis detection and adaptive risk management.

• Extension 3: Link volatility forecasts to dynamic asset allocation constraints and portfolio optimization.

---

## 💼 方案C：因子暴露与风险归因分析

### Proposed Topic
Factor Exposure Estimation and Risk Attribution with Rolling CAPM/Fama-French Models in Python

### Objectives
• Objective 1: Estimate time-varying factor exposures using rolling regressions under CAPM and Fama-French models to quantify systematic risk contributions.

• Objective 2: Perform risk attribution to decompose portfolio variance into factor-driven and idiosyncratic components, enabling targeted risk management.

• Objective 3: Backtest risk forecasts derived from factor models and compare against naive historical-volatility baselines to validate predictive power.

### Data to be Analyzed
• Source 1: Daily returns for a portfolio of stocks/ETFs from Yahoo Finance via yfinance, covering 2015-2025 across multiple sectors.

• Source 2: Factor return series (Fama-French 3-factor and 5-factor models) from Kenneth French's data library, aligned by date; risk-free rate from FRED for excess returns.

• Preprocessing: Date alignment across sources, winsorization of extreme returns (beyond 5 standard deviations), rolling-window estimation choices, and out-of-sample evaluation design.

### Possible Comparisons
• Comparison 1: CAPM vs. FF3/FF5 explanatory power (R², alpha significance, residual volatility) to assess incremental value of multi-factor models.

• Comparison 2: Risk forecast comparison between factor-based and historical-volatility approaches using rolling backtesting.

• Comparison 3: Style/sector portfolio comparison of factor exposures and risk contributions to identify which factors drive risk in different investment styles.

### Expected Outcomes
• Outcome 1: A reproducible framework that outputs rolling betas, factor contributions, and risk decomposition tables/plots for any portfolio.

• Outcome 2: Quantified evidence of which factors drive risk across portfolios and regimes, with clear interpretation of results.

• Outcome 3: Clean, documented code with notebooks demonstrating end-to-end factor risk analytics and actionable insights.

### Possible Extensions
• Extension 1: Incorporate macro factors (interest rates, inflation) and PCA-based dynamic factors for broader economic risk modeling.

• Extension 2: Conditional factor models where factor loadings depend on market conditions (volatility regime, business cycle phase).

• Extension 3: Multi-asset risk attribution (equity + bond + commodity) with cross-asset factor exposures.

---

## 📝 Team Information Template

**Group Leader Name:** [填写]  
**Group Leader Student ID:** [填写]  
**Group Leader Email:** [填写]

**Member 2 Name:** [填写]  
**Member 2 Student ID:** [填写]  
**Member 2 Email:** [填写]

**Member 3 Name:** [填写]  
**Member 3 Student ID:** [填写]  
**Member 3 Email:** [填写]

**Member 4 Name (if applicable):** [填写]  
**Member 4 Student ID:** [填写]  
**Member 4 Email:** [填写]

**Member 5 Name (if applicable):** [填写]  
**Member 5 Student ID:** [填写]  
**Member 5 Email:** [填写]
