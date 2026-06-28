import matplotlib.pyplot as plt
import numpy as np
from .detector import fold_lightcurve
from .fitter import trapezoid_model

# Set clean aesthetic style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = '#fdfdfd'
plt.rcParams['grid.color'] = '#f0f0f0'
plt.rcParams['font.size'] = 10

def plot_lightcurve_stages(time, raw_flux, trend, clean_time, clean_flux, name="Target", save_path=None):
    """
    Plots the raw light curve with the trend line, and the cleaned detrended light curve.
    """
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    
    # 1. Raw flux and trend
    axes[0].scatter(time, raw_flux, s=2, color='gray', alpha=0.5, label='Raw SAP Flux')
    axes[0].plot(time, trend, color='#e74c3c', lw=2, label='Savitzky-Golay Trend')
    axes[0].set_ylabel('Normalized SAP Flux')
    axes[0].set_title(f'Light Curve Detrending - {name}', fontweight='bold')
    axes[0].legend(loc='upper right')
    
    # 2. Cleaned flux
    axes[1].scatter(clean_time, clean_flux, s=2, color='#3498db', alpha=0.6, label='Cleaned Detrended')
    axes[1].set_ylabel('Relative Flux')
    axes[1].set_xlabel('Time (Days)')
    axes[1].legend(loc='upper right')
    
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
    else:
        return fig

def plot_bls_periodogram(periods, power, peak_period, name="Target", save_path=None):
    """
    Plots the BLS periodogram power vs search periods.
    """
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(periods, power, color='#2c3e50', lw=1.2)
    ax.axvline(peak_period, color='#e74c3c', linestyle='--', alpha=0.8, 
               label=f'Peak Period: {peak_period:.4f} days')
    
    ax.set_xlabel('Period (Days)')
    ax.set_ylabel('BLS Power')
    ax.set_title(f'Box Least Squares (BLS) Periodogram - {name}', fontweight='bold')
    ax.legend(loc='upper right')
    
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
    else:
        return fig

def plot_folded_transit(phase, flux, fit_results, best_params, name="Target", save_path=None):
    """
    Plots the folded light curve along with the best-fit trapezoidal model.
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Scatter folded data
    ax.scatter(phase, flux, s=3, color='#95a5a6', alpha=0.4, label='Folded Data')
    
    # Create bin profile for clarity
    nbins = 100
    bin_edges = np.linspace(-0.5, 0.5, nbins + 1)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    bin_indices = np.digitize(phase, bin_edges) - 1
    
    binned_flux = []
    binned_phase = []
    for i in range(nbins):
        mask = bin_indices == i
        if np.sum(mask) > 3:
            binned_flux.append(np.median(flux[mask]))
            binned_phase.append(bin_centers[i])
            
    ax.scatter(binned_phase, binned_flux, s=15, color='#2c3e50', zorder=3, label='Binned Median')
    
    # Plot fit model if successful
    if fit_results.get('success', False):
        p_model = np.linspace(-0.25, 0.25, 1000)
        f_model = trapezoid_model(
            p_model,
            fit_results['t0_offset'],
            fit_results['depth'],
            fit_results['duration'],
            fit_results['ingress_ratio']
        )
        ax.plot(p_model, f_model, color='#e74c3c', lw=2.5, zorder=4, label='Best-Fit Model')
        
    ax.set_xlim(-max(0.15, best_params['duration']*2.0), max(0.15, best_params['duration']*2.0))
    ax.set_xlabel('Phase')
    ax.set_ylabel('Relative Flux')
    
    # Add title with exoplanet parameters
    p_val = best_params['period']
    d_val = fit_results['depth'] * 1e6 # in ppm
    dur_val = fit_results['duration'] * 24.0 # in hours
    
    ax.set_title(f'Folded Light Curve & Fit - {name}\nP = {p_val:.5f} d | Depth = {d_val:.1f} ppm | Dur = {dur_val:.2f} h', 
                 fontweight='bold')
    ax.legend(loc='lower left')
    
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
    else:
        return fig
