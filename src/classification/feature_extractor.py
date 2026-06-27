"""
Feature Engineering for Transit Classification
Extracts 25+ discriminating features from light curve and detection results.
"""
import numpy as np
from scipy import stats
from typing import Dict
import warnings
warnings.filterwarnings('ignore')


def extract_features(time: np.ndarray, flux: np.ndarray,
                     detection: Dict) -> Dict:
    """
    Extract 25+ features for ML classification.
    Features are designed to discriminate between:
    TRANSIT, ECLIPSE, BLEND, STELLAR_VAR, ARTIFACT
    """
    features = {}
    
    # ── Detection-based features ──────────────────────────────────────────────
    features["snr"] = detection.get("snr", 0.0)
    features["sde"] = detection.get("sde", 0.0)
    features["period"] = detection.get("period", 0.0)
    features["depth"] = detection.get("depth", 0.0)
    features["duration"] = detection.get("duration", 0.0)
    features["n_transits"] = detection.get("n_transits", 0)
    features["odd_even_mismatch"] = detection.get("odd_even_mismatch", 0.0)
    
    # Transit duration ratio (duration / period)
    if detection.get("period", 0) > 0:
        features["duration_ratio"] = detection.get("duration", 0) / detection["period"]
    else:
        features["duration_ratio"] = 0.0
    
    # ── Light curve statistics ────────────────────────────────────────────────
    features["flux_std"] = float(np.std(flux))
    features["flux_mad"] = float(np.median(np.abs(flux - np.median(flux))))
    features["flux_skew"] = float(stats.skew(flux))
    features["flux_kurtosis"] = float(stats.kurtosis(flux))
    
    # Fraction of points below median (asymmetry)
    median_flux = np.median(flux)
    features["frac_below_median"] = float(np.mean(flux < median_flux))
    
    # ── Phase-folded curve features ───────────────────────────────────────────
    phase = detection.get("phase", [])
    folded = detection.get("folded_flux", [])
    model = detection.get("model_flux", [])
    
    if len(phase) > 10 and len(folded) > 10:
        folded = np.array(folded)
        phase = np.array(phase)
        
        # In-transit vs out-of-transit scatter ratio
        in_transit = np.abs(phase - 0.5) > 0.4
        out_transit = np.abs(phase - 0.5) < 0.1
        
        if out_transit.sum() > 5 and in_transit.sum() > 5:
            features["in_out_scatter_ratio"] = (
                np.std(folded[out_transit]) / (np.std(folded[in_transit]) + 1e-10)
            )
            oot_folded = folded[out_transit]
            features["transit_asymmetry"] = float(
                np.abs(np.mean(oot_folded[:len(oot_folded)//2]) - 
                       np.mean(oot_folded[len(oot_folded)//2:]))
            )
        else:
            features["in_out_scatter_ratio"] = 1.0
            features["transit_asymmetry"] = 0.0
        
        # V-shape vs flat-bottom (eclipses are V-shaped, transits flat)
        features["shape_v_score"] = _compute_v_shape_score(phase, folded)
        
        # Secondary eclipse depth (at phase 0.5 offset)
        secondary_phase = np.abs(phase - 0.5) < 0.05
        primary_phase = phase < 0.05
        if secondary_phase.sum() > 3 and primary_phase.sum() > 3:
            features["secondary_depth_ratio"] = (
                float(1 - np.min(folded[secondary_phase])) / 
                (float(1 - np.min(folded[primary_phase])) + 1e-10)
            )
        else:
            features["secondary_depth_ratio"] = 0.0
    else:
        features.update({
            "in_out_scatter_ratio": 1.0, "transit_asymmetry": 0.0,
            "shape_v_score": 0.0, "secondary_depth_ratio": 0.0
        })
    
    # ── Periodogram features ──────────────────────────────────────────────────
    power_arr = np.array(detection.get("power_spectrum", {}).get("power", []))
    if len(power_arr) > 10:
        # Peak-to-noise ratio in periodogram
        sorted_power = np.sort(power_arr)
        features["periodogram_peak_noise"] = (
            float(sorted_power[-1]) / (float(np.median(sorted_power)) + 1e-10)
        )
        # Number of significant harmonics
        threshold = np.median(power_arr) + 3 * np.std(power_arr)
        features["n_harmonics"] = int(np.sum(power_arr > threshold))
    else:
        features["periodogram_peak_noise"] = 1.0
        features["n_harmonics"] = 0
    
    # ── Variability features (for STELLAR_VAR discrimination) ─────────────────
    # Quasi-periodicity measure: autocorrelation at period lag
    if detection.get("period", 0) > 0 and len(time) > 50:
        features["autocorr_peak"] = _compute_autocorr_peak(time, flux, detection["period"])
    else:
        features["autocorr_peak"] = 0.0
    
    # ── Depth-based features ──────────────────────────────────────────────────
    # Dilution indicator: very shallow depth in long period → possible blend
    depth = detection.get("depth", 0)
    features["depth_log"] = float(np.log10(max(depth, 1e-8)))
    
    # Short period deep eclipse → binary candidate
    period = detection.get("period", 1.0)
    features["depth_period_ratio"] = depth / (period + 1e-6)
    
    return features


def features_to_vector(features: Dict) -> np.ndarray:
    """Convert feature dict to ordered numpy array for ML input."""
    FEATURE_ORDER = [
        "snr", "sde", "period", "depth", "duration", "n_transits",
        "odd_even_mismatch", "duration_ratio", "flux_std", "flux_mad",
        "flux_skew", "flux_kurtosis", "frac_below_median",
        "in_out_scatter_ratio", "transit_asymmetry", "shape_v_score",
        "secondary_depth_ratio", "periodogram_peak_noise", "n_harmonics",
        "autocorr_peak", "depth_log", "depth_period_ratio"
    ]
    return np.array([features.get(f, 0.0) for f in FEATURE_ORDER])


def _compute_v_shape_score(phase: np.ndarray, flux: np.ndarray) -> float:
    """Compute V-shape score: >0 = V-shaped (eclipse), ~0 = flat-bottom (transit)."""
    in_transit = (phase < 0.05) | (phase > 0.95)
    if in_transit.sum() < 5:
        return 0.0
    flux_in = flux[in_transit]
    phase_in = phase[in_transit].copy()
    phase_in[phase_in > 0.5] -= 1.0
    
    # Fit linear vs flat: V-shape has higher |slope|
    if len(phase_in) < 2:
        return 0.0
    slope, _ = np.polyfit(np.abs(phase_in), flux_in, 1)
    return float(np.abs(slope))


def _compute_autocorr_peak(time: np.ndarray, flux: np.ndarray, period: float) -> float:
    """Compute autocorrelation at the detected period lag."""
    if period <= 0:
        return 0.0
    cadence = np.nanmedian(np.diff(time))
    lag = int(period / cadence)
    if lag >= len(flux):
        return 0.0
    f_norm = flux - np.mean(flux)
    corr = np.correlate(f_norm, f_norm, mode='full')
    corr = corr / (corr[len(corr)//2] + 1e-10)
    mid = len(corr) // 2
    if mid + lag < len(corr):
        return float(corr[mid + lag])
    return 0.0
