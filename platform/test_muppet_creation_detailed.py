#!/usr/bin/env python3
"""
Detailed test of muppet creation to understand what's happening
"""

import requests
import json

def test_muppet_creation():
    """Test muppet creation with detailed debugging"""
    
    platform_url = "https://muppet-platform.s3u.dev"
    
    # Test data for muppet creation
    test_data = {
        "name": "debug-node-test-" + str(int(__import__('time').time())),  # Unique name
        "template": "node-express", 
        "description": "Debug test for node-express validation"
    }
    
    print("🧪 Testing muppet creation with detailed debugging...")
    print(f"📡 Platform URL: {platform_url}")
    print(f"📋 Test data: {json.dumps(test_data, indent=2)}")
    
    try:
        # Make POST request to create muppet
        print("\n📤 Making POST request to /api/v1/muppets...")
        response = requests.post(
            f"{platform_url}/api/v1/muppets",
            json=test_data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=60  # Longer timeout for muppet creation
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📄 Response headers: {dict(response.headers)}")
        
        # Parse response
        try:
            response_data = response.json()
            print(f"📝 Response body: {json.dumps(response_data, indent=2)}")
        except Exception as e:
            print(f"📝 Response body (raw): {response.text}")
            print(f"❌ JSON parse error: {e}")
        
        # Analyze the result
        if response.status_code == 200 or response.status_code == 201:
            print("✅ SUCCESS: Request completed successfully")
            
            # Check if this is actually a creation response
            if isinstance(response_data, dict) and "success" in response_data:
                print("🎉 This looks like a muppet creation response!")
                return True
            elif isinstance(response_data, list):
                print("📋 This looks like a list response (not creation)")
                print("   The POST request might have been treated as GET")
                return False
            else:
                print("❓ Unexpected response format")
                return None
                
        elif response.status_code >= 400:
            print(f"❌ ERROR: Request failed with status {response.status_code}")
            
            if "Missing core template files: .env.local" in str(response_data):
                print("🐛 VALIDATION BUG CONFIRMED: .env.local reported as missing")
                return False
            else:
                print(f"⚠️  Different error: {response_data}")
                return None
        
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - this might indicate the muppet is being created")
        return None
    except requests.exceptions.RequestException as e:
        print(f"🔌 Connection error: {e}")
        return None

def test_list_muppets():
    """Test listing muppets to compare with creation response"""
    platform_url = "https://muppet-platform.s3u.dev"
    
    print("\n📋 Testing GET /api/v1/muppets for comparison...")
    
    try:
        response = requests.get(f"{platform_url}/api/v1/muppets", timeout=10)
        print(f"📊 GET Response status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"📝 GET Response: {json.dumps(response_data, indent=2)}")
        
    except Exception as e:
        print(f"❌ GET request error: {e}")

if __name__ == "__main__":
    print("🔍 Detailed muppet creation test...")
    
    # First test listing to see the format
    test_list_muppets()
    
    # Then test creation
    result = test_muppet_creation()
    
    print(f"\n🎯 RESULT: {result}")