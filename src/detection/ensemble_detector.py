"""
Ensemble Transit Detector Module
Combines BLS, TLS, Lomb-Scargle (LS), and ML confidence for robust exoplanet detection.
"""
import numpy as np
from loguru import logger
from typing import Dict, Tuple, Optional
from astropy.timeseries import BoxLeastSquares, LombScargle
import astropy.units as u

from src.config import TLS_MIN_PERIOD, TLS_MAX_PERIOD, SNR_THRESHOLD, SDE_THRESHOLD
from src.detection.tls_detector import run_tls


def run_lomb_scargle(time: np.ndarray, flux: np.ndarray) -> Dict:
    """
    Run Lomb-Scargle periodogram search for sinusoidal variations (e.g. starspots, pulsation, rotating variables).
    """
    try:
        ls = LombScargle(time, flux)
        # Scan same frequency range as transits
        frequency, power = ls.autopower(
            minimum_frequency=1.0/TLS_MAX_PERIOD,
            maximum_frequency=1.0/TLS_MIN_PERIOD,
            samples_per_peak=5
        )
        
        max_idx = np.argmax(power)
        best_freq = frequency[max_idx]
        best_period = 1.0 / best_freq
        best_power = power[max_idx]
        
        # Calculate false alarm probability
        fap = ls.false_alarm_probability(best_power)
        
        # Estimate SNR based on power vs mean power
        snr = best_power / np.std(power)
        
        return {
            "detected": bool(snr >= SNR_THRESHOLD and fap < 0.01),
            "period": float(best_period),
            "power": float(best_power),
            "fap": float(fap),
            "snr": float(snr),
            "power_spectrum": {
                "periods": (1.0 / frequency).tolist(),
                "power": power.tolist()
            },
            "method": "Lomb-Scargle"
        }
    except Exception as e:
        logger.error(f"Lomb-Scargle failed: {e}")
        return {
            "detected": False, "period": 0.0, "power": 0.0, "fap": 1.0, "snr": 0.0,
            "power_spectrum": {"periods": [], "power": []}, "method": "Lomb-Scargle"
        }


def run_ensemble_detector(time: np.ndarray, flux: np.ndarray, 
                         flux_err: Optional[np.ndarray] = None,
                         ml_confidence: float = 0.5) -> Dict:
    """
    Run the Ensemble detector: Weighted(BLS + TLS + LS + ML).
    Returns the consensus candidate parameters and ensemble scores.
    """
    # 1. Run individual detectors
    # TLS (which automatically falls back to astropy BLS if TLS package is missing)
    tls_res = run_tls(time, flux, flux_err)
    
    # Lomb-Scargle for periodic stellar activity or eclipses
    ls_res = run_lomb_scargle(time, flux)
    
    # Extract BLS metrics specifically
    from astropy.timeseries import BoxLeastSquares
    try:
        bls = BoxLeastSquares(time * u.day, flux)
        durations = np.array([0.01, 0.02, 0.05, 0.1, 0.2]) * TLS_MIN_PERIOD * u.day
        periods = np.linspace(TLS_MIN_PERIOD, TLS_MAX_PERIOD, 1000) * u.day
        pg = bls.power(periods, durations)
        max_idx = np.argmax(pg.power)
        bls_res = {
            "detected": pg.power[max_idx] / np.std(pg.power) >= SNR_THRESHOLD,
            "period": float(pg.period[max_idx].value),
            "power": float(pg.power[max_idx]),
            "snr": float(pg.power[max_idx] / np.std(pg.power)),
            "t0": float(pg.transit_time[max_idx].value),
            "duration": float(pg.duration[max_idx].value)
        }
    except Exception as e:
        logger.warning(f"Astropy BLS failed: {e}")
        bls_res = {"detected": False, "period": 0.0, "power": 0.0, "snr": 0.0, "t0": 0.0, "duration": 0.0}

    # 2. Compile Detection Scores
    # We assign weights to each detection method:
    # TLS: 0.40 (highest accuracy for planet transits)
    # BLS: 0.25 (robust fallback box detector)
    # LS: 0.15 (good for starspots / binaries / rotation)
    # ML: 0.20 (machine learning veto / classifier score)
    
    w_tls = 0.40
    w_bls = 0.25
    w_ls = 0.15
    w_ml = 0.20
    
    score_tls = 1.0 if tls_res.get("detected") else 0.0
    score_bls = 1.0 if bls_res.get("detected") else 0.0
    score_ls = 1.0 if ls_res.get("detected") else 0.0
    score_ml = ml_confidence
    
    final_score = (w_tls * score_tls + 
                   w_bls * score_bls + 
                   w_ls * score_ls + 
                   w_ml * score_ml)
    
    is_detected = final_score >= 0.50
    
    # 3. Consolidate Parameters
    # If TLS detected a signal, prioritize it. Otherwise use the highest SNR detector.
    best_source = "TLS"
    if tls_res.get("detected"):
        best_period = tls_res["period"]
        t0 = tls_res["t0"]
        duration = tls_res["duration"]
        snr = tls_res["snr"]
        fap = tls_res.get("fap", 0.01)
        depth = tls_res["depth"]
    elif bls_res.get("detected"):
        best_period = bls_res["period"]
        t0 = bls_res["t0"]
        duration = bls_res["duration"]
        snr = bls_res["snr"]
        fap = 0.05
        depth = tls_res.get("depth", 0.0)
        best_source = "BLS"
    else:
        best_period = ls_res["period"]
        t0 = time[0] # Fallback
        duration = 0.1 # Fallback
        snr = ls_res["snr"]
        fap = ls_res.get("fap", 1.0)
        depth = 0.0
        best_source = "Lomb-Scargle"
        
    # 4. Phase fold / power spectrum integration
    phase = tls_res.get("phase", [])
    folded_flux = tls_res.get("folded_flux", [])
    model_flux = tls_res.get("model_flux", [])
    power_spectrum = tls_res.get("power_spectrum", {"periods": [], "power": []})
    sde = tls_res.get("sde", snr)
    odd_even_mismatch = tls_res.get("odd_even_mismatch", 0.0)

    return {
        "detected": bool(is_detected),
        "period": float(best_period),
        "t0": float(t0),
        "duration": float(duration),
        "depth": float(depth),
        "snr": float(snr),
        "sde": float(sde),
        "fap": float(fap) if fap is not None else 0.01,
        "ensemble_score": float(final_score),
        "best_detector": best_source,
        "phase": phase,
        "folded_flux": folded_flux,
        "model_flux": model_flux,
        "power_spectrum": power_spectrum,
        "odd_even_mismatch": odd_even_mismatch,
        "individual_results": {
            "tls": {"detected": tls_res.get("detected"), "period": tls_res.get("period"), "snr": tls_res.get("snr")},
            "bls": {"detected": bls_res.get("detected"), "period": bls_res.get("period"), "snr": bls_res.get("snr")},
            "ls": {"detected": ls_res.get("detected"), "period": ls_res.get("period"), "snr": ls_res.get("snr")},
        }
    }
