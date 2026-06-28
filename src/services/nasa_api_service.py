"""
NASA Public APIs Service
- NASA Image & Video Library (no API key required)
- Astronomy Picture of the Day (APOD) — uses DEMO_KEY by default
- All responses disk-cached with 24h TTL
"""
import os
import requests
from typing import List, Dict, Optional
from loguru import logger
from src.services.cache_service import cache_get, cache_set

NASA_IMAGE_API = "https://images-api.nasa.gov"
APOD_API = "https://api.nasa.gov/planetary/apod"
NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")

# 24-hour TTL for images (they don't change often)
IMAGE_TTL = 86400
# 6-hour TTL for APOD
APOD_TTL = 21600


def _safe_get(url: str, params: dict = None, timeout: int = 15) -> Optional[dict]:
    try:
        r = requests.get(url, params=params, timeout=timeout,
                         headers={"User-Agent": "AstroLensAI/2.0"})
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning(f"NASA API request failed ({url}): {e}")
        return None


def search_nasa_images(query: str, media_type: str = "image", page_size: int = 12) -> List[Dict]:
    """
    Search NASA Image & Video Library.
    Returns list of {title, description, url, thumbnail, date, credit, nasa_id}
    """
    cache_key = f"nasa_images:{query}:{media_type}:{page_size}"
    cached = cache_get(cache_key, ttl_seconds=IMAGE_TTL)
    if cached is not None:
        logger.debug(f"NASA images cache hit: {query}")
        return cached

    data = _safe_get(
        f"{NASA_IMAGE_API}/search",
        params={"q": query, "media_type": media_type, "page_size": page_size}
    )

    results = []
    if data and "collection" in data:
        for item in data["collection"].get("items", []):
            try:
                meta = item.get("data", [{}])[0]
                links = item.get("links", [{}])
                thumb = next((l["href"] for l in links if l.get("rel") == "preview"), "")
                results.append({
                    "nasa_id": meta.get("nasa_id", ""),
                    "title": meta.get("title", "Untitled"),
                    "description": meta.get("description", "")[:300],
                    "date": meta.get("date_created", "")[:10],
                    "center": meta.get("center", "NASA"),
                    "credit": meta.get("photographer", meta.get("secondary_creator", "NASA")),
                    "thumbnail": thumb,
                    "url": thumb,  # preview URL is usable as img src
                })
            except Exception:
                continue

    cache_set(cache_key, results)
    logger.info(f"NASA images fetched: {len(results)} results for '{query}'")
    return results


def get_gallery_collections() -> Dict[str, List[Dict]]:
    """
    Fetch curated collections for the image gallery.
    Returns categorised image sets.
    """
    cache_key = "nasa_gallery_collections_v2"
    cached = cache_get(cache_key, ttl_seconds=IMAGE_TTL)
    if cached is not None:
        return cached

    categories = {
        "TESS Mission": search_nasa_images("TESS spacecraft exoplanet", page_size=8),
        "Exoplanets": search_nasa_images("exoplanet artist concept", page_size=8),
        "Stars & Nebulae": search_nasa_images("nebula stars hubble", page_size=8),
        "Galaxies": search_nasa_images("galaxy spiral Milky Way", page_size=8),
        "Mission Control": search_nasa_images("NASA mission control telescope", page_size=6),
    }

    cache_set(cache_key, categories)
    return categories


def get_apod(count: int = 5) -> List[Dict]:
    """
    Fetch recent Astronomy Pictures of the Day.
    Returns list of {title, explanation, url, hdurl, date, copyright}
    """
    cache_key = f"apod_recent:{count}"
    cached = cache_get(cache_key, ttl_seconds=APOD_TTL)
    if cached is not None:
        return cached

    data = _safe_get(
        APOD_API,
        params={"api_key": NASA_API_KEY, "count": count, "thumbs": True}
    )

    results = []
    if isinstance(data, list):
        for item in data:
            results.append({
                "title": item.get("title", ""),
                "explanation": item.get("explanation", "")[:400],
                "date": item.get("date", ""),
                "url": item.get("url", ""),
                "hdurl": item.get("hdurl", item.get("url", "")),
                "media_type": item.get("media_type", "image"),
                "copyright": item.get("copyright", "NASA"),
            })
    elif isinstance(data, dict):  # single result
        results.append({
            "title": data.get("title", ""),
            "explanation": data.get("explanation", "")[:400],
            "date": data.get("date", ""),
            "url": data.get("url", ""),
            "hdurl": data.get("hdurl", data.get("url", "")),
            "media_type": data.get("media_type", "image"),
            "copyright": data.get("copyright", "NASA"),
        })

    cache_set(cache_key, results)
    logger.info(f"APOD fetched: {len(results)} items")
    return results


def get_tess_mission_images() -> List[Dict]:
    """Curated TESS-specific images for the hero/background."""
    return search_nasa_images("TESS transiting exoplanet survey satellite", page_size=6)
