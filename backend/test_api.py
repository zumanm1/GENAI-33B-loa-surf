
#!/usr/bin/env python3
"""
Test script for Network Automation Platform API
Usage: python test_api.py
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_devices():
    """Test devices endpoint"""
    print("\n🖥️  Testing devices endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/devices")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Devices test failed: {e}")
        return False

def test_connectivity():
    """Test connectivity endpoint"""
    print("\n📡 Testing connectivity...")
    try:
        payload = {"devices": ["R15", "R16"]}
        response = requests.post(f"{BASE_URL}/test/connectivity", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Connectivity test failed: {e}")
        return False

def test_config_retrieve():
    """Test configuration retrieve with different methods"""
    print("\n📥 Testing configuration retrieve...")
    
    methods = ['netmiko', 'napalm', 'pyats']
    commands = ['show ip interface brief', 'show version']
    
    for method in methods:
        for command in commands:
            print(f"\n  Testing {method} with '{command}'...")
            try:
                payload = {
                    "device": "R15",
                    "command": command,
                    "method": method,
                    "save_backup": True
                }
                
                response = requests.post(f"{BASE_URL}/config/retrieve", json=payload)
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"  Success: {result.get('success')}")
                    print(f"  Method: {result.get('method')}")
                    print(f"  Parsed: {result.get('parsed', False)}")
                    if result.get('output'):
                        output_preview = str(result['output'])[:200]
                        print(f"  Output preview: {output_preview}...")
                else:
                    print(f"  Error: {response.text}")
                    
            except Exception as e:
                print(f"  ❌ Failed: {e}")
                
            time.sleep(1)  # Brief pause between requests

def main():
    """Run all tests"""
    print("🚀 Network Automation Platform API Tests")
    print("=" * 50)
    
    # Run tests
    tests = [
        ("Health Check", test_health),
        ("Devices List", test_devices),
        ("Connectivity Test", test_connectivity),
        ("Config Retrieve", test_config_retrieve)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 Test Summary:")
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {test_name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")

if __name__ == "__main__":
    main()
