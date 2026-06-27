"""
Light Curve Detrending Module
Removes stellar and instrumental systematics to reveal transit signals.
"""
import numpy as np
from scipy.signal import savgol_filter
from loguru import logger
from typing import Tuple, Optional

try:
    from wotan import flatten
    WOTAN_AVAILABLE = True
except ImportError:
    WOTAN_AVAILABLE = False
    logger.warning("Wotan not available; falling back to Savitzky-Golay")

from src.config import DETREND_WINDOW_LENGTH, SIGMA_CLIP_THRESHOLD


def preprocess_lightcurve(time: np.ndarray, flux: np.ndarray,
                           flux_err: Optional[np.ndarray] = None,
                           quality: Optional[np.ndarray] = None,
                           mask_level: str = "conservative"
                           ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Full preprocessing pipeline:
    1. Quality flag filtering (using quality_flags.py)
    2. Outlier removal (using outlier_removal.py)
    3. Normalization (using normalization.py)
    4. Detrending (Wotan or SG)
    """
    from src.preprocessing.quality_flags import apply_quality_mask
    from src.preprocessing.outlier_removal import combined_outlier_removal
    from src.preprocessing.normalization import normalize_lightcurve
    
    # Step 1: Quality flags filtering if provided
    if quality is not None:
        time, flux, quality, flux_err = apply_quality_mask(time, flux, quality, flux_err, mask_level)
    
    # Step 1.1: Remove NaNs and Infs
    mask = np.isfinite(time) & np.isfinite(flux)
    if flux_err is not None:
        mask &= np.isfinite(flux_err) & (flux_err > 0)
    
    time, flux = time[mask], flux[mask]
    flux_err = flux_err[mask] if flux_err is not None else np.ones(len(flux)) * np.std(flux) * 0.1
    
    # Step 2: Combined Outlier Removal
    time, flux, flux_err = combined_outlier_removal(time, flux, flux_err)
    
    # Step 3: Normalize to median
    flux, flux_err = normalize_lightcurve(flux, flux_err, method="median")
    
    # Step 4: Detrend
    flux_detrended, flux_trend = detrend(time, flux)
    
    return time, flux_detrended, flux_trend, flux_err


def detrend(time: np.ndarray, flux: np.ndarray,
            method: str = "auto") -> Tuple[np.ndarray, np.ndarray]:
    """
    Detrend light curve using Wotan biweight or SG filter.
    Returns (detrended_flux, trend).
    """
    window = DETREND_WINDOW_LENGTH
    
    if WOTAN_AVAILABLE and method in ("auto", "wotan"):
        try:
            # Biweight is robust against outliers (best for transit work)
            flat, trend = flatten(
                time, flux,
                method="biweight",
                window_length=window,
                return_trend=True,
                break_tolerance=0.5
            )
            return flat, trend
        except Exception as e:
            logger.warning(f"Wotan failed ({e}), using SG filter")
    
    # Fallback: Savitzky-Golay
    return _sg_detrend(time, flux)


def _sg_detrend(time: np.ndarray, flux: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Savitzky-Golay detrending fallback."""
    cadence = np.nanmedian(np.diff(time))
    window_pts = int(DETREND_WINDOW_LENGTH / cadence)
    window_pts = window_pts if window_pts % 2 == 1 else window_pts + 1
    window_pts = max(window_pts, 11)
    
    trend = savgol_filter(flux, window_length=min(window_pts, len(flux)//2*2-1), 
                          polyorder=3)
    detrended = flux / (trend + 1e-12)
    return detrended, trend


def sigma_clip(time: np.ndarray, flux: np.ndarray,
               flux_err: np.ndarray, sigma: float = 4.0,
               n_iter: int = 5) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Iterative sigma clipping outlier removal."""
    mask = np.ones(len(flux), dtype=bool)
    for _ in range(n_iter):
        med = np.nanmedian(flux[mask])
        std = np.nanstd(flux[mask])
        new_mask = np.abs(flux - med) < sigma * std
        if new_mask.sum() == mask.sum():
            break
        mask = new_mask
    return time[mask], flux[mask], flux_err[mask]
