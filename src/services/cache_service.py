"""
Disk-based JSON cache service with TTL support.
No Redis dependency — lightweight, file-based, production-safe.
Falls back gracefully on any IO error.
"""
import json
import time
import hashlib
from pathlib import Path
from typing import Any, Optional
from loguru import logger

CACHE_DIR = Path(__file__).parent.parent.parent / "data" / ".api_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _key_path(key: str) -> Path:
    safe = hashlib.md5(key.encode()).hexdigest()
    return CACHE_DIR / f"{safe}.json"


def cache_get(key: str, ttl_seconds: int = 3600) -> Optional[Any]:
    """Return cached value if it exists and is not expired."""
    path = _key_path(key)
    try:
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        age = time.time() - data.get("ts", 0)
        if age > ttl_seconds:
            path.unlink(missing_ok=True)
            return None
        return data.get("value")
    except Exception as e:
        logger.debug(f"Cache miss ({key[:40]}): {e}")
        return None


def cache_set(key: str, value: Any) -> None:
    """Persist value to disk cache."""
    path = _key_path(key)
    try:
        path.write_text(
            json.dumps({"ts": time.time(), "value": value}, default=str),
            encoding="utf-8"
        )
    except Exception as e:
        logger.debug(f"Cache write failed ({key[:40]}): {e}")


def cache_invalidate(key: str) -> None:
    """Delete a specific cache entry."""
    _key_path(key).unlink(missing_ok=True)


def cache_clear_all() -> int:
    """Clear entire cache directory, return count of deleted files."""
    count = 0
    for f in CACHE_DIR.glob("*.json"):
        f.unlink(missing_ok=True)
        count += 1
    return count


def cache_stats() -> dict:
    """Return cache directory statistics."""
    files = list(CACHE_DIR.glob("*.json"))
    total_size = sum(f.stat().st_size for f in files)
    return {
        "entries": len(files),
        "total_kb": round(total_size / 1024, 1),
        "cache_dir": str(CACHE_DIR),
    }
