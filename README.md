# 🌌 AstroLens AI: Production Exoplanet Detection Platform
### ISRO ANTARIKSH Hackathon · Problem Statement 7 · Advanced Production Release

---

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-green.svg?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Streamlit-1.28+-red.svg?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/Docker-Ready-blue.svg?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</p>

---

## 🌟 What We Engineered (v2.0 Architectural Enhancements)

We extended the basic transit detection script into a robust, high-throughput, and scientifically accurate **Exoplanet Discovery & Vetting Platform**. 

Here is a summary of the advanced components added to the repository:

### 1. 🧹 Deep Space Signal Preprocessing Pipeline
* **TESS Quality Flags (`quality_flags.py`)**: Automatic cadence bitmask parsing to filter instrument jitter, coarse pointing, and momentum dumps.
* **Robust Noise Filters (`outlier_removal.py`)**: Integrates Median Absolute Deviation (MAD) limits, single-cadence cosmic-ray spike removal, and multi-iteration sigma clipping.
* **Adaptive Normalization (`normalization.py`)**: Supports Median, IQR, and Percentile-based flux scaling.

### 2. 🔍 Stellar Companion & False Positive Vetting
* **Eclipsing Binary Diagnostic (`secondary_eclipse.py`)**: Scans phase folds at 0.5 offset to flag secondary stellar eclipses, and implements odd-even transit depth mismatch vetting to filter background eclipsing binaries (EBs).
* **Cross-Matching Engine (`cross_match.py`)**: Integrates online TAP query interfaces to verify candidate coordinates and periods against the **NASA Exoplanet Archive** databases.

### 3. 🌡️ Habitable Zone (HZ) Characterization
* **Keplerian Estimator (`habitability.py`)**: Computes semi-major axis (AU), equilibrium temperature ($T_{eq}$), stellar irradiation flux, and classifies planets into size cohorts (Hot Jupiter, Super Earth, Earth-like).

### 4. 🚀 High-Performance REST API Backend
* **FastAPI Server (`main.py`)**: Production-ready service hosting `/predict`, `/upload` (CSV parsing), `/results`, and `/sky-map` endpoints.
* **Background Worker Queue (`worker.py`)**: Enables scalable asynchronous batch processing of large stellar catalogs.

---

## 🛠️ Complete Directory Structure

```
TRASIT-AI/
├── app/
│   ├── api/
│   │   ├── main.py            # FastAPI REST endpoints
│   │   └── worker.py          # Asynchronous job queue runner
│   └── streamlit_app.py       # Streamlit UI dashboard
├── src/
│   ├── acquisition/
│   │   ├── mast_query.py      # MAST API cone search
│   │   ├── cross_match.py     # TAP NASA Exoplanet matching
│   │   └── synthetic_generator.py # Data generators & augments
│   ├── preprocessing/
│   │   ├── detrending.py      # Preprocessing orchestrator
│   │   ├── outlier_removal.py # MAD & cosmic-ray spike filters
│   │   ├── quality_flags.py   # TESS quality bitmasks
│   │   └── normalization.py   # Flux scaling
│   ├── detection/
│   │   ├── tls_detector.py    # Box Least Squares & TLS engine
│   │   ├── secondary_eclipse.py # False-positive & EB vet checks
│   │   └── habitability.py    # Habitable zone classification
│   ├── classification/
│   │   ├── ml_classifier.py   # Ensemble classifier models
│   │   ├── cnn_classifier.py  # 1D CNN classifier model
│   │   └── feature_extractor.py # Stellar shape feature extraction
│   └── fitting/
│       └── batman_fitter.py   # Keplerian batman fitter
```

---

## 🚀 Running and Deploying

### Option A: Local Run
```bash
# Install package
pip install -r requirements.txt
pip install -e .

# Run Dashboard
streamlit run app/streamlit_app.py

# Run API Server
uvicorn app.api.main:app --port 8000 --reload
```

### Option B: Docker Compose (Production Cluster)
```bash
docker-compose up --build
```

---

## 🧪 Pipeline Test Verification
To run the automated verification test suite:
```bash
python test_runner.py
```
- **Signal Recovery**: Reconstructs transit parameters of low-SNR signals.
- **Classification Accuracy**: Validates features with Stratified F1 scores.
- **Auto-Reports**: Generates the compiled PDF report at `reports/TRANSIT_AI_REPORT.pdf`.