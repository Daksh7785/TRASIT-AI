import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

class TransitClassifier:
    def __init__(self, model_path=None):
        self.model_path = model_path
        if model_path and os.path.exists(model_path):
            self.model = joblib.load(model_path)
        else:
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)

    def extract_features(self, time, flux, bls_params):
        """
        Extracts statistical and transit-specific features from a light curve.
        """
        # 1. Base statistics
        std_flux = np.std(flux)
        skew_flux = skew(flux)
        kurt_flux = kurtosis(flux)
        
        # Point to point scatter (high frequency noise)
        p2p_scatter = np.std(np.diff(flux))
        
        # 2. BLS params
        period = bls_params.get('period', 1.0)
        epoch = bls_params.get('epoch', 0.0)
        duration = bls_params.get('duration', 0.1)
        depth = bls_params.get('depth', 0.0)
        snr = bls_params.get('snr', 1.0)
        sde = bls_params.get('sde', 1.0)
        
        # 3. Folded light curve features
        # Compute phase
        phase = ((time - epoch) % period) / period
        phase = np.where(phase > 0.5, phase - 1.0, phase)
        
        # Sort phase and flux
        sort_idx = np.argsort(phase)
        p_sorted = phase[sort_idx]
        f_sorted = flux[sort_idx]
        
        # Out-of-transit vs. in-transit points
        in_transit = np.abs(p_sorted) < (duration / period / 2.0)
        out_transit = ~in_transit
        
        f_in = f_sorted[in_transit]
        f_out = f_sorted[out_transit]
        
        std_in = np.std(f_in) if len(f_in) > 1 else std_flux
        std_out = np.std(f_out) if len(f_out) > 1 else std_flux
        
        in_out_std_ratio = std_in / std_out if std_out > 0 else 1.0
        
        # Odd-even transit depth ratio (crucial for Eclipsing Binaries!)
        # Label each transit event
        transit_number = np.round((time - epoch) / period)
        is_odd = (transit_number % 2) != 0
        
        # Calculate depths for odd and even transits
        f_odd = flux[is_odd]
        f_even = flux[~is_odd]
        
        # Get in-transit points for odd/even
        t_odd_phase = ((time[is_odd] - epoch) % period) / period
        t_odd_phase = np.where(t_odd_phase > 0.5, t_odd_phase - 1.0, t_odd_phase)
        in_transit_odd = np.abs(t_odd_phase) < (duration / period / 2.0)
        
        t_even_phase = ((time[~is_odd] - epoch) % period) / period
        t_even_phase = np.where(t_even_phase > 0.5, t_even_phase - 1.0, t_even_phase)
        in_transit_even = np.abs(t_even_phase) < (duration / period / 2.0)
        
        odd_depth = 1.0 - np.median(f_odd[in_transit_odd]) if np.sum(in_transit_odd) > 0 else depth
        even_depth = 1.0 - np.median(f_even[in_transit_even]) if np.sum(in_transit_even) > 0 else depth
        
        # Difference in depths (relative to depth)
        odd_even_diff = np.abs(odd_depth - even_depth) / (depth + 1e-6)
        
        # Secondary eclipse search (check for secondary dip around phase 0.5)
        phase_sec = 0.5
        sec_window = np.abs(p_sorted - phase_sec) < (duration / period / 2.0)
        if np.sum(sec_window) > 0:
            sec_depth = 1.0 - np.median(f_sorted[sec_window])
        else:
            sec_depth = 0.0
            
        sec_depth_ratio = sec_depth / (depth + 1e-6)
        
        # Symmetry parameter (compare left vs right side of transit)
        left_transit = (p_sorted < 0) & in_transit
        right_transit = (p_sorted > 0) & in_transit
        left_mean = np.mean(f_sorted[left_transit]) if np.sum(left_transit) > 0 else 1.0
        right_mean = np.mean(f_sorted[right_transit]) if np.sum(right_transit) > 0 else 1.0
        asymmetry = np.abs(left_mean - right_mean) / (depth + 1e-6)
        
        # Return dict of features
        return {
            'std_flux': std_flux,
            'skew_flux': skew_flux,
            'kurt_flux': kurt_flux,
            'p2p_scatter': p2p_scatter,
            'period': period,
            'duration': duration,
            'depth': depth,
            'snr': snr,
            'sde': sde,
            'std_in': std_in,
            'std_out': std_out,
            'in_out_std_ratio': in_out_std_ratio,
            'odd_even_diff': odd_even_diff,
            'sec_depth_ratio': sec_depth_ratio,
            'asymmetry': asymmetry
        }

    def train(self, X, y):
        """
        Trains the classifier. X can be a DataFrame or a list of dicts/arrays, y is list/array of labels.
        """
        if isinstance(X, list):
            X = pd.DataFrame(X)
        self.model.fit(X, y)
        if self.model_path:
            # Ensure folder exists
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.model, self.model_path)

    def predict(self, features):
        """
        Predicts label and probability for a single set of features.
        """
        if isinstance(features, dict):
            features = pd.DataFrame([features])
            
        # Reorder columns to match training if necessary
        pred = self.model.predict(features)[0]
        probs = self.model.predict_proba(features)[0]
        classes = self.model.classes_
        
        prob_dict = {classes[i]: probs[i] for i in range(len(classes))}
        return pred, prob_dict
