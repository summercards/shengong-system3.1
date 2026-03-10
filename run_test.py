# run_test.py - Direct test run
import sys
import os

os.chdir(r'I:\项目\shengong-system\godcraft_v4')
sys.path.insert(0, r'I:\项目\shengong-system\godcraft_v4')

import database
import json

print("=== Testing Database Module ===")

# 1. Get all tables
tables = database.get_all_tables()
print(f"[OK] All tables: {tables}")

# 2. Create test project
project_id = database.create_project(
    project_id="test_m2_1",
    title="M2-1 Test",
    genre="Fantasy",
    logline="Test logline",
    target_chapters=10
)
print(f"[OK] Created project ID: {project_id}")

# 3. Get project
proj = database.get_project("test_m2_1")
print(f"[OK] Project: {proj['title']}, Status: {proj['status']}")

# 4. Update status
database.update_project_status("test_m2_1", "active")
proj = database.get_project("test_m2_1")
print(f"[OK] Updated status: {proj['status']}")

# 5. Create job
job_id = database.create_job("test_m2_1", 1)
print(f"[OK] Created job ID: {job_id}")

# 6. Update job status
database.update_job_status(job_id, "running")
job = database.get_job(job_id)
print(f"[OK] Job status: {job['status']}")

# 7. Log event
event_id = database.log_event("test_m2_1", 1, "test", "Test event", {"key": "value"})
print(f"[OK] Event ID: {event_id}")

# 8. Add character relationship
rel_id = database.add_character_relationship("test_m2_1", "char_a", "char_b", "friend", 50)
print(f"[OK] Character relationship ID: {rel_id}")

# 9. Add world graph edge
edge_id = database.add_world_edge("test_m2_1", "town", "forest", "connects", 0.9)
print(f"[OK] World graph edge ID: {edge_id}")

# 10. Add foreshadowing
fs_id = database.add_foreshadowing("test_m2_1", 1, 5, "Mystery prophecy")
print(f"[OK] Foreshadowing ID: {fs_id}")

# 11. Get active foreshadowings
fses = database.get_active_foreshadowings("test_m2_1")
print(f"[OK] Active foreshadowings: {len(fses)}")

# 12. Resolve foreshadowing
database.resolve_foreshadowing(fs_id)
fses = database.get_active_foreshadowings("test_m2_1")
print(f"[OK] After resolve: {len(fses)}")

# 13. Write audit log
log_id = database.write_audit_log("Test input", "test_action", {"param": 1}, "Success")
print(f"[OK] Audit log ID: {log_id}")

# 14. Get audit logs
logs = database.get_audit_logs(5)
print(f"[OK] Audit logs count: {len(logs)}")

print("\n=== All Tests Passed! ===")
