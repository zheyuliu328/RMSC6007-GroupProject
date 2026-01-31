# Factor Exposure and Risk Attribution Framework

**RMSC 6007 Group Project | Term 2, 2025-26**

## 🎯 Project Overview

A professional-grade Python toolkit for estimating systematic risk exposures using CAPM and Fama-French models, with comprehensive risk attribution and backtesting capabilities.

### Key Features
- **Factor Models**: CAPM, Fama-French 3-factor, Fama-French 5-factor
- **Rolling Regressions**: Time-varying beta estimation
- **Risk Decomposition**: Factor contributions to portfolio variance
- **Backtest Framework**: Out-of-sample risk prediction validation

## 🛠️ Technology Stack

### Core Libraries
- **linearmodels** (1.1k⭐) - Panel regression and rolling estimation
- **statsmodels** (10k+⭐) - OLS and statistical tests
- **pandas-datareader** (2.9k⭐) - Fama-French data access
- **yfinance** (14.5k⭐) - Stock returns
- **QuantStats** (6.6k⭐) - Performance analytics

## 📁 Project Structure

```
factor-risk-framework/
├── README.md
├── requirements.txt
├── LICENSE
│
├── data/
│   ├── stock_returns/    # Individual stock data
│   ├── factor_returns/   # FF factors from Ken French
│   └── portfolios/       # Constructed portfolios
│
├── src/
│   ├── factor_loader.py      # FF data downloader
│   ├── exposure_estimation.py # Rolling regressions
│   ├── risk_attribution.py   # Variance decomposition
│   ├── backtesting.py        # Risk forecast validation
│   └── portfolio_builder.py  # Portfolio construction
│
├── notebooks/
│   ├── 01_factor_data.ipynb
│   ├── 02_exposure_analysis.ipynb
│   ├── 03_risk_attribution.ipynb
│   └── 04_backtest_results.ipynb
│
├── tests/
│   ├── test_exposures.py
│   ├── test_attribution.py
│   └── test_backtesting.py
│
└── outputs/
    ├── exposures/        # Beta time series
    ├── attribution/      # Risk decomposition
    └── reports/          # Summary reports
```

## 🚀 Quick Start

```bash
# Setup
git clone https://github.com/your-team/factor-risk-framework.git
cd factor-risk-framework
pip install -r requirements.txt

# Download factor data
python src/factor_loader.py --source french --factors FF3,FF5

# Run analysis
python src/exposure_estimation.py --portfolio tech_stocks --window 252
python src/risk_attribution.py --model FF5
python src/backtesting.py --oos-period 2020-2025
```

## 👥 Team Roles

| Role | Responsibilities | Deliverables |
|------|------------------|--------------|
| **Project Lead** | Framework design, integration | End-to-end pipeline |
| **Factor Analyst** | Exposure estimation, diagnostics | Rolling beta engine |
| **Risk Analyst** | Attribution logic, decomposition | Variance breakdown |
| **Data Engineer** | Data alignment, portfolio construction | Clean datasets |
| **Reporting** | Visualization, interpretation | Analysis reports |

## 📅 Timeline

- **Weeks 1-3**: Data pipeline + basic CAPM/FF3 estimation
- **Weeks 4-6**: Risk attribution framework
- **Weeks 7-9**: Backtesting + model comparison
- **Weeks 10-12**: Documentation + final deliverables

## 📊 Expected Outputs

1. **Factor Exposure Database**: Time-varying betas for all portfolios
2. **Risk Attribution Reports**: Factor contribution tables + charts
3. **Backtest Results**: Predicted vs. realized volatility comparison
4. **Portfolio Insights**: Style analysis and risk recommendations

## 🔬 Analysis Questions

1. How much portfolio risk comes from market vs. style factors?
2. Do factor exposures predict future portfolio volatility?
3. Which factors drive risk in different market regimes?

## 📚 Key References

- Fama, E., & French, K. (1993). Common risk factors in stock returns
- Fama, E., & French, K. (2015). A five-factor asset pricing model
- Sharpe, W. (1992). Asset allocation: Management style and performance

## 🔗 Attribution

Built on [linearmodels](https://github.com/bashtage/linearmodels) and [statsmodels](https://github.com/statsmodels/statsmodels).
Our contributions: Unified factor risk framework, automated attribution, backtesting validation.

## 📝 License

BSD 3-Clause License (matching linearmodels)
