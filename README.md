# RMSC6007 Quantitative Risk Management - Group Project

> **A systematic approach to options risk management with multiple methodologies**  
> Course Project | Spring 2026 | Team [Your Team Name]

---

## 📋 Project Overview

This repository implements a comprehensive options risk management framework, covering both **standard course requirements** and **research-grade extensions**. Our goal is to demonstrate:

- Solid understanding of VaR, volatility modeling, and factor-based risk management
- Production-ready code with proper testing, documentation, and version control
- Research methodology with reproducible data pipelines

---

## 🎯 Implementation Methods

We provide **four complementary approaches**, each addressing different aspects of options risk:

### ✅ Method A: Historical VaR
- Classic Value-at-Risk estimation using historical simulation
- Suitable for portfolio-level risk assessment
- **Status**: ✅ Complete | **Owner**: [Name]

### ✅ Method B: GARCH Volatility Modeling
- Time-series volatility forecasting with GARCH(1,1)
- Captures volatility clustering in options pricing
- **Status**: ✅ Complete | **Owner**: [Name]

### ✅ Method C: Factor Exposure Analysis
- Greeks-based risk decomposition
- Multi-factor sensitivity analysis
- **Status**: ✅ Complete | **Owner**: [Name]

### 🧪 Method D: IV Factor Research (Research Extension)
- **Real options chain snapshot collection** (t0 → t5 forward capture)
- **Factor validity testing** using cross-sectional IV prediction
- **Research-grade pipeline** with reproducible data infrastructure
- **Focus**: Not P&L optimization, but *"Does the factor work? When does it fail?"*
- **Status**: 🚧 Data collection in progress | **Owner**: [Name]

> 💡 **Why Method D?**  
> While A/B/C follow standard course requirements, Method D demonstrates:
> - Advanced data engineering (forward data collection to avoid look-ahead bias)
> - Academic rigor (IC analysis, baseline comparison, mechanism validation)
> - Real-world research workflow (scheduled capture, version control, reproducibility)

---

## 📂 Repository Structure

```
RMSC6007_GroupProject/
├── MethodA/                 # Historical VaR implementation
├── MethodB/                 # GARCH volatility models
├── MethodC/                 # Factor exposure analysis
├── MethodD/                 # 🧪 IV factor research (see dedicated README)
│   ├── README.md            # Detailed research protocol
│   ├── tools/               # Snapshot capture & scheduling
│   ├── experiments/         # Factor validation & demo scripts
│   └── outputs/             # Validation reports
├── scripts/                 # Release / automation scripts
└── README.md                # This file
```

---

## 🚀 Quick Start

### Prerequisites
```bash
python >= 3.9
```

### Option 1: Unified Docker Environment (Recommended)

```bash
cd RMSC6007_GroupProject
docker compose build
docker compose run --rm rmsc6007
```

Inside the container:

```bash
cd MethodD
bash run_all_demos.sh
```

### Option 2: Local Python Environment

```bash
cd RMSC6007_GroupProject/MethodD
pip install -r requirements.txt
bash run_all_demos.sh
```

---

## 👥 Team Collaboration

### Workflow
1. **Create feature branch**: `git checkout -b feature/method-x-enhancement`
2. **Make changes** with clear commit messages
3. **Open Pull Request** with description and test results
4. **Code review** by at least one team member
5. **Merge** after approval

### Communication
- **Weekly sync**: [Day/Time]
- **Issues**: Use GitHub Issues for bugs/questions
- **Documentation**: Update README when adding features

---

## 📊 Deliverables Checklist

- [x] Project proposal (see `GOOGLE_FORM_SUBMISSION.md`)
- [x] Method A implementation + tests
- [x] Method B implementation + tests
- [x] Method C implementation + tests
- [ ] Method D validation report (in progress)
- [ ] Final presentation slides
- [ ] Comprehensive project report

---

## 📖 Documentation

- **Method D Research Protocol**: `MethodD/README.md`
- **Implementation Summaries**: `MethodD/IMPLEMENTATION_SUMMARY.md`
- **Data Spec**: `MethodD/DATA_SPECIFICATION.md`
- **Covered Call Spec**: `MethodD/COVERED_CALL_SPECIFICATION.md`

---

## 🎓 Course Alignment

This project addresses RMSC6007 learning objectives:

| Objective | Implementation |
|-----------|----------------|
| VaR estimation | Method A |
| Volatility modeling | Method B |
| Factor-based risk | Method C |
| Research methodology | Method D |
| Code quality & testing | CI/CD pipeline, unit tests |

---

## 📝 License & Academic Integrity

This is a course project for RMSC6007. Code is for educational purposes only.  
All team members have contributed equally to this work.

---

## 📧 Contact

- **Team Lead**: [Name] - [Email]
- **Method D Lead**: [Name] - [Email]
- **Course**: RMSC6007 Quantitative Risk Management
- **Instructor**: [Professor Name]