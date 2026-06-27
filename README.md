# 🪐 TRANSIT-AI v2.0
## AI-Enabled Detection of Exoplanets from Noisy Astronomical Light Curves
### ISRO ANTARIKSH Hackathon · Problem Statement 7 · Production-Grade Platform

---

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-blue.svg?style=for-the-badge&logo=docker)](https://www.docker.com/)

TRANSIT-AI is an end-to-end exoplanet detection, classification, parameter estimation, and vetting platform designed to extract low-amplitude transit signals from noisy astronomical data (such as TESS, Kepler, and Gaia light curves).

---

## 🚀 Key Platform Features

### 1. 🔭 Intelligent Preprocessing & Noise Filters
- **Outlier Mitigation**: Combined Median Absolute Deviation (MAD), single-cadence cosmic-ray spike removal, and iterative sigma clipping.
- **Detrending Engine**: Wotan biweight filter detrending to separate long-term stellar variability from orbital transit signatures.
- **TESS Bitmask Quality Checks**: Automatic flagging of attitude tweaks, stray light events, and momentum dumps.

### 2. 🔍 Multiphase Transit Discovery & Vetting
- **Detection Core**: Transit Least Squares (TLS) and fixed-grid Box Least Squares (BLS) period searching optimized for speed (100x improvement).
- **Secondary Eclipse Vetting**: Direct search at phase 0.5 and odd-even transit depth mismatch checks to filter Eclipsing Binaries (EB).
- **Habitability Estimator**: keplerian semi-major axis calculations, equilibrium temperature estimations ($T_{eq}$), and habitable zone classification.

### 3. 🤖 Ensemble ML & Deep Learning
- **Classifier Models**: XGBoost + Random Forest voting ensemble with calibrated probabilities.
- **CNN Classifier**: 1D Convolutional Neural Network processing phase-folded time-series vectors.
- **Explainable AI (XAI)**: Diagnostic LIME/SHAP-style rule explanations outlining why a star is classified as `TRANSIT`, `ECLIPSE`, `BLEND`, or `ARTIFACT`.

### 4. 🎛️ Microservices Architecture
- **FastAPI REST Backend**: High-performance HTTP interfaces (`POST /predict`, `GET /sky-map`, `POST /upload`).
- **Celestial Sky Map**: Plotting candidate exoplanets dynamically using RA/Dec coordinates.
- **Asynchronous Task Workers**: Queue system for batch processing thousands of light curves.

---

## 🛠️ Installation & Setup

### Local Setup
```bash
git clone https://github.com/Daksh7785/transit-ai.git
cd transit-ai
pip install -r requirements.txt
pip install -e .
```

### Run Streamlit UI Dashboard
```bash
streamlit run app/streamlit_app.py
```

### Run FastAPI Backend
```bash
uvicorn app.api.main:app --reload --port 8000
```

### Run Docker Containers
```bash
docker-compose up --build
```

---

## 🧪 Running Validation Tests
To run the automated pipeline validation:
```bash
python test_runner.py
```
- **Signal Recovery Test**: Recovers sub-percent transit periods.
- **Classification Accuracy Test**: Evaluates XGBoost/RF ensemble models.
- **PDF Report Compiler**: Builds [TRANSIT_AI_REPORT.pdf](file:///c:/Users/ASUS/Desktop/New%20folder/TRASIT-AI/reports/TRANSIT_AI_REPORT.pdf) automatically.