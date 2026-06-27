import json
import os

class FeatureStore:
    """Feature store repository to cache and index extracted light curve parameters."""
    
    def __init__(self, filepath: str = "data/metadata/feature_store.json"):
        self.filepath = filepath
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.features = self._load_store()

    def _load_store(self) -> dict:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_features(self, tic_id: str, feature_dict: dict):
        """Save exoplanet features to local feature store index."""
        self.features[tic_id] = feature_dict
        with open(self.filepath, "w") as f:
            json.dump(self.features, f, indent=4)

    def get_features(self, tic_id: str) -> dict:
        return self.features.get(tic_id, {})
