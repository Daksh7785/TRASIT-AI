"""
Transit Least Squares (TLS) Detector
Best-in-class transit detection algorithm.
Ref: Hippke & Heller (2019), A&A 623, A39
"""
import numpy as np
from loguru import logger
from typing import Dict, Optional
from src.config import (
    TLS_MIN_PERIOD, TLS_MAX_PERIOD, TLS_OVERSAMPLING,
    SNR_THRESHOLD, SDE_THRESHOLD, MIN_TRANSITS
)

try:
    from transitleastsquares import transitleastsquares, cleaned_array
    TLS_AVAILABLE = True
except ImportError:
    TLS_AVAILABLE = False
    logger.warning("TLS not available; falling back to BLS detector")


def run_tls(time: np.ndarray, flux: np.ndarray,
            flux_err: Optional[np.ndarray] = None,
            period_min: float = TLS_MIN_PERIOD,
            period_max: float = TLS_MAX_PERIOD) -> Dict:
    """
    Run TLS transit search on a preprocessed light curve.
    Returns dict with detection results and statistics.
    """
    if not TLS_AVAILABLE:
        return _run_bls_fallback(time, flux, period_min, period_max)
    
    # Clean arrays
    t, f = cleaned_array(time, flux)
    if flux_err is not None:
        _, err = cleaned_array(time, flux_err)
    else:
        err = np.ones(len(f)) * np.std(f) * 0.1
    
    if len(t) < 100:
        return _empty_result("Insufficient data points")
    
    try:
        model = transitleastsquares(t, f, err)
        results = model.power(
            minimum_period=period_min,
            maximum_period=period_max,
            oversampling_factor=TLS_OVERSAMPLING,
            duration_grid_step=1.05,
            use_threads=1
        )
        
        is_detection = (
            results.SDE >= SDE_THRESHOLD and
            results.snr >= SNR_THRESHOLD and
            results.distinct_transit_count >= MIN_TRANSITS
        )
        
        return {
            "detected": is_detection,
            "period": float(results.period),
            "period_uncertainty": float(results.period_uncertainty),
            "t0": float(results.T0),
            "duration": float(results.duration),
            "depth": float(results.depth),
            "depth_err": float(results.depth_err) if hasattr(results, 'depth_err') else 0.0,
            "snr": float(results.snr),
            "sde": float(results.SDE),
            "fap": float(results.FAP) if hasattr(results, 'FAP') else None,
            "n_transits": int(results.distinct_transit_count),
            "odd_even_mismatch": float(results.odd_even_mismatch) if hasattr(results, 'odd_even_mismatch') else 0.0,
            "power_spectrum": {
                "periods": results.periods.tolist(),
                "power": results.power.tolist()
            },
            "phase": results.folded_phase.tolist() if hasattr(results, 'folded_phase') else [],
            "folded_flux": results.folded_y.tolist() if hasattr(results, 'folded_y') else [],
            "model_flux": results.model_folded_model.tolist() if hasattr(results, 'model_folded_model') else [],
            "method": "TLS"
        }
    
    except Exception as e:
        logger.error(f"TLS failed: {e}")
        return _empty_result(str(e))


def _run_bls_fallback(time, flux, period_min, period_max) -> Dict:
    """BLS fallback if TLS is not installed."""
    from astropy.timeseries import BoxLeastSquares
    import astropy.units as u
    
    # Ensure min/max period are floats
    period_min = float(period_min)
    period_max = float(period_max)
    
    # Downsample if light curve is long to speed up BLS search
    if len(time) > 2000:
        step = len(time) // 2000
        time_search = time[::step]
        flux_search = flux[::step]
    else:
        time_search = time
        flux_search = flux
        
    bls = BoxLeastSquares(time_search * u.day, flux_search)
    
    # Strictly ensure durations < period_min to prevent astropy validation error
    durations = np.array([0.01, 0.02, 0.05, 0.1, 0.2]) * period_min * u.day
    
    # Use a fixed grid of 1000 periods to make it extremely fast!
    periods = np.linspace(period_min, period_max, 1000) * u.day
    
    periodogram = bls.power(periods, durations)
    
    max_idx = np.argmax(periodogram.power)
    best_period = float(periodogram.period[max_idx].value)
    best_power = float(periodogram.power[max_idx])
    
    stats = bls.compute_stats(periodogram.period[max_idx], 
                               periodogram.duration[max_idx],
                               periodogram.transit_time[max_idx])
    
    snr = best_power / np.std(periodogram.power)
    is_detection = snr >= SNR_THRESHOLD
    
    # Generate folded light curve parameters for classification features
    t0 = float(periodogram.transit_time[max_idx].value)
    phase = ((time - t0) % best_period) / best_period
    phase = np.where(phase > 0.5, phase - 1.0, phase)
    
    sort_idx = np.argsort(phase)
    phase_sorted = phase[sort_idx]
    flux_sorted = flux[sort_idx]
    
    return {
        "detected": is_detection,
        "period": best_period,
        "period_uncertainty": best_period * 0.01,
        "t0": t0,
        "duration": float(periodogram.duration[max_idx].value),
        "depth": float(stats["depth"][0]),
        "depth_err": float(stats["depth"][1]),
        "snr": snr,
        "sde": snr,
        "fap": None,
        "n_transits": int(stats["transit_times"].size) if "transit_times" in stats else 0,
        "odd_even_mismatch": 0.0,
        "power_spectrum": {
            "periods": periodogram.period.value.tolist(),
            "power": periodogram.power.tolist()
        },
        "phase": (phase_sorted + 0.5).tolist(),  # shift to [0, 1] to match TLS features
        "folded_flux": flux_sorted.tolist(),
        "model_flux": flux_sorted.tolist(),     # fallback
        "method": "BLS"
    }


def _empty_result(reason: str) -> Dict:
    return {
        "detected": False, "period": 0.0, "period_uncertainty": 0.0,
        "t0": 0.0, "duration": 0.0, "depth": 0.0, "depth_err": 0.0,
        "snr": 0.0, "sde": 0.0, "fap": 1.0, "n_transits": 0,
        "odd_even_mismatch": 0.0, "power_spectrum": {"periods": [], "power": []},
        "phase": [], "folded_flux": [], "model_flux": [],
        "method": "NONE", "reason": reason
    }
