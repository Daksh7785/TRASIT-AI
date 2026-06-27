# Production Release v2.0 - 1D Convolutional Neural Network
"""
1D Convolutional Neural Network Classifier
Operates directly on phase-folded light curve segments.
"""
import numpy as np
from loguru import logger
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from src.config import CLASS_LABELS, MODELS_DIR

# Conditional TensorFlow import
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logger.warning("TensorFlow not available. CNN classifier disabled.")

PHASE_GRID_SIZE = 201  # Must be fixed — interpolate all phase folds to this size
N_CLASSES = len(CLASS_LABELS)


def interpolate_to_grid(phase: np.ndarray, flux: np.ndarray,
                         n_points: int = PHASE_GRID_SIZE) -> np.ndarray:
    """
    Interpolate phase-folded curve to fixed grid of n_points.
    All CNNs require fixed input size.
    """
    if len(phase) < 5:
        return np.ones(n_points)
    
    grid = np.linspace(0, 1, n_points)
    # Sort by phase
    sort_idx = np.argsort(phase)
    phase_s = np.array(phase)[sort_idx]
    flux_s = np.array(flux)[sort_idx]
    
    # Interpolate
    interp_flux = np.interp(grid, phase_s, flux_s, left=flux_s[0], right=flux_s[-1])
    
    # Normalize to [0, 1]
    f_min, f_max = interp_flux.min(), interp_flux.max()
    if f_max - f_min > 0:
        interp_flux = (interp_flux - f_min) / (f_max - f_min)
    
    return interp_flux


def build_cnn_model(n_points: int = PHASE_GRID_SIZE,
                    n_classes: int = N_CLASSES) -> "keras.Model":
    """
    Build 1D CNN for transit classification.
    """
    inputs = keras.Input(shape=(n_points, 1), name="phase_fold_input")
    
    # Block 1: Local feature detection
    x = layers.Conv1D(32, kernel_size=7, padding="same", activation="relu")(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling1D(2)(x)
    x = layers.Dropout(0.1)(x)
    
    # Block 2: Broader feature detection
    x = layers.Conv1D(64, kernel_size=5, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling1D(2)(x)
    x = layers.Dropout(0.1)(x)
    
    # Block 3: High-level pattern
    x = layers.Conv1D(128, kernel_size=3, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.GlobalAveragePooling1D()(x)
    
    # Classifier head
    x = layers.Dense(64, activation="relu")(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(32, activation="relu")(x)
    outputs = layers.Dense(n_classes, activation="softmax", name="class_probs")(x)
    
    model = keras.Model(inputs, outputs, name="TransitCNN")
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    return model


class CNNClassifier:
    """1D CNN transit classifier with training and inference."""
    
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.label_to_idx = {lbl: i for i, lbl in enumerate(CLASS_LABELS)}
        self.idx_to_label = {i: lbl for i, lbl in enumerate(CLASS_LABELS)}
    
    def prepare_input(self, detection: Dict) -> np.ndarray:
        """Convert detection result to CNN input array."""
        phase = detection.get("phase", [])
        flux = detection.get("folded_flux", [])
        
        if len(phase) < 5 or len(flux) < 5:
            return np.ones(PHASE_GRID_SIZE)
        
        return interpolate_to_grid(np.array(phase), np.array(flux))
    
    def train(self, detections: List[Dict], labels: List[str],
              epochs: int = 30, batch_size: int = 32) -> Dict:
        """Train CNN on phase-folded light curve data."""
        if not TF_AVAILABLE:
            logger.warning("TensorFlow not available — CNN training skipped")
            return {"trained": False}
        
        # Prepare data
        X = np.array([self.prepare_input(d) for d in detections])
        X = X.reshape(-1, PHASE_GRID_SIZE, 1)
        y = np.array([self.label_to_idx.get(lbl, 0) for lbl in labels])
        
        self.model = build_cnn_model()
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            verbose=1
        )
        self.is_trained = True
        return {"trained": True, "final_loss": history.history["loss"][-1]}
    
    def predict(self, detection: Dict) -> Dict:
        """Predict using 1D CNN."""
        if not TF_AVAILABLE or not self.is_trained or self.model is None:
            return {"label": "UNKNOWN", "confidence": 0.0}
        
        x = self.prepare_input(detection).reshape(1, PHASE_GRID_SIZE, 1)
        proba = self.model.predict(x, verbose=0)[0]
        class_idx = np.argmax(proba)
        label = self.idx_to_label[class_idx]
        return {
            "label": label,
            "confidence": float(proba[class_idx]),
            "probabilities": {lbl: float(p) for lbl, p in zip(CLASS_LABELS, proba)}
        }
    
    def save(self, path: Path = MODELS_DIR / "cnn_model.keras"):
        """Save CNN model."""
        if TF_AVAILABLE and self.model is not None:
            self.model.save(str(path))
            logger.success(f"CNN model saved → {path}")
    
    def load(self, path: Path = MODELS_DIR / "cnn_model.keras") -> bool:
        """Load CNN model."""
        if not TF_AVAILABLE:
            return False
        try:
            self.model = keras.models.load_model(str(path))
            self.is_trained = True
            logger.success(f"CNN model loaded from {path}")
            return True
        except Exception as e:
            logger.warning(f"Could not load CNN model: {e}")
            return False
