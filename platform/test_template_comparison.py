#!/usr/bin/env python3
"""
Test both Java and Node template creation to compare behavior
"""

import requests
import json
import time

def test_template_creation(template_name, test_name_suffix):
    """Test creating a muppet with specific template"""
    
    platform_url = "https://muppet-platform.s3u.dev"
    timestamp = int(time.time())
    
    test_data = {
        "name": f"test-{template_name}-{test_name_suffix}-{timestamp}",
        "template": template_name,
        "description": f"Test {template_name} template creation"
    }
    
    print(f"\n🧪 Testing {template_name} template creation...")
    print(f"📋 Test data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(
            f"{platform_url}/api/v1/muppets",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"📝 Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
            
            # Check for success
            if response.status_code in [200, 201]:
                if isinstance(response_data, dict):
                    if response_data.get("success"):
                        print("✅ SUCCESS: Muppet creation succeeded")
                        print(f"   Muppet name: {response_data.get('muppet', {}).get('name', 'Unknown')}")
                        return "success"
                    else:
                        print("❌ FAILED: Response indicates failure")
                        print(f"   Error: {response_data}")
                        return "failed"
                else:
                    print("❌ UNEXPECTED: Response is not a dict")
                    print(f"   Response: {response_data}")
                    return "unexpected"
            else:
                print(f"❌ HTTP ERROR: Status {response.status_code}")
                if "Missing core template files" in str(response_data):
                    print("🐛 VALIDATION ERROR: Template validation failed")
                    if ".env.local" in str(response_data):
                        print("   Specific issue: .env.local reported as missing")
                    return "validation_error"
                else:
                    print(f"   Error: {response_data}")
                    return "http_error"
        
        except Exception as e:
            print(f"❌ JSON Parse Error: {e}")
            print(f"   Raw response: {response.text[:500]}...")
            return "parse_error"
            
    except Exception as e:
        print(f"❌ Request Error: {e}")
        return "request_error"

def main():
    print("🔍 Comparing Java vs Node template creation...")
    
    # Test Java template (should work)
    java_result = test_template_creation("java-micronaut", "comparison")
    
    # Test Node template (should fail)
    node_result = test_template_creation("node-express", "comparison")
    
    print(f"\n📊 RESULTS SUMMARY:")
    print(f"   Java (java-micronaut): {java_result}")
    print(f"   Node (node-express): {node_result}")
    
    if java_result == "success" and node_result == "validation_error":
        print("\n🎯 CONCLUSION: Node template has validation regression")
        print("   Java template works fine, Node template fails validation")
        print("   This confirms the .env.local validation bug is specific to node-express")
    elif java_result == "success" and node_result == "success":
        print("\n✅ CONCLUSION: Both templates work - no regression")
    elif java_result != "success" and node_result != "success":
        print("\n❌ CONCLUSION: Both templates broken - platform issue")
    else:
        print(f"\n❓ CONCLUSION: Mixed results - needs investigation")

if __name__ == "__main__":
    main()