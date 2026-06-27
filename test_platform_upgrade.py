import pytest
import numpy as np
from src.services.astronomy_service import AstronomyService
from src.services.catalog_service import CatalogService
from src.services.mission_service import MissionService
from src.validation.injection_recovery import InjectionRecoveryEngine
from src.pipeline.dataset_builder import AutomatedDatasetBuilder
from src.pipeline.feature_store import FeatureStore

class DummyDetector:
    def detect(self, time, flux):
        return {"period": 4.654, "snr": 15.2, "sde": 9.4}

def test_astronomy_services():
    astro = AstronomyService()
    params = astro.fetch_nasa_parameters("TOI-125b")
    assert "pl_orbper" in params
    assert params["pl_orbper"] == 4.654

def test_catalog_services():
    cat = CatalogService()
    coords = cat.fetch_gaia_coordinates("DR3_1234567")
    assert "ra" in coords
    assert "dec" in coords

def test_mission_services():
    mission = MissionService()
    status = mission.fetch_live_tess_status()
    assert "current_sector" in status
    assert status["current_sector"] == 68

def test_injection_recovery():
    detector = DummyDetector()
    engine = InjectionRecoveryEngine(detector)
    
    time = np.linspace(0, 10, 1000)
    flux = np.ones(1000)
    
    # Inject transit
    injected_flux = engine.inject_transit(time, flux, period=4.654, depth_ppm=2000, duration_hours=2.0)
    assert len(injected_flux) == len(flux)
    assert np.min(injected_flux) < 1.0
    
    # Test recovery
    res = engine.run_recovery_test(time, flux, period=4.654, depth_ppm=2000, duration_hours=2.0)
    assert res["is_recovered"] is True
    assert res["snr"] == 15.2

def test_dataset_builder():
    builder = AutomatedDatasetBuilder(data_root="data_test")
    split = builder.generate_data_split(["TIC_1", "TIC_2", "TIC_3", "TIC_4", "TIC_5"], ["TRANSIT", "ECLIPSE", "TRANSIT", "ARTIFACT", "BLEND"])
    assert "train" in split
    assert "val" in split
    assert "test" in split

def test_feature_store():
    store = FeatureStore(filepath="data_test/metadata/feature_store.json")
    feats = {"period": 5.43, "depth": 1500, "snr": 12.4}
    store.save_features("TIC_999", feats)
    
    loaded = store.get_features("TIC_999")
    assert loaded["period"] == 5.43
    assert loaded["depth"] == 1500

if __name__ == "__main__":
    pytest.main([__file__])
