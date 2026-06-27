import os
import numpy as np
import logging

logger = logging.getLogger(__name__)

class AutomatedDatasetBuilder:
    """Ingestion pipeline to download metadata, perform splits, and organize datasets."""
    
    def __init__(self, data_root: str = "data"):
        self.data_root = data_root
        self.dirs = ["raw", "processed", "metadata", "labels"]
        self._initialize_directories()

    def _initialize_directories(self):
        """Create target local cache storage directories."""
        for d in self.dirs:
            os.makedirs(os.path.join(self.data_root, d), exist_ok=True)

    def generate_data_split(self, ids: list, labels: list, val_ratio: float = 0.2, test_ratio: float = 0.1):
        """Generates train/validation/test index splits for MLOps tracking."""
        n = len(ids)
        indices = np.arange(n)
        np.random.shuffle(indices)
        
        n_test = int(n * test_ratio)
        n_val = int(n * val_ratio)
        
        test_idx = indices[:n_test]
        val_idx = indices[n_test:n_test + n_val]
        train_idx = indices[n_test + n_val:]
        
        return {
            "train": [ids[i] for i in train_idx],
            "val": [ids[i] for i in val_idx],
            "test": [ids[i] for i in test_idx]
        }
