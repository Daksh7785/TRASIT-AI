import numpy as np

class InjectionRecoveryEngine:
    """Scientific validation engine to test detection completeness by injecting transits."""
    
    def __init__(self, detector):
        self.detector = detector

    def inject_transit(self, time: np.ndarray, flux: np.ndarray, period: float, depth_ppm: float, duration_hours: float, t0: float = 0.0) -> np.ndarray:
        """Inject a simulated box transit model into a real astronomical light curve."""
        injected_flux = flux.copy()
        depth = depth_ppm / 1e6
        duration_days = duration_hours / 24.0
        
        # Symmetrical box model transit phase folding
        phase = ((time - t0) % period) / period
        phase = np.where(phase > 0.5, phase - 1.0, phase)
        
        transit_mask = np.abs(phase * period) < (duration_days / 2.0)
        injected_flux[transit_mask] *= (1.0 - depth)
        
        return injected_flux

    def run_recovery_test(self, time: np.ndarray, flux: np.ndarray, period: float, depth_ppm: float, duration_hours: float) -> dict:
        """Test if the detector can recover the injected planet signal."""
        injected_flux = self.inject_transit(time, flux, period, depth_ppm, duration_hours)
        
        # Search for transit using detector
        results = self.detector.detect(time, injected_flux)
        
        recovered_period = results.get("period", 0.0)
        is_recovered = False
        
        # Check if period matches within 5% tolerance
        if abs(recovered_period - period) / period < 0.05:
            is_recovered = True
            
        return {
            "injected_period": period,
            "injected_depth": depth_ppm,
            "recovered_period": recovered_period,
            "is_recovered": is_recovered,
            "snr": results.get("snr", 0.0),
            "sde": results.get("sde", 0.0)
        }
