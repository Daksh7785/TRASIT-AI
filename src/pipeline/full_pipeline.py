"""
TRANSIT-AI Full Pipeline Orchestrator
End-to-end: download → preprocess → detect → classify → fit → report
"""
import numpy as np
import pandas as pd
from pathlib import Path
from loguru import logger
from typing import List, Dict, Optional
from joblib import Parallel, delayed
from tqdm import tqdm

from src.config import (
    RESULTS_DIR, MODELS_DIR, N_JOBS, BATCH_SIZE,
    SNR_THRESHOLD, CONFIDENCE_THRESHOLD
)
from src.acquisition.tess_downloader import download_sector_targets
from src.acquisition.synthetic_generator import (
    generate_demo_science_batch, generate_training_dataset
)
from src.preprocessing.detrending import preprocess_lightcurve
from src.detection.ensemble_detector import run_ensemble_detector
from src.classification.feature_extractor import extract_features
from src.classification.ml_classifier import TransitClassifier
from src.fitting.batman_fitter import fit_transit
from src.reporting.pdf_report_generator import generate_pdf_report


class TransitAIPipeline:
    """Main TRANSIT-AI pipeline orchestrator."""
    
    def __init__(self):
        self.classifier = TransitClassifier()
        self.results = []
        self._load_or_train_model()
    
    def _load_or_train_model(self):
        """Load pre-trained model or train from scratch."""
        model_path = MODELS_DIR / "transit_classifier.pkl"
        loaded = self.classifier.load(model_path)
        
        if not loaded:
            logger.info("No pre-trained model found. Training from synthetic data...")
            self._train_model()
    
    def _train_model(self, n_per_class: int = 200):  # Reduced to 200 to keep it fast while robust
        """Generate synthetic data and train classifier."""
        df = generate_training_dataset(n_per_class)
        
        X_list, y_list = [], []
        for _, row in df.iterrows():
            # Create minimal detection dict from training params
            det = {
                "snr": row["snr"], "sde": row["snr"] * 0.9,
                "period": row["period"], "depth": row["depth"],
                "duration": row["duration"], "n_transits": 3,
                "odd_even_mismatch": 0.05 if row["label"] != "ECLIPSE" else 0.4,
                "phase": [], "folded_flux": [],
                "power_spectrum": {"periods": [], "power": []}
            }
            features = extract_features(np.array([0, 1, 2]), np.array([1, 1, 1]), det)
            
            from src.classification.feature_extractor import features_to_vector
            X_list.append(features_to_vector(features))
            y_list.append(row["label"])
        
        X = np.array(X_list)
        y = self.classifier.le.transform(y_list)
        
        metrics = self.classifier.train(X, y)
        logger.info(f"Training complete: {metrics}")
        self.classifier.save()
    
    def process_single(self, lc_data: Dict) -> Dict:
        """Process a single light curve through the full pipeline."""
        tic_id = lc_data["tic_id"]
        time = np.array(lc_data["time"])
        flux = np.array(lc_data["flux"])
        flux_err = np.array(lc_data.get("flux_err")) if lc_data.get("flux_err") is not None else np.ones(len(flux)) * 0.001
        
        result = {"tic_id": tic_id, "source": lc_data.get("source", "unknown")}
        
        try:
            # Step 1: Preprocess
            time_c, flux_c, trend, flux_err_c = preprocess_lightcurve(time, flux, flux_err)
            
            if len(time_c) < 50:
                result.update({"status": "SKIPPED", "reason": "Too few points after preprocessing"})
                return result
            
            # Step 2: Detect
            detection = run_ensemble_detector(time_c, flux_c, flux_err_c)
            result["detection"] = detection
            
            # Step 3: Feature extraction
            features = extract_features(time_c, flux_c, detection)
            
            # Step 4: Classify
            classification = self.classifier.predict(features)
            result["classification"] = classification
            
            # Step 5: Fit (only for confident transit/eclipse detections)
            if (detection["detected"] and 
                classification["label"] in ("TRANSIT", "ECLIPSE") and
                classification["confidence"] >= CONFIDENCE_THRESHOLD):
                fitting = fit_transit(time_c, flux_c, detection, run_mcmc=False)
            else:
                fitting = {"fitted": False}
            result["fitting"] = fitting
            
            # Step 6: Compile final result
            result["status"] = "PROCESSED"
            result["is_candidate"] = (
                detection["detected"] and
                classification["label"] == "TRANSIT" and
                classification["confidence"] >= CONFIDENCE_THRESHOLD
            )
            result["time"] = time_c.tolist()
            result["flux"] = flux_c.tolist()
            result["trend"] = trend.tolist()
            result["true_label"] = lc_data.get("true_label")
            
        except Exception as e:
            logger.error(f"Pipeline failed for {tic_id}: {e}")
            result["status"] = "ERROR"
            result["error"] = str(e)
        
        return result
    
    def run(self, mode: str = "synthetic", 
            n_lcs: int = 100,
            sector: int = 1) -> List[Dict]:
        """
        Run the full pipeline.
        mode: 'synthetic' | 'tess' | 'demo'
        """
        logger.info(f"🚀 TRANSIT-AI Pipeline starting | mode={mode} | n={n_lcs}")
        
        # Acquire data
        if mode == "tess":
            lc_batch = download_sector_targets(sector=sector, max_lcs=n_lcs)
        else:
            lc_batch = self._convert_synthetic(generate_demo_science_batch(n_lcs))
        
        logger.info(f"Processing {len(lc_batch)} light curves...")
        
        # Process sequentially to avoid multi-threading deadlocks
        results = [self.process_single(lc) for lc in tqdm(lc_batch, desc="Processing LCs")]
        
        self.results = [r for r in results if r is not None]
        
        # Save results
        self._save_results()
        
        # Generate report
        generate_pdf_report(self.results)
        
        logger.success(f"✅ Pipeline complete! Processed {len(self.results)} LCs")
        candidates = [r for r in self.results if r.get("is_candidate")]
        logger.info(f"🪐 Transit candidates found: {len(candidates)}")
        
        return self.results
    
    def _convert_synthetic(self, batch: List[Dict]) -> List[Dict]:
        return [{
            "tic_id": item["tic_id"],
            "time": item["time"],
            "flux": item["flux"],
            "flux_err": np.ones(len(item["flux"])) * 0.001,
            "source": "SYNTHETIC",
            "true_label": item.get("true_label"),
            "true_params": item.get("true_params")
        } for item in batch]
    
    def _save_results(self):
        """Save all results to CSV files."""
        records = []
        for r in self.results:
            if r.get("status") != "PROCESSED":
                continue
            det = r.get("detection", {})
            clf = r.get("classification", {})
            fit = r.get("fitting", {})
            
            records.append({
                "tic_id": r["tic_id"],
                "source": r.get("source"),
                "true_label": r.get("true_label"),
                "detected": det.get("detected", False),
                "period": det.get("period", 0),
                "depth": det.get("depth", 0),
                "duration": det.get("duration", 0),
                "snr": det.get("snr", 0),
                "sde": det.get("sde", 0),
                "n_transits": det.get("n_transits", 0),
                "pred_label": clf.get("label"),
                "confidence": clf.get("confidence", 0),
                "is_candidate": r.get("is_candidate", False),
                "fitted_depth": fit.get("depth"),
                "fitted_period": fit.get("period"),
                "fitted_duration": fit.get("duration"),
                "chi2_reduced": fit.get("chi2_reduced"),
            })
        
        df = pd.DataFrame(records)
        out = RESULTS_DIR / "pipeline_results.csv"
        df.to_csv(out, index=False)
        logger.info(f"Results saved → {out}")
