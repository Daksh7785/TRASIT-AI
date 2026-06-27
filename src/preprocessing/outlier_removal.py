# Production Release v2.0 - Optimized Outlier Filtering Pipeline
"""
Outlier Removal Methods
Multiple strategies for photometric outlier removal.
"""
import numpy as np
from scipy import stats
from loguru import logger
from typing import Tuple


def sigma_clip_iterative(time: np.ndarray, flux: np.ndarray,
                          flux_err: np.ndarray = None,
                          sigma: float = 4.0,
                          n_iter: int = 10) -> Tuple:
    """
    Iterative sigma clipping.
    Continues until no more points removed or n_iter reached.
    """
    mask = np.ones(len(flux), dtype=bool)
    
    for iteration in range(n_iter):
        med = np.nanmedian(flux[mask])
        std = np.nanstd(flux[mask])
        
        if std == 0:
            break
        
        new_mask = mask & (np.abs(flux - med) < sigma * std)
        
        n_removed = mask.sum() - new_mask.sum()
        if n_removed == 0:
            break
        
        mask = new_mask
    
    logger.debug(f"Sigma clip: removed {(~mask).sum()} outliers "
                 f"({(~mask).sum()/len(mask):.1%})")
    
    result = [time[mask], flux[mask]]
    if flux_err is not None:
        result.append(flux_err[mask])
    return tuple(result)


def mad_outlier_removal(time: np.ndarray, flux: np.ndarray,
                         flux_err: np.ndarray = None,
                         threshold: float = 5.0) -> Tuple:
    """
    Median Absolute Deviation (MAD) outlier removal.
    More robust than sigma clipping for heavy-tailed distributions.
    MAD = median(|x_i - median(x)|)
    """
    med = np.nanmedian(flux)
    mad = np.nanmedian(np.abs(flux - med))
    
    # Normalize MAD to sigma (1.4826 factor for Gaussian)
    sigma_mad = 1.4826 * mad
    
    if sigma_mad == 0:
        return sigma_clip_iterative(time, flux, flux_err)
    
    mask = np.abs(flux - med) < threshold * sigma_mad
    
    logger.debug(f"MAD removal: kept {mask.sum()}/{len(flux)} points")
    
    result = [time[mask], flux[mask]]
    if flux_err is not None:
        result.append(flux_err[mask])
    return tuple(result)


def remove_single_cadence_spikes(time: np.ndarray, flux: np.ndarray,
                                  flux_err: np.ndarray = None,
                                  window: int = 5,
                                  sigma: float = 5.0) -> Tuple:
    """
    Remove single-cadence spikes by comparing each point to its neighbors.
    Particularly important for cosmic ray events.
    """
    n = len(flux)
    mask = np.ones(n, dtype=bool)
    
    for i in range(window, n - window):
        neighbors = np.concatenate([flux[i-window:i], flux[i+1:i+window+1]])
        local_med = np.median(neighbors)
        local_std = np.std(neighbors)
        
        if local_std > 0 and np.abs(flux[i] - local_med) > sigma * local_std:
            mask[i] = False
    
    result = [time[mask], flux[mask]]
    if flux_err is not None:
        result.append(flux_err[mask])
    return tuple(result)


def combined_outlier_removal(time: np.ndarray, flux: np.ndarray,
                               flux_err: np.ndarray = None) -> Tuple:
    """
    Full outlier removal pipeline:
    1. Single-cadence spike removal (cosmic rays)
    2. MAD-based removal (systematic outliers)
    3. Iterative sigma clipping (final cleanup)
    """
    # Step 1
    if flux_err is not None:
        time, flux, flux_err = remove_single_cadence_spikes(time, flux, flux_err)
        time, flux, flux_err = mad_outlier_removal(time, flux, flux_err)
        time, flux, flux_err = sigma_clip_iterative(time, flux, flux_err)
        return time, flux, flux_err
    else:
        time, flux = remove_single_cadence_spikes(time, flux)
        time, flux = mad_outlier_removal(time, flux)
        time, flux = sigma_clip_iterative(time, flux)
        return time, flux, None
