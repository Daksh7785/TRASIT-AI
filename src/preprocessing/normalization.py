"""
Flux Normalization Methods
Multiple strategies for TESS light curve normalization.
"""
import numpy as np
from typing import Tuple
from loguru import logger


def normalize_median(flux: np.ndarray, 
                     flux_err: np.ndarray = None) -> Tuple[np.ndarray, np.ndarray]:
    """Divide by median flux. Most common for transit work."""
    median = np.nanmedian(flux)
    if median == 0 or np.isnan(median):
        logger.warning("Median flux is zero or NaN, skipping normalization")
        return flux, flux_err
    normalized = flux / median
    err_norm = flux_err / median if flux_err is not None else None
    return normalized, err_norm


def normalize_percentile(flux: np.ndarray,
                         flux_err: np.ndarray = None,
                         percentile: float = 95.0) -> Tuple:
    """Normalize by a high percentile — good for variable stars."""
    ref = np.nanpercentile(flux, percentile)
    if ref == 0:
        return normalize_median(flux, flux_err)
    normalized = flux / ref
    err_norm = flux_err / ref if flux_err is not None else None
    return normalized, err_norm


def normalize_iqr(flux: np.ndarray,
                  flux_err: np.ndarray = None) -> Tuple:
    """
    IQR normalization: center on median, scale by IQR.
    Robust to outliers and deep eclipses.
    """
    q25 = np.nanpercentile(flux, 25)
    q75 = np.nanpercentile(flux, 75)
    median = np.nanmedian(flux)
    iqr = q75 - q25
    
    if iqr == 0:
        return normalize_median(flux, flux_err)
    
    normalized = (flux - median) / iqr + 1.0
    err_norm = flux_err / iqr if flux_err is not None else None
    return normalized, err_norm


def compute_cdpp(flux: np.ndarray, time: np.ndarray,
                 transit_duration_hr: float = 1.0) -> float:
    """
    Combined Differential Photometric Precision (CDPP).
    Measure of noise on transit timescales.
    Returns CDPP in ppm.
    
    Formula: CDPP = std(binned_flux) / sqrt(n_bins) * 1e6
    """
    cadence_hr = np.nanmedian(np.diff(time)) * 24
    n_per_bin = max(1, int(transit_duration_hr / cadence_hr))
    
    n_bins = len(flux) // n_per_bin
    if n_bins < 2:
        return float(np.std(flux) * 1e6)
    
    binned = flux[:n_bins * n_per_bin].reshape(n_bins, n_per_bin).mean(axis=1)
    cdpp_ppm = float(np.std(binned) * 1e6 / np.sqrt(1))
    return cdpp_ppm


def normalize_lightcurve(flux: np.ndarray,
                          flux_err: np.ndarray = None,
                          method: str = "median") -> Tuple:
    """Unified normalization interface."""
    methods = {
        "median": normalize_median,
        "percentile": normalize_percentile,
        "iqr": normalize_iqr,
    }
    fn = methods.get(method, normalize_median)
    return fn(flux, flux_err)
