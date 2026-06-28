import numpy as np
from astropy.timeseries import BoxLeastSquares

def run_bls_search(time, flux, flux_err=None, min_period=0.5, max_period=10.0, min_duration=0.05, max_duration=0.5):
    """
    Runs a Box Least Squares (BLS) period search on the light curve.
    Returns:
        results: astropy BLS results object
        best_params: dict containing period, epoch, duration, depth, SNR, SDE
    """
    # Ensure duration is physically realistic and strictly less than minimum period
    # Transits usually last <10% of period. Let's enforce max_duration <= min_period * 0.3
    max_dur = min(max_duration, min_period * 0.3)
    min_dur = min(min_duration, max_dur * 0.5)
    
    if flux_err is None:
        flux_err = np.ones_like(flux) * 0.001
        
    model = BoxLeastSquares(time, flux, dy=flux_err)
    
    # Define durations to search over
    durations = np.linspace(min_dur, max_dur, 10)
    
    # Auto-generate a frequency/period grid
    results = model.autopower(durations, minimum_period=min_period, maximum_period=max_period)
    
    # Find the peak
    index = np.argmax(results.power)
    best_period = results.period[index]
    best_duration = results.duration[index]
    best_epoch = results.transit_time[index]
    best_depth = results.depth[index]
    
    # Calculate SNR and SDE
    best_snr = results.power[index] / np.median(results.power) # simple SNR metric
    
    # SDE = (peak_power - mean_power) / std_power
    mean_power = np.mean(results.power)
    std_power = np.std(results.power)
    best_sde = (results.power[index] - mean_power) / std_power if std_power > 0 else 0
    
    best_params = {
        'period': best_period,
        'epoch': best_epoch,
        'duration': best_duration,
        'depth': best_depth,
        'snr': best_snr,
        'sde': best_sde,
        'power_peak': results.power[index]
    }
    
    return results, best_params

def fold_lightcurve(time, flux, period, epoch):
    """
    Folds the light curve at a given period and epoch.
    Phase is normalized between -0.5 and 0.5 with 0.0 representing transit center.
    """
    # Normalize phases to 0-1
    phase = ((time - epoch) % period) / period
    
    # Shift phase to -0.5 to 0.5
    phase = np.where(phase > 0.5, phase - 1.0, phase)
    
    # Sort phases
    sort_idx = np.argsort(phase)
    return phase[sort_idx], flux[sort_idx]
