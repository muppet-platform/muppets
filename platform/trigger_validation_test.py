#!/usr/bin/env python3
"""
Trigger a node-express validation to generate logs we can check
"""

import requests
import json
import time

def trigger_validation_test():
    """Trigger node-express template validation to generate logs"""
    
    platform_url = "https://muppet-platform.s3u.dev"
    
    # Use a unique name to avoid conflicts
    timestamp = int(time.time())
    test_data = {
        "name": f"log-test-{timestamp}",
        "template": "node-express", 
        "description": "Test to generate validation logs"
    }
    
    print("🧪 Triggering node-express template validation...")
    print(f"📡 Platform URL: {platform_url}")
    print(f"📋 Test data: {json.dumps(test_data, indent=2)}")
    print(f"⏰ Timestamp: {timestamp}")
    
    try:
        print("\n📤 Making POST request...")
        response = requests.post(
            f"{platform_url}/api/v1/muppets",
            json=test_data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=30
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        # Parse response
        try:
            response_data = response.json()
            print(f"📝 Response: {json.dumps(response_data, indent=2)}")
        except Exception as e:
            print(f"📝 Response (raw): {response.text}")
        
        # Check for validation error
        if response.status_code >= 400:
            if "Missing core template files: .env.local" in str(response_data):
                print("\n🎯 VALIDATION ERROR CONFIRMED!")
                print("   The .env.local validation bug is still present")
                print("   Check CloudWatch logs for detailed validation logs")
                return "validation_error"
            else:
                print(f"\n⚠️  Different error: {response_data}")
                return "other_error"
        else:
            print("\n✅ No validation error occurred")
            return "success"
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return "request_failed"

def print_log_instructions():
    """Print instructions for checking CloudWatch logs"""
    print("\n📋 To check the validation logs:")
    print("1. Go to CloudWatch Logs: https://us-west-2.console.aws.amazon.com/cloudwatch/home?region=us-west-2#logsV2:log-groups")
    print("2. Look for log group: /ecs/muppet-platform")
    print("3. Check the most recent log stream")
    print("4. Search for log entries containing:")
    print("   - 'Validating template: node-express'")
    print("   - 'Template validation failed'")
    print("   - 'Missing core template files'")
    print("   - '.env.local'")
    print("\n🔍 Look for the timestamp around when this test ran")

if __name__ == "__main__":
    print("🔍 Triggering validation test to generate logs...")
    
    result = trigger_validation_test()
    
    print(f"\n🎯 Test result: {result}")
    
    if result == "validation_error":
        print("\n🐛 The validation bug is confirmed!")
        print("   This means the deployed platform does NOT have the validation fix")
    elif result == "success":
        print("\n✅ No validation error - the fix might be working")
    
    print_log_instructions()