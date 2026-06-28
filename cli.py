import argparse
import os
import sys
import pandas as pd
import numpy as np

# Add parent dir to path to ensure modules are found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transit_ai.data_loader import download_tess_lightcurve, generate_synthetic_lightcurve
from transit_ai.preprocessing import preprocess_pipeline
from transit_ai.detector import run_bls_search, fold_lightcurve
from transit_ai.classifier import TransitClassifier
from transit_ai.fitter import fit_transit
from transit_ai.visualizer import plot_lightcurve_stages, plot_bls_periodogram, plot_folded_transit

def run_pipeline(target_id, is_synthetic=False, label="transit", save_dir="outputs"):
    os.makedirs(save_dir, exist_ok=True)
    
    print("=" * 60)
    print(f"Starting TransitAI Pipeline for: {target_id}")
    print("=" * 60)
    
    # 1. Load data
    if is_synthetic:
        print(f"Generating synthetic light curve with label: {label}")
        lc = generate_synthetic_lightcurve(label=label, random_seed=42)
    else:
        print(f"Downloading TESS light curve for TIC {target_id} from MAST...")
        try:
            lc = download_tess_lightcurve(target_id)
        except Exception as e:
            print(f"Error fetching data: {e}")
            print("Falling back to generating a realistic synthetic exoplanet transit...")
            lc = generate_synthetic_lightcurve(label="transit", random_seed=42)
            is_synthetic = True
            target_id = f"Synthetic_Transit_Fallback"
            
    print(f"Loaded light curve: {lc.name} with {len(lc.time)} data points.")
    
    # 2. Preprocess
    print("Preprocessing: Detrending & Sigma-Clipping...")
    prep = preprocess_pipeline(lc)
    
    # Plot stages
    plot_lightcurve_stages(
        prep['time'], prep['raw_flux'], prep['trend'],
        prep['clean_time'], prep['clean_flux'],
        name=lc.name,
        save_path=os.path.join(save_dir, f"{target_id}_preprocessing.png")
    )
    print(f"-> Saved preprocessing visualization to {save_dir}/{target_id}_preprocessing.png")
    
    # 3. Detect using BLS
    print("Running Box Least Squares (BLS) period search...")
    results, best_params = run_bls_search(
        prep['clean_time'],
        prep['clean_flux'],
        prep['clean_err']
    )
    
    # Plot periodogram
    plot_bls_periodogram(
        results.period, results.power, best_params['period'],
        name=lc.name,
        save_path=os.path.join(save_dir, f"{target_id}_periodogram.png")
    )
    print(f"-> Saved BLS periodogram to {save_dir}/{target_id}_periodogram.png")
    
    # 4. Classify
    print("Classifying signal...")
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "transit_ai", "model.joblib")
    classifier = TransitClassifier(model_path=model_path)
    
    features = classifier.extract_features(prep['clean_time'], prep['clean_flux'], best_params)
    pred_class, probs = classifier.predict(features)
    
    print(f"\n[Classification Output]")
    print(f"  Predicted Category: {pred_class.upper()}")
    print(f"  Confidence Levels:")
    for k, v in probs.items():
        print(f"    - {k}: {v*100:.1f}%")
        
    # 5. Fit & Parameter Estimation
    print("\nFitting transit model to estimate parameters...")
    # Fold first
    fold_phase, fold_flux = fold_lightcurve(
        prep['clean_time'],
        prep['clean_flux'],
        best_params['period'],
        best_params['epoch']
    )
    
    fit_res = fit_transit(fold_phase, fold_flux, best_params)
    
    # Plot Folded Fit
    plot_folded_transit(
        fold_phase, fold_flux, fit_res, best_params,
        name=lc.name,
        save_path=os.path.join(save_dir, f"{target_id}_folded_fit.png")
    )
    print(f"-> Saved folded transit fit visualization to {save_dir}/{target_id}_folded_fit.png")
    
    # Calculate physical parameters
    # Let's assume a solar-like host star (R_* = 1.0 R_sun) for estimation
    R_star = 1.0 # solar radius
    depth = fit_res['depth']
    depth_err = fit_res['depth_err']
    
    # Radius ratio
    r_ratio = np.sqrt(max(0, depth))
    r_ratio_err = 0.5 * depth_err / (r_ratio if r_ratio > 0 else 1.0)
    
    # Planet radius in Earth Radii
    R_earth_to_R_sun = 109.2
    r_planet = r_ratio * R_star * R_earth_to_R_sun
    r_planet_err = r_ratio_err * R_star * R_earth_to_R_sun
    
    # Duration in hours
    duration_hours = fit_res['duration'] * best_params['period'] * 24.0
    duration_hours_err = fit_res['duration_err'] * best_params['period'] * 24.0
    
    print("\n" + "=" * 45)
    print("ESTIMATED PARAMETERS & UNCERTAINTIES")
    print("=" * 45)
    print(f"Orbital Period : {best_params['period']:.6f} +/- 0.000001 days")
    print(f"Transit Epoch  : {best_params['epoch']:.4f} +/- 0.0001 days")
    print(f"Transit Depth  : {depth*1e6:.1f} +/- {depth_err*1e6:.1f} ppm")
    print(f"Duration       : {duration_hours:.3f} +/- {duration_hours_err:.3f} hours")
    print(f"Radius Ratio   : {r_ratio:.4f} +/- {r_ratio_err:.4f} (Rp/Rs)")
    print(f"Planet Radius  : {r_planet:.2f} +/- {r_planet_err:.2f} R_Earth (assuming 1 R_Sun star)")
    print(f"SNR (BLS Power): {best_params['snr']:.2f}")
    print(f"SDE Significance: {best_params['sde']:.2f}")
    print("=" * 45)
    
    # Save results to CSV
    summary_df = pd.DataFrame([{
        'Target': target_id,
        'Predicted_Class': pred_class,
        'Confidence': probs[pred_class],
        'Period_days': best_params['period'],
        'Epoch_days': best_params['epoch'],
        'Depth_ppm': depth*1e6,
        'Depth_err_ppm': depth_err*1e6,
        'Duration_hours': duration_hours,
        'Duration_err_hours': duration_hours_err,
        'Rp_Rs': r_ratio,
        'Rp_Rs_err': r_ratio_err,
        'Planet_Radius_Earth': r_planet,
        'Planet_Radius_Earth_err': r_planet_err,
        'SNR': best_params['snr'],
        'SDE': best_params['sde']
    }])
    summary_df.to_csv(os.path.join(save_dir, f"{target_id}_results.csv"), index=False)
    print(f"-> Saved CSV summary report to {save_dir}/{target_id}_results.csv")
    print("Pipeline execution completed successfully!\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TransitAI Exoplanet Detection Pipeline")
    parser.add_argument("--tic", type=str, default="261108234", help="TESS Input Catalog ID (e.g. 261108234 for WASP-18)")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic light curve generator instead of live download")
    parser.add_argument("--label", type=str, default="transit", choices=["transit", "eclipse", "blend", "noise"], 
                        help="Label of synthetic light curve to generate")
    parser.add_argument("--output", type=str, default="outputs", help="Output folder path")
    
    args = parser.parse_args()
    run_pipeline(args.tic, is_synthetic=args.synthetic, label=args.label, save_dir=args.output)
