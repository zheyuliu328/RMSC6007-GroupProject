# Unified VaR/ES Risk Measurement and Backtesting Framework

**RMSC 6007 Group Project | Term 2, 2025-26**

## 🎯 Project Overview

A production-ready Python framework that integrates multiple open-source libraries to provide comprehensive Value-at-Risk (VaR) and Expected Shortfall (ES) analysis with automated backtesting and reporting.

### Key Features
- **4 VaR/ES Methods**: Historical Simulation, Parametric (Gaussian), Monte Carlo, GARCH-based
- **Regulatory Backtesting**: Kupiec POF test, Christoffersen independence test
- **Automated Reporting**: Interactive HTML tear sheets with risk metrics and visualizations
- **One-Click Reproducibility**: Single Jupyter notebook to run entire analysis

## 🛠️ Technology Stack

### Core Libraries (All 100+ Stars)
- **QuantStats** (6.6k⭐) - Portfolio analytics and risk reporting
- **arch** (1.5k⭐) - GARCH volatility modeling
- **vectorbt** (6.5k⭐) - Backtesting and rolling window experiments
- **yfinance** (14.5k⭐) - Market data acquisition
- **statsmodels** (10k+⭐) - Statistical modeling and tests

### Supporting Tools
- pandas, numpy - Data manipulation
- matplotlib, plotly - Visualization
- pytest - Unit testing (target: 80%+ coverage)

## 📁 Project Structure

```
var-es-framework/
├── README.md
├── requirements.txt
├── setup.py
├── LICENSE (Apache 2.0)
│
├── data/
│   ├── raw/              # Downloaded price data
│   └── processed/        # Computed returns and features
│
├── src/
│   ├── __init__.py
│   ├── data_loader.py    # yfinance wrapper + caching
│   ├── var_models.py     # 4 VaR/ES implementations
│   ├── backtesting.py    # Kupiec, Christoffersen tests
│   ├── reporting.py      # HTML report generation
│   └── utils.py          # Helper functions
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_var_comparison.ipynb
│   └── 03_final_report.ipynb  # One-click demo
│
├── tests/
│   ├── test_var_models.py
│   ├── test_backtesting.py
│   └── test_data_loader.py
│
├── docs/
│   ├── methodology.md
│   ├── api_reference.md
│   └── results_interpretation.md
│
└── outputs/
    ├── reports/          # Generated HTML reports
    └── figures/          # Saved visualizations
```

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/your-team/var-es-framework.git
cd var-es-framework
pip install -r requirements.txt

# 2. Download data (5-10 indices, 2015-2025)
python src/data_loader.py --assets SPY,HSI,EWJ --start 2015-01-01

# 3. Run analysis
jupyter notebook notebooks/03_final_report.ipynb

# 4. Generate report
python src/reporting.py --output outputs/reports/risk_report.html
```

## 👥 Team Roles & Deliverables

| Role | Member | Responsibilities | Deliverables |
|------|--------|------------------|--------------|
| **Project Lead** | [Name] | Repo structure, API design, integration | Unified API, final demo script |
| **Risk Modeler** | [Name] | VaR/ES implementations, numerical stability | 4 methods + unit tests |
| **Backtesting** | [Name] | Statistical tests, coverage analysis | Backtesting framework + results |
| **Data Engineer** | [Name] | Data pipeline, reproducibility | Data scripts + notebooks |
| **Reporting** | [Name] | Visualization, documentation | HTML reports + README |

## 📅 Timeline (12 Weeks)

### Phase 1: Foundation (Weeks 1-3)
- Week 1: Repo setup, data pipeline, basic VaR implementations
- Week 2: Complete all 4 VaR methods, unit tests
- Week 3: Backtesting framework, initial validation

### Phase 2: Integration (Weeks 4-6)
- Week 4: Integrate QuantStats reporting
- Week 5: Rolling window experiments with vectorbt
- Week 6: Cross-method comparison analysis

### Phase 3: Refinement (Weeks 7-9)
- Week 7: Documentation, code review
- Week 8: Performance optimization, edge cases
- Week 9: Final report generation

### Phase 4: Delivery (Weeks 10-12)
- Week 10: Presentation preparation
- Week 11: Final testing, bug fixes
- Week 12: Project submission

## 📊 Expected Outputs

1. **Python Package**: Installable via `pip install -e .`
2. **Benchmark Report**: Comparison table of all methods across assets
3. **Interactive Notebook**: One-click reproducible analysis
4. **Documentation**: API reference + methodology guide
5. **Test Suite**: 80%+ code coverage

## 🔬 Validation Metrics

- **VaR Accuracy**: Coverage ratio (target: 95% for 95% VaR)
- **Backtesting**: Kupiec p-value > 0.05 (fail to reject)
- **Performance**: <5 seconds per asset per method
- **Reproducibility**: Same results across runs (fixed random seed)

## 📚 Key References

- Basel Committee on Banking Supervision (2019). Minimum capital requirements for market risk
- Christoffersen, P. (1998). Evaluating interval forecasts
- Kupiec, P. (1995). Techniques for verifying the accuracy of risk measurement models

## 🔗 Baseline Libraries & Attribution

This project builds upon:
- [QuantStats](https://github.com/ranaroussi/quantstats) - Apache 2.0 License
- [arch](https://github.com/bashtage/arch) - University of Illinois/NCSA License
- [vectorbt](https://github.com/polakowo/vectorbt) - Apache 2.0 License

**Our contributions:**
- Unified API for VaR/ES computation across 4 methods
- Standardized backtesting framework with regulatory tests
- Automated comparative analysis pipeline
- Comprehensive documentation and reproducible examples
- 80%+ test coverage with unit and integration tests

## 📝 License

Apache License 2.0 - See LICENSE file for details
