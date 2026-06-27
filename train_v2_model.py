import numpy as np
import pandas as pd
from pathlib import Path
from loguru import logger
from src.acquisition.synthetic_generator import GENERATORS
from src.preprocessing.detrending import preprocess_lightcurve
from src.detection.tls_detector import run_tls
from src.classification.feature_extractor import extract_features, features_to_vector
from src.classification.ml_classifier import TransitClassifier
from src.config import CLASS_LABELS, MODELS_DIR

def train_model():
    X_list = []
    y_list = []
    
    n_per_class = 60  # Large enough to generalize, small enough to train quickly (300 samples total)
    logger.info(f"Generating and extracting features for {n_per_class} samples per class...")
    
    for label in CLASS_LABELS:
        generator = GENERATORS[label]
        logger.info(f"Processing class: {label}")
        for i in range(n_per_class):
            t, flux, params = generator()
            # Preprocess
            tc, fc, trend, fe = preprocess_lightcurve(t, flux)
            # Detection
            det = run_tls(tc, fc, fe)
            # Extract features
            feats = extract_features(tc, fc, det)
            vec = features_to_vector(feats)
            
            X_list.append(vec)
            y_list.append(label)
            
    X = np.array(X_list)
    clf = TransitClassifier()
    y = clf.le.transform(y_list)
    
    # Train
    metrics = clf.train(X, y, use_smote=True)
    logger.info(f"Training metrics: {metrics}")
    
    # Save
    clf.save(MODELS_DIR / "transit_classifier.pkl")
    logger.success("Model successfully trained and saved!")

if __name__ == "__main__":
    train_model()
