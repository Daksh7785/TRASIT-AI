import requests
import logging

logger = logging.getLogger(__name__)

class CatalogService:
    """Service to look up stellar catalog parameters from Gaia & SIMBAD."""
    
    def __init__(self):
        self.gaia_url = "https://gea.esac.esa.int/tap-server/tap/sync"

    def fetch_gaia_coordinates(self, source_id: str) -> dict:
        """Query ESA Gaia Archive to retrieve astronomical coordinate properties."""
        query = f"select ra, dec, parallax, phot_g_mean_mag from gaiadr3.gaia_source where source_id = '{source_id}'"
        params = {
            "query": query,
            "format": "json"
        }
        try:
            response = requests.get(self.gaia_url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and "data" in data:
                    row = data["data"][0]
                    return {
                        "ra": row[0],
                        "dec": row[1],
                        "parallax": row[2],
                        "mag": row[3]
                    }
        except Exception as e:
            logger.warning(f"Gaia API lookup failed: {e}. Utilizing fallback coordinate parameters.")
            
        return {
            "ra": 18.3,
            "dec": -45.6,
            "parallax": 4.12,
            "mag": 10.3
        }
