# test_m2_2_manual.py - Manual test for M2-2
import sys
import os
os.chdir('I:/项目/shengong-system/godcraft_v4')
sys.path.insert(0, '.')

print("=" * 50)
print("M2-2 Manual Test")
print("=" * 50)

# Test 1: Schema Validator
print("\n[1] Testing Schema Validator...")
from utils.schema_validator import validate_data, check_trust_delta, SCHEMAS

# Valid project
data = {'project_id': 'test001', 'title': 'Test', 'genre': 'fantasy'}
is_valid, errors = validate_data('project', data)
print(f"  Valid project: {is_valid}")

# Invalid project (missing genre - should fail)
data = {'project_id': 'test002', 'title': 'Test'}  # missing genre
is_valid, errors = validate_data('project', data)
print(f"  Invalid project (missing genre): validated={is_valid}, expected=False")

# trust_delta check
result = check_trust_delta(0, 10)
print(f"  trust_delta (0->10): needs_review={result['needs_review']}, expected=True")

result = check_trust_delta(5, 6)
print(f"  trust_delta (5->6): needs_review={result['needs_review']}, expected=False")

# Test 2: Structured Store
print("\n[2] Testing Structured Store...")
from structured_store import StructuredStore, store

# Use unique project ID
import time
unique_id = int(time.time())

# Create project
success, msg, result = store.create_project(
    project_id=f'm2_test_{unique_id}',
    title='M2 Test Novel',
    genre='fantasy',
    logline='Testing M2-2',
    target_chapters=50
)
print(f"  Create project: success={success}, msg={msg}")

# Get project
proj = store.get_project(f'm2_test_{unique_id}')
print(f"  Get project: title={proj['title'] if proj else 'None'}")

# Create job (only if project exists)
if proj:
    success, msg, job_id = store.create_job(f'm2_test_{unique_id}', 1)
    print(f"  Create job: success={success}, job_id={job_id}")
    
    if success and job_id > 0:
        # Update job
        success, msg = store.update_job(job_id, status='running')
        print(f"  Update job status: success={success}")
        
        # Get job
        job = store.get_job(job_id)
        print(f"  Get job: status={job['status'] if job else 'None'}")

# Test 3: Trust Delta Review
print("\n[3] Testing trust_delta review mechanism...")

# Create project with current_chapter = 0
test_proj_id = f'm2_delta_test_{unique_id}'
store.create_project(test_proj_id, 'Delta Test', 'scifi', 'Testing delta', 100)

from database import execute_write
execute_write("UPDATE novel_projects SET current_chapter=0 WHERE project_id=?", (test_proj_id,))

# Try update with trust_delta (should fail due to review)
success, msg = store.update_project(test_proj_id, current_chapter=10, _trust_delta=True)
print(f"  Update with trust_delta (0->10): success={success}, expected=False")
print(f"  Message: {msg[:60]}...")

# Try update without trust_delta (should succeed)
success, msg = store.update_project(test_proj_id, current_chapter=5)
print(f"  Update without trust_delta: success={success}")

# Verify
proj = store.get_project(test_proj_id)
print(f"  Verified current_chapter: {proj['current_chapter']}")

print("\n" + "=" * 50)
print("All M2-2 tests completed!")
print("=" * 50)
