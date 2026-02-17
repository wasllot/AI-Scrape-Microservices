
import requests
import json
import time

BASE_URL = "https://api.reinaldotineo.online/scraper"

def test_health():
    print("🏥 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("   ✅ Health Check Passed!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"   ❌ Health Check Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"   ❌ Connection Error: {e}")

def test_universal_extract():
    print("\n🕷️ Testing Universal Extraction (Example.com)...")
    payload = {
        "url": "https://example.com",
        "extraction_rules": {
            "title": {"selector": "h1"},
            "paragraph": {"selector": "p"}
        },
        "use_cache": False
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/extract", json=payload)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            print(f"   ✅ Extraction Successful in {duration:.2f}s!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"   ❌ Extraction Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"   ❌ Connection Error: {e}")

if __name__ == "__main__":
    print(f"🚀 Testing Scraper Service at {BASE_URL}")
    test_health()
    test_universal_extract()
