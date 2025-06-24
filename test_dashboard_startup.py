import os
import requests
import time
import json

def test_dashboard_running():
    print("\n[TEST] Checking dashboard is running on port 8002...")
    for _ in range(10):
        try:
            r = requests.get("http://localhost:8002/api/dashboard-numbers", timeout=2)
            if r.status_code == 200:
                print("✅ Dashboard API is up.")
                return r.json()
        except Exception as e:
            time.sleep(1)
    print("❌ Dashboard API not responding on port 8002.")
    return None

def test_dashboard_pid():
    print("[TEST] Checking dashboard.pid file...")
    if not os.path.exists("dashboard.pid"):
        print("❌ dashboard.pid file does not exist.")
        return False
    with open("dashboard.pid") as f:
        pid = f.read().strip()
        if not pid.isdigit():
            print(f"❌ dashboard.pid does not contain a valid PID: {pid}")
            return False
        print(f"✅ dashboard.pid exists and contains PID {pid}")
        return True

def test_dashboard_job_count(api_json):
    print("[TEST] Checking dashboard job count matches database...")
    if not api_json or 'profile_stats' not in api_json:
        print("❌ Dashboard API response missing 'profile_stats' key.")
        return False
    nirajan_stats = api_json['profile_stats'].get('Nirajan')
    if not nirajan_stats:
        print("❌ No stats for Nirajan profile in dashboard API.")
        return False
    dashboard_jobs = nirajan_stats.get('jobs', {}).get('total_jobs', -1)
    print(f"Dashboard reports {dashboard_jobs} jobs for Nirajan.")
    # Now check database directly
    try:
        from src.core.job_database import get_job_db
        db = get_job_db("Nirajan")
        db_stats = db.get_stats()
        db_jobs = db_stats.get('total_jobs', -2)
        print(f"Database reports {db_jobs} jobs for Nirajan.")
        if dashboard_jobs == db_jobs:
            print("✅ Dashboard job count matches database.")
            return True
        else:
            print("❌ Dashboard job count does not match database.")
            return False
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

def main():
    api_json = test_dashboard_running()
    if not api_json:
        print("[FAIL] Dashboard not running or API error.")
        return
    if not test_dashboard_pid():
        print("[FAIL] dashboard.pid check failed.")
        return
    if not test_dashboard_job_count(api_json):
        print("[FAIL] Dashboard/database job count mismatch.")
        return
    print("\n🎉 All dashboard startup and data checks passed!")

if __name__ == "__main__":
    main() 