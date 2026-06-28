import numpy as np
import pandas as pd
import warnings

# Suppress lightkurve and astropy warnings for clean terminal outputs
warnings.filterwarnings('ignore', category=UserWarning)

try:
    import lightkurve as lk
except ImportError:
    lk = None

class LightCurveData:
    def __init__(self, time, flux, flux_err=None, name="Target"):
        self.time = np.array(time)
        self.flux = np.array(flux)
        if flux_err is None:
            self.flux_err = np.ones_like(flux) * 0.001
        else:
            self.flux_err = np.array(flux_err)
        self.name = name

    def to_df(self):
        return pd.DataFrame({
            'time': self.time,
            'flux': self.flux,
            'flux_err': self.flux_err
        })

def download_tess_lightcurve(tic_id, sector=None):
    """
    Downloads TESS light curve for a given TIC ID.
    If sector is not provided, downloads the first available sector.
    """
    if lk is None:
        raise ImportError("lightkurve is not installed. Run 'pip install lightkurve'")
    
    # Clean TIC ID prefix if provided
    tic_str = str(tic_id).lower()
    if tic_str.startswith("tic"):
        tic_str = tic_str.replace("tic", "").strip()
    
    query_str = f"TIC {tic_str}"
    
    try:
        # Search light curves
        search_result = lk.search_lightcurve(query_str, mission="TESS")
        if len(search_result) == 0:
            raise ValueError(f"No TESS light curves found for {query_str}")
        
        if sector is not None:
            search_result = search_result[search_result.author == "SPOC"] # Prefer SPOC
            # Filter by sector
            sectors = [int(s.replace("Sector ", "")) for s in search_result.observation]
            if sector in sectors:
                idx = sectors.index(sector)
                lc_file = search_result[idx]
            else:
                lc_file = search_result[0]
        else:
            # Prefer SPOC author
            spoc_results = search_result[search_result.author == "SPOC"]
            if len(spoc_results) > 0:
                lc_file = spoc_results[0]
            else:
                lc_file = search_result[0]
                
        lc = lc_file.download()
        if lc is None:
            raise ValueError(f"Download failed for {query_str}")
            
        # Clean nan values
        lc = lc.remove_nans()
        
        # Extract pdcflux (pre-search data conditioned flux) or regular flux
        flux_col = 'pdcsap_flux' if 'pdcsap_flux' in lc.columns else 'flux'
        
        # Normalize flux if not normalized
        flux = lc[flux_col].value
        flux_err = lc[flux_col + "_err"].value if (flux_col + "_err") in lc.columns else None
        
        # Handle unit objects
        if hasattr(flux, 'value'):
            flux = flux.value
        if hasattr(flux_err, 'value'):
            flux_err = flux_err.value
            
        median_flux = np.nanmedian(flux)
        flux_norm = flux / median_flux
        if flux_err is not None:
            flux_err_norm = flux_err / median_flux
        else:
            flux_err_norm = None
            
        return LightCurveData(lc.time.value, flux_norm, flux_err_norm, name=f"TIC {tic_str}")
    except Exception as e:
        raise RuntimeError(f"Error fetching data from MAST: {str(e)}")

def generate_synthetic_lightcurve(label, length=2000, noise_level=0.001, period=3.5, depth=0.01, duration=0.15, random_seed=None):
    """
    Generates synthetic light curve.
    Labels: 'transit', 'eclipse', 'blend', 'noise'
    """
    if random_seed is not None:
        np.random.seed(random_seed)
        
    time = np.linspace(0, 15.0, length) # 15 days observation
    
    # Base flux is 1.0
    flux = np.ones_like(time)
    
    # Phase calculation
    t0 = 1.0 # transit/eclipse midpoint epoch
    phase = ((time - t0) % period) / period
    
    # Duration in phase units
    duration_phase = duration / period
    
    # 1. Transits (flat-bottomed or slight curvature)
    if label == 'transit':
        # Add dips
        for i, p in enumerate(phase):
            if p < duration_phase:
                # Flat bottom transit with ingress/egress
                # Trapezoidal model
                norm_p = p / duration_phase
                if norm_p < 0.15: # ingress
                    flux[i] -= depth * (norm_p / 0.15)
                elif norm_p > 0.85: # egress
                    flux[i] -= depth * ((1.0 - norm_p) / 0.15)
                else: # flat bottom
                    flux[i] -= depth
                    
    # 2. Eclipses (V-shaped, primary & secondary dips)
    elif label == 'eclipse':
        # Primary eclipse at phase 0, secondary at phase 0.5
        sec_depth = depth * 0.4
        for i, p in enumerate(phase):
            # Primary eclipse
            if p < duration_phase:
                norm_p = p / duration_phase
                flux[i] -= depth * (1.0 - 2.0 * abs(norm_p - 0.5)) # V-shape
            # Secondary eclipse
            p_sec = (p - 0.5) % 1.0
            if p_sec < duration_phase:
                norm_p = p_sec / duration_phase
                flux[i] -= sec_depth * (1.0 - 2.0 * abs(norm_p - 0.5)) # V-shape

    # 3. Blends (shallow transit with high background flux contamination)
    elif label == 'blend':
        # Highly diluted transit (diluted by a factor of 10)
        diluted_depth = depth * 0.1
        for i, p in enumerate(phase):
            if p < duration_phase:
                norm_p = p / duration_phase
                if norm_p < 0.15:
                    flux[i] -= diluted_depth * (norm_p / 0.15)
                elif norm_p > 0.85:
                    flux[i] -= diluted_depth * ((1.0 - norm_p) / 0.15)
                else:
                    flux[i] -= diluted_depth
        # Add high stellar rotation/spot modulation simulating background binary
        flux += 0.0005 * np.sin(2 * np.pi * time / 1.2)

    # 4. Noise/Other
    elif label == 'noise':
        # Stellar spot modulation or rotation
        flux += 0.002 * np.sin(2 * np.pi * time / 4.0)
        # Random instrument jump/drift
        drift = 0.001 * np.exp(-((time - 7.5)/3.0)**2)
        flux += drift

    # Add instrumental red noise (low frequency) + white noise
    white_noise = np.random.normal(0, noise_level, length)
    red_noise = np.zeros(length)
    for i in range(1, length):
        red_noise[i] = 0.6 * red_noise[i-1] + np.random.normal(0, noise_level * 0.3)
        
    flux += white_noise + red_noise
    
    return LightCurveData(time, flux, np.ones_like(time)*noise_level, name=f"Synthetic {label.upper()}")
