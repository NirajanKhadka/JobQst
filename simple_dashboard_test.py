import requests
import json

def check_dashboard_health():
    """Checks the health of the running dashboard and prints the response."""
    try:
        response = requests.get("http://localhost:8002/api/health", timeout=5)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        health_data = response.json()
        
        print("✅ Dashboard is running and responded with:")
        print(json.dumps(health_data, indent=2))
        
        if health_data.get("profile") and health_data["profile"] != "Unknown":
            print("\n🎉 Success! The profile name is being sent correctly.")
        else:
            print("\n⚠️ The profile name is still 'Unknown' or missing.")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to the dashboard: {e}")
    except json.JSONDecodeError:
        print("❌ Failed to decode the JSON response from the dashboard.")

if __name__ == "__main__":
    check_dashboard_health() 