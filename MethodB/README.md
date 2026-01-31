# GARCH Volatility Forecasting and VaR Prediction Framework

**RMSC 6007 Group Project | Term 2, 2025-26**

## 🎯 Project Overview

An academic-grade Python framework for volatility modeling using GARCH-family models, with emphasis on conditional volatility forecasting and its impact on VaR prediction accuracy.

### Key Features
- **Multiple GARCH Models**: GARCH(1,1), EGARCH, GJR-GARCH, TGARCH
- **Volatility Forecasting**: 1-day, 5-day, 20-day ahead predictions
- **VaR Translation**: Convert volatility forecasts to risk estimates
- **Model Comparison**: AIC/BIC, forecast RMSE, backtesting performance

## 🛠️ Technology Stack

### Core Libraries
- **arch** (1.5k⭐) - GARCH model estimation and forecasting
- **statsmodels** (10k+⭐) - Time series diagnostics
- **yfinance** (14.5k⭐) - Market data
- **vectorbt** (6.5k⭐) - Rolling window backtesting
- **QuantStats** (6.6k⭐) - Performance reporting

## 📁 Project Structure

```
garch-var-framework/
├── README.md
├── requirements.txt
├── LICENSE
│
├── data/
│   ├── raw/              # Price data
│   ├── processed/        # Returns + realized volatility
│   └── forecasts/        # Model predictions
│
├── src/
│   ├── volatility_models.py   # GARCH implementations
│   ├── var_forecasting.py     # Volatility → VaR conversion
│   ├── model_selection.py     # AIC/BIC comparison
│   ├── backtesting.py         # Forecast evaluation
│   └── visualization.py       # Volatility plots
│
├── notebooks/
│   ├── 01_data_prep.ipynb
│   ├── 02_garch_estimation.ipynb
│   ├── 03_forecast_evaluation.ipynb
│   └── 04_var_comparison.ipynb
│
├── tests/
│   ├── test_garch_models.py
│   ├── test_forecasting.py
│   └── test_model_selection.py
│
└── outputs/
    ├── model_results/    # Fitted model objects
    ├── forecasts/        # Prediction CSVs
    └── reports/          # Analysis reports
```

## 🚀 Quick Start

```bash
# Setup
git clone https://github.com/your-team/garch-var-framework.git
cd garch-var-framework
pip install -r requirements.txt

# Run full pipeline
python src/volatility_models.py --assets SPY,HSI --models GARCH,EGARCH,GJR
python src/var_forecasting.py --horizon 1,5,20
python src/backtesting.py --generate-report
```

## 👥 Team Roles

| Role | Responsibilities | Deliverables |
|------|------------------|--------------|
| **Project Lead** | Architecture, integration | Unified pipeline |
| **GARCH Expert** | Model implementation, diagnostics | 4 GARCH variants |
| **Forecasting** | Prediction logic, evaluation | Forecast engine |
| **Data Engineer** | Data prep, rolling windows | Clean datasets |
| **Analyst** | Interpretation, reporting | Analysis report |

## 📅 Timeline

- **Weeks 1-3**: GARCH model implementation + validation
- **Weeks 4-6**: Forecasting pipeline + VaR conversion
- **Weeks 7-9**: Backtesting + model comparison
- **Weeks 10-12**: Documentation + final report

## 📊 Expected Outputs

1. **GARCH Library**: Wrapper around arch with enhanced features
2. **Forecast Database**: Predictions for all models/assets/horizons
3. **Comparison Report**: Model selection guidance
4. **Academic Paper**: Methodology + empirical findings

## 🔬 Research Questions

1. Do asymmetric GARCH models (EGARCH/GJR) outperform symmetric GARCH?
2. What is the optimal forecast horizon for VaR prediction?
3. Does GARCH-based VaR beat simpler methods in crisis periods?

## 📚 Key References

- Bollerslev, T. (1986). Generalized autoregressive conditional heteroskedasticity
- Nelson, D. (1991). Conditional heteroskedasticity in asset returns: EGARCH
- Glosten, L., Jagannathan, R., & Runkle, D. (1993). GJR-GARCH

## 🔗 Attribution

Built on [arch](https://github.com/bashtage/arch) by Kevin Sheppard.
Our contributions: Multi-model comparison framework, VaR translation, automated evaluation.

## 📝 License

University of Illinois/NCSA License (matching arch library)
