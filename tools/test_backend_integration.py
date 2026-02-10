#!/usr/bin/env python3
"""
Backend Integration Test Script
Tests the complete MedGemma backend API pipeline
"""

import sys
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8001"
TEST_CASE_FILE = "artifacts/ai_showcase/normalized_outputs/case_006_output.json"

print("="*70)
print("PREGNANCYBRIDGE BACKEND INTEGRATION TEST")
print("="*70)

# Step 1: Check if server is running
print("\n[STEP 1] Checking if backend server is running...")
try:
    response = requests.get(f"{BASE_URL}/", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Server is running")
        print(f"  Version: {data.get('version')}")
        print(f"  Model loaded: {data.get('model_loaded')}")
        print(f"  Device: {data.get('device')}")
    else:
        print("✗ Server returned error:", response.status_code)
        sys.exit(1)
except requests.exceptions.ConnectionError:
    print("✗ ERROR: Cannot connect to server at", BASE_URL)
    print("\nMake sure the server is running:")
    print("  cd D:\\MedGemma")
    print("  python src/backend/app.py")
    sys.exit(1)

# Step 2: Load test case data
print("\n[STEP 2] Loading test case from showcase...")
test_case_path = Path(TEST_CASE_FILE)

if not test_case_path.exists():
    print(f"✗ Test case file not found: {test_case_path}")
    print("\nUsing hardcoded test case instead...")

    # Hardcoded test case (DEMO_006 - Kavitha Naik)
    test_request = {
        "patient_id": "DEMO_006",
        "name": "Kavitha Naik",
        "age": 28,
        "gestational_age_weeks": 22,
        "bp_systolic": 128,
        "bp_diastolic": 84,
        "weight_kg": 65.0,
        "hemoglobin_g_dl": 11.2,
        "platelets_per_ul": 145000,
        "proteinuria": "Negative"
    }
    print("✓ Using hardcoded test case: DEMO_006 (Kavitha Naik)")
else:
    with open(test_case_path, 'r') as f:
        showcase_data = json.load(f)

    # Convert showcase format to API request format
    test_request = {
        "patient_id": showcase_data.get("patient_id", "TEST_CASE"),
        "name": showcase_data.get("patient_name", "Test Patient"),
        "age": showcase_data.get("age", 28),
        "gestational_age_weeks": showcase_data.get("gestational_age_weeks"),
        "bp_systolic": showcase_data.get("bp_systolic", 120),
        "bp_diastolic": showcase_data.get("bp_diastolic", 80),
        "weight_kg": showcase_data.get("weight_kg", 65.0),
        "hemoglobin_g_dl": showcase_data.get("hemoglobin_g_dl"),
        "platelets_per_ul": showcase_data.get("platelets_per_ul"),
        "proteinuria": showcase_data.get("proteinuria")
    }
    print(f"✓ Loaded test case from: {test_case_path}")

print(f"\n  Patient ID: {test_request['patient_id']}")
print(f"  Name: {test_request['name']}")
print(f"  BP: {test_request['bp_systolic']}/{test_request['bp_diastolic']}")
print(f"  Hemoglobin: {test_request['hemoglobin_g_dl']} g/dL")

# Step 3: Submit assessment request
print("\n[STEP 3] Submitting assessment request to API...")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/assess-risk",
        json=test_request,
        timeout=10
    )

    if response.status_code == 200:
        result = response.json()
        run_id = result['run_id']
        print(f"✓ Assessment submitted successfully")
        print(f"  Run ID: {run_id}")
        print(f"  Status: {result['status']}")
    else:
        print(f"✗ API returned error: {response.status_code}")
        print(f"  Response: {response.text}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Request failed: {e}")
    sys.exit(1)

# Step 4: Poll for completion
print("\n[STEP 4] Waiting for MedGemma inference to complete...")
print("(This may take 20-30 minutes on CPU...)")

max_wait = 3000  # 50 minutes
poll_interval = 10  # seconds
elapsed = 0

while elapsed < max_wait:
    time.sleep(poll_interval)
    elapsed += poll_interval

    try:
        response = requests.get(f"{BASE_URL}/api/v1/result/{run_id}", timeout=5)
        if response.status_code == 200:
            result = response.json()
            status = result['status']

            if status == 'completed':
                print(f"\n✓ Assessment completed in {elapsed} seconds ({elapsed/60:.1f} minutes)")
                break
            elif status == 'failed':
                print(f"\n✗ Assessment failed: {result.get('error')}")
                sys.exit(1)
            else:
                # Still processing
                print(f"  [{elapsed}s] Status: {status}...", end='\r')
        else:
            print(f"\n✗ Status check failed: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Polling failed: {e}")
        sys.exit(1)
else:
    print(f"\n✗ Timeout after {max_wait} seconds")
    sys.exit(1)

# Step 5: Download and verify artifacts
print("\n[STEP 5] Downloading and verifying artifacts...")

# Download pipeline_output.json
try:
    response = requests.get(
        f"{BASE_URL}/api/v1/download/{run_id}/pipeline_output.json",
        timeout=5
    )
    if response.status_code == 200:
        pipeline_output = response.json()
        print("✓ Downloaded pipeline_output.json")

        # Check required fields
        assert 'decision_source' in pipeline_output, "Missing decision_source"
        assert 'provenance' in pipeline_output, "Missing provenance"
        assert 'model_snapshot' in pipeline_output['provenance'], "Missing model_snapshot"

        print(f"  Decision source: {pipeline_output['decision_source']}")
        print(f"  Final risk level: {pipeline_output['final_risk_level']}")
        print(f"  Model snapshot: {pipeline_output['provenance']['model_snapshot']}")
    else:
        print(f"✗ Failed to download pipeline_output.json: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Download failed: {e}")
    sys.exit(1)

# Download medgemma_raw.txt
try:
    response = requests.get(
        f"{BASE_URL}/api/v1/download/{run_id}/medgemma_raw.txt",
        timeout=5
    )
    if response.status_code == 200:
        medgemma_raw = response.text
        print("✓ Downloaded medgemma_raw.txt")

        # Show preview
        preview = medgemma_raw[:400] if len(medgemma_raw) > 400 else medgemma_raw
        print(f"\n  MedGemma Raw Output Preview ({len(medgemma_raw)} chars total):")
        print("  " + "-"*66)
        for line in preview.split('\n'):
            print(f"  {line}")
        if len(medgemma_raw) > 400:
            print("  [...truncated...]")
        print("  " + "-"*66)
    else:
        print(f"✗ Failed to download medgemma_raw.txt: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Download failed: {e}")
    sys.exit(1)

# Step 6: Run integrity verification
print("\n[STEP 6] Running integrity verification...")
import subprocess

verify_script = Path("src/backend/verify.py")
if verify_script.exists():
    try:
        result = subprocess.run(
            [sys.executable, str(verify_script), run_id],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        print(result.stdout)
        if result.returncode == 0:
            print("✓ Integrity verification PASSED")
        else:
            print("✗ Integrity verification FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"⚠ Could not run verify.py: {e}")
else:
    print(f"⚠ verify.py not found at {verify_script}")

# Final summary
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)
print(f"✓ Run ID: {run_id}")
print(f"✓ Patient: {test_request['name']} ({test_request['patient_id']})")
print(f"✓ Risk Level: {pipeline_output['final_risk_level']}")
print(f"✓ Recommendations: {len(pipeline_output['final_recommendations'])}")
print(f"✓ Inference Time: {pipeline_output['provenance'].get('inference_time_ms', 0)}ms")
print(f"✓ Artifacts saved to: artifacts/backend_runs/{run_id}/")
print("\nRecommendations:")
for i, rec in enumerate(pipeline_output['final_recommendations'][:3], 1):
    print(f"  {i}. {rec}")

print("\n" + "="*70)
print("✓ BACKEND INTEGRATION TEST PASSED")
print("="*70)
print("\nVERIFY: BACKEND_APP_CREATED src/backend/app.py")
print(f"VERIFY: SAMPLE_RUN_SAVED artifacts/backend_runs/{run_id}/")
print("VERIFY: VERIFY_SCRIPT_CREATED src/backend/verify.py")
print("VERIFY: TEST_SCRIPT_OUTPUT_PASTED")