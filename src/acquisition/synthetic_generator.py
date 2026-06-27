"""
Synthetic Light Curve Generator
Generates realistic TESS-like light curves for all 5 signal classes.
Used as fallback when TESS data download fails or for model training.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from loguru import logger
from typing import Tuple, List, Dict
from src.config import SYNTHETIC_DIR, CLASS_LABELS

try:
    import batman
    BATMAN_AVAILABLE = True
except ImportError:
    BATMAN_AVAILABLE = False
    logger.warning("batman-package not available; falling back to pure-Python trapezoidal model for synthetic data")

def generate_transit_lc(
    t_span: float = 27.4,
    cadence: float = 2 / 1440,  # 2-min in days
    period: float = None,
    depth: float = None,
    duration: float = None,
    noise_level: float = None,
    contamination: float = 0.0,
) -> Tuple[np.ndarray, np.ndarray, Dict]:
    """Generate a realistic planetary transit light curve."""
    rng = np.random.default_rng()
    
    period = period or rng.uniform(0.8, 12.0)
    depth = depth or rng.uniform(0.0001, 0.02)    # 100ppm to 2%
    duration = duration or rng.uniform(0.05, 0.15) * period
    noise_level = noise_level or rng.uniform(0.0005, 0.003)
    t0 = rng.uniform(0, period)
    
    t = np.arange(0, t_span, cadence)
    
    if BATMAN_AVAILABLE:
        try:
            params = batman.TransitParams()
            params.t0 = t0
            params.per = period
            params.rp = np.sqrt(depth)          # Rp/Rs
            params.a = 15.0                      # semi-major axis (Rs units)
            params.inc = rng.uniform(87.0, 90.0) # inclination
            params.ecc = 0.0
            params.w = 90.0
            params.u = [0.4, 0.25]
            params.limb_dark = "quadratic"
            
            m = batman.TransitModel(params, t)
            flux = m.light_curve(params)
        except Exception as e:
            logger.warning(f"batman model failed ({e}), using trapezoidal fallback")
            flux = _trapezoid_model_flux(t, t0, period, depth, duration)
    else:
        flux = _trapezoid_model_flux(t, t0, period, depth, duration)
    
    # Add contamination (blend dilution)
    if contamination > 0:
        flux = flux * (1 - contamination) + contamination
    
    # Add correlated + white noise (realistic TESS systematics)
    white = rng.normal(0, noise_level, len(t))
    red_noise = _generate_red_noise(len(t), noise_level * 0.5, cadence)
    flux = flux + white + red_noise
    
    true_params = {
        "period": period, "depth": depth, "duration": duration,
        "t0": t0, "snr": depth / noise_level, "label": "TRANSIT"
    }
    return t, flux, true_params

def _trapezoid_model_flux(t, t0, period, depth, duration):
    """Fallback pure-Python trapezoidal model."""
    flux = np.ones_like(t)
    phase = ((t - t0) % period) / period
    phase = np.where(phase > 0.5, phase - 1.0, phase)
    
    # Ingress/egress is 15% of duration
    ingress = 0.15 * duration / period
    half_dur = (duration / 2.0) / period
    half_flat = half_dur - ingress
    
    dt = np.abs(phase)
    flat_mask = dt <= half_flat
    flux[flat_mask] = 1.0 - depth
    
    ingress_mask = (dt > half_flat) & (dt < half_dur)
    fraction = (half_dur - dt[ingress_mask]) / ingress
    flux[ingress_mask] = 1.0 - depth * fraction
    return flux

def generate_eclipsing_binary_lc(t_span=27.4, cadence=2/1440) -> Tuple:
    """Generate eclipsing binary — primary + secondary eclipses."""
    rng = np.random.default_rng()
    period = rng.uniform(0.5, 5.0)
    primary_depth = rng.uniform(0.02, 0.3)       # deep primary
    secondary_depth = rng.uniform(0.005, primary_depth * 0.8)
    noise = rng.uniform(0.001, 0.005)
    t0 = rng.uniform(0, period)
    
    t = np.arange(0, t_span, cadence)
    flux = np.ones(len(t))
    
    # Primary & Secondary eclipses
    for params_set in [(primary_depth, t0, period), (secondary_depth, t0 + period/2, period)]:
        d, tc, per = params_set
        dur = rng.uniform(0.02, 0.1) * per
        phase = ((t - tc) % per) / per
        phase[phase > 0.5] -= 1.0
        in_eclipse = np.abs(phase) < (dur / (2 * per))
        flux[in_eclipse] -= d * np.cos(np.pi * phase[in_eclipse] * per / dur) ** 2
    
    flux += _generate_red_noise(len(t), noise, cadence) + np.random.normal(0, noise, len(t))
    
    true_params = {
        "period": period, "depth": primary_depth, "duration": rng.uniform(0.05, 0.15) * period,
        "t0": t0, "snr": primary_depth / noise, "label": "ECLIPSE",
        "secondary_depth": secondary_depth
    }
    return t, flux, true_params

def generate_blend_lc(t_span=27.4, cadence=2/1440) -> Tuple:
    """Diluted transit from a background eclipsing binary — looks like shallow transit."""
    rng = np.random.default_rng()
    t, flux_true, params = generate_eclipsing_binary_lc(t_span, cadence)
    
    # Dilute by contamination factor 0.7-0.95 (target star dominates aperture)
    contamination = rng.uniform(0.7, 0.95)
    flux = flux_true * (1 - contamination) + contamination
    
    params["label"] = "BLEND"
    params["contamination"] = contamination
    params["depth"] = params["depth"] * (1 - contamination)
    return t, flux, params

def generate_stellar_variability_lc(t_span=27.4, cadence=2/1440) -> Tuple:
    """Generate starspot rotational variability or pulsations."""
    rng = np.random.default_rng()
    t = np.arange(0, t_span, cadence)
    
    # Quasi-periodic sinusoidal modulation (starspots)
    P_rot = rng.uniform(1.0, 25.0)
    amp = rng.uniform(0.005, 0.05)
    phase = rng.uniform(0, 2 * np.pi)
    
    # Multi-frequency to simulate complex variability
    flux = 1.0
    for i in range(1, 4):
        flux_add = (amp / i) * np.sin(2 * np.pi * t / (P_rot / i) + phase * i)
        flux = flux + flux_add if i == 1 else flux + flux_add * rng.uniform(0.1, 0.5)
    
    noise = rng.uniform(0.001, 0.004)
    flux += np.random.normal(0, noise, len(t))
    
    true_params = {
        "period": P_rot, "depth": amp, "duration": 0.0,
        "t0": 0.0, "snr": amp / noise, "label": "STELLAR_VAR"
    }
    return t, flux, true_params

def generate_artifact_lc(t_span=27.4, cadence=2/1440) -> Tuple:
    """Instrumental artifacts, momentum dumps, scattered light."""
    rng = np.random.default_rng()
    t = np.arange(0, t_span, cadence)
    flux = np.ones(len(t))
    noise = rng.uniform(0.001, 0.005)
    
    # Sudden discontinuity (momentum dump)
    n_dumps = rng.integers(1, 4)
    for _ in range(n_dumps):
        idx = rng.integers(len(t) // 4, 3 * len(t) // 4)
        flux[idx:] += rng.uniform(-0.02, 0.02)
    
    # Random single-point or short spikes
    n_spikes = rng.integers(3, 15)
    spike_idx = rng.choice(len(t), n_spikes, replace=False)
    flux[spike_idx] += rng.uniform(-0.05, 0.05, n_spikes)
    
    flux += np.random.normal(0, noise, len(t))
    
    true_params = {
        "period": 0.0, "depth": 0.0, "duration": 0.0,
        "t0": 0.0, "snr": 0.0, "label": "ARTIFACT"
    }
    return t, flux, true_params

def _generate_red_noise(n: int, amplitude: float, cadence: float) -> np.ndarray:
    """Generate 1/f correlated noise via power spectrum method."""
    freqs = np.fft.rfftfreq(n, d=cadence)
    freqs[0] = 1.0  # avoid div by zero
    power = amplitude / np.sqrt(freqs)
    phases = np.random.uniform(0, 2 * np.pi, len(freqs))
    spectrum = power * np.exp(1j * phases)
    noise = np.fft.irfft(spectrum, n=n)
    return noise * (amplitude / (noise.std() + 1e-10))

GENERATORS = {
    "TRANSIT": generate_transit_lc,
    "ECLIPSE": generate_eclipsing_binary_lc,
    "BLEND": generate_blend_lc,
    "STELLAR_VAR": generate_stellar_variability_lc,
    "ARTIFACT": generate_artifact_lc,
}

def generate_training_dataset(n_per_class: int = 500) -> pd.DataFrame:
    """Generate balanced training dataset with all 5 classes."""
    logger.info(f"Generating {n_per_class} samples per class × {len(CLASS_LABELS)} classes")
    records = []
    
    for label in CLASS_LABELS:
        generator = GENERATORS[label]
        for i in range(n_per_class):
            try:
                t, flux, params = generator()
                records.append({
                    "tic_id": f"SYN_{label}_{i:04d}",
                    "label": label,
                    "period": params["period"],
                    "depth": params["depth"],
                    "duration": params["duration"],
                    "snr": params["snr"],
                    "t_json": t[:500].tolist(),      # first 500 points for storage
                    "f_json": flux[:500].tolist(),
                })
            except Exception as e:
                logger.warning(f"Generation failed for {label} sample {i}: {e}")
    
    df = pd.DataFrame(records)
    out_path = SYNTHETIC_DIR / "training_dataset.csv"
    df.drop(columns=["t_json", "f_json"]).to_csv(out_path, index=False)
    logger.success(f"Saved {len(df)} synthetic training samples → {out_path}")
    return df

def generate_demo_science_batch(n_lcs: int = 100) -> List[Dict]:
    """Generate a batch of science light curves (mixed classes) for demo."""
    rng = np.random.default_rng(42)
    # Realistic class distribution: mostly non-transits
    weights = [0.05, 0.10, 0.10, 0.35, 0.40]  # TRANSIT, EB, BLEND, VAR, ARTIFACT
    labels = rng.choice(CLASS_LABELS, size=n_lcs, p=weights)
    
    batch = []
    for i, label in enumerate(labels):
        t, flux, params = GENERATORS[label]()
        batch.append({
            "tic_id": f"SYN_DEMO_{i:05d}",
            "time": t,
            "flux": flux,
            "true_label": label,
            "true_params": params
        })
    logger.info(f"Generated demo batch: {n_lcs} light curves")
    return batch
