import numpy as np
from scipy.optimize import curve_fit

def trapezoid_model(t, t0, depth, duration, ingress_ratio):
    """
    Trapezoidal transit model.
    t: phase/time values
    t0: transit center offset
    depth: transit depth (positive value)
    duration: total duration of transit (width at base)
    ingress_ratio: ratio of ingress/egress duration to total duration (0 to 0.5)
    """
    # Clip parameters to physical boundaries inside the model
    depth = max(0.0, depth)
    duration = max(0.001, duration)
    ingress_ratio = np.clip(ingress_ratio, 0.001, 0.5)
    
    ingress_duration = duration * ingress_ratio
    half_dur = duration / 2.0
    half_flat = half_dur - ingress_duration
    
    # Distance from center
    dt = np.abs(t - t0)
    
    # Model calculation
    flux = np.ones_like(t)
    
    # In flat bottom
    flat_mask = dt <= half_flat
    flux[flat_mask] = 1.0 - depth
    
    # In ingress/egress
    ingress_mask = (dt > half_flat) & (dt < half_dur)
    # Linear interpolation
    fraction = (half_dur - dt[ingress_mask]) / ingress_duration
    flux[ingress_mask] = 1.0 - depth * fraction
    
    return flux

def fit_transit(phase, flux, initial_guess):
    """
    Fits the trapezoid model to folded light curve data.
    initial_guess: dict containing period, epoch, duration, depth
    """
    # Filter data around transit center to speed up and stabilize fit
    dur = initial_guess['duration']
    fit_mask = np.abs(phase) < max(0.25, dur * 2.0)
    
    p_fit = phase[fit_mask]
    f_fit = flux[fit_mask]
    
    if len(p_fit) < 10:
        # Fallback if too few points
        p_fit = phase
        f_fit = flux
        
    # Guess parameters: [t0, depth, duration, ingress_ratio]
    p0 = [
        0.0,  # t0 center offset
        initial_guess.get('depth', 0.01),
        dur,
        0.1   # ingress ratio default
    ]
    
    # Define bounds:
    # t0: within 20% of duration
    # depth: 0 to 0.2
    # duration: 0.001 to 0.5 (in phase units)
    # ingress_ratio: 0.001 to 0.5
    bounds = (
        [-dur * 0.2, 0.0, 0.001, 0.001],
        [dur * 0.2, 0.2, 0.5, 0.5]
    )
    
    try:
        popt, pcov = curve_fit(
            trapezoid_model,
            p_fit,
            f_fit,
            p0=p0,
            bounds=bounds,
            maxfev=2000
        )
        
        # Calculate standard errors (uncertainties) from covariance matrix
        perr = np.sqrt(np.diag(pcov))
        
        fit_results = {
            't0_offset': popt[0],
            'depth': popt[1],
            'duration': popt[2],
            'ingress_ratio': popt[3],
            't0_offset_err': perr[0],
            'depth_err': perr[1],
            'duration_err': perr[2],
            'ingress_ratio_err': perr[3],
            'success': True
        }
    except Exception as e:
        # Fallback to initial guess if fit fails
        fit_results = {
            't0_offset': 0.0,
            'depth': initial_guess.get('depth', 0.01),
            'duration': dur,
            'ingress_ratio': 0.1,
            't0_offset_err': 0.0,
            'depth_err': 0.0,
            'duration_err': 0.0,
            'ingress_ratio_err': 0.0,
            'success': False,
            'error': str(e)
        }
        
    return fit_results
