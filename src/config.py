"""
TRANSIT-AI Configuration
All constants, paths, and hyperparameters in one place.
"""
import os
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SYNTHETIC_DIR = DATA_DIR / "synthetic"
TRAINING_DIR = DATA_DIR / "training"
RESULTS_DIR = DATA_DIR / "results"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"

for d in [RAW_DIR, PROCESSED_DIR, SYNTHETIC_DIR, TRAINING_DIR, 
          RESULTS_DIR, MODELS_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── TESS Configuration ────────────────────────────────────────────────────────
TESS_SECTOR = 1                    # Sector to download
TESS_CADENCE = "short"             # "short" = 2-min, "fast" = 20-sec
MAX_LIGHTCURVES = 500              # Limit for demo (set to 30000 for full run)
TESS_MISSION = "TESS"

# ── Preprocessing ─────────────────────────────────────────────────────────────
SIGMA_CLIP_THRESHOLD = 4.0        # Sigma for outlier removal
DETREND_WINDOW_LENGTH = 0.75      # Window in days for Wotan biweight
NORMALIZE_TO_MEDIAN = True

# ── Detection ─────────────────────────────────────────────────────────────────
# BLS parameters
BLS_MIN_PERIOD = 0.5              # days
BLS_MAX_PERIOD = 15.0             # days
BLS_DURATION_GRID = [0.01, 0.02, 0.05, 0.1, 0.15, 0.2]  # fraction of period

# TLS parameters
TLS_MIN_PERIOD = 0.5
TLS_MAX_PERIOD = 15.0
TLS_OVERSAMPLING = 5
TLS_DURATION_GRID_STEP = 1.05

# Detection thresholds
SNR_THRESHOLD = 7.0               # Minimum SNR to flag candidate
SDE_THRESHOLD = 7.0               # Signal Detection Efficiency threshold
MIN_TRANSITS = 2                  # Minimum number of transits required
FAP_THRESHOLD = 0.01              # False Alarm Probability threshold

# ── Classification ────────────────────────────────────────────────────────────
CLASS_LABELS = ["TRANSIT", "ECLIPSE", "BLEND", "STELLAR_VAR", "ARTIFACT"]
CLASS_COLORS = {
    "TRANSIT": "#00FF88",
    "ECLIPSE": "#FF6B35",
    "BLEND": "#FFD700",
    "STELLAR_VAR": "#8B5CF6",
    "ARTIFACT": "#6B7280"
}
CONFIDENCE_THRESHOLD = 0.6        # Min confidence to report detection

# ── Fitting ───────────────────────────────────────────────────────────────────
BATMAN_LIMB_DARKENING = "quadratic"
BATMAN_LD_COEFFS = [0.4, 0.25]
MCMC_N_WALKERS = 32
MCMC_N_STEPS = 2000
MCMC_BURN_IN = 500
FIT_TRANSIT_DEPTH_BOUNDS = (1e-6, 0.5)  # (min, max) in relative flux units

# ── Pipeline ──────────────────────────────────────────────────────────────────
N_JOBS = -1                       # Parallel jobs (-1 = all cores)
BATCH_SIZE = 50                   # Light curves per batch
USE_SYNTHETIC_FALLBACK = True     # Auto-generate data if download fails

# ── Report ────────────────────────────────────────────────────────────────────
REPORT_TITLE = "TRANSIT-AI: Exoplanet Detection Report"
REPORT_AUTHOR = "TRANSIT-AI Pipeline"
MAX_REPORT_PAGES = 3
