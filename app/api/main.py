import os
import sys
import numpy as np
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from pathlib import Path
from loguru import logger

# Add project root to python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pipeline.full_pipeline import TransitAIPipeline
from src.acquisition.mast_query import query_tic_by_id
from src.preprocessing.detrending import preprocess_lightcurve
from src.detection.habitability import classify_habitability
from app.api.worker import enqueue_batch_job, get_job_status

app = FastAPI(title="TRANSIT-AI API", description="Exoplanet Detection & Vetting API Platform", version="2.0.0")

@app.post("/batch-jobs")
def create_batch_job(n_lcs: int = 100):
    job_id = enqueue_batch_job(n_lcs)
    return {"job_id": job_id, "status": "QUEUED"}

@app.get("/batch-jobs/{job_id}")
def check_batch_job(job_id: str):
    return get_job_status(job_id)

# Lazy initialize pipeline
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = TransitAIPipeline()
    return _pipeline

class LightCurveInput(BaseModel):
    tic_id: str
    time: List[float]
    flux: List[float]
    flux_err: Optional[List[float]] = None

class PredictionResponse(BaseModel):
    tic_id: str
    detected: bool
    label: str
    confidence: float
    parameters: Dict
    habitability: Optional[Dict] = None

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "2.0.0"}

@app.post("/predict", response_model=PredictionResponse)
def predict_light_curve(data: LightCurveInput):
    pipeline = get_pipeline()
    
    # Process
    try:
        flux_err = np.array(data.flux_err) if data.flux_err else np.ones(len(data.flux)) * np.std(data.flux) * 0.1
        res = pipeline.process_single({
            "tic_id": data.tic_id,
            "time": np.array(data.time),
            "flux": np.array(data.flux),
            "flux_err": flux_err
        })
        
        # Calculate habitability if transit detected
        habitability_info = None
        det = res.get("detection", {})
        if det.get("detected") and "period" in det:
            habitability_info = classify_habitability(
                period=det["period"],
                depth=det["depth"],
                R_star=1.0,  # solar default
                M_star=1.0
            )
        
        return PredictionResponse(
            tic_id=data.tic_id,
            detected=bool(det.get("detected", False)),
            label=res.get("classification", {}).get("label", "UNKNOWN"),
            confidence=float(res.get("classification", {}).get("confidence", 0.0)),
            parameters={
                "period": det.get("period", 0.0),
                "duration": det.get("duration", 0.0),
                "depth": det.get("depth", 0.0),
                "t0": det.get("t0", 0.0),
                "snr": det.get("snr", 0.0),
                "sde": det.get("sde", 0.0),
            },
            habitability=habitability_info
        )
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_lightcurve_file(file: UploadFile = File(...)):
    """Upload Light Curve file (CSV or FITS) and return candidates."""
    try:
        content = await file.read()
        # Parse CSV
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file.file)
            if "time" not in df.columns or "flux" not in df.columns:
                raise HTTPException(status_code=400, detail="CSV must contain 'time' and 'flux' columns")
            
            time_arr = df["time"].values
            flux_arr = df["flux"].values
            err_arr = df["flux_err"].values if "flux_err" in df.columns else None
            
            # Query pipeline
            pipeline = get_pipeline()
            res = pipeline.process_single({
                "tic_id": file.filename.split(".")[0],
                "time": time_arr,
                "flux": flux_arr,
                "flux_err": err_arr
            })
            return res
        else:
            raise HTTPException(status_code=400, detail="Only .csv files supported in this demo")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results")
def get_results():
    """Retrieve historical pipeline results."""
    from src.config import DATA_DIR
    results_path = DATA_DIR / "results" / "pipeline_results.csv"
    if not results_path.exists():
        return {"results": []}
    
    df = pd.read_csv(results_path)
    return {"results": df.to_dict(orient="records")}

@app.get("/sky-map")
def get_sky_map_data():
    """Retrieve celestial candidate data for Sky Map visualizations."""
    from src.config import DATA_DIR
    results_path = DATA_DIR / "results" / "pipeline_results.csv"
    if not results_path.exists():
        return {"candidates": []}
    
    df = pd.read_csv(results_path)
    candidates = []
    
    for _, row in df.iterrows():
        # Query MAST/TIC parameters for RA/Dec
        tic_id = row.get("tic_id", "")
        # Parse numeric parts if synth or real
        try:
            tic_num = int("".join(filter(str.isdigit, str(tic_id))))
            star_info = query_tic_by_id(tic_num)
            ra = star_info.get("ra", np.random.uniform(0, 360))
            dec = star_info.get("dec", np.random.uniform(-90, 90))
        except:
            ra = np.random.uniform(0, 360)
            dec = np.random.uniform(-90, 90)
            
        candidates.append({
            "tic_id": tic_id,
            "ra": ra,
            "dec": dec,
            "label": row.get("label", "UNKNOWN"),
            "confidence": row.get("confidence", 0.0),
            "period": row.get("period", 0.0),
            "depth": row.get("depth", 0.0),
        })
        
    return {"candidates": candidates}
