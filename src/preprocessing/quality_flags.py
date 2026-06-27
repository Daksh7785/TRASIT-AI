# Production Release v2.0 - Optimized Quality Flag Masking
"""
TESS Quality Flag Filtering
TESS assigns quality bitmask flags to each cadence.
We must filter out bad cadences before any science.
Reference: TESS Data Release Notes, Sector 1+
"""
import numpy as np
from loguru import logger

# TESS Quality Flag Bitmask Definitions
QUALITY_FLAGS = {
    1:    "Attitude tweak",
    2:    "Safe mode",
    4:    "Coarse point",
    8:    "Earth point",
    16:   "Argabrightening event",
    32:   "Desat event",
    64:   "Cosmic ray in optimal aperture",
    128:  "Manual exclude",
    256:  "No fine point",
    512:  "Impulsive outlier",
    1024: "Argabrightening in 2+ CCDs",
    2048: "Cosmic ray in collateral pixel",
    4096: "Stray light from Earth/Moon",
}

# Conservative mask — removes most problematic cadences
CONSERVATIVE_QUALITY_MASK = (
    2 | 4 | 8 | 16 | 32 | 128 | 256 | 2048 | 4096
)

# Permissive mask — only removes critical issues
PERMISSIVE_QUALITY_MASK = 2 | 4 | 8 | 128


def apply_quality_mask(time: np.ndarray, flux: np.ndarray,
                        quality: np.ndarray,
                        flux_err: np.ndarray = None,
                        mask_level: str = "conservative") -> tuple:
    """
    Filter light curve using TESS quality bitmask.
    
    Args:
        time, flux, quality, flux_err: Light curve arrays
        mask_level: 'conservative' (removes ~5% cadences) or 'permissive'
    
    Returns:
        Filtered (time, flux, quality, flux_err) arrays
    """
    bitmask = (CONSERVATIVE_QUALITY_MASK if mask_level == "conservative" 
               else PERMISSIVE_QUALITY_MASK)
    
    # Keep cadences where quality flag has no overlap with our bitmask
    good = (quality & bitmask) == 0
    n_removed = (~good).sum()
    frac_removed = n_removed / len(quality) if len(quality) > 0 else 0
    
    if frac_removed > 0.3:
        logger.warning(f"Quality filtering removed {frac_removed:.1%} of cadences! "
                       f"Consider using permissive mask.")
    else:
        logger.debug(f"Quality filtering: removed {n_removed} cadences ({frac_removed:.1%})")
    
    result = [time[good], flux[good], quality[good]]
    if flux_err is not None:
        result.append(flux_err[good])
    
    return tuple(result)


def flag_momentum_dumps(time: np.ndarray, flux: np.ndarray,
                         quality: np.ndarray) -> np.ndarray:
    """
    Identify momentum dump times (bitmask bit 32).
    Returns boolean array True where momentum dump occurred.
    """
    return (quality & 32) > 0


def interpolate_across_gaps(time: np.ndarray, flux: np.ndarray,
                              max_gap_hours: float = 0.5) -> tuple:
    """
    Linear interpolation across data gaps < max_gap_hours.
    Larger gaps are left as-is (TLS handles them via break_tolerance).
    """
    cadence_hours = np.nanmedian(np.diff(time)) * 24  # convert days to hours
    max_gap_cadences = int(max_gap_hours / cadence_hours)
    
    if max_gap_cadences < 2:
        return time, flux
    
    dt = np.diff(time)
    gap_indices = np.where(dt > max_gap_hours / 24)[0]
    
    if len(gap_indices) == 0:
        return time, flux
    
    t_out, f_out = list(time), list(flux)
    offset = 0
    
    for idx in gap_indices:
        real_idx = idx + offset
        t_start = t_out[real_idx]
        t_end = t_out[real_idx + 1]
        gap_size = t_end - t_start
        
        if gap_size > max_gap_hours / 24:
            continue
        
        n_interp = int(gap_size / (cadence_hours / 24)) - 1
        if n_interp <= 0:
            continue
        
        t_interp = np.linspace(t_start, t_end, n_interp + 2)[1:-1]
        f_interp = np.interp(t_interp, [t_start, t_end], 
                              [t_out[real_idx], t_out[real_idx + 1]])
        
        for i, (t, f) in enumerate(zip(t_interp, f_interp)):
            t_out.insert(real_idx + 1 + i, t)
            f_out.insert(real_idx + 1 + i, f)
        
        offset += n_interp
    
    return np.array(t_out), np.array(f_out)
