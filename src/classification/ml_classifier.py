"""
ML Ensemble Classifier for Transit Signal Classification
XGBoost + Random Forest voting ensemble with calibrated probabilities.
"""
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from loguru import logger
from typing import Dict, List, Tuple, Optional

from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import xgboost as xgb
from imblearn.over_sampling import SMOTE

from src.config import CLASS_LABELS, MODELS_DIR, CONFIDENCE_THRESHOLD
from src.classification.feature_extractor import features_to_vector


class TransitClassifier:
    """
    Ensemble classifier: XGBoost + Random Forest with calibrated probabilities.
    """
    
    def __init__(self):
        self.le = LabelEncoder()
        self.le.fit(CLASS_LABELS)
        self.model = None
        self.is_trained = False
    
    def build_model(self) -> VotingClassifier:
        """Construct the ensemble model."""
        xgb_clf = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="mlogloss",
            random_state=42,
            n_jobs=-1
        )
        rf_clf = RandomForestClassifier(
            n_estimators=200,
            max_depth=None,
            min_samples_split=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        )
        ensemble = VotingClassifier(
            estimators=[("xgb", xgb_clf), ("rf", rf_clf)],
            voting="soft",
            weights=[0.6, 0.4]
        )
        return ensemble
    
    def train(self, X: np.ndarray, y: np.ndarray,
              use_smote: bool = True) -> Dict:
        """Train the classifier with optional SMOTE oversampling."""
        logger.info(f"Training on {len(X)} samples with {X.shape[1]} features")
        
        # Clean any NaNs in features
        X = np.nan_to_num(X)
        
        # Handle class imbalance
        if use_smote:
            try:
                sm = SMOTE(random_state=42, k_neighbors=min(5, min(np.bincount(y)) - 1))
                X, y = sm.fit_resample(X, y)
                logger.info(f"After SMOTE: {len(X)} samples")
            except Exception as e:
                logger.warning(f"SMOTE failed: {e}. Using original data.")
        
        # Cross-validation
        model = self.build_model()
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(model, X, y, cv=cv, scoring="f1_weighted", n_jobs=-1)
        logger.info(f"CV F1 (weighted): {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        
        # Final training
        model.fit(X, y)
        self.model = model
        self.is_trained = True
        
        return {
            "cv_f1_mean": float(cv_scores.mean()),
            "cv_f1_std": float(cv_scores.std()),
            "n_train_samples": len(X),
            "n_features": X.shape[1]
        }
    
    def predict(self, features_dict: Dict) -> Dict:
        """
        Predict class and confidence for a single light curve.
        Returns: {label, confidence, probabilities, is_confident}
        """
        if not self.is_trained:
            return self._fallback_rule_based(features_dict)
        
        X = features_to_vector(features_dict).reshape(1, -1)
        proba = self.model.predict_proba(X)[0]
        class_idx = np.argmax(proba)
        label = self.le.inverse_transform([class_idx])[0]
        confidence = float(proba[class_idx])
        
        return {
            "label": label,
            "confidence": confidence,
            "is_confident": confidence >= CONFIDENCE_THRESHOLD,
            "probabilities": {
                cls: float(p) for cls, p in zip(self.le.classes_, proba)
            }
        }
    
    def predict_batch(self, features_list: List[Dict]) -> List[Dict]:
        """Batch prediction for multiple light curves."""
        return [self.predict(f) for f in features_list]
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """Evaluate on test set."""
        if not self.is_trained:
            return {}
        y_pred = self.model.predict(X)
        report = classification_report(
            y, y_pred,
            target_names=self.le.classes_,
            output_dict=True
        )
        cm = confusion_matrix(y, y_pred)
        return {
            "classification_report": report,
            "confusion_matrix": cm.tolist(),
            "accuracy": float(np.mean(y == y_pred))
        }
    
    def save(self, path: Path = MODELS_DIR / "transit_classifier.pkl"):
        """Save trained model."""
        joblib.dump({"model": self.model, "le": self.le, "is_trained": self.is_trained}, path)
        logger.success(f"Model saved → {path}")
    
    def load(self, path: Path = MODELS_DIR / "transit_classifier.pkl") -> bool:
        """Load pre-trained model. Returns True if successful."""
        try:
            data = joblib.load(path)
            self.model = data["model"]
            self.le = data["le"]
            self.is_trained = data["is_trained"]
            logger.success(f"Model loaded from {path}")
            return True
        except Exception as e:
            logger.warning(f"Could not load model: {e}")
            return False
    
    def _fallback_rule_based(self, features: Dict) -> Dict:
        """Rule-based fallback when model is not trained."""
        snr = features.get("snr", 0)
        depth = features.get("depth", 0)
        odd_even = features.get("odd_even_mismatch", 0)
        secondary = features.get("secondary_depth_ratio", 0)
        v_score = features.get("shape_v_score", 0)
        
        if snr < 3:
            label, conf = "ARTIFACT", 0.7
        elif odd_even > 0.3 or secondary > 0.3:
            label, conf = "ECLIPSE", 0.75
        elif depth > 0.02 and v_score > 0.5:
            label, conf = "ECLIPSE", 0.65
        elif depth < 0.0002:
            label, conf = "BLEND", 0.6
        elif snr >= 7 and 0.0001 < depth < 0.02:
            label, conf = "TRANSIT", 0.65
        else:
            label, conf = "STELLAR_VAR", 0.5
        
        return {
            "label": label,
            "confidence": conf,
            "is_confident": conf >= CONFIDENCE_THRESHOLD,
            "probabilities": {cls: (conf if cls == label else (1-conf)/4) for cls in CLASS_LABELS}
        }
