"""
Auto PDF Report Generator (3 pages max as per PS requirement)
"""
from fpdf import FPDF
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import numpy as np
from loguru import logger
from src.config import REPORTS_DIR


class TransitAIReport(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(50, 100, 200)
        self.cell(0, 8, "TRANSIT-AI: Exoplanet Detection Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(50, 100, 200)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
    
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"TRANSIT-AI Pipeline | Page {self.page_no()} | {datetime.now().strftime('%Y-%m-%d')}", align="C")


def generate_pdf_report(results: List[Dict], output_path: Path = None) -> Path:
    """Generate the mandatory 3-page report."""
    if output_path is None:
        output_path = REPORTS_DIR / "TRANSIT_AI_REPORT.pdf"
    
    pdf = TransitAIReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # ── Page 1: Methodology + Overview ───────────────────────────────────────
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(30, 30, 80)
    pdf.cell(0, 10, "TRANSIT-AI: AI-Enabled Exoplanet Detection", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "ISRO ANTARIKSH Hackathon · Problem Statement 7", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    def section(title, body):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(50, 80, 180)
        pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 5, body)
        pdf.ln(2)
    
    section("1. Methodology", (
        "TRANSIT-AI implements a 6-stage automated pipeline:\n"
        "(i) DATA ACQUISITION: High-cadence TESS 2-min light curves downloaded via lightkurve/MAST API. "
        "Synthetic fallback (batman-generated) ensures demo reliability.\n"
        "(ii) PREPROCESSING: NaN removal, iterative sigma-clipping (4-sigma), Wotan biweight detrending "
        "(window=0.75d) to isolate stellar/instrumental systematics from astrophysical signals.\n"
        "(iii) DETECTION: Transit Least Squares (TLS) scans periods 0.5-15d. SDE >= 7 and SNR >= 7 "
        "with >= 2 transits required. BLS (astropy) serves as fallback.\n"
        "(iv) CLASSIFICATION: XGBoost + Random Forest ensemble on 22 engineered features "
        "(SNR, depth, odd-even mismatch, secondary eclipse ratio, V-shape score, periodogram metrics). "
        "SMOTE oversampling handles class imbalance. 5-fold CV for validation.\n"
        "(v) FITTING: batman transit model fitted via differential evolution (global) + Nelder-Mead "
        "(local) optimization. Parameter uncertainties from bootstrap (N=100) or emcee MCMC (N=2000).\n"
        "(vi) REPORTING: SNR = transit_depth / per-point_RMS; confidence = classifier calibrated probability."
    ))
    
    section("2. Assumptions", (
        "- Limb darkening: quadratic law, [u1,u2]=[0.4,0.25] (solar-type star).\n"
        "- Circular orbits (e=0) for period computation; eccentric systems not fitted.\n"
        "- Blends modeled as diluted eclipsing binaries; contamination factor estimated from depth ratio.\n"
        "- TLS assumes stellar density ~1 g/cm^3 for duration grid; individual stellar parameters improve fits.\n"
        "- MCMC run only for confirmed transit candidates to save computation time."
    ))
    
    section("3. Tools & Libraries", (
        "lightkurve (TESS data), transitleastsquares (TLS), wotan (detrending), batman (transit model), "
        "emcee (MCMC), xgboost + scikit-learn (classification), imbalanced-learn (SMOTE), "
        "scipy (optimization), astropy (BLS/units), streamlit (dashboard), fpdf2 (this report), "
        "plotly + matplotlib (visualization), numpy/pandas (numerics)."
    ))
    
    # ── Page 2: Results ────────────────────────────────────────────────────────
    pdf.add_page()
    section("4. Results Summary", "")
    
    processed = [r for r in results if r.get("status") == "PROCESSED"]
    candidates = [r for r in processed if r.get("is_candidate")]
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(230, 240, 255)
    headers = ["Metric", "Value"]
    col_w = [90, 90]
    for h, w in zip(headers, col_w):
        pdf.cell(w, 7, h, border=1, fill=True)
    pdf.ln()
    
    stats = [
        ("Total Light Curves Processed", str(len(processed))),
        ("Transit Candidates Found", str(len(candidates))),
        ("Detection Rate (all signals)", f"{np.mean([r['detection']['detected'] for r in processed if 'detection' in r]):.1%}" if processed else "0.0%"),
        ("Mean Classifier Confidence", f"{np.mean([r['classification']['confidence'] for r in processed if 'classification' in r]):.1%}" if processed else "0.0%"),
        ("Mean SNR of Candidates", f"{np.mean([r['detection']['snr'] for r in candidates if 'detection' in r]):.1f}-sigma" if candidates else "N/A"),
        ("Pipeline Execution Mode", "SYNTHETIC (demo) / TESS (production)"),
    ]
    
    pdf.set_font("Helvetica", "", 9)
    for i, (k, v) in enumerate(stats):
        fill = i % 2 == 0
        pdf.set_fill_color(245, 248, 255)
        pdf.cell(90, 6, k, border=1, fill=fill)
        pdf.cell(90, 6, v, border=1, fill=fill)
        pdf.ln()
    
    pdf.ln(5)
    
    # Top candidates table
    if candidates:
        section("5. Top Transit Candidates", "")
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(200, 220, 255)
        cols = ["TIC ID", "Period (d)", "Depth (ppm)", "Dur (hr)", "SNR", "Conf"]
        widths = [40, 28, 28, 24, 20, 20]
        for c, w in zip(cols, widths):
            pdf.cell(w, 6, c, border=1, fill=True)
        pdf.ln()
        
        pdf.set_font("Helvetica", "", 8)
        for r in candidates[:15]:  # top 15
            det = r.get("detection", {})
            clf = r.get("classification", {})
            row = [
                r["tic_id"][:18],
                f"{det.get('period', 0):.4f}",
                f"{det.get('depth', 0)*1e6:.1f}",
                f"{det.get('duration', 0)*24:.2f}",
                f"{det.get('snr', 0):.1f}",
                f"{clf.get('confidence', 0):.1%}",
            ]
            for val, w in zip(row, widths):
                pdf.cell(w, 5, str(val), border=1)
            pdf.ln()
    
    # ── Page 3: Uncertainty + Methods ─────────────────────────────────────────
    pdf.add_page()
    section("6. Uncertainty Estimation", (
        "PERIOD UNCERTAINTY: Reported directly from TLS as formal 1-sigma from the power spectrum peak width. "
        "Typical uncertainty: 0.01-0.1% of the best-fit period.\n\n"
        "DEPTH UNCERTAINTY: Bootstrap resampling (N=100) of the phase-folded light curve. "
        "For confirmed candidates, full MCMC (emcee, 32 walkers, 2000 steps, 500 burn-in) samples "
        "posterior distributions of Rp/Rs, a/Rs, inclination, and midpoint offset simultaneously. "
        "1-sigma credible intervals reported as depth_err.\n\n"
        "DURATION UNCERTAINTY: Derived from batman model geometry; propagated from Rp/Rs and a/Rs "
        "posterior samples.\n\n"
        "CLASSIFICATION CONFIDENCE: Calibrated soft-voting ensemble probability. "
        "XGBoost (60% weight) + Random Forest (40% weight). "
        "Confidence >= 60% required to report as classified signal.\n\n"
        "SNR COMPUTATION: SNR = transit_depth / sigma_per_point, where sigma is the RMS scatter "
        "of out-of-transit flux. False Alarm Probability (FAP) computed from TLS empirical "
        "significance levels (Hippke & Heller 2019). FAP < 0.01 considered significant.\n\n"
        "ODD-EVEN MISMATCH: Difference in depth between odd and even transits. "
        "Mismatch > 3-sigma indicates eclipsing binary contamination."
    ))
    
    section("7. Classification Criteria", (
        "TRANSIT: SNR >= 7, SDE >= 7, depth 100-20000 ppm, odd/even mismatch <0.3, "
        "no secondary eclipse, flat-bottom shape.\n"
        "ECLIPSE: Deep (>2%), V-shaped, possible secondary at phase 0.5, odd/even asymmetry.\n"
        "BLEND: Shallow diluted signal, secondary eclipse of similar depth ratio, "
        "background contamination indicator >0.5.\n"
        "STELLAR_VAR: Quasi-periodic smooth modulation, high autocorrelation, "
        "no sharp ingress/egress features.\n"
        "ARTIFACT: Discontinuities, single-epoch spikes, no periodicity, momentum dump signatures."
    ))
    
    section("8. Limitations & Future Work", (
        "- Stellar density assumption (1 g/cm^3) introduces systematic in a/Rs; "
        "stellar parameter cross-matching with TIC catalog would improve fits.\n"
        "- 1D CNN classifier on raw phase-folded curves (implemented but not ensemble-integrated) "
        "could improve blend/transit discrimination.\n"
        "- Full sector processing (20-30k LCs) requires ~4 hours on 8-core machine; "
        "GPU acceleration of TLS is planned.\n"
        "- Eccentric orbit fitting and TTVs (Transit Timing Variations) not yet implemented."
    ))
    
    pdf.output(str(output_path))
    logger.success(f"PDF Report generated → {output_path}")
    return output_path
