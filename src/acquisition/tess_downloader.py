"""
TESS Light Curve Downloader
Downloads high-cadence TESS data from MAST via lightkurve.
Falls back to synthetic data if download fails.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from loguru import logger
from typing import List, Dict, Optional
import lightkurve as lk
from src.config import (
    RAW_DIR, TESS_SECTOR, TESS_CADENCE, MAX_LIGHTCURVES,
    USE_SYNTHETIC_FALLBACK
)
from src.acquisition.synthetic_generator import generate_demo_science_batch


def download_sector_targets(sector: int = TESS_SECTOR, 
                             max_lcs: int = MAX_LIGHTCURVES) -> List[Dict]:
    """
    Download light curves for a full TESS sector.
    Returns list of dicts with tic_id, time, flux arrays.
    """
    logger.info(f"Attempting to download TESS Sector {sector} ({max_lcs} LCs)")
    
    # Search for targets in this sector (short cadence = 2-min)
    try:
        search_result = lk.search_lightcurve(
            target="TIC *",
            sector=sector,
            exptime=120,             # 2-minute cadence
            mission="TESS",
            limit=max_lcs
        )
        
        if len(search_result) == 0:
            raise ValueError("No results returned from MAST search")
        
        logger.info(f"Found {len(search_result)} targets. Downloading...")
        
        lightcurves = []
        for i, row in enumerate(search_result):
            try:
                lc_collection = row.download()
                if lc_collection is None:
                    continue
                lc = lc_collection.normalize().remove_nans().remove_outliers(sigma=5)
                lightcurves.append({
                    "tic_id": f"TIC_{row.target_name}",
                    "time": lc.time.value,
                    "flux": lc.flux.value,
                    "flux_err": lc.flux_err.value if hasattr(lc, 'flux_err') else None,
                    "sector": sector,
                    "source": "TESS_MAST"
                })
                if (i + 1) % 50 == 0:
                    logger.info(f"Downloaded {i+1}/{min(max_lcs, len(search_result))} LCs")
                    
            except Exception as e:
                logger.warning(f"Failed to download {row.target_name}: {e}")
                continue
        
        logger.success(f"Successfully downloaded {len(lightcurves)} light curves")
        return lightcurves
    
    except Exception as e:
        logger.error(f"TESS download failed: {e}")
        if USE_SYNTHETIC_FALLBACK:
            logger.warning("⚡ Falling back to SYNTHETIC data (demo mode)")
            return _convert_synthetic_to_standard(generate_demo_science_batch(max_lcs))
        raise


def download_by_tic_ids(tic_ids: List[int], sector: int = None) -> List[Dict]:
    """Download specific TIC IDs (for curated validation set)."""
    lightcurves = []
    for tic_id in tic_ids:
        try:
            search = lk.search_lightcurve(f"TIC {tic_id}", mission="TESS", 
                                           exptime=120, sector=sector)
            if len(search) == 0:
                continue
            lc = search[0].download().normalize().remove_nans()
            lightcurves.append({
                "tic_id": f"TIC_{tic_id}",
                "time": lc.time.value,
                "flux": lc.flux.value,
                "flux_err": lc.flux_err.value if hasattr(lc, 'flux_err') else None,
                "sector": sector,
                "source": "TESS_MAST"
            })
        except Exception as e:
            logger.warning(f"TIC {tic_id} download failed: {e}")
    return lightcurves


def _convert_synthetic_to_standard(batch: List[Dict]) -> List[Dict]:
    """Convert synthetic generator output to standard pipeline format."""
    return [{
        "tic_id": item["tic_id"],
        "time": item["time"],
        "flux": item["flux"],
        "flux_err": np.ones(len(item["flux"])) * 0.001,
        "sector": 0,
        "source": "SYNTHETIC",
        "true_label": item.get("true_label"),
        "true_params": item.get("true_params")
    } for item in batch]
