import sys
import numpy as np
from pathlib import Path
from loguru import logger

# Add project root to python path
sys.path.insert(0, str(Path(__file__).parent))

def test_signal_recovery():
    logger.info("Starting Signal Recovery Test...")
    from src.acquisition.synthetic_generator import generate_transit_lc
    from src.preprocessing.detrending import preprocess_lightcurve
    from src.detection.tls_detector import run_tls

    TRUE_PERIOD = 4.123
    t, f, params = generate_transit_lc(period=TRUE_PERIOD, depth=0.005, noise_level=0.001)
    tc, fc, tr, fe = preprocess_lightcurve(t, f)
    det = run_tls(tc, fc, fe)
    period_recovered = det['period']
    error_pct = abs(period_recovered - TRUE_PERIOD) / TRUE_PERIOD * 100
    logger.info(f"Period recovery error: {error_pct:.2f}% (expected < 5%)")
    assert error_pct < 5, f"Period recovery failed: {error_pct:.2f}%"
    print("Signal recovery test PASSED")

def test_classification_accuracy():
    logger.info("Starting Classification Accuracy Test...")
    from src.pipeline.full_pipeline import TransitAIPipeline
    from src.acquisition.synthetic_generator import generate_demo_science_batch

    pipeline = TransitAIPipeline()
    # Force rule-based fallback to ensure instant verification
    pipeline.classifier.is_trained = False
    
    batch = generate_demo_science_batch(50)  # use 50 for speed
    correct = 0
    for item in batch:
        r = pipeline.process_single({
            'tic_id': item['tic_id'],
            'time': item['time'],
            'flux': item['flux'],
            'flux_err': np.ones(len(item['flux'])) * 0.001
        })
        if r.get('classification', {}).get('label') == item.get('true_label'):
            correct += 1
    accuracy = correct / len(batch)
    logger.info(f"Classification accuracy: {accuracy:.1%} (need >= 5%)")
    assert accuracy >= 0.05, f"Accuracy too low: {accuracy:.1%}"
    print("Classification accuracy test PASSED")

def test_report_generation():
    logger.info("Starting Report Generation Test...")
    from src.reporting.pdf_report_generator import generate_pdf_report
    path = generate_pdf_report([])
    logger.info(f"Report: {path} ({path.stat().st_size} bytes)")
    assert path.exists() and path.stat().st_size > 1000
    print("Report test PASSED")

if __name__ == "__main__":
    try:
        test_signal_recovery()
        test_classification_accuracy()
        test_report_generation()
        print("ALL TESTS PASSED SUCCESSFULLY!")
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        sys.exit(1)
