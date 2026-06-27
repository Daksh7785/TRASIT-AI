# Production Release v2.0 - Eclipsing Binary Diagnostics
"""
Secondary Eclipse Detection
Tests for secondary eclipse at phase 0.5 offset.
"""
import numpy as np
from scipy.signal import find_peaks
from typing import Dict, Optional


def detect_secondary_eclipse(time: np.ndarray, flux: np.ndarray,
                               period: float, t0: float,
                               duration: float) -> Dict:
    """
    Search for secondary eclipse at phase 0.5 offset.
    """
    if period <= 0 or duration <= 0:
        return {"secondary_detected": False, "secondary_depth": 0.0, "depth_ratio": 0.0}
    
    # Phase-fold
    phase = ((time - t0) % period) / period
    
    # Primary: phase 0 ± (duration/period/2)
    half_dur_phase = (duration / period) / 2
    
    # Secondary: phase 0.5 ± (duration/period/2)
    primary_mask = np.abs(phase) < half_dur_phase * 2
    secondary_mask = np.abs(phase - 0.5) < half_dur_phase * 2
    
    # Also check phase 0.9 (for eccentric orbits)
    oot_mask = (~primary_mask) & (~secondary_mask)
    
    if primary_mask.sum() < 3 or oot_mask.sum() < 10:
        return {"secondary_detected": False, "secondary_depth": 0.0, "depth_ratio": 0.0}
    
    oot_level = np.nanmedian(flux[oot_mask])
    
    # Primary depth
    primary_depth = oot_level - np.nanmin(flux[primary_mask]) if primary_mask.sum() > 0 else 0.0
    
    # Secondary depth at phase 0.5
    secondary_depth = 0.0
    secondary_phase_center = 0.0
    
    if secondary_mask.sum() >= 3:
        secondary_min = np.nanmin(flux[secondary_mask])
        secondary_depth = max(0.0, oot_level - secondary_min)
    
    # Search for secondary anywhere in phase
    # Bin phase into 200 bins and look for dip away from primary
    n_bins = 200
    bins = np.linspace(0, 1, n_bins + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    binned_flux = np.zeros(n_bins)
    bin_counts = np.zeros(n_bins)
    
    for i in range(n_bins):
        in_bin = (phase >= bins[i]) & (phase < bins[i+1])
        if in_bin.sum() > 0:
            binned_flux[i] = np.nanmedian(flux[in_bin])
            bin_counts[i] = in_bin.sum()
        else:
            binned_flux[i] = oot_level
    
    # Exclude primary region from secondary search
    primary_bin_mask = np.abs(bin_centers) < half_dur_phase * 3
    binned_flux_masked = binned_flux.copy()
    binned_flux_masked[primary_bin_mask] = oot_level
    
    # Find dip (inverted peak)
    dip_depths = oot_level - binned_flux_masked
    peaks, properties = find_peaks(dip_depths, height=primary_depth * 0.05,
                                    distance=int(n_bins * half_dur_phase))
    
    has_secondary = False
    best_secondary_depth = secondary_depth
    best_secondary_phase = 0.5
    
    if len(peaks) > 0:
        best_peak_idx = peaks[np.argmax(dip_depths[peaks])]
        best_secondary_phase = bin_centers[best_peak_idx]
        best_secondary_depth = max(secondary_depth, dip_depths[best_peak_idx])
        
        # Secondary is significant if >3% of primary depth
        if best_secondary_depth > 0.03 * primary_depth and primary_depth > 0:
            has_secondary = True
    
    depth_ratio = (best_secondary_depth / primary_depth) if primary_depth > 0 else 0.0
    
    # EB diagnostics
    is_likely_eb = (
        depth_ratio > 0.1 or           # Strong secondary → EB
        (depth_ratio > 0.03 and abs(best_secondary_phase - 0.5) < 0.05) or  # At phase 0.5 → EB
        depth_ratio > 0.3              # Very deep secondary → definitely EB
    )
    
    return {
        "secondary_detected": has_secondary,
        "secondary_depth": float(best_secondary_depth),
        "secondary_depth_ppm": float(best_secondary_depth * 1e6),
        "secondary_phase": float(best_secondary_phase),
        "depth_ratio": float(depth_ratio),
        "primary_depth": float(primary_depth),
        "is_likely_eb": is_likely_eb,
        "eb_confidence": min(1.0, depth_ratio * 3.0),
        "phase_offset_from_half": float(abs(best_secondary_phase - 0.5))
    }


def odd_even_mismatch_test(time: np.ndarray, flux: np.ndarray,
                            period: float, t0: float,
                            duration: float) -> Dict:
    """
    Odd-even transit depth mismatch test.
    For a planet: odd ≈ even transit depth.
    For an EB: alternating primary/secondary → odd ≠ even depths.
    """
    if period <= 0:
        return {"odd_even_mismatch": 0.0, "odd_depth": 0.0, "even_depth": 0.0}
    
    transit_times = []
    t_start = t0
    while t_start < time.max():
        transit_times.append(t_start)
        t_start += period
    
    half_dur = duration / 2
    odd_depths, even_depths = [], []
    
    for i, tc in enumerate(transit_times):
        in_transit = np.abs(time - tc) < half_dur
        if in_transit.sum() < 3:
            continue
        oot = (np.abs(time - tc) > half_dur) & (np.abs(time - tc) < half_dur * 4)
        if oot.sum() < 5:
            continue
        oot_level = np.nanmedian(flux[oot])
        depth = oot_level - np.nanmin(flux[in_transit])
        if i % 2 == 0:
            even_depths.append(max(0, depth))
        else:
            odd_depths.append(max(0, depth))
    
    if not odd_depths or not even_depths:
        return {"odd_even_mismatch": 0.0, "odd_depth": 0.0, "even_depth": 0.0}
    
    odd_mean = np.mean(odd_depths)
    even_mean = np.mean(even_depths)
    avg_depth = (odd_mean + even_mean) / 2
    
    mismatch = abs(odd_mean - even_mean) / (avg_depth + 1e-10)
    
    return {
        "odd_even_mismatch": float(mismatch),
        "odd_depth": float(odd_mean),
        "even_depth": float(even_mean),
        "n_odd_transits": len(odd_depths),
        "n_even_transits": len(even_depths),
        "is_eb_indicator": mismatch > 0.1
    }
