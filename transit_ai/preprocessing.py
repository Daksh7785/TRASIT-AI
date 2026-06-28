import numpy as np
from scipy.signal import savgol_filter

def sigma_clip(time, flux, flux_err=None, sigma_lower=4.0, sigma_upper=3.0, window_size=49):
    """
    Performs sigma clipping to remove outliers (e.g. cosmic rays, flares).
    Assumes time series is detrended or locally flat.
    Uses running median for clipping.
    """
    clean_time = []
    clean_flux = []
    clean_err = [] if flux_err is not None else None
    
    # Calculate median filter using rolling window
    half_w = window_size // 2
    n = len(flux)
    
    # Simple rolling median and std
    medians = np.zeros(n)
    stds = np.zeros(n)
    for i in range(n):
        start = max(0, i - half_w)
        end = min(n, i + half_w + 1)
        medians[i] = np.median(flux[start:end])
        stds[i] = np.std(flux[start:end])
        
    # Standard deviation fallback if too small (e.g., flat mock data)
    stds[stds < 1e-6] = 1e-6
    
    residual = flux - medians
    
    # Filter points
    mask = (residual >= -sigma_lower * stds) & (residual <= sigma_upper * stds)
    
    if flux_err is not None:
        return time[mask], flux[mask], flux_err[mask]
    return time[mask], flux[mask], None

def detrend_lightcurve(time, flux, window_length=101, polyorder=2):
    """
    Detrends the light curve using a Savitzky-Golay filter to remove long-term stellar variability.
    Ensures window_length is odd.
    """
    if len(flux) < window_length:
        # Reduce window length if data is too short
        window_length = len(flux) // 2 * 2 - 1
        if window_length < 3:
            return flux # can't detrend
            
    # Run Savitzky-Golay filter
    trend = savgol_filter(flux, window_length, polyorder)
    
    # Divide out the trend to normalize
    detrended_flux = flux / trend
    
    return detrended_flux, trend

def preprocess_pipeline(lc_data, detrend_window=101, clip_sigma_lower=4.0, clip_sigma_upper=3.0):
    """
    Runs the full preprocessing pipeline:
    1. Detrending using Savitzky-Golay filter.
    2. Outlier removal using sigma clipping.
    Returns: time, original_flux, detrended_flux, trend, clean_time, clean_flux, clean_err
    """
    # 1. Detrending
    detrended_flux, trend = detrend_lightcurve(lc_data.time, lc_data.flux, window_length=detrend_window)
    
    # 2. Sigma clipping on detrended flux
    clean_time, clean_flux, clean_err = sigma_clip(
        lc_data.time, 
        detrended_flux, 
        lc_data.flux_err, 
        sigma_lower=clip_sigma_lower, 
        sigma_upper=clip_sigma_upper
    )
    
    return {
        'time': lc_data.time,
        'raw_flux': lc_data.flux,
        'detrended_flux': detrended_flux,
        'trend': trend,
        'clean_time': clean_time,
        'clean_flux': clean_flux,
        'clean_err': clean_err
    }
