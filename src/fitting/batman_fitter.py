"""
Batman Transit Model Fitter
Fits transit parameters with uncertainty estimation.
Falls back to pure-Python trapezoidal fitting if batman-package is not compiled/available.
"""
import numpy as np
from scipy.optimize import minimize, differential_evolution, curve_fit
from loguru import logger
from typing import Dict, Optional, Tuple

try:
    import batman
    BATMAN_AVAILABLE = True
except ImportError:
    BATMAN_AVAILABLE = False
    logger.warning("batman-package not available; falling back to pure-Python trapezoidal model for transit fitting")

from src.config import (
    BATMAN_LIMB_DARKENING, BATMAN_LD_COEFFS,
    MCMC_N_WALKERS, MCMC_N_STEPS, MCMC_BURN_IN
)


def fit_transit(time: np.ndarray, flux: np.ndarray,
                detection: Dict,
                run_mcmc: bool = False) -> Dict:
    """
    Fit transit model to phase-folded light curve.
    Returns fitted parameters with uncertainties.
    """
    period = detection.get("period", 1.0)
    t0 = detection.get("t0", 0.0)
    depth = max(detection.get("depth", 0.01), 1e-6)
    duration = detection.get("duration", 0.1)
    
    # Phase-fold
    phase = ((time - t0) % period) / period
    phase[phase > 0.5] -= 1.0
    
    # Sort by phase
    sort_idx = np.argsort(phase)
    phase_sorted = phase[sort_idx]
    flux_sorted = flux[sort_idx]
    
    if not BATMAN_AVAILABLE:
        return _fit_trapezoid_fallback(phase_sorted, flux_sorted, period, t0, depth, duration)

    # Initial parameter guess
    rp = np.sqrt(depth)
    a_over_rs = _estimate_scaled_semimajor(period, duration)
    
    p0 = np.array([rp, a_over_rs, 89.5, 0.0])  # [rp, a/Rs, inc, offset]
    bounds = [(0.001, 0.7), (2.0, 200.0), (70.0, 90.0), (-0.05, 0.05)]
    
    # Optimize with differential evolution (global) then refine
    try:
        result_de = differential_evolution(
            _batman_residuals_de,
            bounds=bounds,
            args=(phase_sorted, flux_sorted, period),
            seed=42, maxiter=200, tol=1e-8,
            workers=1
        )
        p_best = result_de.x
    except Exception:
        p_best = p0
    
    # Local refinement
    try:
        result_local = minimize(
            _batman_residuals_de,
            p_best,
            args=(phase_sorted, flux_sorted, period),
            method="Nelder-Mead",
            options={"maxiter": 5000, "xatol": 1e-8, "fatol": 1e-10}
        )
        p_best = result_local.x
    except Exception:
        pass
    
    # Compute fitted model
    flux_model = _batman_model(p_best, phase_sorted, period)
    residuals = flux_sorted - flux_model
    rms = float(np.sqrt(np.nanmean(residuals**2)))
    
    # Parameter uncertainties from Hessian (approx)
    fitted_depth = float(p_best[0]**2)
    fitted_rp = float(p_best[0])
    
    # Uncertainty estimation (bootstrap or MCMC)
    if run_mcmc and len(time) > 200:
        uncertainties = _mcmc_uncertainties(phase_sorted, flux_sorted, period, p_best)
    else:
        uncertainties = _bootstrap_uncertainties(phase_sorted, flux_sorted, period, p_best)
    
    # Compute chi-squared
    noise = rms if rms > 0 else 1e-4
    chi2 = float(np.sum((residuals / noise)**2))
    chi2_reduced = chi2 / max(len(residuals) - 4, 1)
    
    return {
        "fitted": True,
        "period": period,
        "period_err": detection.get("period_uncertainty", period * 0.001),
        "t0": t0,
        "depth": fitted_depth,
        "depth_err": float(uncertainties.get("depth_err", fitted_depth * 0.1)),
        "depth_ppm": fitted_depth * 1e6,
        "rp_rs": fitted_rp,
        "a_rs": float(p_best[1]),
        "inclination": float(p_best[2]),
        "duration": duration,
        "duration_err": float(uncertainties.get("duration_err", duration * 0.1)),
        "rms": rms,
        "chi2_reduced": chi2_reduced,
        "phase": phase_sorted.tolist(),
        "flux_folded": flux_sorted.tolist(),
        "flux_model": flux_model.tolist(),
        "residuals": residuals.tolist()
    }


def _fit_trapezoid_fallback(phase, flux, period, t0_init, depth_init, duration_init):
    """Fallback pure-Python trapezoidal fitting when batman-package is missing."""
    def trapezoid_model_fit(ph, t_offset, depth, dur_phase, ingress_ratio):
        # Clip inside to avoid mathematical errors
        depth = max(0.0, depth)
        dur_phase = max(0.001, dur_phase)
        ingress_ratio = np.clip(ingress_ratio, 0.001, 0.5)
        
        ingress = dur_phase * ingress_ratio
        half_dur = dur_phase / 2.0
        half_flat = half_dur - ingress
        
        dt = np.abs(ph - t_offset)
        flux_out = np.ones_like(ph)
        
        flat_mask = dt <= half_flat
        flux_out[flat_mask] = 1.0 - depth
        
        ingress_mask = (dt > half_flat) & (dt < half_dur)
        fraction = (half_dur - dt[ingress_mask]) / ingress
        flux_out[ingress_mask] = 1.0 - depth * fraction
        return flux_out

    # Bounds: [t_offset, depth, dur_phase, ingress_ratio]
    dur_phase_guess = duration_init / period
    p0 = [0.0, depth_init, dur_phase_guess, 0.1]
    bounds = (
        [-0.1, 0.0, 0.001, 0.001],
        [0.1, 0.5, 0.5, 0.5]
    )
    
    try:
        popt, pcov = curve_fit(trapezoid_model_fit, phase, flux, p0=p0, bounds=bounds, maxfev=2000)
        perr = np.sqrt(np.diag(pcov))
        
        t_offset, depth_fit, dur_phase_fit, ingress_ratio_fit = popt
        depth_err = perr[1]
        duration_err = perr[2] * period
        
        # Derived values
        flux_model = trapezoid_model_fit(phase, *popt)
        residuals = flux - flux_model
        rms = float(np.sqrt(np.nanmean(residuals**2)))
        
        # batman matching approximations
        rp_rs = np.sqrt(depth_fit)
        # a/Rs can be approximated from Kepler's third law / transit geometry
        a_rs = 1.0 / (np.sin(dur_phase_fit * np.pi) + 1e-10)
        
        return {
            "fitted": True,
            "period": period,
            "period_err": period * 0.001,
            "t0": t0_init + t_offset * period,
            "depth": float(depth_fit),
            "depth_err": float(depth_err),
            "depth_ppm": float(depth_fit * 1e6),
            "rp_rs": float(rp_rs),
            "a_rs": float(a_rs),
            "inclination": 90.0,
            "duration": float(dur_phase_fit * period),
            "duration_err": float(duration_err),
            "rms": rms,
            "chi2_reduced": float(np.sum((residuals / (rms + 1e-10))**2) / max(len(residuals)-4, 1)),
            "phase": phase.tolist(),
            "flux_folded": flux.tolist(),
            "flux_model": flux_model.tolist(),
            "residuals": residuals.tolist()
        }
    except Exception as e:
        logger.error(f"Fallback trapezoidal fitting failed: {e}")
        return {"fitted": False}


def _batman_model(params: np.ndarray, phase: np.ndarray, period: float) -> np.ndarray:
    """Evaluate batman transit model at given phases."""
    rp, a_rs, inc, offset = params
    rp = max(abs(rp), 0.001)
    a_rs = max(a_rs, 2.0)
    
    bp = batman.TransitParams()
    bp.t0 = 0.0
    bp.per = 1.0                    # phase-normalized
    bp.rp = rp
    bp.a = a_rs
    bp.inc = np.clip(inc, 70, 90)
    bp.ecc = 0.0
    bp.w = 90.0
    bp.u = BATMAN_LD_COEFFS
    bp.limb_dark = BATMAN_LIMB_DARKENING
    
    try:
        m = batman.TransitModel(bp, phase)
        return m.light_curve(bp) + offset
    except Exception:
        return np.ones(len(phase)) + offset


def _batman_residuals_de(params, phase, flux, period):
    """Residual function for optimization."""
    model = _batman_model(params, phase, period)
    return float(np.sum((flux - model)**2))


def _estimate_scaled_semimajor(period: float, duration: float) -> float:
    """Estimate a/Rs from period and duration (Seager & Mallén-Ornelas 2003)."""
    if duration <= 0:
        return 15.0
    a_rs = np.pi * period / (duration * np.pi)
    return max(min(a_rs, 150.0), 3.0)


def _bootstrap_uncertainties(phase, flux, period, p_best, n_boot=100) -> Dict:
    """Bootstrap parameter uncertainty estimation."""
    rp_vals, duration_vals = [], []
    n = len(phase)
    
    for _ in range(n_boot):
        idx = np.random.choice(n, n, replace=True)
        p_s, f_s = phase[idx], flux[idx]
        sort_i = np.argsort(p_s)
        try:
            r = minimize(
                _batman_residuals_de, p_best,
                args=(p_s[sort_i], f_s[sort_i], period),
                method="Nelder-Mead",
                options={"maxiter": 500}
            )
            rp_vals.append(r.x[0]**2)
            duration_vals.append(r.x[0] / (r.x[1] + 1e-6))
        except Exception:
            pass
    
    if len(rp_vals) > 10:
        return {
            "depth_err": float(np.std(rp_vals)),
            "duration_err": float(np.std(duration_vals)) if duration_vals else 0.0
        }
    return {"depth_err": p_best[0]**2 * 0.1, "duration_err": 0.01}


def _mcmc_uncertainties(phase, flux, period, p_best) -> Dict:
    """MCMC parameter uncertainty (emcee). Called only for confirmed transits."""
    try:
        import emcee
        
        def log_likelihood(params):
            if any(p < 0 for p in [params[0], params[1]]):
                return -np.inf
            model = _batman_model(params, phase, period)
            return -0.5 * np.sum((flux - model)**2 / 0.001**2)
        
        def log_prior(params):
            rp, a, inc, off = params
            if 0.001 < rp < 0.7 and 2 < a < 200 and 70 < inc < 90 and -0.05 < off < 0.05:
                return 0.0
            return -np.inf
        
        log_prob = lambda p: log_likelihood(p) + log_prior(p)
        
        ndim = 4
        nwalkers = MCMC_N_WALKERS
        pos = p_best + 1e-4 * np.random.randn(nwalkers, ndim)
        
        sampler = emcee.EnsembleSampler(nwalkers, ndim, log_prob)
        sampler.run_mcmc(pos, MCMC_N_STEPS, progress=False)
        
        flat_samples = sampler.get_chain(discard=MCMC_BURN_IN, thin=15, flat=True)
        
        return {
            "depth_err": float(np.std(flat_samples[:, 0]**2)),
            "duration_err": float(np.std(flat_samples[:, 0] / flat_samples[:, 1]))
        }
    except Exception as e:
        logger.warning(f"MCMC failed: {e}. Using bootstrap.")
        return _bootstrap_uncertainties(phase, flux, period, p_best)
