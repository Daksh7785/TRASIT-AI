# test_integration.py — RUN THIS AFTER ALL FILES ARE CREATED
from src.pipeline.full_pipeline import TransitAIPipeline

pipeline = TransitAIPipeline()
results = pipeline.run(mode="synthetic", n_lcs=20)

# Assertions
processed = [r for r in results if r.get("status") == "PROCESSED"]
assert len(processed) >= 15, f"Too few processed: {len(processed)}"

# Check at least some detections
detected = [r for r in processed if r.get("detection", {}).get("detected")]
print(f"Detected: {len(detected)}/{len(processed)}")

# Check classification coverage
classified = [r for r in processed if r.get("classification", {}).get("label")]
assert len(classified) == len(processed), "Some LCs not classified"

# Check report generated
from pathlib import Path
assert Path("reports/TRANSIT_AI_REPORT.pdf").exists(), "Report not generated"

print("ALL INTEGRATION TESTS PASSED")
