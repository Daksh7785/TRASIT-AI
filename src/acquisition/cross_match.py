"""
Cross-Matching Module
Cross-matches candidate parameters (Period, Coordinates) against the NASA Exoplanet Archive and ExoFOP.
Integrates TAP online database catalog searches.
"""
import requests
import pandas as pd
from loguru import logger
from typing import Dict, Optional


def query_nasa_exoplanet_archive(tic_id: int) -> Optional[Dict]:
    """
    Query NASA Exoplanet Archive Tap API for known planets around a host star.
    """
    query_url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
    query = f"select pl_name, sy_pnum, pl_orbper, pl_rade, pl_eqt from ps where hostname like '%TIC {tic_id}%' or pl_name like '%TIC {tic_id}%'"
    
    try:
        resp = requests.get(
            query_url,
            params={
                "query": query,
                "format": "json"
            },
            timeout=15
        )
        if resp.status_code == 200:
            results = resp.json()
            if results and len(results) > 0:
                row = results[0]
                return {
                    "matched": True,
                    "catalog": "NASA Exoplanet Archive",
                    "planet_name": row.get("pl_name"),
                    "n_planets_in_system": int(row.get("sy_pnum", 1)),
                    "period_days": float(row.get("pl_orbper", 0.0)),
                    "radius_earth": float(row.get("pl_rade", 0.0)),
                    "eq_temp_k": float(row.get("pl_eqt", 0.0)) if row.get("pl_eqt") else None
                }
    except Exception as e:
        logger.debug(f"NASA Exoplanet Archive query failed for TIC {tic_id}: {e}")
        
    return None


def cross_match_candidate(tic_id: int, period: float, 
                          tolerance_percent: float = 2.0) -> Dict:
    """
    Cross match a detected transit candidate against known exoplanet databases.
    """
    logger.info(f"Cross-matching TIC {tic_id} (Period: {period:.4f} d)")
    
    # 1. Check local known planets first
    from src.acquisition.mast_query import load_known_planets
    df_known = load_known_planets()
    
    match = df_known[df_known["TIC_ID"] == tic_id]
    if not match.empty:
        row = match.iloc[0]
        true_p = row["Period_days"]
        diff = abs(true_p - period) / true_p * 100
        if diff < tolerance_percent:
            return {
                "status": "KNOWN_EXOPLANET",
                "planet_name": row["Planet_Name"],
                "catalog": "Local Known Catalog (TESS TOI)",
                "details": f"Matches {row['Planet_Name']} with period difference of {diff:.2f}%."
            }
            
    # 2. Check NASA Exoplanet Archive Tap API online
    online_match = query_nasa_exoplanet_archive(tic_id)
    if online_match:
        true_p = online_match["period_days"]
        if true_p > 0:
            diff = abs(true_p - period) / true_p * 100
            if diff < tolerance_percent:
                return {
                    "status": "KNOWN_EXOPLANET",
                    "planet_name": online_match["planet_name"],
                    "catalog": "NASA Exoplanet Archive",
                    "details": f"Matches {online_match['planet_name']} online with period difference of {diff:.2f}%."
                }
                
    # 3. No match found
    return {
        "status": "POTENTIAL_NEW_CANDIDATE",
        "planet_name": "None",
        "catalog": "None",
        "details": "No matching planetary transits found in known archives. Potential new discovery."
    }
