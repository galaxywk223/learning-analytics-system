
import requests
import datetime
import sys
import time

BASE_URL = "http://127.0.0.1:5000"
USERNAME = "test_stage_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
EMAIL = f"{USERNAME}@example.com"
PASSWORD = "password123"

session = requests.Session()

def log(msg):
    print(f"[TEST] {msg}")

def fail(msg):
    print(f"[FAIL] {msg}")
    sys.exit(1)

def register_and_login():
    log(f"Registering user {USERNAME}...")
    res = session.post(f"{BASE_URL}/api/auth/register", json={
        "username": USERNAME,
        "email": EMAIL,
        "password": PASSWORD
    })
    if res.status_code != 201:
        fail(f"Registration failed: {res.text}")
    
    log("Logging in...")
    res = session.post(f"{BASE_URL}/api/auth/login", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    if res.status_code != 200:
        fail(f"Login failed: {res.text}")
    
    token = res.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    log("Login successful.")

def create_category_and_subcategory():
    log("Creating category...")
    res = session.post(f"{BASE_URL}/api/categories", json={"name": "Test Cat"})
    if res.status_code != 201:
        fail(f"Category creation failed: {res.text}")
    cat_id = res.json()["category"]["id"]
    
    log("Creating subcategory...")
    res = session.post(f"{BASE_URL}/api/categories/{cat_id}/subcategories", json={"name": "Test Sub"})
    if res.status_code != 201:
        fail(f"Subcategory creation failed: {res.text}")
    sub_id = res.json()["subcategory"]["id"]
    return sub_id

def create_stage(name, start_date):
    log(f"Creating stage '{name}' start={start_date}...")
    res = session.post(f"{BASE_URL}/api/stages", json={"name": name, "start_date": start_date})
    if res.status_code != 201:
        fail(f"Stage creation failed: {res.text}")
    return res.json()["stage"]

def update_stage(stage_id, start_date):
    log(f"Updating stage {stage_id} start={start_date}...")
    res = session.put(f"{BASE_URL}/api/stages/{stage_id}", json={"start_date": start_date})
    if res.status_code != 200:
        fail(f"Stage update failed: {res.text}")
    return res.json()["stage"]

def create_log(log_date, sub_id, task="Test Task"):
    log(f"Creating log date={log_date}...")
    res = session.post(f"{BASE_URL}/api/records/crud", json={
        "task": task,
        "log_date": log_date,
        "subcategory_id": sub_id,
        "actual_duration": 60
    })
    # Note: verify correct endpoint. records_crud.py registers blueprint 'records_crud'.
    # Check parent registration prefix. Usually Blueprint("records_crud", __name__) registered at some prefix.
    # Assuming /api/records/crud based on blueprint name or similar context (checking app/__init__.py would confirm)
    # But usually it's /api/records or similar.
    # Wait, in records_crud.py line 16: @crud_bp.route("/", ...)
    # I need to know the prefix.
    # I will guess /api/records based on naming convention. If 404, I'll check __init__.py.
    
    if res.status_code != 201:
        # Retry with /api/records if 404
        if res.status_code == 404:
             return None
        fail(f"Log creation failed: {res.text}")
    return res.json()["data"]

def get_log(log_id):
    res = session.get(f"{BASE_URL}/api/records/crud/{log_id}")
    if res.status_code != 200:
        fail(f"Get log failed: {res.text}")
    return res.json()["data"]

def update_log_date(log_id, new_date):
    log(f"Updating log {log_id} date={new_date}...")
    res = session.put(f"{BASE_URL}/api/records/crud/{log_id}", json={"log_date": new_date})
    if res.status_code != 200:
        fail(f"Log update failed: {res.text}")
    return res.json()["data"]

def main():
    try:
        register_and_login()
        sub_id = create_category_and_subcategory()
        
        # Test requires /api/records or /api/records/crud. Let's probe.
        # records_crud blueprint is likely registered.
        # I'll Assume /api/records
        global BASE_LOG_URL
        BASE_LOG_URL = f"{BASE_URL}/api/records" 
        
        # 1. Create Stages
        stage_a = create_stage("Stage A", "2025-01-01")
        stage_b = create_stage("Stage B", "2025-02-01")
        
        # 2. Create Log in Stage A (2025-01-15)
        res = session.post(f"{BASE_URL}/api/records", json={
             "task": "Log 1", "log_date": "2025-01-15", "subcategory_id": sub_id, "actual_duration": 30
        })
        if res.status_code == 404:
            # Maybe path is /api/records/crud ?
            res = session.post(f"{BASE_URL}/api/records/crud", json={
                 "task": "Log 1", "log_date": "2025-01-15", "subcategory_id": sub_id, "actual_duration": 30
            })
            if res.status_code == 201:
                 # Found it
                 pass
            else:
                 fail(f"Could not find log endpoint: {res.status_code}")
        
        if res.status_code != 201:
             fail(f"Log 1 creation failed: {res.text}")
        
        log1 = res.json()["data"]
        # Verify Stage A
        full_log1 = get_log(log1["id"])
        if full_log1["stage"]["id"] != stage_a["id"]:
            fail(f"Log 1 should be Stage A ({stage_a['id']}) but is {full_log1['stage']['id']}")
        log("Log 1 correctly assigned to Stage A.")

        # 3. Create Log in Stage B (2025-02-15)
        # Use known good endpoint
        log_endpoint = res.request.url
        res = session.post(log_endpoint, json={
             "task": "Log 2", "log_date": "2025-02-15", "subcategory_id": sub_id, "actual_duration": 30
        })
        log2 = res.json()["data"]
        full_log2 = get_log(log2["id"])
        if full_log2["stage"]["id"] != stage_b["id"]:
            fail(f"Log 2 should be Stage B ({stage_b['id']}) but is {full_log2['stage']['id']}")
        log("Log 2 correctly assigned to Stage B.")
        
        # 4. Update Log 1 Date -> Moves to Stage B
        update_res = session.put(f"{log_endpoint}/{log1['id']}", json={"log_date": "2025-02-05"})
        if update_res.status_code != 200:
             fail(f"Log 1 update failed: {update_res.text}")
        
        full_log1_updated = get_log(log1["id"])
        if full_log1_updated["stage"]["id"] != stage_b["id"]:
            fail(f"Log 1 (moved to Feb 5) should be Stage B ({stage_b['id']}) but is {full_log1_updated['stage']['id']}")
        log("Log 1 correctly moved to Stage B after date update.")
        
        # 5. Update Stage B Start Date to 2025-01-10 (retroactive change)
        # This implies Stage A is effectively shorter? Or actually Stage B covers more time.
        # Log 3 on 2025-01-12 should now be Stage B.
        # Wait, create Log 3 first? No, let's create it.
        
        # Create Log 3 on 2025-01-12. Currently Stage A (Start Jan 1) < Jan 12 < Stage B (Start Feb 1).
        # So should be Stage A.
        res = session.post(log_endpoint, json={
             "task": "Log 3", "log_date": "2025-01-12", "subcategory_id": sub_id, "actual_duration": 30
        })
        log3 = res.json()["data"]
        full_log3 = get_log(log3["id"])
        if full_log3["stage"]["id"] != stage_a["id"]:
             fail(f"Log 3 (Jan 12) should be Stage A initially but is {full_log3['stage']['id']}")
        log("Log 3 correctly assigned to Stage A initially.")
        
        # Now Update Stage B to start Jan 10
        update_stage(stage_b["id"], "2025-01-10")
        
        # Verify Log 3 (Jan 12) is now Stage B (Start Jan 10 <= Jan 12)
        # Because we updated Stage B, ensure_log_stage_consistency should have run.
        full_log3_updated = get_log(log3["id"])
        if full_log3_updated["stage"]["id"] != stage_b["id"]:
             fail(f"Log 3 (Jan 12) should be auto-moved to Stage B (Start Jan 10) but is {full_log3_updated['stage']['id']}")
        log("Log 3 correctly auto-moved to Stage B after Stage B start date update!")
        
        print("\n[SUCCESS] ALL TESTS PASSED!")
        
    except Exception as e:
        fail(f"Exception: {e}")

if __name__ == "__main__":
    main()
