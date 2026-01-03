#!/usr/bin/env python3
"""
Test script to check if the deployed platform has the template validation fix
"""

import requests
import json

def test_node_express_creation():
    """Test creating a node-express muppet to see if validation passes"""
    
    platform_url = "https://muppet-platform.s3u.dev"
    
    # Test data for muppet creation
    test_data = {
        "name": "test-validation-check",
        "template": "node-express", 
        "description": "Test to check if template validation is fixed"
    }
    
    print("🧪 Testing node-express template validation on deployed platform...")
    print(f"📡 Platform URL: {platform_url}")
    print(f"📋 Test data: {test_data}")
    
    try:
        # Make request to create muppet
        response = requests.post(
            f"{platform_url}/api/v1/muppets",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📄 Response headers: {dict(response.headers)}")
        
        # Parse response
        try:
            response_data = response.json()
            print(f"📝 Response body: {json.dumps(response_data, indent=2)}")
        except:
            print(f"📝 Response body (raw): {response.text}")
        
        # Analyze the result
        if response.status_code == 200 or response.status_code == 201:
            print("✅ SUCCESS: Muppet creation succeeded - validation fix is deployed!")
            return True
        elif response.status_code >= 400:
            response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"error": response.text}
            
            if "Missing core template files: .env.local" in str(response_data):
                print("❌ VALIDATION BUG STILL EXISTS: .env.local reported as missing")
                print("   This means the deployed platform does NOT have the validation fix")
                return False
            else:
                print(f"⚠️  Different error occurred: {response_data}")
                print("   This might be a different issue (not the validation bug)")
                return None
        
    except requests.exceptions.RequestException as e:
        print(f"🔌 Connection error: {e}")
        return None

def test_platform_health():
    """Check if platform is responding"""
    platform_url = "https://muppet-platform.s3u.dev"
    
    try:
        response = requests.get(f"{platform_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"🏥 Platform health: {health_data}")
            return True
        else:
            print(f"🏥 Platform health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"🏥 Platform health check error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing deployed platform validation...")
    
    # First check if platform is healthy
    if not test_platform_health():
        print("❌ Platform is not healthy, cannot test validation")
        exit(1)
    
    # Test the validation
    result = test_node_express_creation()
    
    if result is True:
        print("\n🎉 CONCLUSION: Template validation fix is deployed and working!")
    elif result is False:
        print("\n🐛 CONCLUSION: Template validation bug still exists in deployed platform")
        print("   The deployed platform needs to be updated with the latest code")
    else:
        print("\n❓ CONCLUSION: Unable to determine validation status due to other issues")